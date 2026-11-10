#!/usr/bin/env python3
"""LOG rule 17: ReasonEmbed pool 50 vs 100 per final system, on the rule-8 train subsample (weight re-chosen in the
rule-8 grid for each pool; saved runs of reason_rerank.py). Pool 100 is adopted only with train >= +0.005 and
bootstrap lower bound > 0. Dev reported once.

    python3 rule17_choice.py --runs ../research/runs_v13 --data ../../reteco_data_v11 --kit ../../RETECO/starter_kit \
        --out ../research/runs_v13/select/rule17.json
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bm25s_run import ndcg_fn  # noqa: E402
from dense_index import T1, T2  # noqa: E402
from hybrid import bootstrap, read_run  # noqa: E402
from week1_run import load_qrels  # noqa: E402

SYSTEMS = {"2a_history_main": (2, "2ah_hybrid", "2ah_hybrid_p100", "qrels"),
           "1a": (1, "1a_rerun", "1a_rerun_p100", "qrels"),
           "2a_current_B": (2, "2a_nomaxp", "2a_nomaxp_p100", "qrels"),
           "1b": (1, "1b_rerun", "1b_rerun_p100", "qrels_steps")}


def per_topic(runs, tr, name, data, ndcg, split, qn):
    out = {}
    for dom in (T1 if tr == 1 else T2):
        p = os.path.join(runs, f"t{tr}_{dom}_{split}_{name}__best.tsv")
        if not os.path.exists(p):
            return None
        run = read_run(p)
        gold = load_qrels(os.path.join(data, "track1_tempo" if tr == 1 else "track2_recor", dom, f"{qn}_{split}.txt"))
        out[dom] = [ndcg([d for d, _ in run[q]], gold[q], 10) for q in sorted(run)]
    return out


def macro(pt):
    return round(sum(sum(v) / len(v) for v in pt.values()) / len(pt), 4)


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
    out = json.load(open(a.out)) if os.path.exists(a.out) else {}
    for k, (tr, p50, p100, qn) in SYSTEMS.items():
        r = {sp: (per_topic(sr, tr, p50, a.data, ndcg, sp, qn), per_topic(sr, tr, p100, a.data, ndcg, sp, qn))
             for sp in ("train", "dev")}
        if r["train"][1] is None:
            continue
        tb = bootstrap(r["train"][1], r["train"][0])
        m = {f"p{n}": {sp: macro(r[sp][i]) for sp in r} for i, n in ((0, 50), (1, 100))}
        adopt = m["p100"]["train"] - m["p50"]["train"] >= a.margin and tb["ci95"][0] > 0
        rep = json.load(open(os.path.join(a.runs, "reason", f"t{tr}_reasonembed-4b.json")))
        out[k] = {**m, "train_boot": tb, "dev_boot": bootstrap(r["dev"][1], r["dev"][0]),
                  "weights": {"p50": rep[p50].get("best_on_train"), "p100": rep[p100].get("best_on_train")},
                  "chosen": "100" if adopt else "50"}
        print(k, json.dumps(out[k]), flush=True)
    json.dump(out, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
