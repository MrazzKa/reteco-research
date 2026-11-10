#!/usr/bin/env python3
"""LOG rule 18: a second embedder (Qwen3-Embedding-4B) averaged with ReasonEmbed over the same top-50 pool.

Inputs: two reason_rerank.py --save-scores dumps over the SAME hybrid pool (they carry the fused scores ("none")
and the raw embedder scores ("raw")). E = mean(z(ReasonEmbed), z(second)) over the pool of each topic; grid as in
rule 8 (top-N by E; (1 - w) minmax(fused) + w minmax(E)). Chosen on train; adopted over the current system
(ReasonEmbed alone, its rule-8 way) with +0.005 and bootstrap lower bound > 0.

    python3 ensemble_embed.py --cond 2a_history --a R/scores/2ah_hybrid.json --b R/scores/2ah_hybrid_q3e.json ...
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bm25s_run import ndcg_fn  # noqa: E402
from hybrid import bootstrap  # noqa: E402
from llm_rerank import CONDS, query_texts  # noqa: E402
from reason_rerank import DEPTHS, WEIGHTS, rank  # noqa: E402
import tiebreak  # noqa: E402


def z(d):
    v = np.array(list(d.values()), dtype=np.float64)
    s = v.std()
    return {k: ((x - v.mean()) / s if s > 0 else 0.0) for k, x in d.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cond", required=True, choices=sorted(CONDS))
    ap.add_argument("--a", required=True, help="ReasonEmbed dump (current system)")
    ap.add_argument("--b", required=True, help="second embedder dump, same pool")
    ap.add_argument("--data", required=True)
    ap.add_argument("--kit", required=True)
    ap.add_argument("--margin", type=float, default=0.005)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    tiebreak.set_mode("sha1")
    ndcg = ndcg_fn(a.kit)
    A, B = json.load(open(a.a)), json.load(open(a.b))
    k, p = A["best"].split("=")
    cur_how = (k, float(p) if k == "interp" else int(p))
    hows = [("none", 0)] + [("top", n) for n in DEPTHS if n <= 50] + [("interp", w) for w in WEIGHTS]
    res = {}
    for sp in ("train", "dev"):
        for dom, tops in A["none"][sp].items():
            _, gold = query_texts(a.data, a.cond, sp, dom)
            for q, pool in tops.items():
                pool = [tuple(x) for x in pool]
                assert [d for d, _ in pool] == [d for d, _ in B["none"][sp][dom][q]], (dom, q)
                ra, rb = A["raw"][sp][dom][q], B["raw"][sp][dom][q]
                za, zb = z(ra), z(rb)
                e = {d: (za[d] + zb[d]) / 2 for d in ra}
                g = gold.get(q, set())
                res.setdefault(("current", None), {}).setdefault(sp, {}).setdefault(dom, []).append(
                    ndcg(rank(pool, cur_how, ra), g, 10))
                for how in hows:
                    for lab, sc in (("ensemble", e), ("second_only", rb)):
                        res.setdefault((lab, how), {}).setdefault(sp, {}).setdefault(dom, []).append(
                            ndcg(rank(pool, how, sc), g, 10))
    mac = {key: {sp: round(sum(sum(v) / len(v) for v in r[sp].values()) / len(r[sp]), 4) for sp in r} for key, r in res.items()}
    out = {"cond": a.cond, "current_way": A["best"], "current": mac[("current", None)], "grid": {}}
    for lab in ("ensemble", "second_only"):
        best = max(hows, key=lambda h: (mac[(lab, h)]["train"], -hows.index(h)))
        out["grid"][lab] = {f"{h[0]}={h[1]}": mac[(lab, h)] for h in hows}
        out[f"{lab}_best"] = {"how": f"{best[0]}={best[1]}", **mac[(lab, best)],
                              "train_minus_current": bootstrap(res[(lab, best)]["train"], res[("current", None)]["train"]),
                              "dev_minus_current": bootstrap(res[(lab, best)]["dev"], res[("current", None)]["dev"])}
    eb = out["ensemble_best"]
    out["adopted"] = eb["train"] - out["current"]["train"] >= a.margin and eb["train_minus_current"]["ci95"][0] > 0
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(out, open(a.out, "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "grid"}, indent=1))


if __name__ == "__main__":
    main()
