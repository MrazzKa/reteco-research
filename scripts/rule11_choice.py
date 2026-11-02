#!/usr/bin/env python3
"""LOG rule 11, hybrid stage: H0 (week-4 history hybrid) vs Ha (LLM input: current + <= 3 earlier
questions) vs Hb (Ha + earlier answers). Train only: the best is adopted over H0 with margin +0.005 and
bootstrap lower bound > 0; Hb additionally needs the same margin over Ha. Prints and writes the choice.

    python3 rule11_choice.py --runs ../research/runs_v13 --out ../research/runs_v13/select/rule11.json
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hybrid import bootstrap  # noqa: E402


def load(path, cond):
    rep = json.load(open(path))["conditions"][cond]
    s = rep["systems"]["linear*"]
    return {"report": path, "condition": cond, "cfg": s["cfg"], "train": s["train_macro"], "dev": s["dev_macro"],
            "train_pt": rep["train_per_topic"]["linear*"], "dev_pt": rep["dev_per_topic"]["linear*"]}


def adopted(x, y, margin):
    b = bootstrap(x["train_pt"], y["train_pt"])
    return b, (x["train"] - y["train"] >= margin and b["ci95"][0] > 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True)
    ap.add_argument("--margin", type=float, default=0.005)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    R = a.runs
    c = {"H0": load(f"{R}/hybrid/bge-base_L512_t2.json", "2a_history"),
         "Ha": load(f"{R}/hist/t2/hybrid.json", "2a_hist3q__q+r+h"),
         "Hb": load(f"{R}/hist/t2/hybrid.json", "2a_hist3qa__q+r+h")}
    tests = {}
    tests["Ha_vs_H0"], ok_a = adopted(c["Ha"], c["H0"], a.margin)
    tests["Hb_vs_H0"], ok_b0 = adopted(c["Hb"], c["H0"], a.margin)
    tests["Hb_vs_Ha"], ok_ba = adopted(c["Hb"], c["Ha"], a.margin)
    if ok_b0 and ok_ba:
        chosen = "Hb"
    elif ok_a:
        chosen = "Ha"
    else:
        chosen = "H0"
    dev = {k: bootstrap(v["dev_pt"], c["H0"]["dev_pt"]) for k, v in c.items() if k != "H0"}
    out = {"rule": "11", "chosen": chosen, "train": {k: v["train"] for k, v in c.items()},
           "dev": {k: v["dev"] for k, v in c.items()}, "cfg": {k: v["cfg"] for k, v in c.items()},
           "train_tests": tests, "dev_minus_H0": dev,
           "chosen_spec": {k: c[chosen][k] for k in ("report", "condition")}}
    print(json.dumps({k: v for k, v in out.items()}, indent=1))
    json.dump(out, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
