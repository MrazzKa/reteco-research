#!/usr/bin/env python3
"""Build a per-domain / macro comparison table across retrieval systems.

Each --run argument is `label=path/to/results.json`. Rows are domains, columns are
systems, for one condition (e.g. 1a). Official pyserini references come from
week1_run.REF. Also prints macro averages over the domains common to all systems,
so the comparison is not distorted by different domain coverage.

    python3 compare_systems.py --condition 1a --track 1 \
        --run "bm25s-lucene=../research/runs_v11/track1_lucene/results.json" \
        --run "bm25s-plain=../research/runs_v11/track1_plain/results.json" \
        --out ../research/comparison_1a.md
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from week1_run import REF  # noqa: E402


def load(path, track, condition):
    rows = json.load(open(path, encoding="utf-8"))
    return {r["domain"]: r for r in rows
            if r["track"] == track and r["run"] == condition}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="append", required=True, help="label=results.json")
    ap.add_argument("--track", type=int, required=True)
    ap.add_argument("--condition", required=True)
    ap.add_argument("--ref", help="REF key for the official column (e.g. 1a, 1b, 2a_current)")
    ap.add_argument("--split", default="dev")
    ap.add_argument("--title", default="")
    ap.add_argument("--out")
    a = ap.parse_args()

    systems = []
    for spec in a.run:
        label, path = spec.split("=", 1)
        systems.append((label, load(path, a.track, a.condition)))

    domains = sorted(set().union(*[set(d) for _, d in systems]))
    common = sorted(set.intersection(*[set(d) for _, d in systems])) if systems else []
    ref_key = a.ref
    header = ["domain", "n"] + [s for s, _ in systems] + (["official"] if ref_key else [])
    lines = [f"### {a.title or a.condition} ({a.split})", "",
             "| " + " | ".join(header) + " |",
             "| --- | ---: |" + " ---: |" * (len(header) - 2)]
    for dom in domains:
        n = next((d[dom]["n"] for _, d in systems if dom in d), "")
        cells = [f"{d[dom]['ndcg10']:.4f}" if dom in d else "" for _, d in systems]
        if ref_key:
            ref = REF.get(ref_key, {}).get(dom)
            cells.append(f"{(ref[0] if a.split == 'train' else ref[1]):.4f}" if ref else "")
        lines.append(f"| {dom} | {n} | " + " | ".join(cells) + " |")

    def macro(d, doms):
        vals = [d[x]["ndcg10"] for x in doms if x in d]
        return sum(vals) / len(vals) if vals else float("nan")

    lines.append(f"| **macro ({len(common)} common)** |  | "
                 + " | ".join(f"**{macro(d, common):.4f}**" for _, d in systems)
                 + (" | **" + f"{sum((REF[ref_key][x][1] if a.split == 'dev' else REF[ref_key][x][0]) for x in common if x in REF.get(ref_key, {})) / max(1, len([x for x in common if x in REF.get(ref_key, {})])):.4f}" + "**" if ref_key else "")
                 + " |")
    text = "\n".join(lines) + "\n"
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(text)
    print(text)


if __name__ == "__main__":
    main()
