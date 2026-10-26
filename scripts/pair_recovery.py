#!/usr/bin/env python3
"""Week-4 dev gold categories (BM25-only / dense-only / both / neither at depth 100) under a new system.

Reads research/runs_v12/categories/pairs.jsonl (dev, bge-small L512 + BM25, one row per
(topic, gold document)) and, for every listed system, whether each gold document is in its
top 100 (and top 10). A system is (label, BM25 run dir, dense run dir, run-file condition,
hybrid report, condition in the report): its hybrid list is recomputed with the frozen
`linear*` configuration; its BM25 and dense lists are read from the run files.

Also splits BM25-only pairs into "match only beyond the window" (query-stem overlap rises by
> 0.1 once text past the encoder window is counted) and the rest, as in the week-4 case study.

    python3 pair_recovery.py --sys base=../research/runs_v13/qexp/t2/bm25/runs,...  --out out.json
"""
import argparse
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hybrid import Query, read_run, system  # noqa: E402

PAIRS = "../research/runs_v12/categories/pairs.jsonl"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sys", nargs="+", required=True,
                    help="label=cond:bm25dir:densedir:runcond:hybrid.json:reportcond (track inferred from cond)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    pairs = [json.loads(x) for x in open(PAIRS) if x.strip()]
    out = {}
    for spec in a.sys:
        label, rest = spec.split("=", 1)
        cond, bdir, ddir, rcond, hrep, hcond = rest.split(":")
        track = 1 if cond.startswith("1") else 2
        cfg = json.load(open(hrep))["conditions"][hcond]["systems"]["linear*"]["cfg"]
        sel = [p for p in pairs if p["cond"] == cond]
        cache = {}
        acc = defaultdict(lambda: defaultdict(int))
        for p in sel:
            dom = p["domain"]
            if dom not in cache:
                pre = f"t{track}_{dom}_dev_{rcond}"
                cache[dom] = (read_run(os.path.join(bdir, pre + ".tsv")), read_run(os.path.join(ddir, pre + ".tsv")))
            bm, de = cache[dom]
            q = Query(bm.get(p["qid"], []), de.get(p["qid"], []))
            h = system(q, cfg)
            cats = [p["cat100"]]
            if p["cat100"] == "bm25_only":
                cats.append("bm25_only|beyond_window" if p["overlap"] > p["overlap_win"] + 0.1 else "bm25_only|within")
            for c in cats + ["all"]:
                r = acc[c]
                r["n"] += 1
                r["hybrid@100"] += p["doc"] in h[:100]
                r["hybrid@10"] += p["doc"] in h[:10]
                r["bm25@100"] += p["doc"] in [d for d, _ in q.bm[:100]]
                r["dense@100"] += p["doc"] in [d for d, _ in q.de[:100]]
        out[label] = {"cond": cond, "cfg": cfg, "by_category": {c: dict(v) for c, v in acc.items()}}
        print(f"== {label} ({cond})")
        for c in sorted(acc):
            v = acc[c]
            print(f"  {c:<26} n {v['n']:>4}  hybrid@100 {v['hybrid@100']:>4}  hybrid@10 {v['hybrid@10']:>4}  "
                  f"bm25@100 {v['bm25@100']:>4}  dense@100 {v['dense@100']:>4}")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(out, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
