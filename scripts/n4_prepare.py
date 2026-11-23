#!/usr/bin/env python3
"""N4 (LOG 2026-11-23; analysis, no choice): several LLM draws of the main runs — releases, configs and LLM inputs.

Realisation 0 = the research generation cache (configs/submission.json as it is). Realisation s = 1, 2, 3 = a fresh
generation of every LLM input of the runs below, in one llm_expand call per track whose input order is shuffled
with random.Random(s) (temperature 0; a different batch composition), cached under runs_v13/n4/llm/s<s>/t<track>.

Runs per realisation (submit.py with --stages, scored on the dev topics and on the rule-8 train subsample):
  1a, 1b                       dev: the release; trainsub: runs_v13/n4/rel/t1 (examples/steps of the subsample)
  2a_history_rr (+ __re = 2a_history, __hybrid)   dev: the release; trainsub: runs_v13/a2/data_ref
  2a_history_noans (= M0)      same topics (answers removed inside submit.py)
  2a_history on the LLM-written answers (A2)       runs_v13/a2/data_gen (dev, trainsub); the written answers are
                               the A2 ones (one draw, fixed); only the query-side generations are redrawn.

    python3 n4_prepare.py --root .. --data ../../reteco_data_v11 --seed 1
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dense_index import T1  # noqa: E402

R = "research/runs_v13"


def jobs(root, data):
    """[(label, data dir, split, [variants])] — the submit.py invocations of one realisation."""
    n4, a2 = os.path.join(root, R, "n4"), os.path.join(root, R, "a2")
    return [("t1_dev", data, "dev", ["1a", "1b"]),
            ("t1_trainsub", os.path.join(n4, "rel", "t1"), "trainsub", ["1a", "1b"]),
            ("t2_dev", data, "dev", ["2a_history_rr", "2a_history_noans"]),
            ("t2_trainsub", os.path.join(a2, "data_ref"), "trainsub", ["2a_history_rr", "2a_history_noans"]),
            ("gen_dev", os.path.join(a2, "data_gen"), "dev", ["2a_history"]),
            ("gen_trainsub", os.path.join(a2, "data_gen"), "trainsub", ["2a_history"])]


def t1_release(root, data):
    """Track-1 topic files of the rule-8 train subsample (ids taken from the main runs' score dumps)."""
    out = os.path.join(root, R, "n4", "rel", "t1")
    sub = {c: json.load(open(os.path.join(root, R, "scores", f"{n}.json")))["scores"]["train"]
           for c, n in (("1a", "1a_rerun"), ("1b", "1b_rerun"))}
    n = {"1a": 0, "1b": 0}
    for dom in T1:
        sd, od = os.path.join(data, "track1_tempo", dom), os.path.join(out, "track1_tempo", dom)
        os.makedirs(od, exist_ok=True)
        dst = os.path.join(od, "documents.jsonl")
        if not os.path.lexists(dst):
            os.symlink(os.path.abspath(os.path.join(sd, "documents.jsonl")), dst)
        keep_a = set(sub["1a"].get(dom, {}))
        keep_b = set(sub["1b"].get(dom, {}))
        with open(os.path.join(sd, "examples_train.jsonl"), encoding="utf-8") as f, \
                open(os.path.join(od, "examples_trainsub.jsonl"), "w", encoding="utf-8") as g:
            for line in f:
                if line.strip() and json.loads(line)["id"] in keep_a:
                    g.write(line if line.endswith("\n") else line + "\n")
                    n["1a"] += 1
        with open(os.path.join(sd, "steps_train.jsonl"), encoding="utf-8") as f, \
                open(os.path.join(od, "steps_trainsub.jsonl"), "w", encoding="utf-8") as g:
            for line in f:
                if not line.strip():
                    continue
                r = json.loads(line)
                r["steps"] = [s for s in r.get("steps", []) if s["step_id"] in keep_b]
                if r["steps"]:
                    g.write(json.dumps(r, ensure_ascii=False) + "\n")
                    n["1b"] += len(r["steps"])
    assert n == {"1a": sum(len(v) for v in sub["1a"].values()), "1b": sum(len(v) for v in sub["1b"].values())}, n
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--seed", type=int, required=True)
    a = ap.parse_args()
    import submit
    print("t1 trainsub release:", t1_release(a.root, a.data), flush=True)
    conf = json.load(open(os.path.join(a.root, "configs", "submission.json")))
    if a.seed > 0:
        for v in conf["variants"].values():
            if "llm" in v:
                v["llm"]["cache"] = f"{R}/n4/llm/s{a.seed}/t{v['track']}"
    cdir = os.path.join(a.root, R, "n4", "configs")
    os.makedirs(cdir, exist_ok=True)
    json.dump(conf, open(os.path.join(cdir, f"s{a.seed}.json"), "w"), indent=1)
    if a.seed == 0:
        return
    bodies = {1: [], 2: []}
    for label, data, split, variants in jobs(a.root, a.data):
        for v in variants:
            cfg = conf["variants"][v]
            for dom in cfg["domains"]:
                bodies[cfg["track"]] += [b for _, _, b, _ in submit.topics(data, split, cfg, dom)]
    ldir = os.path.join(a.root, R, "n4", "llm", f"s{a.seed}")
    os.makedirs(ldir, exist_ok=True)
    for tr, bs in bodies.items():
        uniq = sorted(set(bs))
        json.dump(uniq, open(os.path.join(ldir, f"bodies_t{tr}.json"), "w", encoding="utf-8"))
        print(f"seed {a.seed} track {tr}: {len(bs)} inputs, {len(uniq)} unique", flush=True)


if __name__ == "__main__":
    main()
