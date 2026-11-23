#!/usr/bin/env python3
"""N4 (LOG 2026-11-23 13:06; analysis, no choice): spread of the main numbers over LLM draws.

Realisations r0 (research cache) and r1..r3 (fresh generations, shuffled batch composition), each scored on dev and
on the rule-8 train subsample from the submit.py files under runs_v13/n4/sub/s<r>/ (official nDCG@10, domain macro).
Differences of the paper are computed within each realisation, then summarised (mean, SD, min, max, range).
"+LLM" uses the q systems of N1 (no LLM, so the same in every realisation).

    python3 n4_report.py --root .. --data ../../reteco_data_v11 --kit ../../RETECO/starter_kit \
        --out ../research/runs_v13/n4/report.json
"""
import argparse
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bm25s_run import ndcg_fn  # noqa: E402
from dense_index import T1, T2  # noqa: E402
from hybrid import read_run  # noqa: E402
from week1_run import load_qrels  # noqa: E402

R = "research/runs_v13"
# system -> (track, qrels name, path under s<r>/ with {sp} = dev | trainsub)
SYS = {"1a": (1, "qrels", "t1_{sp}/1a"), "1a hybrid": (1, "qrels", "t1_{sp}/1a__hybrid"),
       "1b": (1, "qrels_steps", "t1_{sp}/1b"), "1b hybrid": (1, "qrels_steps", "t1_{sp}/1b__hybrid"),
       "2a_history_rr": (2, "qrels", "t2_{sp}/2a_history_rr"), "2a_history": (2, "qrels", "t2_{sp}/2a_history_rr__re"),
       "2a history hybrid": (2, "qrels", "t2_{sp}/2a_history_rr__hybrid"),
       "M0": (2, "qrels", "t2_{sp}/2a_history_noans"), "LLM-written answers": (2, "qrels", "gen_{sp}/2a_history")}
QSYS = {"1a": ("n1_1a_q", 1, "qrels"), "1b": ("n1_1b_q", 1, "qrels_steps"), "2a_history": ("2ah_h0", 2, "qrels")}
DIFFS = {"reference answers - M0": ("2a_history", "M0"),
         "LLM-written answers - M0": ("LLM-written answers", "M0"),
         "+ReasonEmbed 1a": ("1a", "1a hybrid"), "+ReasonEmbed 1b": ("1b", "1b hybrid"),
         "+ReasonEmbed 2a history": ("2a_history", "2a history hybrid"),
         "+LLM 1a": ("1a", "q:1a"), "+LLM 1b": ("1b", "q:1b"), "+LLM 2a history": ("2a_history", "q:2a_history"),
         "+reranker 2a history": ("2a_history_rr", "2a_history")}
RESEARCH = {"dev": {"1a": 0.3667, "1b": 0.4053, "2a_history_rr": 0.5507, "2a_history": 0.5475, "M0": 0.4908,
                    "LLM-written answers": 0.4823, "1a hybrid": 0.3258, "1b hybrid": 0.3505, "2a history hybrid": 0.4601},
            "trainsub": {"1a": 0.3078, "1b": 0.3754, "2a_history_rr": 0.5999, "2a_history": 0.583, "M0": 0.522,
                         "LLM-written answers": 0.5205, "1a hybrid": 0.2823, "1b hybrid": 0.3442,
                         "2a history hybrid": 0.517}}


def summ(v):
    return {"values": [round(x, 4) for x in v], "mean": round(statistics.mean(v), 4),
            "sd": round(statistics.stdev(v), 4) if len(v) > 1 else 0.0, "min": round(min(v), 4),
            "max": round(max(v), 4), "range": round(max(v) - min(v), 4)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--kit", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--realisations", nargs="+", type=int, default=[0, 1, 2, 3])
    a = ap.parse_args()
    ndcg = ndcg_fn(a.kit)
    qcache = {}

    def gold(tr, name, dom, split):
        k = (tr, name, dom, split)
        if k not in qcache:
            sub = "track1_tempo" if tr == 1 else "track2_recor"
            qcache[k] = load_qrels(os.path.join(a.data, sub, dom, f"{name}_{split}.txt"))
        return qcache[k]

    # q systems of N1 (no LLM): per-topic dicts for both splits
    qpt = {}
    for s, (name, tr, qn) in QSYS.items():
        dump = json.load(open(os.path.join(a.root, R, "scores", f"{name}.json")))
        for sp, rsp in (("dev", "dev"), ("trainsub", "train")):
            for dom, qs in dump["scores"][rsp].items():
                g = gold(tr, qn, dom, rsp)
                qpt.setdefault((s, sp), {})[dom] = {q: ndcg([d for d, _ in v], g[q], 10) for q, v in qs.items()}
    rep = {"realisations": a.realisations, "systems": {}, "diffs": {}, "r0_check": {}, "identical_generations": {}}
    vals = {}
    for sp, rsp in (("dev", "dev"), ("trainsub", "train")):
        for r in a.realisations:
            base = os.path.join(a.root, R, "n4", "sub", f"s{r}")
            pt = {}
            for s, (tr, qn, pat) in SYS.items():
                d = os.path.join(base, pat.format(sp=sp))
                doms = T1 if tr == 1 else T2
                if not all(os.path.exists(os.path.join(d, f"{dom}.txt")) for dom in doms):
                    continue
                pt[s] = {}
                for dom in doms:
                    run = read_run(os.path.join(d, f"{dom}.txt"))
                    g = gold(tr, qn, dom, rsp)
                    pt[s][dom] = {q: ndcg([x for x, _ in run[q]], g[q], 10) for q in run if q in g}
            for s, (name, tr, qn) in QSYS.items():
                pt[f"q:{s}"] = qpt[(s, sp)]
            mac = {}
            for s, dd in pt.items():
                mac[s] = sum(sum(v.values()) / len(v) for v in dd.values()) / len(dd)
                vals.setdefault((sp, s), []).append(mac[s])
            # topic sets must agree for the paired differences
            for dname, (x, y) in DIFFS.items():
                if x in pt and y in pt:
                    assert all(set(pt[x][d]) == set(pt[y][d]) for d in pt[x]), (dname, sp, r)
                    vals.setdefault((sp, "diff:" + dname), []).append(mac[x] - mac[y])
            if r == 0:
                rep["r0_check"][sp] = {s: {"n4": round(mac[s], 4), "research": RESEARCH[sp].get(s),
                                           "equal": RESEARCH[sp].get(s) is None or round(mac[s], 4) == RESEARCH[sp][s]}
                                       for s in mac if not s.startswith("q:")}
            print(f"[{sp} r{r}] " + "  ".join(f"{s} {m:.4f}" for s, m in mac.items() if not s.startswith("q:")), flush=True)
    for (sp, s), v in vals.items():
        if s.startswith("diff:"):
            rep["diffs"].setdefault(sp, {})[s[5:]] = summ(v)
        elif not s.startswith("q:"):
            rep["systems"].setdefault(sp, {})[s] = summ(v)
        else:
            rep["systems"].setdefault(sp, {})[s] = {"value": round(v[0], 4)}
    # share of generations identical to the research cache
    from qexp_search import load_gen
    for r in a.realisations:
        if r == 0:
            continue
        for t in (1, 2):
            for p in ("reason", "hyde"):
                new = load_gen(os.path.join(a.root, R, "n4", "llm", f"s{r}", f"t{t}"), p)
                old = load_gen(os.path.join(a.root, R, "llm", f"t{t}"), p)
                same = sum(1 for k, v in new.items() if old.get(k) == v)
                rep["identical_generations"][f"s{r}.t{t}.{p}"] = {"n": len(new), "identical_to_research": same}
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(rep, open(a.out, "w"), indent=1)
    for sp in rep["diffs"]:
        print(f"== {sp}")
        for s, x in rep["systems"][sp].items():
            if "mean" in x:
                print(f"  {s:<24} mean {x['mean']:.4f} sd {x['sd']:.4f} range {x['range']:.4f}  {x['values']}")
        for s, x in rep["diffs"][sp].items():
            print(f"  {s:<28} mean {x['mean']:+.4f} sd {x['sd']:.4f} range {x['range']:.4f}  {x['values']}")
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
