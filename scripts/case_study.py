#!/usr/bin/env python3
"""Render the BM25-only / dense-only / both / neither examples as readable Markdown.

Reads `categories.json` from gold_categories.py (examples already chosen there by the
fixed rule) and writes, per example: track/domain, the full query (HTML stripped), for
Track 2 the conversation history, the beginning of the gold document, the gold document's
rank in each system, and each system's top 3 with snippets. A `Reading:` line is left for
the hand-written explanation, which is added afterwards and marked as preliminary.

    python3 case_study.py --data ../../reteco_data_v11 --cats ../research/runs_v12/categories \
        --bm25 ../research/runs_v12/bm25 --dense ../research/runs_v12/dense/bge-small_L512 \
        --out ../research/cases/examples_raw.md
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gold_categories import CATS, clean, fetch, topics  # noqa: E402
from hybrid import read_run  # noqa: E402

TITLE = {"bm25_only": "BM25-only", "dense_only": "Dense-only", "both": "Both", "neither": "Neither"}


def snip(text, n):
    t = clean(text)
    return t if len(t) <= n else t[:n] + " …"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--cats", required=True)
    ap.add_argument("--bm25", required=True)
    ap.add_argument("--dense", required=True)
    ap.add_argument("--split", default="dev")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rep = json.load(open(os.path.join(a.cats, "categories.json")))
    L = []
    for cat in CATS:
        L += [f"## {TITLE[cat]} (at k=100)", ""]
        for n, ex in enumerate(rep["examples"][cat], 1):
            tr, dom, cond, qid, g = ex["track"], ex["domain"], ex["cond"], ex["qid"], ex["doc"]
            pre = f"t{tr}_{dom}_{a.split}_{cond}.tsv"
            bm = read_run(os.path.join(a.bm25, f"t{tr}", "runs", pre))[qid]
            de = read_run(os.path.join(a.dense, f"t{tr}", "runs", pre))[qid]
            tops, gold = topics(a.data, tr, dom, a.split, cond)
            golds = gold[qid]
            texts = fetch(a.data, tr, dom, {g} | {d for d, _ in bm[:3]} | {d for d, _ in de[:3]} | set(golds))
            rb = "not in top 1000" if ex["bm25_rank"] is None else ex["bm25_rank"]
            rd = "not in top 1000" if ex["dense_rank"] is None else ex["dense_rank"]
            L += [f"### {TITLE[cat]} {n}: Track {tr}, `{dom}`, `{qid}` ({cond})", "",
                  f"Gold document `{g}` — **BM25 rank: {rb} · dense rank: {rd}** "
                  f"(this topic has {len(golds)} gold document(s))", ""]
            if tr == 2 and tops[qid].get("history"):
                L += [f"**Conversation so far (turn {tops[qid]['turn']}):** {snip(tops[qid]['history'], 900)}", ""]
            L += [f"**Query:** {clean(tops[qid]['query'])}", "",
                  f"**Gold document (beginning):** {snip(texts.get(g, '(missing)'), 600)}", ""]
            for label, run in (("BM25", bm), ("Dense (bge-small)", de)):
                L.append(f"**{label} top 3:**")
                for r, (d, s) in enumerate(run[:3], 1):
                    mark = " ✅ gold" if d in golds else ""
                    L.append(f"{r}. `{d}`{mark} — {snip(texts.get(d, ''), 220)}")
                L.append("")
            L += ["**Reading (preliminary, not human-validated):** ", "", "---", ""]
    with open(a.out, "w") as f:
        f.write("\n".join(L))
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
