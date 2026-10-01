#!/usr/bin/env python3
"""Rerank a BM25 run's top-k with a dense encoder (CPU-affordable everywhere).

Two systems are reported per condition:
  * `<cond>_rerank`  — dense cosine over the BM25 top-k, nothing else;
  * `<cond>_rrf`     — reciprocal-rank fusion of the BM25 order and that reranking.

Only documents inside the BM25 top-k are ever scored, so recall is capped by BM25;
that cap is reported as `recall_cap` (nDCG@10 of an oracle that puts every gold
document found in the top-k first).

    python3 dense_rerank.py --data ../../reteco_data_v11 --kit ../../RETECO/starter_kit \
        --split dev --track 1 --domains iota quant --model bge-small \
        --runs ../research/runs_v11/track1_lucene/runs --out ../research/runs_v11/rerank_bge
"""
import argparse
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from week1_run import load_qrels, write_run  # noqa: E402
from bm25s_run import by_turn, ndcg_fn, score  # noqa: E402
from dense_run import MODELS, encode, load_model, plan_track1, plan_track2, rrf  # noqa: E402


def read_run_scored(path, depth):
    out = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                qid, _, doc, rank, sc, *_ = line.split()
                out.setdefault(qid, [])
                if len(out[qid]) < depth:
                    out[qid].append(doc)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--kit", required=True)
    ap.add_argument("--split", default="dev", choices=("train", "dev"))
    ap.add_argument("--track", type=int, required=True, choices=(1, 2))
    ap.add_argument("--domains", nargs="+", required=True)
    ap.add_argument("--model", default="bge-small", choices=sorted(MODELS))
    ap.add_argument("--runs", required=True, help="directory with the BM25 run files")
    ap.add_argument("--depth", type=int, default=100)
    ap.add_argument("--max-len", type=int, default=256)
    ap.add_argument("--batch", type=int, default=64)
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
        print(f"\n[{prefix} / {dom} / rerank-{a.model}]", flush=True)
        plan = plan_track1(d, a.split) if a.track == 1 else plan_track2(d, a.split)
        plan = [p for p in plan if not a.conditions or p[0] in a.conditions]
        bm = {}
        for name, _, _ in plan:
            path = os.path.join(a.runs, f"{prefix}_{dom}_{a.split}_{name}.tsv")
            if os.path.exists(path):
                bm[name] = read_run_scored(path, a.depth)
        if not bm:
            print("    no BM25 runs found, skipping", flush=True)
            continue

        wanted = {doc for run in bm.values() for ranked in run.values() for doc in ranked}
        t0 = time.time()
        ids, texts = [], []
        with open(os.path.join(d, "documents.jsonl"), encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    rec = json.loads(line)
                    if rec[key] in wanted:
                        ids.append(rec[key])
                        texts.append(rec.get("content", "") or "")
        print(f"    {len(ids):,} candidate docs read in {time.time() - t0:.0f}s", flush=True)
        emb = encode(model, texts, dprefix, a.batch, f"{dom} candidates")
        del texts
        pos = {doc: i for i, doc in enumerate(ids)}

        for name, queries, gold in plan:
            if name not in bm:
                continue
            uniq = sorted({q for _, q in queries})
            qemb = encode(model, uniq, qprefix, a.batch, f"{name} queries")
            qrow = {q: i for i, q in enumerate(uniq)}
            reranked, fused = {}, {}
            for qid, qtext in queries:
                cand = bm[name].get(qid, [])
                if not cand:
                    reranked[qid], fused[qid] = [], []
                    continue
                rows = np.array([pos[c] for c in cand])
                sims = emb[rows] @ qemb[qrow[qtext]]
                order = np.argsort(-sims)
                reranked[qid] = [(cand[i], float(sims[i])) for i in order]
                fused[qid] = rrf([[cand[i] for i in order], cand], depth=a.depth)
            for label, run in (("rerank", reranked), ("rrf", fused)):
                write_run(os.path.join(runs_dir, f"{prefix}_{dom}_{a.split}_{name}_{label}.tsv"),
                          run, f"{a.model}_{label}")
                m, per = score(run, gold, ndcg)
                row = {"track": a.track, "domain": dom, "split": a.split,
                       "run": f"{name}_{label}", "n": len(gold), "ndcg10": round(m, 4),
                       "system": f"{label}-{a.model}+bm25s", "depth": a.depth}
                if a.track == 2:
                    row["by_turn"] = by_turn(per)
                results.append(row)
                print(f"      -> {name} {label}: {m:.4f}", flush=True)
            # recall ceiling of the candidate set
            cap = {qid: [(doc, 1.0) for doc in bm[name].get(qid, []) if doc in gold.get(qid, set())]
                   for qid, _ in queries}
            mcap, _ = score(cap, gold, ndcg)
            results.append({"track": a.track, "domain": dom, "split": a.split,
                            "run": f"{name}_recall_cap", "n": len(gold),
                            "ndcg10": round(mcap, 4), "system": f"oracle-cap-top{a.depth}"})
            print(f"      -> {name} recall cap (oracle over BM25 top-{a.depth}): {mcap:.4f}",
                  flush=True)
            with open(results_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=1)
        del emb
    print(f"\nwrote {results_path}", flush=True)


if __name__ == "__main__":
    main()
