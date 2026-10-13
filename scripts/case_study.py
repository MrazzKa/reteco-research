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


def pct(c, k):
    n = sum(c.values())
    return n, [f"{c[x]} ({100 * c[x] / n:.1f}%)" for x in CATS]


def tables(rep):
    """Category counts: overall by track/condition at k=10/100, then per domain."""
    c = rep["counts"]
    head = "| " + " | ".join(TITLE[x] for x in CATS) + " |"
    L = ["## 1. How many gold documents each system finds (dev, all domains)", "",
         "Unit: one (topic, gold document) pair. A gold document is *found* by a system if it is "
         "in that system's top k.", "",
         "| track | condition | k | gold pairs " + head, "| --- | --- | ---: | ---: |" + " ---: |" * 4]
    for key in sorted(k for k in c if "|ALL|" in k):
        tr, cond, _, k = key.split("|")
        n, cells = pct(c[key], k)
        L.append(f"| {tr} | {cond} | {k} | {n} | " + " | ".join(cells) + " |")
    L.append("")
    for cond in ("1a", "1b_query+step", "2a_current", "2a_history"):
        tr = "1" if cond.startswith("1") else "2"
        doms = sorted({k.split("|")[2] for k in c if k.startswith(f"{tr}|{cond}|") and "|ALL|" not in k})
        L += [f"### Per domain — Track {tr} `{cond}`", "",
              "| domain | gold pairs | k=10: " + " | ".join(TITLE[x] for x in CATS)
              + " | k=100: " + " | ".join(TITLE[x] for x in CATS) + " |",
              "| --- | ---: |" + " ---: |" * 8]
        for dom in doms:
            n, c10 = pct(c[f"{tr}|{cond}|{dom}|10"], 10)
            _, c100 = pct(c[f"{tr}|{cond}|{dom}|100"], 100)
            L.append(f"| {dom} | {n} | " + " | ".join(c10) + " | " + " | ".join(c100) + " |")
        L.append("")
    f = rep["features_k100"]
    L += ["## 2. What separates the categories (all pairs, k=100)", "",
          "Means over every pair in the category (not just the examples). `overlap` = share of the "
          "query's content stems found in the gold document; `overlap in window` = same, counting "
          f"only the first ~{int(0.75 * rep['window'])} words the encoder sees; `match only beyond "
          "window` = overlap rises by more than 0.1 once the rest of the document is counted.", "",
          "| track / condition | category | pairs | overlap | overlap in window | gold words | "
          "gold longer than window | match only beyond window | query has a number | its numbers found in gold |",
          "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for key in sorted(f):
        tr, cond, cat = key.split("|")
        v = f[key]
        nh = "" if v.get("nums_hit") is None else f"{v['nums_hit']:.2f}"
        L.append(f"| {tr} `{cond}` | {TITLE[cat]} | {v['n']} | {v['overlap']:.2f} | {v['overlap_win']:.2f} | "
                 f"{v['gold_words']:.0f} | {v['gold_beyond_window']:.2f} | {v['match_only_beyond_window']:.2f} | "
                 f"{v['q_nums']:.2f} | {nh} |")
    return L + [""]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--cats", required=True)
    ap.add_argument("--bm25", required=True)
    ap.add_argument("--dense", required=True)
    ap.add_argument("--split", default="dev")
    ap.add_argument("--readings", help="JSON {\"<category>|<n>\": text} of hand-written readings")
    ap.add_argument("--intro", help="Markdown file placed before the generated tables")
    ap.add_argument("--outro", help="Markdown file appended after the examples")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rep = json.load(open(os.path.join(a.cats, "categories.json")))
    readings = json.load(open(a.readings)) if a.readings else {}
    L = open(a.intro).read().rstrip().split("\n") + [""] if a.intro else []
    L += tables(rep)
    L += ["## 3. Examples (dev, category at k=100, fixed-seed sample)", ""]
    for cat in CATS:
        L += [f"### 3.{CATS.index(cat) + 1} {TITLE[cat]}", ""]
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
            L += [f"#### {TITLE[cat]} {n}: Track {tr}, `{dom}`, `{qid}` ({cond})", "",
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
            L += [f"**Reading (preliminary, not human-validated):** {readings.get(f'{cat}|{n}', '')}",
                  "", "---", ""]
    if a.outro:
        L += open(a.outro).read().rstrip().split("\n")
    with open(a.out, "w") as f:
        f.write("\n".join(L))
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
