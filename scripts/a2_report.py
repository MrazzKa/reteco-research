#!/usr/bin/env python3
"""A2 report: the frozen main 2a run with LLM-written vs reference earlier answers, the rule-14 run without
answers and the current-turn run B; train subsample and dev; macro, turn groups and depth (t2_breakdown.py).

    python3 a2_report.py --runs ../research/runs_v13 --data ../../reteco_data_v11 --kit ../../RETECO/starter_kit
"""
import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--kit", required=True)
    a = ap.parse_args()
    R, A = a.runs, os.path.join(a.runs, "a2")
    F = os.path.join(R, "foreign", "runs")
    plans = {
        "trainsub": ("train", [("main, reference answers", f"{A}/sub_ref/trainsub/2a_history/{{dom}}.txt"),
                               ("main, LLM-written answers", f"{A}/sub_gen/trainsub/2a_history/{{dom}}.txt"),
                               ("no answers (rule 14, H0q+RE)", f"{F}/{{pre}}_2ahq_h0q__best.tsv"),
                               ("current turn B", f"{F}/{{pre}}_2a_nomaxp__best.tsv")]),
        "dev": ("dev", [("main, reference answers", f"{R}/submit/dev/2a_history/{{dom}}.txt"),
                        ("main, LLM-written answers", f"{A}/sub_gen/dev/2a_history/{{dom}}.txt"),
                        ("no answers (rule 14, H0q+RE)", f"{R}/submit/dev/2a_history_q/{{dom}}.txt"),
                        ("current turn B", f"{R}/submit/dev/2a_nomaxp/{{dom}}.txt")]),
    }
    out = {}
    for key, (split, systems) in plans.items():
        tmp = os.path.join(A, f"breakdown_{key}.json")
        cmd = [sys.executable, os.path.join(HERE, "t2_breakdown.py"), "--data", a.data, "--kit", a.kit, "--split", split,
               "--only-run-topics", "--out", tmp] + [x for lab, pat in systems for x in ("--run", f"{lab}={pat}")]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
        out[key] = json.load(open(tmp))
    rows = [json.loads(x) for x in open(os.path.join(A, "answers.jsonl"), encoding="utf-8") if x.strip()]
    words = [len(r["output"].split()) for r in rows]
    out["answers"] = {"n": len(rows), "mean_words": round(sum(words) / max(1, len(words)), 1),
                      "cut": sum(r["finish"] == "length" for r in rows), "empty": sum(not r["output"].strip() for r in rows)}
    json.dump(out, open(os.path.join(A, "report.json"), "w"), indent=1)
    for key in plans:
        print(key)
        for lab, r in out[key].items():
            g = r["groups"]
            print(f"  {lab:<32} macro {r['macro']:.4f}  first {g.get('first_turn', {}).get('ndcg10')}  recycled "
                  f"{g.get('recycled_gold', {}).get('ndcg10')}  new {g.get('new_gold', {}).get('ndcg10')}  "
                  f"vs reference {next((v for k, v in r.items() if k.startswith('vs_')), None)}")
    print(out["answers"])


if __name__ == "__main__":
    main()
