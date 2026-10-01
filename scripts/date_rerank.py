#!/usr/bin/env python3
"""E2: explicit-date reranking of a Track-1a BM25 run (first version, no tuning).

Rule (fixed in advance, one variable: rerank on/off):
  * take the retrieval run's top-`depth` documents for a query;
  * if the query states no explicit year, leave the ranking untouched;
  * otherwise stable-sort the top-`depth` so that documents stating a year inside
    the query's [min-1, max+1] span come first, keeping the retriever's order
    inside each group.

No weights, no thresholds, nothing fitted. Develop on train; report dev once.

    python3 date_rerank.py --data ../../reteco_data_v11 --kit ../../RETECO/starter_kit \
        --split train --runs ../research/runs_v11/track1_lucene/runs \
        --out ../research/runs_v11/e2_dates_train.json
"""
import argparse
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from week1_run import load_qrels, read_jsonl  # noqa: E402
from bm25s_run import ndcg_fn  # noqa: E402
from date_feasibility import years  # noqa: E402

MODES = ["hard", "top20", "top10", "rrf"]

DOMAINS = ["bitcoin", "cardano", "economics", "genealogy", "history", "hsm", "iota",
           "law", "monero", "politics", "quant", "travel", "workplace"]


def read_run(path):
    out = defaultdict(list)
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                qid, _, doc, *_ = line.split()
                out[qid].append(doc)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--kit", required=True)
    ap.add_argument("--split", default="train", choices=("train", "dev"))
    ap.add_argument("--runs", required=True, help="directory with t1_<dom>_<split>_1a.tsv")
    ap.add_argument("--depth", type=int, default=100)
    ap.add_argument("--domains", nargs="+", default=DOMAINS)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    ndcg = ndcg_fn(a.kit)

    rows = []
    for dom in a.domains:
        run_path = os.path.join(a.runs, f"t1_{dom}_{a.split}_1a.tsv")
        if not os.path.exists(run_path):
            print(f"skip {dom}: no run file", flush=True)
            continue
        d = os.path.join(a.data, "track1_tempo", dom)
        run = read_run(run_path)
        gold = load_qrels(os.path.join(d, f"qrels_{a.split}.txt"))
        qyears = {r["id"]: years(r["query"])
                  for r in read_jsonl(os.path.join(d, f"examples_{a.split}.jsonl"))}
        wanted = {doc for qid in gold for doc in run.get(qid, [])[:a.depth]}
        doc_years = {}
        with open(os.path.join(d, "documents.jsonl"), encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    rec = json.loads(line)
                    if rec["id"] in wanted:
                        doc_years[rec["id"]] = years(rec.get("content", "") or "")

        before, touched = [], 0
        after = {m: [] for m in MODES}
        for qid, g in gold.items():
            ranked = run.get(qid, [])[:a.depth]
            before.append(ndcg(ranked[:10], g, 10))
            qy = qyears.get(qid, set())
            if not qy:
                for m in MODES:
                    after[m].append(before[-1])
                continue
            touched += 1
            lo, hi = min(qy) - 1, max(qy) + 1
            dated = {doc for doc in ranked
                     if any(lo <= y <= hi for y in doc_years.get(doc, ()))}
            for m in MODES:
                if m == "hard":                      # promote over the whole top-100
                    window = len(ranked)
                elif m == "top20":                   # reorder only the visible head
                    window = 20
                else:                                # top10
                    window = 10
                if m == "rrf":                       # blend both orders instead
                    date_order = ([d for d in ranked if d in dated]
                                  + [d for d in ranked if d not in dated])
                    fused = defaultdict(float)
                    for order in (ranked, date_order):
                        for rank, doc in enumerate(order, 1):
                            fused[doc] += 1.0 / (60 + rank)
                    new = [d for d, _ in sorted(fused.items(), key=lambda x: (-x[1], x[0]))]
                else:
                    head = ranked[:window]
                    new = ([d for d in head if d in dated]
                           + [d for d in head if d not in dated] + ranked[window:])
                after[m].append(ndcg(new[:10], g, 10))
        n = len(before)
        row = {"domain": dom, "n": n, "dated_queries": touched,
               "before": round(sum(before) / n, 4) if n else 0.0}
        for m in MODES:
            row[m] = round(sum(after[m]) / n, 4) if n else 0.0
            row[m + "_delta"] = round(row[m] - row["before"], 4)
        rows.append(row)
        print(f"{dom:12s} n={n:4d} dated={touched:4d} base {row['before']:.4f}  "
              + "  ".join(f"{m} {row[m + '_delta']:+.4f}" for m in MODES), flush=True)

    macro_b = sum(r["before"] for r in rows) / len(rows)
    macros = {m: sum(r[m] for r in rows) / len(rows) for m in MODES}
    summary = {"split": a.split, "depth": a.depth, "rows": rows,
               "macro_before": round(macro_b, 4),
               "macro": {m: round(v, 4) for m, v in macros.items()},
               "macro_delta": {m: round(v - macro_b, 4) for m, v in macros.items()}}
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    print(f"\nmacro base {macro_b:.4f}; "
          + "; ".join(f"{m} {macros[m]:.4f} ({macros[m] - macro_b:+.4f})" for m in MODES)
          + f"\nwrote {a.out}")


if __name__ == "__main__":
    main()
