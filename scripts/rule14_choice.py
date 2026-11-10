#!/usr/bin/env python3
"""LOG rule 14: the best 2a system without earlier answers, chosen on the rule-8 train subsample.

Candidates in order of complexity (saved top-50 runs of reason_rerank.py, rule-chosen weight):
B (current turn, no MaxP) < H0q + ReasonEmbed < Haq + ReasonEmbed. The best by train macro nDCG@10 is
adopted only if it beats every simpler candidate by >= margin with paired-bootstrap lower bound > 0;
otherwise it is dropped and the rule is applied to the rest (B by default). Dev reported once each.

    python3 rule14_choice.py --runs ../research/runs_v13 --data ../../reteco_data_v11 --kit ../../RETECO/starter_kit \
        --out ../research/runs_v13/select/rule14.json
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bm25s_run import ndcg_fn  # noqa: E402
from dense_index import T2  # noqa: E402
from hybrid import bootstrap, read_run  # noqa: E402
from week1_run import load_qrels  # noqa: E402


def per_topic(runs, name, data, ndcg, split):
    out = {}
    for dom in T2:
        run = read_run(os.path.join(runs, f"t2_{dom}_{split}_{name}__best.tsv"))
        gold = load_qrels(os.path.join(data, "track2_recor", dom, f"qrels_{split}.txt"))
        out[dom] = {q: ndcg([d for d, _ in run[q]], gold[q], 10) for q in sorted(run)}
    return out


def macro(pt):
    return round(sum(sum(v.values()) / len(v) for v in pt.values()) / len(pt), 4)


def lists(pt):
    return {d: [v[q] for q in sorted(v)] for d, v in pt.items()}


def choose(order_, train, margin):
    """order_: simplest first. Returns (chosen, tests)."""
    tests, left = {}, list(order_)
    while len(left) > 1:
        best = max(left, key=lambda k: (macro(train[k]), -order_.index(k)))
        ok = True
        for simpler in left[:left.index(best)]:
            b = bootstrap(lists(train[best]), lists(train[simpler]))
            tests[f"{best}_vs_{simpler}"] = b
            ok &= macro(train[best]) - macro(train[simpler]) >= margin and b["ci95"][0] > 0
        if ok:
            return best, tests
        left.remove(best)
    return left[0], tests


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
    cands = {"B": "2a_nomaxp", "H0q+RE": "2ahq_h0q", "Haq+RE": "2ahq_haq"}
    order_ = ["B", "H0q+RE", "Haq+RE"]
    train = {k: per_topic(sr, v, a.data, ndcg, "train") for k, v in cands.items()}
    dev = {k: per_topic(sr, v, a.data, ndcg, "dev") for k, v in cands.items()}
    for k in cands:
        assert {d: sorted(v) for d, v in train[k].items()} == {d: sorted(v) for d, v in train["B"].items()}, k
    chosen, tests = choose(order_, train, a.margin)
    rep = json.load(open(os.path.join(a.runs, "reason", "t2_reasonembed-4b.json")))
    out = {"rule": "14", "chosen": chosen, "chosen_run": cands[chosen],
           "train_sub": {k: macro(v) for k, v in train.items()}, "dev": {k: macro(v) for k, v in dev.items()},
           "weights": {k: rep[v].get("best_on_train") for k, v in cands.items()},
           "re_none": {k: rep[v]["by_how"]["none=0"] for k, v in cands.items()},
           "train_tests": tests,
           "dev_minus_B": {k: bootstrap(lists(dev[k]), lists(dev["B"])) for k in cands if k != "B"},
           "train_topics": sum(len(v) for v in train["B"].values()),
           "dev_topics": sum(len(v) for v in dev["B"].values())}
    print(json.dumps(out, indent=1))
    json.dump(out, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
