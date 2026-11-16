#!/usr/bin/env python3
"""S2c: write the `2a_history_sr` block of configs/submission.json from the rule-19 outputs (no hand-typed
numbers): the chosen candidate (sr/report.json), its fusion (sr/t2/hybrid.json, linear*), ReasonEmbed way
(reason/t2_reasonembed-4b.json) and reranker way (rerank/rule16_sr_<S>_qwen3-reranker-0.6b.json). Everything
else is copied from `2a_history_rr`. The block is a separate run: it enters neither `_main_runs` nor `_auto_2a`.

    python3 sr_config.py --runs ../research/runs_v13 --config ../configs/submission.json
"""
import argparse
import copy
import json
import os


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True)
    ap.add_argument("--config", required=True)
    a = ap.parse_args()
    R = a.runs
    rep = json.load(open(os.path.join(R, "sr", "report.json")))
    ch = rep["chosen"]  # S1 | S2
    name = {"S1": "sr_S1", "S2": "sr_S2", "S3": "sr_S3"}[ch]
    cond = {"S1": "2a_hist3qa__q+r+h+s", "S2": "2a_hist3qa__q+s+h", "S3": "2a_hist3qa_sr__q+r+h"}[ch]
    comp = {"S1": ["q", "r", "h", "s"], "S2": ["q", "s", "h"], "S3": ["q", "r", "h"]}[ch]
    hf = "hybrid_s3.json" if ch == "S3" else "hybrid.json"
    hyb = json.load(open(os.path.join(R, "sr", "t2", hf)))["conditions"][cond]["systems"]["linear*"]["cfg"]
    rea = json.load(open(os.path.join(R, "reason", "t2_reasonembed-4b.json")))[name]
    rr = json.load(open(os.path.join(R, "rerank", f"rule16_{name}_qwen3-reranker-0.6b.json")))
    conf = json.load(open(a.config))
    v = copy.deepcopy(conf["variants"]["2a_history_rr"])
    v["run_id"] = "UA_2a_history_sr"
    v["variant"] = "+".join(comp)
    v["bm25"]["text"] = " \\n ".join(comp)
    v["dense"]["query_vector"] = "normalised sum of " + ", ".join(
        {"q": "e_query(q)", "r": "e_query(r)", "h": "e_doc(h)", "s": "e_query(s)"}[c] for c in comp)
    v["hybrid"] = {k: hyb[k] for k in ("kind", "kb", "kd", "norm", "alpha") if k in hyb}
    k, p = rea["best_on_train"].split("=")
    v["reasonembed"]["how"] = k
    v["reasonembed"]["w"] = float(p) if k == "interp" else int(p)
    v["reasonembed"]["query"] = ("Hb query (current question first + <= 3 earlier Q/A turns, whitespace-collapsed) + "
                                 "'\\nReasoning: ' + s; history cut so that the instructed query fits max_len (never s)")
    best = rr["best_on_train"]  # e.g. interp@20_w0.4 | only@10 | none@20
    kind, rest = best.split("@")
    depth = int(rest.split("_")[0])
    if kind == "none" or not rr["adopted"]:  # rule 16 margin (LOG 2026-11-16 15:20)
        v.pop("llm_rerank", None)
    else:
        v["llm_rerank"]["how"] = kind
        v["llm_rerank"]["depth"] = depth
        v["llm_rerank"]["w"] = float(rest.split("_w")[1]) if "_w" in rest else 0.0
        v["llm_rerank"]["query"] = "same construction as the ReasonEmbed query, history cut to query_len (never s)"
    v["sr"] = {"components": comp, "fallback": "2a_history_rr", "field": "subquestion_reasoning (current turn; text only, "
               "never subquestion_reasoning_metadata)", "rule": "LOG rule 19 (2026-11-16)", "candidate": ch,
               "llm_input": ch == "S3"}
    v["history"]["reasonembed_query"] = "see reasonembed.query (Hb text + SR)"
    if ch == "S3":
        v["history"]["llm_input"] = ("Hb input + 'What the documents should cover (task annotation): <SR>' after the "
                                     "current question (llm_expand.history_body_sr)")
    row = next(r for r in rep["rows"] if r["system"] == rep["chosen_system"])
    v["train_research"], v["dev_research"] = row["train"], row["dev"]
    v["source"] = (f"rule 19 candidate {ch} (BM25 {' + '.join(comp)}; s = subquestion_reasoning), fusion "
                   f"{hyb.get('norm')} a {hyb.get('alpha')} on train, ReasonEmbed {rea['best_on_train']}, reranker {best if rr['adopted'] else 'not adopted (rule 16 margin)'} "
                   f"(train subsample); base = 2a_history_rr")
    v["role"] = "separate run (rule 19, subquestion_reasoning); not main — the supervisor decides"
    conf["variants"]["2a_history_sr"] = v
    conf["_separate_runs"] = {"2a": ["2a_history_sr"], "why": "rule 19: tested as a separate run (supervisor, 11.11)"}
    json.dump(conf, open(a.config, "w"), indent=1, ensure_ascii=False)
    open(a.config, "a").write("\n")
    print(json.dumps({k: v[k] for k in ("variant", "hybrid", "source", "train_research", "dev_research")}, indent=1))


if __name__ == "__main__":
    main()
