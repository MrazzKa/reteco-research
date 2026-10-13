#!/usr/bin/env python3
"""Data check: do Track-2 document ids reveal which documents are gold?

Counts, per Track-2 domain, document ids of the form `..._doc_<n>`, `..._google_neg_<n>`
and anything else, over the whole corpus and over the gold documents of train+dev.
Diagnostic only — no system in this repo reads document ids for ranking.

    python3 id_artifact.py --data ../../reteco_data_v11 --out ../research/runs_v12/id_artifact.json
"""
import argparse
import json
import os
import re
from collections import Counter

from dense_index import T2


def kind(doc_id):
    if re.search(r"_doc_\d+$", doc_id):
        return "doc"
    return "google_neg" if "google_neg" in doc_id else "other"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rep = {}
    for dom in T2:
        d = os.path.join(a.data, "track2_recor", dom)
        gold = set()
        for split in ("train", "dev"):
            for line in open(os.path.join(d, f"qrels_{split}.txt")):
                _, _, doc, rel = line.split()
                if int(rel) > 0:
                    gold.add(doc)
        ids = [json.loads(x)["doc_id"] for x in open(os.path.join(d, "documents.jsonl"))]
        ca, cg = Counter(map(kind, ids)), Counter(map(kind, gold))
        rep[dom] = {"corpus": dict(ca), "gold": dict(cg), "gold_total": len(gold),
                    "share_gold_with_doc_id": round(cg["doc"] / len(gold), 4),
                    "share_corpus_with_doc_id": round(ca["doc"] / len(ids), 4),
                    "p_gold_given_doc_id": round(cg["doc"] / ca["doc"], 4) if ca["doc"] else None}
        print(dom, rep[dom])
    json.dump(rep, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
