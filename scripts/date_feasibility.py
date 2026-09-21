#!/usr/bin/env python3
"""Measure explicit temporal expressions in Track-1 train retrieval data."""
import argparse
import json
import re
from pathlib import Path

from week1_run import FastBM25, _load_kit, load_qrels

YEAR = re.compile(r"\b(?:1[5-9]\d\d|20\d\d)\b")
DECADE = re.compile(r"\b(?:1[5-9]\d0s|20\d0s)\b", re.I)
MONTH_YEAR = re.compile(
    r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|"
    r"Dec(?:ember)?)\s+(?:1[5-9]\d\d|20\d\d)\b", re.I)


def years(text):
    found = {int(m.group()) for m in YEAR.finditer(text)}
    found.update(int(m.group()[:4]) for m in DECADE.finditer(text))
    found.update(int(m.group()[-4:]) for m in MONTH_YEAR.finditer(text))
    return found


def pct(n, d):
    return f"{n / d:.1%}" if d else "n/a"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--kit", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    bm25, _ = _load_kit(str(a.kit))
    rows = []
    totals = [0] * 11
    for domain_dir in sorted((a.data / "track1_tempo").iterdir()):
        if not domain_dir.is_dir():
            continue
        queries = [json.loads(line) for line in
                   (domain_dir / "examples_train.jsonl").open(encoding="utf-8") if line.strip()]
        gold = load_qrels(domain_dir / "qrels_train.txt")
        index = FastBM25(bm25.tokenize)
        doc_years = {}
        with (domain_dir / "documents.jsonl").open(encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    doc = json.loads(line)
                    index.add(doc["id"], doc.get("content", ""))
                    doc_years[doc["id"]] = years(doc.get("content", ""))
        index.finalize()
        # Counts use query-document pairs, so a passage relevant to two queries counts twice.
        c = [0] * 11
        query_distinct = []
        for rec in queries:
            qid, qyears = rec["id"], years(rec["query"])
            c[0] += 1
            c[1] += bool(qyears)
            query_distinct.append(len(qyears))
            relevant = gold.get(qid, set())
            c[2] += len(relevant)
            c[3] += sum(bool(doc_years.get(doc)) for doc in relevant)
            ranked = [doc for doc, _ in index.search(rec["query"], 100)
                      if doc not in relevant][:10]
            c[4] += len(ranked)
            c[5] += sum(bool(doc_years.get(doc)) for doc in ranked)
            if qyears:
                low, high = min(qyears) - 1, max(qyears) + 1
                c[6] += len(relevant)
                c[7] += sum(any(low <= y <= high for y in doc_years.get(doc, ()))
                            for doc in relevant)
                c[8] += len(ranked)
                c[9] += sum(any(low <= y <= high for y in doc_years.get(doc, ()))
                            for doc in ranked)
        values = sorted(query_distinct)
        median = (values[(len(values) - 1) // 2] + values[len(values) // 2]) / 2 if values else 0
        c[10] = median
        for i in range(10):
            totals[i] += c[i]
        rows.append((domain_dir.name, c))
        print(f"{domain_dir.name}: {c[0]} train queries", flush=True)

    lines = ["# Explicit date feasibility, Track 1 train", "",
             "Patterns: years `\\b(1[5-9]\\d\\d|20\\d\\d)\\b`, decades "
             "`\\b(1[5-9]\\d0s|20\\d0s)\\b`, and English month-year "
             "(`January 2017` or `Jan 2017`, similarly for other months). "
             "Decades map to their first year. Overlap means a document has a year "
             "within the query's minimum-to-maximum year span, extended by one year "
             "on either side. Passages are counted per query-document pair.", "",
             "| domain | train queries | queries dated | gold dated | non-gold BM25 top-10 dated | median years/query | gold span overlap | non-gold span overlap |",
             "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for name, c in rows + [("all (micro)", totals)]:
        med = "" if name == "all (micro)" else f"{c[10]:g}"
        lines.append(f"| {name} | {c[0]} | {pct(c[1], c[0])} | {pct(c[3], c[2])} | "
                     f"{pct(c[5], c[4])} | {med} | {pct(c[7], c[6])} | {pct(c[9], c[8])} |")
    lines += ["", "This is a train-only feasibility diagnostic, not an evaluated reranker. "
              "The overlap comparison uses only queries with explicit years. "
              "Explicit dates may be absent even when temporal reasoning is required.", ""]
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
