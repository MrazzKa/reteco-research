#!/usr/bin/env python3
"""Compact sheet of a larger fixed-seed sample per category, for rough error-type counts.

Same rule as gold_categories.py (conditions 1a / 2a_current, category at k=100, pairs
sorted, random.Random(20260921).shuffle, one pair per query), but `--n` per track and
the examples already shown in the case study are skipped. Each row shows the query, the
gold document's beginning and both systems' top-1, so a reader can assign a preliminary
error type. Labels are written by hand into research/cases/, never fed back to a system.

    python3 label_sample.py --data ../../reteco_data_v11 --cats ../research/runs_v12/categories \
        --bm25 ../research/runs_v12/bm25 --dense ../research/runs_v12/dense/bge-small_L512 \
        --category neither --n 8 --out ../research/runs_v12/categories/sheet_neither.md
"""
import argparse
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from case_study import snip  # noqa: E402
from gold_categories import EXAMPLE_COND, SEED, fetch, topics  # noqa: E402
from hybrid import read_run  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--cats", required=True)
    ap.add_argument("--bm25", required=True)
    ap.add_argument("--dense", required=True)
    ap.add_argument("--category", required=True)
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    shown = {(e["track"], e["domain"], e["qid"])
             for e in json.load(open(os.path.join(a.cats, "categories.json")))["examples"][a.category]}
    pairs = [json.loads(x) for x in open(os.path.join(a.cats, "pairs.jsonl"))]
    pool = sorted([p for p in pairs if p["cond"] == EXAMPLE_COND[p["track"]] and p["cat100"] == a.category],
                  key=lambda p: (p["track"], p["domain"], p["qid"], p["doc"]))
    random.Random(SEED).shuffle(pool)
    chosen, used = [], set(shown)
    for track in (1, 2):
        n = 0
        for p in pool:
            key = (p["track"], p["domain"], p["qid"])
            if p["track"] == track and key not in used and n < a.n:
                chosen.append(p)
                used.add(key)
                n += 1
    L = [f"# Labelling sheet — {a.category} at k=100 ({len(chosen)} pairs, seed {SEED}, "
         f"examples already in the case study skipped)", ""]
    for i, p in enumerate(chosen, 1):
        tr, dom, qid, g = p["track"], p["domain"], p["qid"], p["doc"]
        pre = f"t{tr}_{dom}_dev_{p['cond']}.tsv"
        bm = read_run(os.path.join(a.bm25, f"t{tr}", "runs", pre))[qid]
        de = read_run(os.path.join(a.dense, f"t{tr}", "runs", pre))[qid]
        tops, _ = topics(a.data, tr, dom, "dev", p["cond"])
        texts = fetch(a.data, tr, dom, {g, bm[0][0], de[0][0]})
        L += [f"## {i}. T{tr} `{dom}` `{qid}` — gold `{g}` · BM25 rank {p['bm25_rank']} · dense rank {p['dense_rank']}",
              ""]
        if tr == 2 and tops[qid].get("history"):
            L.append(f"- history: {snip(tops[qid]['history'], 300)}")
        L += [f"- query: {snip(tops[qid]['query'], 500)}",
              f"- gold: {snip(texts.get(g, ''), 400)}",
              f"- BM25 #1: {snip(texts.get(bm[0][0], ''), 200)}",
              f"- dense #1: {snip(texts.get(de[0][0], ''), 200)}", "", "label: ", ""]
    open(a.out, "w").write("\n".join(L))
    print(f"wrote {a.out} ({len(chosen)} pairs)")


if __name__ == "__main__":
    main()
