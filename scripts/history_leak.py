#!/usr/bin/env python3
"""How much of the Track-2 history gain is "answer already in the history"?

For each turn: `recycled` = share of its gold documents that were gold for an earlier turn
of the same conversation (whose reference answer sits in `conversation_history`), and
`ans_overlap` = share of the gold document's content stems that occur in the history's
A: lines. Turns are grouped (first turn / later turn with all-new gold / later turn with
recycled gold) and nDCG@10 of each system is reported per group, current vs history.

A large history gain on recycled-gold turns and a small one on new-gold turns means the
history mostly points back to documents already found, not that it helps find new ones.

    python3 history_leak.py --data ../../reteco_data_v11 --kit ../../RETECO/starter_kit \
        --bm25 ../research/runs_v12/bm25/t2/runs --dense ../research/runs_v12/dense/bge-small_L512/t2/runs \
        --out ../research/runs_v12/history_leak.json
"""
import argparse
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from week1_run import BRIGHT_DOMAINS, load_qrels  # noqa: E402
from bm25s_run import ndcg_fn  # noqa: E402
from dense_index import T2  # noqa: E402
from hybrid import Query, read_run, system  # noqa: E402

LINEAR = {"kind": "linear", "kb": 100, "kd": 100, "norm": "zscore", "alpha": 0.7}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--kit", required=True)
    ap.add_argument("--bm25", required=True)
    ap.add_argument("--dense", required=True)
    ap.add_argument("--splits", nargs="+", default=["train", "dev"])
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    ndcg = ndcg_fn(a.kit)
    out = {}
    for split in a.splits:
        groups = defaultdict(lambda: defaultdict(list))
        stats = defaultdict(list)
        for dom in T2:
            d = os.path.join(a.data, "track2_recor", dom)
            bench = json.load(open(os.path.join(d, f"benchmark_{split}.json"), encoding="utf-8"))
            bench = [bench] if isinstance(bench, dict) else bench
            gold = load_qrels(os.path.join(d, f"qrels_{split}.txt"))
            runs = {}
            for cond, dcond in (("2a_current", "2a_current"), ("2a_history", "2a_history_qfirst")):
                pre = f"t2_{dom}_{split}"
                runs[cond] = (read_run(os.path.join(a.bm25, f"{pre}_{cond}.tsv")),
                              read_run(os.path.join(a.dense, f"{pre}_{dcond}.tsv")))
            src = "BRIGHT" if dom in BRIGHT_DOMAINS else "StackExchange"
            for c in bench:
                seen = set()
                for t in sorted(c["turns"], key=lambda t: t["turn_id"]):
                    qid = f"{c['id']}_turn_{t['turn_id']}"
                    g = gold.get(qid)
                    if not g:
                        continue
                    rec = len(g & seen) / len(g)
                    grp = "first_turn" if not seen else ("recycled_gold" if rec > 0 else "new_gold")
                    stats[f"{src}|recycled_share"].append(rec if seen else None)
                    for cond, (bm, de) in runs.items():
                        q = Query(bm.get(qid, []), de.get(qid, []))
                        for label, cfg in (("bm25", {"kind": "bm25"}), ("dense", {"kind": "dense"}),
                                           ("hybrid", LINEAR)):
                            v = ndcg(system(q, cfg), g, 10)
                            groups[f"{src}|{grp}"][f"{cond}|{label}"].append(v)
                            groups[f"ALL|{grp}"][f"{cond}|{label}"].append(v)
                    seen |= g
        res = {}
        for grp, sysd in sorted(groups.items()):
            res[grp] = {"n_turns": len(next(iter(sysd.values()))),
                        **{k: round(sum(v) / len(v), 4) for k, v in sysd.items()}}
        later = {k: [x for x in v if x is not None] for k, v in stats.items()}
        res["later_turns_with_any_recycled_gold"] = {
            k.split("|")[0]: round(sum(1 for x in v if x > 0) / len(v), 4) for k, v in later.items()}
        out[split] = res
        print(f"== {split}")
        for grp, r in res.items():
            print(f"  {grp}: {r}")
    json.dump(out, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
