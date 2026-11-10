#!/usr/bin/env python3
"""LOG rule 17, CPU part: share of train gold documents that the frozen hybrid of each final system puts in
its top 100 but not its top 50 (the ceiling of a ReasonEmbed pool of 100 instead of 50).

    python3 pool_depth.py --runs ../research/runs_v13 --data ../../reteco_data_v11 --out R/select/rule17_ceiling.json
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dense_index import T1, T2  # noqa: E402
from hybrid import Query, qrels_for, read_run  # noqa: E402
from tie_study import fused, order  # noqa: E402
import tiebreak  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--splits", nargs="+", default=["train", "dev"])
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    tiebreak.set_mode("sha1")
    R = a.runs
    systems = {  # name: (track, hybrid report, condition, bm25 dir, dense dir)
        "1a": (1, f"{R}/qexp/t1/hybrid_1a.json", "1a__q+r+h", f"{R}/qexp/t1/bm25/runs", f"{R}/qexp/t1/dense/runs"),
        "1b": (1, f"{R}/qexp/t1/hybrid_1b.json", "1b_query+step__q+r+h", f"{R}/qexp/t1/bm25/runs", f"{R}/qexp/t1/dense/runs"),
        "2a_current_B": (2, f"{R}/qexp/t2/hybrid_2a_current.json", "2a_current__q+r+h", f"{R}/qexp/t2/bm25/runs", f"{R}/qexp/t2/dense/runs"),
        "2a_history_main": (2, f"{R}/hist/t2/hybrid.json", "2a_hist3qa__q+r+h", f"{R}/hist/t2/bm25/runs", f"{R}/hist/t2/dense/runs"),
    }
    out = {}
    for name, (tr, rep, cond, bdir, ddir) in systems.items():
        hc = json.load(open(rep))["conditions"][cond]
        cfg, dcond = hc["systems"]["linear*"]["cfg"], hc["dense_condition"]
        out[name] = {}
        for sp in a.splits:
            tot = {"gold": 0, "top50": 0, "top100": 0, "pool_len_lt_100": 0}
            per_dom = {}
            for dom in (T1 if tr == 1 else T2):
                pre = f"t{tr}_{dom}_{sp}"
                bm, de = read_run(os.path.join(bdir, f"{pre}_{cond}.tsv")), read_run(os.path.join(ddir, f"{pre}_{dcond}.tsv"))
                gold = qrels_for(a.data, tr, dom, sp, cond)
                c = {"gold": 0, "top50": 0, "top100": 0}
                for q, g in gold.items():
                    pool = [d for d, _ in order(fused(Query(bm.get(q, []), de.get(q, [])), cfg))]
                    tot["pool_len_lt_100"] += len(pool) < 100
                    c["gold"] += len(g)
                    c["top50"] += len(set(pool[:50]) & set(g))
                    c["top100"] += len(set(pool[:100]) & set(g))
                for k in c:
                    tot[k] += c[k]
                per_dom[dom] = round((c["top100"] - c["top50"]) / max(1, c["gold"]), 4)
            tot["share_51_100"] = round((tot["top100"] - tot["top50"]) / max(1, tot["gold"]), 4)
            tot["recall50"] = round(tot["top50"] / max(1, tot["gold"]), 4)
            tot["macro_share_51_100"] = round(sum(per_dom.values()) / len(per_dom), 4)
            tot["per_domain_share_51_100"] = per_dom
            tot["run_rule17"] = tot["share_51_100"] >= 0.03
            out[name][sp] = tot
            print(f"{name:<16} {sp:<5} gold {tot['gold']:>5}  recall@50 {tot['recall50']:.3f}  in 51-100 "
                  f"{tot['share_51_100']:.3%} (macro {tot['macro_share_51_100']:.3%})  run={tot['run_rule17']}", flush=True)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(out, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
