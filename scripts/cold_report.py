#!/usr/bin/env python3
"""B3: summary of the cold run (empty LLM / ReasonEmbed / reranker caches) on a slice of a synthetic test release,
from the submit.py manifests, and a scaled estimate for the full test (~350 1a queries, ~820 1b steps at the dev
ratio of 2.34 steps per query, ~200 2a turns; organisers' figures, News/README).

    python3 cold_report.py --cold ../research/runs_v13/cold --log ../research/runs_v13/logs/queue_1110e.log
"""
import argparse
import glob
import json
import os
import re

TEST = {"1a": 350, "1b": 820, "2a": 200}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cold", required=True)
    ap.add_argument("--log", required=True)
    a = ap.parse_args()
    rows, by_sub = [], {"1a": 0.0, "1b": 0.0, "2a": 0.0}
    n_sub = {}
    for man in sorted(glob.glob(os.path.join(a.cold, "sub", "*", "manifest.json"))):
        m = json.load(open(man))
        v, t = m["variant"], m["timing_s"]
        wall = sum(t.get(k, 0) for k in ("llm_total_s", "bm25_index_s", "bm25_search_s", "dense_index_load_s",
                                         "dense_search_s", "fusion_s", "reasonembed_s", "llm_rerank_s"))
        q = m["config"]["query"]
        sub = "1a" if q == "1a" else ("1b" if q.startswith("1b") else "2a")
        by_sub[sub] += wall
        n_sub[sub] = max(n_sub.get(sub, 0), m["n_topics"])
        notes = ", ".join(f"{k} {t[k]}" for k in ("llm_reason_generated", "reasonembed_new_docs", "llm_rerank_new_pairs") if k in t)
        rows.append({"part": f"{v} ({', '.join(m['domains'])})", "topics": m["n_topics"], "wall_s": wall,
                     "per_topic_s": wall / max(1, m["n_topics"]), "notes": notes, "timing": t})
    log = open(a.log).read()
    mt = re.search(r"COLD track1 (\d+) s, track2 (\d+) s", log)
    totals = {"track1_s": int(mt.group(1)), "track2_s": int(mt.group(2))} if mt else {}
    est = {s_: by_sub[s_] / max(1, n_sub.get(s_, 1)) * TEST[s_] for s_ in TEST if n_sub.get(s_)}
    out = {"about": "Synthetic test release (dev topics of iota, quant / drones, politics; gold removed), every cache empty "
                    "(LLM generations, ReasonEmbed vectors, reranker scores) in research/runs_v13/cold; corpus artefacts "
                    "(dense corpus index, MaxP passages) prebuilt. Wall time = sum of the stage timings of submit.py; LLM "
                    "time includes ~2 min of vLLM start-up per prompt and variant that needs generations.",
           "rows": rows, "totals_measured": totals, "per_subtask_s": by_sub, "topics_per_subtask": n_sub,
           "scaled_full_test_s": est,
           "estimate": ("Scaled to the full test by topics per sub-task (sum over all variants of the sub-task): " +
                        ", ".join(f"{k} ≈ {v / 60:.0f} min" for k, v in est.items()) +
                        f"; total ≈ {sum(est.values()) / 3600:.1f} h (+ BM25 indexing is per domain, not per topic, so "
                        "this over-counts it for Track 1).")}
    json.dump(out, open(os.path.join(a.cold, "cold_report.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=1))
    for r in rows:
        print(r["part"], r["topics"], round(r["wall_s"]), r["notes"])


if __name__ == "__main__":
    main()
