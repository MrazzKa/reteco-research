#!/usr/bin/env python3
"""Week-5 final system per sub-track (rules 6-8) vs the week-4 final system, -> runs_v13/final.json.

Week-4 systems are re-scored with the sha1 tie key (runs_v13 step 1): hybrids from the runs_v13
hybrid reports; the Track-2 current-turn cross-encoder system is recomputed per dev topic from
the cached cross-encoder scores (top 50 reordered, rerank_ce.py logic) for the paired bootstrap.

    python3 final_systems.py --out ../research/runs_v13/final.json
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bm25s_run import ndcg_fn  # noqa: E402
from dense_index import T2  # noqa: E402
from hybrid import Query, bootstrap, qrels_for, read_run, system  # noqa: E402
import tiebreak  # noqa: E402

R = "../research/runs_v13"


def jl(p):
    return json.load(open(os.path.join(R, p)))


def hyb(path, cond):
    c = jl(path)["conditions"][cond]
    s = c["systems"]["linear*"]
    return s["train_macro"], s["dev_macro"], c["dev_per_topic"]["linear*"]


def ce_week4_dev(data, kit):
    """Week-4 Track-2 current system (bge-base hybrid + CE top 50) per dev topic, sha1 ties."""
    ndcg = ndcg_fn(kit)
    rep = jl("hybrid/bge-base_L512_t2.json")["conditions"]["2a_current"]
    cfg = rep["systems"]["linear*"]["cfg"]
    n = int(jl("ce/t2.json")["2a_current"]["chosen_depth_on_train"])
    out = {}
    for dom in T2:
        pre = f"t2_{dom}_dev"
        bm = read_run(os.path.join(R, "bm25/t2/runs", f"{pre}_2a_current.tsv"))
        de = read_run(os.path.join(R, "dense/bge-base_L512/t2/runs", f"{pre}_2a_current.tsv"))
        sc = json.load(open(os.path.join(R, "ce", f"scores_t2_{dom}_dev_2a_current.json")))
        gold = qrels_for(data, 2, dom, "dev", "2a_current")
        v = []
        for q, g in sorted(gold.items()):
            h = system(Query(bm.get(q, []), de.get(q, [])), cfg)
            head = sorted(h[:n], key=lambda d: (-sc[q][d], tiebreak.key(d)))
            v.append(ndcg(head + h[n:], g, 10))
        out[dom] = v
    return out


def macro(d):
    return round(sum(sum(v) / len(v) for v in d.values()) / len(d), 4)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="../../reteco_data_v11")
    ap.add_argument("--kit", default="../../RETECO/starter_kit")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    cmp_ = jl("tiebreak/compare.json")
    final = {}
    # week-4 systems, sha1 ties
    w4 = {"1a": hyb("hybrid/bge-small_L256_t1.json", "1a"),
          "1b_query+step": hyb("hybrid/bge-small_L256_t1.json", "1b_query+step"),
          "2a_history": hyb("hybrid/bge-base_L512_t2.json", "2a_history")}
    ce_dev = ce_week4_dev(a.data, a.kit)
    w4_ce = jl("ce/t2.json")["2a_current"]
    reason = {}
    for t in (1, 2):
        p = os.path.join(R, f"reason/t{t}_reasonembed-4b.json")
        if os.path.exists(p):
            reason.update(json.load(open(p)))
    for cond, track in (("1a", 1), ("1b_query+step", 1), ("2a_current", 2)):
        s6, s7 = jl(f"select/rule6_{cond}.json"), jl(f"select/rule7_{cond}.json")
        v = s6["chosen"]
        if s7["adopted"] and s7["chosen"].startswith("maxp"):
            path = f"maxp/t{track}/" + ("hybrid_2a_current.json" if track == 2 else f"hybrid_{cond[:2]}.json")
            name = f"BM25 + MaxP dense hybrid, query {v}"
        else:
            path = f"qexp/t{track}/" + ("hybrid_2a_current.json" if track == 2 else f"hybrid_{cond[:2]}.json")
            name = f"BM25 + dense hybrid, query {v}"
        tr, dv, pt = hyb(path, f"{cond}__{v}")
        r8 = reason.get(f"{cond}__{v}")
        stage = None
        if r8 and r8.get("best_on_train", "none=0") != "none=0":
            tb = r8["train_bootstrap_best_minus_none"]
            bh = r8["by_how"]
            gain = bh[r8["best_on_train"]]["train"] - bh["none=0"]["train"]
            if gain >= 0.005 and tb and tb["ci95"][0] > 0:
                stage = r8
        if stage:
            name += f" + ReasonEmbed ({stage['best_on_train']}, top {stage['pool']})"
            tr, dv = stage["by_how"][stage["best_on_train"]]["train"], stage["by_how"][stage["best_on_train"]]["dev"]
            pt = stage["dev_per_topic_best"]
        if cond == "2a_current":
            base_pt, w4dev = ce_dev, w4_ce["by_depth"][str(w4_ce["chosen_depth_on_train"])]["dev_macro"]
            w4name = "bge-base hybrid + cross-encoder top 50"
        else:
            base_pt, w4dev = w4[cond][2], w4[cond][1]
            w4name = "bge-small L256 hybrid"
        final[cond] = {"system": name, "train": tr, "dev": dv, "week4_system": w4name,
                       "week4_dev": cmp_[cond]["ce" if cond == "2a_current" else "hybrid"]["dev_old"],
                       "week4_dev_sha1": w4dev, "week4_dev_sha1_recomputed": macro(base_pt),
                       "dev_boot": bootstrap(pt, base_pt)}
    tr, dv, _ = w4["2a_history"]
    final["2a_history"] = {"system": "BM25 + bge-base hybrid (week 4, not expanded)", "train": tr, "dev": dv,
                           "week4_system": "same", "week4_dev": cmp_["2a_history"]["hybrid"]["dev_old"],
                           "week4_dev_sha1": dv, "dev_boot": None}
    json.dump(final, open(a.out, "w"), indent=1)
    for c, r in final.items():
        print(f"{c:<14} {r['system']:<60} train {r['train']}  dev {r['dev']}  | week-4 dev {r['week4_dev']} "
              f"(sha1 {r['week4_dev_sha1']})  boot {r['dev_boot']}")


if __name__ == "__main__":
    main()
