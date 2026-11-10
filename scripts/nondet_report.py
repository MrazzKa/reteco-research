#!/usr/bin/env python3
"""B3b: run-to-run noise from LLM nondeterminism on dev. Compares the dev runs built with a fresh LLM cache
(research/runs_v13/nondet/sub) against the cached ones (research/runs_v13/submit/dev): macro nDCG@10 of each,
paired bootstrap of fresh − cached (topics within domain), per-domain differences, and the share of identical
generations (same key, same text).

    python3 nondet_report.py --runs ../research/runs_v13 --data ../../reteco_data_v11 --kit ../../RETECO/starter_kit
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bm25s_run import ndcg_fn  # noqa: E402
from hybrid import bootstrap, qrels_for, read_run  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def load_gen(p):
    out = {}
    if os.path.exists(p):
        for ln in open(p, encoding="utf-8"):
            if ln.strip():
                r = json.loads(ln)
                out[r["key"]] = r["output"]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--kit", required=True)
    a = ap.parse_args()
    R = a.runs
    ndcg = ndcg_fn(a.kit)
    conf = json.load(open(os.path.join(os.path.dirname(HERE), "configs", "submission.json")))
    out = {"generations": {}, "variants": {}}
    for t in ("t1", "t2"):
        for pr in ("reason", "hyde"):
            f, w = load_gen(f"{R}/nondet/llm/{t}/{pr}.jsonl"), load_gen(f"{R}/llm/{t}/{pr}.jsonl")
            out["generations"][f"{t}_{pr}"] = {"fresh": len(f), "identical": sum(f[k] == w.get(k) for k in f)}
    for v in sorted(os.listdir(f"{R}/nondet/sub")):
        if not os.path.isdir(f"{R}/nondet/sub/{v}"):
            continue
        cfg = conf["variants"][v]
        tr = cfg["track"]
        fresh, cached = {}, {}
        for dom in cfg["domains"]:
            g = qrels_for(a.data, tr, dom, "dev", "1b" if cfg["query"].startswith("1b") else "x")
            for lab, src, store in (("fresh", f"{R}/nondet/sub", fresh), ("cached", f"{R}/submit/dev", cached)):
                r = read_run(f"{src}/{v}/{dom}.txt")
                store[dom] = [ndcg([d for d, _ in r.get(q, [])], g[q], 10) for q in sorted(g)]
        mac = lambda x: round(sum(sum(v_) / len(v_) for v_ in x.values()) / len(x), 4)
        out["variants"][v] = {"fresh": mac(fresh), "cached": mac(cached), "fresh_minus_cached": bootstrap(fresh, cached),
                              "per_domain_diff": {d: round(sum(fresh[d]) / len(fresh[d]) - sum(cached[d]) / len(cached[d]), 4)
                                                  for d in fresh}}
        x = out["variants"][v]
        print(f"{v:<16} fresh {x['fresh']:.4f} cached {x['cached']:.4f} diff {x['fresh_minus_cached']}", flush=True)
    print(json.dumps(out["generations"]))
    json.dump(out, open(f"{R}/nondet/report.json", "w"), indent=1)


if __name__ == "__main__":
    main()
