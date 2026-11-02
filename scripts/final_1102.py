#!/usr/bin/env python3
"""Rule 12 and the 2026-11-02 submission table (runs_v13/final_1102.json, select/rule12.json).

Reads the foreign-gold report (per-topic train-subsample and dev nDCG@10 of every stage), the rule-10
decision in it, the rule-11 choice and the ReasonEmbed reports. Rule 12: main 2a run = best train macro
among {best current-turn system after rule 10, best history system after rule 11}; history (the more
complex input) needs +0.005 and a bootstrap lower bound > 0.

    python3 final_1102.py --runs ../research/runs_v13
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hybrid import bootstrap  # noqa: E402

A = "+ ReasonEmbed (MaxP pool) = A"
B = "+ ReasonEmbed (no MaxP) = B"
H = "hist + ReasonEmbed (rule 11)"


def row(F, cond, stage, sub, role, run_id, what, train_view="train_sub"):
    s = F[cond][stage]
    return {"sub": sub, "role": role, "run_id": run_id, "what": what, "stage": stage,
            "train": s[train_view]["ndcg10"] if train_view in s else None, "dev": s["dev"]["ndcg10"],
            "dev_testlike": s["dev"]["ndcg10_testlike"], "n_testlike": s["dev"]["n_testlike"],
            "foreign_dev": s["dev"]["foreign_share_top10"],
            "foreign_train": s[train_view]["foreign_share_top10"] if train_view in s else None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True)
    a = ap.parse_args()
    R = a.runs
    F = json.load(open(os.path.join(R, "foreign", "report.json")))
    r10 = F["rule10"]
    cur = A if r10["decision"].startswith("keep MaxP") else B
    cur_alt = B if cur == A else A
    r11 = json.load(open(os.path.join(R, "select", "rule11.json")))
    rep = json.load(open(os.path.join(R, "reason", "t2_reasonembed-4b.json")))
    hist_re = rep["2ah_hybrid"]
    hc, hh = F["2a_current"][cur]["train_sub"], F["2a_history"][H]["train_sub"]
    common = sorted(set(hc["_per_topic"]) & set(hh["_per_topic"]))
    assert all(len(hc["_per_topic"][d]) == len(hh["_per_topic"][d]) for d in common), "train subsamples differ"
    b = bootstrap({d: hh["_per_topic"][d] for d in common}, {d: hc["_per_topic"][d] for d in common})
    hist_main = (hh["ndcg10"] - hc["ndcg10"] >= 0.005) and b["ci95"][0] > 0
    r12 = {"rule": "12", "current_system": cur, "history_system": f"rule 11 {r11['chosen']} + ReasonEmbed "
           f"({hist_re['best_on_train']})", "train": {"current": hc["ndcg10"], "history": hh["ndcg10"]},
           "dev": {"current": F["2a_current"][cur]["dev"]["ndcg10"], "history": F["2a_history"][H]["dev"]["ndcg10"]},
           "train_history_minus_current": b,
           "decision": "main 2a = with history" if hist_main else "main 2a = current turn"}
    json.dump(r12, open(os.path.join(R, "select", "rule12.json"), "w"), indent=1)
    print(json.dumps(r12, indent=1))
    t1 = json.load(open(os.path.join(R, "reason", "t1_reasonembed-4b.json")))
    w1a = t1["1a_rerun"]["best_on_train"]
    w1b = t1["1b_rerun"]["best_on_train"]
    wa = rep["2a_maxp"]["best_on_train"]
    wb = rep["2a_nomaxp"]["best_on_train"]
    what = {A: f"Qwen3-4B q+r+h → BM25 + bge-base MaxP hybrid → ReasonEmbed top 50 ({wa})",
            B: f"Qwen3-4B q+r+h → BM25 + bge-base hybrid (no MaxP) → ReasonEmbed top 50 ({wb})",
            H: (f"history: Qwen3-4B q+r+h on current question + ≤ 3 earlier turns ({r11['chosen']}) → hybrid → "
                f"ReasonEmbed top 50 ({hist_re['best_on_train']})")}
    rid = {A: "UA_2a_maxp", B: "UA_2a_nomaxp", H: "UA_2a_history"}
    rows = [row(F, "1a", "+ ReasonEmbed", "1a", "main", "UA_1a_main",
                f"Qwen3-4B q+r+h → BM25 + bge-small L256 hybrid → ReasonEmbed top 50 ({w1a})"),
            row(F, "1a", "+ q+r+h", "1a", "fallback", "UA_1a_noRE", "same without ReasonEmbed"),
            row(F, "1b", "+ ReasonEmbed", "1b", "main", "UA_1b_main",
                f"Qwen3-4B q+r+h (query + step) → BM25 + bge-small L256 hybrid → ReasonEmbed top 50 ({w1b})"),
            row(F, "1b", "+ q+r+h", "1b", "fallback", "UA_1b_noRE", "same without ReasonEmbed")]
    order2 = [H, cur, cur_alt] if hist_main else [cur, H, cur_alt]
    for i, st in enumerate(order2):
        cond = "2a_history" if st == H else "2a_current"
        rows.append(row(F, cond, st, "2a", "main" if i == 0 else "fallback", rid[st], what[st]))
    notes = [
        "1a/1b fallbacks are the train-chosen q+r+h hybrids without ReasonEmbed. Train column = the rule-8 "
        "subsample (≤ 30 topics per domain) for every row, so rows are comparable.",
        f"Rule 10: {r10['decision']}; rule 11 hybrid choice {r11['chosen']}; rule 12: {r12['decision']}.",
        "Test-like topics are almost all topics (train and dev share very few gold documents), so this column "
        "is close to the full dev number; the foreign-gold share is the more informative column.",
    ]
    json.dump({"rows": rows, "notes": notes, "rule12": r12}, open(os.path.join(R, "final_1102.json"), "w"), indent=1)
    for r in rows:
        print(r["sub"], r["role"], r["run_id"], r["train"], r["dev"], r["dev_testlike"], r["foreign_dev"])


if __name__ == "__main__":
    main()
