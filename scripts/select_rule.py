#!/usr/bin/env python3
"""Apply a pre-registered train-only choice rule over hybrid.py reports (LOG rules 6, 7).

Each candidate is (label, hybrid report, condition inside it). The baseline is the
candidate given by --baseline. The best candidate by train macro nDCG@10 (tuned hybrid,
`linear*`) is adopted only if it beats the baseline by >= --margin on train AND the paired
bootstrap over train topics has a 95% lower bound > 0. Dev numbers of every candidate are
reported (one measurement each), with a dev bootstrap of chosen - baseline.

    python3 select_rule.py --rule 6 --cond 1a --baseline q \
        --cand q=../research/runs_v13/qexp/t1/hybrid_1a.json:1a__q ... --out sel.json
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hybrid import bootstrap  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rule", required=True)
    ap.add_argument("--cond", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--cand", nargs="+", required=True, help="label=report.json:condition")
    ap.add_argument("--margin", type=float, default=0.005)
    ap.add_argument("--system", default="linear*")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    c = {}
    for spec in a.cand:
        label, rest = spec.split("=", 1)
        path, cond = rest.rsplit(":", 1)
        rep = json.load(open(path))["conditions"][cond]
        s = rep["systems"][a.system]
        c[label] = {"report": path, "condition": cond, "cfg": s["cfg"], "train": s["train_macro"],
                    "dev": s["dev_macro"], "train_pt": rep["train_per_topic"][a.system],
                    "dev_pt": rep["dev_per_topic"][a.system],
                    "bm25_train": rep["systems"]["bm25"]["train_macro"], "bm25_dev": rep["systems"]["bm25"]["dev_macro"],
                    "dense_train": rep["systems"]["dense"]["train_macro"], "dense_dev": rep["systems"]["dense"]["dev_macro"]}
    base = c[a.baseline]
    best = max(c, key=lambda k: c[k]["train"])
    tb = bootstrap(c[best]["train_pt"], base["train_pt"]) if best != a.baseline else None
    adopt = (best != a.baseline and c[best]["train"] - base["train"] >= a.margin and tb["ci95"][0] > 0)
    chosen = best if adopt else a.baseline
    out = {"rule": a.rule, "cond": a.cond, "baseline": a.baseline, "margin": a.margin, "best_on_train": best,
           "train_bootstrap_best_minus_baseline": tb, "adopted": adopt, "chosen": chosen,
           "dev_bootstrap_chosen_minus_baseline": (bootstrap(c[chosen]["dev_pt"], base["dev_pt"])
                                                   if chosen != a.baseline else None),
           "candidates": {k: {kk: vv for kk, vv in v.items() if not kk.endswith("_pt")} for k, v in c.items()},
           "dev_bootstrap_each_minus_baseline": {k: bootstrap(v["dev_pt"], base["dev_pt"])
                                                 for k, v in c.items() if k != a.baseline}}
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(out, open(a.out, "w"), indent=1)
    print(f"rule {a.rule} {a.cond}:")
    for k, v in sorted(c.items(), key=lambda x: -x[1]["train"]):
        print(f"  {k:<10} bm25 {v['bm25_train']:.4f}/{v['bm25_dev']:.4f}  dense {v['dense_train']:.4f}/{v['dense_dev']:.4f}"
              f"  hybrid train {v['train']:.4f}  dev {v['dev']:.4f}")
    print(f"  best on train {best}; train bootstrap {tb}; adopted={adopt} -> {chosen}")
    if out["dev_bootstrap_chosen_minus_baseline"]:
        print(f"  dev chosen - baseline {out['dev_bootstrap_chosen_minus_baseline']}")


if __name__ == "__main__":
    main()
