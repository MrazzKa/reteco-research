#!/usr/bin/env python3
"""ANN vs exact dense search over the cached embeddings (dense_index.py), per domain, DEV.

  exact      GPU brute-force inner product (dense_search.py) — the reference
  faiss_flat FAISS IndexFlatIP on CPU, float32 — an independent exact cross-check
  faiss_hnsw FAISS HNSW (M=32, efConstruction=200, efSearch=128), inner product
  ngt        NGT ANNG graph (cosine), search epsilon 0.1  (Steve's ann-benchmarks pointer)

Reported: nDCG@10, recall@10 / recall@100 of each ANN list against the exact list,
index build seconds, mean query latency (single-threaded search for NGT and HNSW), peak RSS.
Vectors are float16 on disk and converted to float32 for FAISS/NGT.

    python3 ann_eval.py --data ../../reteco_data_v11 --kit ../../RETECO/starter_kit --track 2 \
        --domains all --emb ../research/runs_v12/emb --model bge-small --max-len 512 \
        --out ../research/runs_v12/ann/bge-small_L512_t2.json
"""
import argparse
import json
import os
import resource
import shutil
import sys
import tempfile
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bm25s_run import ndcg_fn  # noqa: E402
from dense_index import T1, T2, domain_dir  # noqa: E402
from dense_search import GpuIndex, plan  # noqa: E402
from embed_models import load_encoder  # noqa: E402

COND = {1: "1a", 2: "2a_current"}


def overlap(a, b, k):
    return sum(len(set(x[:k]) & set(y[:k])) / max(len(y[:k]), 1) for x, y in zip(a, b)) / len(a)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--kit", required=True)
    ap.add_argument("--track", type=int, required=True)
    ap.add_argument("--domains", nargs="+", default=["all"])
    ap.add_argument("--emb", required=True)
    ap.add_argument("--model", default="bge-small")
    ap.add_argument("--max-len", type=int, default=512)
    ap.add_argument("--k", type=int, default=100)
    ap.add_argument("--epsilon", type=float, default=0.1)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    import faiss
    import ngtpy
    import torch
    ndcg = ndcg_fn(a.kit)
    doms = (T1 if a.track == 1 else T2) if a.domains == ["all"] else a.domains
    enc = load_encoder(a.model, a.max_len)
    rep = json.load(open(a.out)) if os.path.exists(a.out) else {}
    sub = "track1_tempo" if a.track == 1 else "track2_recor"
    for dom in doms:
        if dom in rep:
            continue
        gi = GpuIndex(domain_dir(a.emb, a.model, a.max_len, a.track, dom))
        ids = gi.ids
        name, queries, gold = [p for p in plan(a.track, os.path.join(a.data, sub, dom), "dev")
                               if p[0] == COND[a.track]][0]
        uniq = sorted({q for _, q in queries})
        qe16 = enc.encode_queries(uniq)
        qe = qe16.astype(np.float32)
        t0 = time.time()
        exact = [[d for d, _ in r] for r in gi.search(qe16, a.k)]
        lat = {"exact_gpu": (time.time() - t0) / len(uniq)}
        mat = gi.mat.float().cpu().numpy()
        gi.free()
        res, build = {"exact_gpu": exact}, {}
        # FAISS flat (exact, CPU)
        t0 = time.time()
        fl = faiss.IndexFlatIP(mat.shape[1])
        fl.add(mat)
        build["faiss_flat"] = time.time() - t0
        t0 = time.time()
        _, I = fl.search(qe, a.k)
        lat["faiss_flat"] = (time.time() - t0) / len(uniq)
        res["faiss_flat"] = [[ids[j] for j in row] for row in I]
        del fl
        # FAISS HNSW
        faiss.omp_set_num_threads(8)
        t0 = time.time()
        hn = faiss.IndexHNSWFlat(mat.shape[1], 32, faiss.METRIC_INNER_PRODUCT)
        hn.hnsw.efConstruction = 200
        hn.add(mat)
        build["faiss_hnsw"] = time.time() - t0
        hn.hnsw.efSearch = 128
        faiss.omp_set_num_threads(1)
        t0 = time.time()
        _, I = hn.search(qe, a.k)
        lat["faiss_hnsw"] = (time.time() - t0) / len(uniq)
        res["faiss_hnsw"] = [[ids[j] for j in row] for row in I]
        del hn
        # NGT ANNG
        tmp = tempfile.mkdtemp()
        path = os.path.join(tmp, "ngt").encode()
        t0 = time.time()
        ngtpy.create(path, mat.shape[1], distance_type="Cosine")
        ix = ngtpy.Index(path)
        ix.batch_insert(mat, num_threads=8)
        build["ngt"] = time.time() - t0
        t0 = time.time()
        res["ngt"] = [[ids[h] for h, _ in ix.search(q, size=a.k, epsilon=a.epsilon)] for q in qe]
        lat["ngt"] = (time.time() - t0) / len(uniq)
        ix.close()
        shutil.rmtree(tmp)
        row_of = {q: i for i, q in enumerate(uniq)}
        out = {"docs": len(ids), "condition": name, "n_queries": len(uniq)}
        for label, lists in res.items():
            run = {qid: lists[row_of[q]] for qid, q in queries}
            nd = [ndcg(run.get(q, []), g, 10) for q, g in gold.items()]
            out[label] = {"ndcg10": round(sum(nd) / len(nd), 4),
                          "recall10_vs_exact": round(overlap(lists, exact, 10), 4),
                          "recall100_vs_exact": round(overlap(lists, exact, 100), 4),
                          "build_s": round(build.get(label, 0.0), 1),
                          "ms_per_query": round(1000 * lat[label], 2)}
        out["peak_rss_gb"] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2**20, 2)
        rep[dom] = out
        print(f"  [t{a.track}/{dom}] {len(ids):,} docs  " + "  ".join(
            f"{k}: nDCG {v['ndcg10']:.4f} R@10 {v['recall10_vs_exact']:.3f} build {v['build_s']}s "
            f"{v['ms_per_query']}ms" for k, v in out.items() if isinstance(v, dict)), flush=True)
        json.dump(rep, open(a.out, "w"), indent=1)
        del mat
        torch.cuda.empty_cache()
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
