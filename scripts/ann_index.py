#!/usr/bin/env python3
"""Dense retrieval over a whole domain corpus: exact search vs an NGT ANN index.

Steve's week-2 note: move the encoders from reranking to retrieval, with an ANN
index over the embedding vectors (ann-benchmarks). This script does that and
reports what the approximation costs:

  * embeds the corpus once and caches the vectors (`<out>/emb/<domain>.npy`);
  * `exact`  — brute-force cosine over all vectors: the quality ceiling of this
    encoder and the reference the ANN index is measured against;
  * `ann`    — NGT (ANNG graph, cosine) with the same vectors;
  * reports nDCG@10 for both, recall@10 of ANN against exact, index build time
    and per-query latency.

    python3 ann_index.py --data ../../reteco_data_v11 --kit ../../RETECO/starter_kit \
        --split dev --track 1 --domains iota --model bge-small \
        --out ../research/runs_v11/ann
"""
import argparse
import json
import os
import shutil
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from week1_run import write_run  # noqa: E402
from bm25s_run import by_turn, ndcg_fn, score  # noqa: E402
from dense_run import MODELS, corpus, encode, load_model, plan_track1, plan_track2  # noqa: E402


def embed_corpus(model, dprefix, path, key, cache, batch, label):
    if os.path.exists(cache + ".npy") and os.path.exists(cache + ".ids.json"):
        emb = np.load(cache + ".npy")
        ids = json.load(open(cache + ".ids.json", encoding="utf-8"))
        print(f"    reusing cached embeddings: {emb.shape}", flush=True)
        return emb, ids, 0.0
    ids, texts = corpus(path, key)
    t0 = time.time()
    emb = encode(model, texts, dprefix, batch, label)
    took = time.time() - t0
    os.makedirs(os.path.dirname(cache), exist_ok=True)
    np.save(cache + ".npy", emb)
    json.dump(ids, open(cache + ".ids.json", "w", encoding="utf-8"))
    return emb, ids, took


def exact_search(emb, ids, qemb, k):
    t0 = time.time()
    out = []
    for s in range(0, len(qemb), 64):
        sims = qemb[s:s + 64] @ emb.T
        idx = np.argpartition(-sims, min(k, sims.shape[1] - 1), axis=1)[:, :k]
        for r in range(idx.shape[0]):
            order = idx[r][np.argsort(-sims[r, idx[r]])]
            out.append([(ids[j], float(sims[r, j])) for j in order])
    return out, (time.time() - t0) / max(len(qemb), 1)


def ann_search(emb, ids, qemb, k, path, epsilon):
    import ngtpy
    if os.path.exists(path):
        shutil.rmtree(path)
    t0 = time.time()
    ngtpy.create(path.encode(), emb.shape[1], distance_type="Cosine")
    index = ngtpy.Index(path.encode())
    index.batch_insert(emb, num_threads=os.cpu_count())
    index.save()
    build = time.time() - t0
    t0 = time.time()
    out = []
    for q in qemb:
        hits = index.search(q, size=k, epsilon=epsilon)
        out.append([(ids[i], 1.0 - float(d)) for i, d in hits])
    return out, build, (time.time() - t0) / max(len(qemb), 1)


def recall_at_k(ann, exact, k=10):
    vals = []
    for a, e in zip(ann, exact):
        gold = {d for d, _ in e[:k]}
        if gold:
            vals.append(len({d for d, _ in a[:k]} & gold) / len(gold))
    return sum(vals) / len(vals) if vals else float("nan")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--kit", required=True)
    ap.add_argument("--split", default="dev", choices=("train", "dev"))
    ap.add_argument("--track", type=int, required=True, choices=(1, 2))
    ap.add_argument("--domains", nargs="+", required=True)
    ap.add_argument("--model", default="bge-small", choices=sorted(MODELS))
    ap.add_argument("--max-len", type=int, default=256)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--k", type=int, default=100)
    ap.add_argument("--epsilon", type=float, default=0.1, help="NGT search range; higher = more accurate, slower")
    ap.add_argument("--conditions", nargs="*")
    ap.add_argument("--device", help='force "cpu" or "cuda"; default: cuda when available')
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    ndcg = ndcg_fn(a.kit)
    runs_dir = os.path.join(a.out, "runs")
    os.makedirs(runs_dir, exist_ok=True)
    results_path = os.path.join(a.out, "results.json")
    results = json.load(open(results_path, encoding="utf-8")) if os.path.exists(results_path) else []
    model, qprefix, dprefix = load_model(a.model, a.max_len, a.device)
    prefix = "t1" if a.track == 1 else "t2"
    sub = "track1_tempo" if a.track == 1 else "track2_recor"
    key = "id" if a.track == 1 else "doc_id"

    for dom in a.domains:
        d = os.path.join(a.data, sub, dom)
        print(f"\n[{prefix} / {dom} / dense-{a.model}]", flush=True)
        emb, ids, enc_time = embed_corpus(
            model, dprefix, os.path.join(d, "documents.jsonl"), key,
            os.path.join(a.out, "emb", f"{dom}_{a.model}"), a.batch, f"{dom} corpus")
        plan = plan_track1(d, a.split) if a.track == 1 else plan_track2(d, a.split)
        plan = [p for p in plan if not a.conditions or p[0] in a.conditions]
        ann_path = os.path.join(a.out, "index", f"{dom}_{a.model}")
        os.makedirs(os.path.dirname(ann_path), exist_ok=True)
        build_time = None
        for name, queries, gold in plan:
            if not queries:
                continue
            uniq = sorted({q for _, q in queries})
            qemb = encode(model, uniq, qprefix, a.batch, f"{name} queries")
            row_of = {q: i for i, q in enumerate(uniq)}
            ex, ex_lat = exact_search(emb, ids, qemb, a.k)
            an, build, an_lat = ann_search(emb, ids, qemb, a.k, ann_path, a.epsilon)
            build_time = build if build_time is None else build_time
            for label, lists, lat in (("dense_exact", ex, ex_lat), ("dense_ann", an, an_lat)):
                run = {qid: lists[row_of[q]] for qid, q in queries}
                write_run(os.path.join(runs_dir, f"{prefix}_{dom}_{a.split}_{name}_{label}.tsv"),
                          run, f"{a.model}_{label}")
                m, per = score(run, gold, ndcg)
                row = {"track": a.track, "domain": dom, "split": a.split,
                       "run": f"{name}_{label}", "n": len(gold), "ndcg10": round(m, 4),
                       "system": f"{label}-{a.model}", "docs": len(ids),
                       "query_latency_s": round(lat, 4), "encode_s": round(enc_time, 1)}
                if label == "dense_ann":
                    row["recall10_vs_exact"] = round(recall_at_k(an, ex), 4)
                    row["index_build_s"] = round(build, 1)
                    row["epsilon"] = a.epsilon
                if a.track == 2:
                    row["by_turn"] = by_turn(per)
                results.append(row)
                print(f"      -> {name} {label}: nDCG@10 {m:.4f}  {lat * 1000:.1f} ms/query"
                      + (f"  recall@10 vs exact {row['recall10_vs_exact']:.3f}"
                         f"  build {build:.0f}s" if label == "dense_ann" else ""), flush=True)
            with open(results_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=1)
    print(f"\nwrote {results_path}", flush=True)


if __name__ == "__main__":
    main()
