#!/usr/bin/env python3
"""Track-2 dev breakdown of saved runs: macro nDCG@10, turn groups and turn depth (LOG rule 12).

Groups (as in history_leak.py): first turn; later turn whose gold shares a document with an earlier
turn's gold ("recycled"); later turn with only new gold ("new gold", 79 dev turns). Depth buckets
T1 ... T5+ as in the official scorer. Group/depth numbers are means over turns (micro); the headline is
the official domain macro. Paired bootstrap (within domain) for each system against the first one.

    python3 t2_breakdown.py --data ../../reteco_data_v11 --kit ../../RETECO/starter_kit --split dev \
        --run "current=../research/runs_v13/foreign/runs/{pre}_2a_maxp__best.tsv" \
        --run "history=../research/runs_v13/foreign/runs/{pre}_2ah_hybrid__best.tsv" --out out.json
"""
import argparse
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bm25s_run import ndcg_fn  # noqa: E402
from dense_index import T2  # noqa: E402
from hybrid import bootstrap, read_run  # noqa: E402
from week1_run import load_qrels  # noqa: E402


def bucket(qid):
    t = int(qid.rsplit("_turn_", 1)[1])
    return "T5+" if t >= 5 else f"T{t}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--kit", required=True)
    ap.add_argument("--split", default="dev")
    ap.add_argument("--run", action="append", required=True, help="label=path pattern with {pre} = t2_<dom>_<split>")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    ndcg = ndcg_fn(a.kit)
    systems = [r.split("=", 1) for r in a.run]
    per = {lab: defaultdict(list) for lab, _ in systems}
    grp = {lab: defaultdict(list) for lab, _ in systems}
    dep = {lab: defaultdict(list) for lab, _ in systems}
    for dom in T2:
        d = os.path.join(a.data, "track2_recor", dom)
        bench = json.load(open(os.path.join(d, f"benchmark_{a.split}.json"), encoding="utf-8"))
        bench = [bench] if isinstance(bench, dict) else bench
        gold = load_qrels(os.path.join(d, f"qrels_{a.split}.txt"))
        group = {}
        for c in bench:
            seen = set()
            for t in sorted(c["turns"], key=lambda t: int(t["turn_id"])):
                qid = f"{c['id']}_turn_{t['turn_id']}"
                g = gold.get(qid)
                if not g:
                    continue
                group[qid] = "first_turn" if not seen else ("recycled_gold" if g & seen else "new_gold")
                seen |= g
        for lab, pat in systems:
            run = read_run(pat.format(pre=f"t2_{dom}_{a.split}"))
            for qid in sorted(gold):
                v = ndcg([x for x, _ in run.get(qid, [])], gold[qid], 10)
                per[lab][dom].append(v)
                grp[lab][group.get(qid, "first_turn")].append(v)
                dep[lab][bucket(qid)].append(v)
    out = {}
    base = systems[0][0]
    for lab, _ in systems:
        macro = sum(sum(v) / len(v) for v in per[lab].values()) / len(per[lab])
        out[lab] = {"macro": round(macro, 4),
                    "groups": {g: {"n": len(v), "ndcg10": round(sum(v) / len(v), 4)} for g, v in sorted(grp[lab].items())},
                    "depth": {b: {"n": len(v), "ndcg10": round(sum(v) / len(v), 4)} for b, v in sorted(dep[lab].items())},
                    "vs_" + base: bootstrap(per[lab], per[base]) if lab != base else None}
        print(lab, json.dumps(out[lab]), flush=True)
    json.dump(out, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
