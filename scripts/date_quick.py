#!/usr/bin/env python3
"""Fast explicit-date feasibility on Track-1 TRAIN, without BM25.

Same regexes as date_feasibility.py. Instead of BM25 non-gold top-10 (slow on the
large corpora), the contrast is a fixed random sample of corpus documents
(seed 0, 2,000 per domain). Random documents are an easier contrast than BM25
top-10 negatives, so a gold-vs-random gap is an upper bound on what a date
reranker could exploit.
"""
import argparse
import json
import random
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from date_feasibility import years

SAMPLE = 2000


def one(domain_dir):
    domain_dir = Path(domain_dir)
    queries = [json.loads(l) for l in (domain_dir / "examples_train.jsonl").open(encoding="utf-8") if l.strip()]
    gold_ids = {g for q in queries for g in q["gold_ids"]}
    gold_years, sample, seen = {}, [], 0
    rng = random.Random(0)
    with (domain_dir / "documents.jsonl").open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            seen += 1
            doc = json.loads(line)
            if doc["id"] in gold_ids:
                gold_years[doc["id"]] = years(doc.get("content", ""))
            # reservoir sample of corpus documents
            if len(sample) < SAMPLE:
                sample.append(doc.get("content", ""))
            else:
                j = rng.randrange(seen)
                if j < SAMPLE:
                    sample[j] = doc.get("content", "")
    sample_years = [years(t) for t in sample]
    c = dict(n=len(queries), q_dated=0, gold=0, gold_dated=0, rand=len(sample_years),
             rand_dated=sum(bool(y) for y in sample_years),
             ov_gold_n=0, ov_gold=0, ov_rand_n=0, ov_rand=0)
    distinct = []
    for q in queries:
        qy = years(q["query"])
        distinct.append(len(qy))
        c["q_dated"] += bool(qy)
        gold = q["gold_ids"]
        c["gold"] += len(gold)
        c["gold_dated"] += sum(bool(gold_years.get(g)) for g in gold)
        if qy:
            lo, hi = min(qy) - 1, max(qy) + 1
            c["ov_gold_n"] += len(gold)
            c["ov_gold"] += sum(any(lo <= y <= hi for y in gold_years.get(g, ())) for g in gold)
            c["ov_rand_n"] += len(sample_years)
            c["ov_rand"] += sum(any(lo <= y <= hi for y in ys) for ys in sample_years)
    d = sorted(distinct)
    c["median_years"] = (d[(len(d) - 1) // 2] + d[len(d) // 2]) / 2 if d else 0
    print(f"{domain_dir.name}: {c['n']} train queries, {seen} docs", flush=True)
    return domain_dir.name, c


def pct(a, b):
    return f"{a / b:.1%}" if b else "n/a"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    dirs = sorted(p for p in (a.data / "track1_tempo").iterdir() if p.is_dir())
    with ProcessPoolExecutor(a.workers) as ex:
        rows = sorted(ex.map(one, map(str, dirs)))
    keys = ["n", "q_dated", "gold", "gold_dated", "rand", "rand_dated", "ov_gold_n", "ov_gold", "ov_rand_n", "ov_rand"]
    tot = {k: sum(c[k] for _, c in rows) for k in keys}
    lines = ["| domain | train queries | queries dated | gold dated | random-corpus dated | median years/query | gold span overlap | random span overlap |",
             "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for name, c in rows + [("**all (micro)**", tot)]:
        med = f"{c['median_years']:g}" if "median_years" in c else ""
        lines.append(f"| {name} | {c['n']} | {pct(c['q_dated'], c['n'])} | {pct(c['gold_dated'], c['gold'])} | "
                     f"{pct(c['rand_dated'], c['rand'])} | {med} | {pct(c['ov_gold'], c['ov_gold_n'])} | "
                     f"{pct(c['ov_rand'], c['ov_rand_n'])} |")
    a.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    json.dump(dict(rows), open(a.out.with_suffix(".json"), "w"), indent=1)
    print(f"wrote {a.out}")


if __name__ == "__main__":
    sys.exit(main())
