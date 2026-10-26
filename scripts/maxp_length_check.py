#!/usr/bin/env python3
"""Are long documents (those with passages beyond the first window) gold more often? (LOG 2026-10-26 MaxP caveat)

Per Track-2 domain: documents with extra passages (passage_index.py maps), train+dev gold, and
their overlap. Also the MaxP gain of plain dense retrieval per domain (qexp vs maxp runs, query q).

    python3 maxp_length_check.py --out ../research/runs_v13/maxp/length_gold.json
"""
import argparse
import glob
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dense_index import T2, domain_dir, load_cache  # noqa: E402
from week1_run import load_qrels  # noqa: E402

R = "../research/runs_v13"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="../../reteco_data_v11")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    base = {(r["split"], r["domain"]): r["ndcg10"] for r in json.load(open(f"{R}/qexp/t2/results.json"))
            if r["system"] == "dense" and r["variant"] == "q"}
    maxp = {(r["split"], r["domain"]): r["ndcg10"] for r in json.load(open(f"{R}/maxp/t2/results.json"))
            if r["system"] == "dense" and r["variant"] == "q"}
    out = {}
    for dom in T2:
        ids, _, _ = load_cache(domain_dir("../research/runs_v12/emb", "bge-base", 512, 2, dom))
        rows = set()
        for p in sorted(glob.glob(f"{R}/emb/bge-base_P510s382/t2/{dom}/shard_*.map.npy")):
            rows |= set(np.load(p).tolist())
        long_ = {ids[r] for r in rows}
        gold = set()
        for sp in ("train", "dev"):
            for g in load_qrels(os.path.join(a.data, "track2_recor", dom, f"qrels_{sp}.txt")).values():
                gold |= g
        out[dom] = {"docs": len(ids), "long_docs": len(long_), "gold": len(gold), "gold_and_long": len(gold & long_),
                    "share_long_that_is_gold": round(len(gold & long_) / max(len(long_), 1), 3),
                    "share_gold_that_is_long": round(len(gold & long_) / max(len(gold), 1), 3),
                    "share_corpus_long": round(len(long_) / len(ids), 4),
                    "dense_q_gain_train": round(maxp[("train", dom)] - base[("train", dom)], 4),
                    "dense_q_gain_dev": round(maxp[("dev", dom)] - base[("dev", dom)], 4)}
        print(dom, out[dom])
    json.dump(out, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
