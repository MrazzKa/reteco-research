#!/usr/bin/env python3
"""Submission table of 2026-11-10: every variant of configs/submission.json scored from the submit.py dev
files (official qrels; per-topic nDCG@10 with the starter-kit implementation), with a 95% bootstrap interval
of the domain macro (topics resampled within domain, 10,000 draws, seed 20260921). Train = the number the
variant was chosen on (rule-8 subsample) from configs/submission.json ("train_research").

    python3 final_1110.py --sub ../research/runs_v13/submit/dev --data ../../reteco_data_v11 \
        --kit ../../RETECO/starter_kit --out ../research/runs_v13/final_1110.json
"""
import argparse
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bm25s_run import ndcg_fn  # noqa: E402
from hybrid import read_run  # noqa: E402
from week1_run import load_qrels  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def macro_ci(per_dom, n=10000, seed=20260921):
    rng = random.Random(seed)
    doms = sorted(per_dom)
    obs = sum(sum(per_dom[d]) / len(per_dom[d]) for d in doms) / len(doms)
    vals = []
    for _ in range(n):
        tot = 0.0
        for d in doms:
            x = per_dom[d]
            tot += sum(x[rng.randrange(len(x))] for _ in x) / len(x)
        vals.append(tot / len(doms))
    vals.sort()
    return round(obs, 4), [round(vals[int(0.025 * n)], 4), round(vals[int(0.975 * n)], 4)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=os.path.join(os.path.dirname(HERE), "configs", "submission.json"))
    ap.add_argument("--sub", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--kit", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    conf = json.load(open(a.config))
    ndcg = ndcg_fn(a.kit)
    rows = []
    for name, cfg in conf["variants"].items():
        vdir = os.path.join(a.sub, name)
        if not os.path.isdir(vdir):
            print(f"skip {name}: no dev files", flush=True)
            continue
        sub = "track1_tempo" if cfg["track"] == 1 else "track2_recor"
        per = {}
        for dom in cfg["domains"]:
            run = read_run(os.path.join(vdir, f"{dom}.txt"))
            qn = "qrels_steps_dev.txt" if cfg["query"].startswith("1b") else "qrels_dev.txt"
            gold = load_qrels(os.path.join(a.data, sub, dom, qn))
            per[dom] = [ndcg([d for d, _ in run.get(q, [])], gold[q], 10) for q in sorted(gold)]
        m, ci = macro_ci(per)
        rows.append({"variant": name, "run_id": cfg["run_id"], "role": cfg.get("role"), "track": cfg["track"],
                     "query": cfg["query"], "source": cfg.get("source"), "train": cfg.get("train_research"),
                     "dev": m, "dev_ci95": ci, "dev_research": cfg.get("dev_research"),
                     "topics": sum(len(v) for v in per.values())})
        print(f"{name:<14} dev {m:.4f} [{ci[0]:.4f}, {ci[1]:.4f}]  research {cfg.get('dev_research')}", flush=True)
    json.dump({"rows": rows, "main": conf.get("_main_runs"), "fallbacks": conf.get("_fallback_runs"),
               "auto_2a": conf.get("_auto_2a")}, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
