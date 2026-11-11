#!/usr/bin/env python3
"""C1: report of the full cold dress rehearsal (research/runs_v13/cold_full; LOG 2026-11-10 21:45, 2026-11-11).

Reads the official scores of every run (score.json from score_submission.py), compares each cold run with the warm
dev run of the same name (research/runs_v13/submit/dev; paired bootstrap, topics within domain), counts identical
LLM generations against the B3b fresh draw (research/runs_v13/nondet/llm) and against the research cache, and sums
the stage timings into wall time per track with a test-size estimate.

    python3 c1_report.py --runs ../research/runs_v13 --data ../../reteco_data_v11 --kit ../../RETECO/starter_kit \
        --pregen-t1 800.8 --out ../research/runs_v13/cold_full/c1_report.json
"""
import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bm25s_run import ndcg_fn  # noqa: E402
from dense_index import T1, T2  # noqa: E402
from hybrid import bootstrap, qrels_for, read_run  # noqa: E402
from nondet_report import load_gen  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
TEST = {"1a": 350, "1b": 820, "2a": 200}  # organisers' figures (as in cold_report.py)
DEV = {"1a": 519, "1b": 1214, "2a": 858}
TOL = 0.005  # pass criterion written before the run


def sub_of(q):
    return "1a" if q == "1a" else ("1b" if q.startswith("1b") else "2a")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--kit", required=True)
    ap.add_argument("--pregen-t1", type=float, required=True,
                    help="Track-1 pre-generation seconds (queue_1110k.log; the file was overwritten by the Track-2 call)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    R, C = a.runs, os.path.join(a.runs, "cold_full")
    ndcg = ndcg_fn(a.kit)
    score = json.load(open(os.path.join(C, "score.json")))
    dec = json.load(open(os.path.join(C, "sub", "2a_auto", "decision.json")))
    out = {"runs": {}, "generations": {}, "timing": {}, "auto_2a": dec["summary"]}
    for v, s in score.items():
        mp = os.path.join(C, "sub", v, "manifest.json")
        src = v if os.path.exists(mp) else max(dec["summary"], key=dec["summary"].get)
        man = json.load(open(os.path.join(C, "sub", src, "manifest.json")))
        tr, q = man["config"]["track"], man["config"]["query"]
        A, B = {}, {}
        for dom in (T1 if tr == 1 else T2):
            g = qrels_for(a.data, tr, dom, "dev", "1b" if q.startswith("1b") else "x")
            rc = read_run(os.path.join(C, "sub", v, f"{dom}.txt"))
            rw = read_run(os.path.join(R, "submit", "dev", src, f"{dom}.txt"))
            A[dom] = [ndcg([d for d, _ in rc.get(t, [])], g[t], 10) for t in sorted(g)]
            B[dom] = [ndcg([d for d, _ in rw.get(t, [])], g[t], 10) for t in sorted(g)]
        checks = s["checks"].values()
        out["runs"][v] = {"sub": sub_of(q), "official": s["official_macro_ndcg10"], "research": s["research_dev"],
                          "diff": s["diff_vs_research"], "within_tol": abs(s["diff_vs_research"]) <= TOL,
                          "cold_minus_warm": bootstrap(A, B),
                          "checker_ok": all(c["format_checker_exit"] == 0 for c in checks),
                          "sanity_ok": all(c["judged_missing"] == 0 and c["duplicates"] == 0 and c["unknown_docs"] == 0
                                           and c["nonincreasing_violations"] == 0 for c in checks)}
    for t in ("t1", "t2"):
        for p in ("reason", "hyde"):
            cold = load_gen(os.path.join(C, "cache", "llm", t, f"{p}.jsonl"))
            b3b = load_gen(os.path.join(R, "nondet", "llm", t, f"{p}.jsonl"))
            res = load_gen(os.path.join(R, "llm", t, f"{p}.jsonl"))
            out["generations"][f"{t}_{p}"] = {
                "cold": len(cold),
                "identical_to_b3b_fresh": sum(cold[k] == b3b.get(k) for k in cold),
                "identical_to_research_cache": sum(cold[k] == res.get(k) for k in cold)}
    # timing: stage sums per variant (manifests) + pre-generation per track
    walls = {"1": a.pregen_t1, "2": json.load(open(os.path.join(C, "sub", "pregenerate_timing.json")))["pregenerate_total_s"]}
    pregen = dict(walls)
    per_sub = {"1a": 0.0, "1b": 0.0, "2a": 0.0}
    fixed = {"1a": 0.0, "1b": 0.0, "2a": 0.0}
    rows = []
    for mp in sorted(glob.glob(os.path.join(C, "sub", "*", "manifest.json"))):
        m = json.load(open(mp))
        t = m["timing_s"]
        wall = sum(v for k, v in t.items() if k.endswith("_s"))
        sb = sub_of(m["config"]["query"])
        walls[str(m["config"]["track"])] += wall
        per_sub[sb] += wall - t.get("bm25_index_s", 0)
        fixed[sb] += t.get("bm25_index_s", 0)
        rows.append({"variant": m["variant"], "sub": sb, "topics": m["n_topics"], "wall_s": round(wall, 1),
                     "bm25_index_s": t.get("bm25_index_s", 0), "reasonembed_s": t.get("reasonembed_s", 0),
                     "reasonembed_new_docs": t.get("reasonembed_new_docs", 0),
                     "llm_rerank_s": t.get("llm_rerank_s", 0), "llm_rerank_new_pairs": t.get("llm_rerank_new_pairs", 0)})
    # test estimate: per-topic parts scale with topics, BM25 indexing is per domain (fixed); pre-generation scales
    # with LLM inputs (Track 1: 1a queries + 1b steps; Track 2: turns)
    t1_scale = (TEST["1a"] + TEST["1b"]) / (DEV["1a"] + DEV["1b"])
    est = {sb: per_sub[sb] * TEST[sb] / DEV[sb] + fixed[sb] for sb in per_sub}
    est_total = sum(est.values()) + pregen["1"] * t1_scale + pregen["2"] * TEST["2a"] / DEV["2a"]
    out["timing"] = {"rows": rows, "pregenerate_s": pregen, "wall_s_track": {k: round(v) for k, v in walls.items()},
                     "wall_s_total": round(sum(walls.values())), "test_estimate_s": round(est_total),
                     "test_estimate_by_sub_s": {k: round(v) for k, v in est.items()}}
    json.dump(out, open(a.out, "w"), indent=1)
    for v, x in out["runs"].items():
        print(f"{v:<16} official {x['official']:.4f} research {x['research']:.4f} diff {x['diff']:+.4f} "
              f"ok {x['within_tol']} checker {x['checker_ok']} sanity {x['sanity_ok']} cold-warm {x['cold_minus_warm']}")
    print(json.dumps(out["generations"]))
    print("wall per track", out["timing"]["wall_s_track"], "total", out["timing"]["wall_s_total"],
          "test estimate", out["timing"]["test_estimate_s"], out["timing"]["test_estimate_by_sub_s"])


if __name__ == "__main__":
    main()
