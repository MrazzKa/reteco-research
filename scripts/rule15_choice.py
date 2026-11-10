#!/usr/bin/env python3
"""LOG rule 15: per-source query variant for Track 2 (BRIGHT / StackExchange domain groups).

For 2a current (B) and 2a history (main): q-system = plain-query hybrid + ReasonEmbed (weight chosen on the
whole train subsample), q+r+h system = the current one. In group G the q-system replaces the current one only
if, on the train-subsample topics of G, q − q+r+h >= margin with bootstrap lower bound > 0. Dev once.

    python3 rule15_choice.py --runs ../research/runs_v13 --data ../../reteco_data_v11 --kit ../../RETECO/starter_kit \
        --out ../research/runs_v13/select/rule15.json
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bm25s_run import ndcg_fn  # noqa: E402
from hybrid import bootstrap  # noqa: E402
from rule14_choice import lists, macro, per_topic  # noqa: E402

GROUPS = {"BRIGHT": ["biology", "earth_science", "economics", "psychology", "robotics", "sustainable_living"],
          "StackExchange": ["drones", "hardware", "law", "medicalsciences", "politics"]}


def sub(pt, doms):
    return {d: pt[d] for d in doms}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--kit", required=True)
    ap.add_argument("--margin", type=float, default=0.005)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    ndcg = ndcg_fn(a.kit)
    sr = os.path.join(a.runs, "foreign", "runs")
    rep = json.load(open(os.path.join(a.runs, "reason", "t2_reasonembed-4b.json")))
    out = {"rule": "15", "groups": GROUPS, "conditions": {}}
    for cond, (qrun, qrhrun) in {"2a_current": ("2a_cur_q", "2a_nomaxp"), "2a_history": ("2ah_h0", "2ah_hybrid")}.items():
        pt = {v: {sp: per_topic(sr, n, a.data, ndcg, sp) for sp in ("train", "dev")}
              for v, n in (("q", qrun), ("q+r+h", qrhrun))}
        res = {"q_weight": rep[qrun].get("best_on_train"), "q+r+h_weight": rep[qrhrun].get("best_on_train"),
               "all": {v: {sp: macro(pt[v][sp]) for sp in ("train", "dev")} for v in pt}, "groups": {}}
        comb = {sp: {} for sp in ("train", "dev")}
        for g, doms in GROUPS.items():
            m = {v: {sp: macro(sub(pt[v][sp], doms)) for sp in ("train", "dev")} for v in pt}
            tb = bootstrap(lists(sub(pt["q"]["train"], doms)), lists(sub(pt["q+r+h"]["train"], doms)))
            use_q = m["q"]["train"] - m["q+r+h"]["train"] >= a.margin and tb["ci95"][0] > 0
            db = bootstrap(lists(sub(pt["q"]["dev"], doms)), lists(sub(pt["q+r+h"]["dev"], doms)))
            res["groups"][g] = {"macro": m, "train_q_minus_qrh": tb, "dev_q_minus_qrh": db,
                                "chosen": "q" if use_q else "q+r+h"}
            for sp in comb:
                comb[sp].update(sub(pt["q" if use_q else "q+r+h"][sp], doms))
            print(f"{cond:<11} {g:<14} q {m['q']}  q+r+h {m['q+r+h']}  train q-qrh {tb}  -> {res['groups'][g]['chosen']}"
                  f"  (dev q-qrh {db})", flush=True)
        res["combined"] = {sp: macro(comb[sp]) for sp in comb}
        res["combined_minus_current_dev"] = bootstrap(lists(comb["dev"]), lists(pt["q+r+h"]["dev"]))
        out["conditions"][cond] = res
        print(f"{cond}: combined {res['combined']}  current {res['all']['q+r+h']}", flush=True)
    json.dump(out, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
