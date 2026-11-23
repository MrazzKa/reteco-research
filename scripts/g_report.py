#!/usr/bin/env python3
"""Rule 20 (LOG 2026-11-23 12:58): Track-1 guidance as separate runs — choice on train, report, config block.

Candidates per sub-task: G1 (g joins BM25 / dense / ReasonEmbed query; main LLM texts) and G2 (the LLM also sees g).
Each candidate's final system = its train-chosen hybrid + the rule-8 ReasonEmbed way if it beats "none" on the train
subsample by >= +0.005 with bootstrap lower bound > 0 (else the hybrid). The candidate with the better final
train-subsample macro is the run `1a_guid` / `1b_guid`. Reported against the main run on the train subsample and
dev (paired bootstrap within domain, 10,000, seed 20260921). With --write-config the variant blocks are written into
configs/submission.json (`_separate_runs`).

    python3 g_report.py --root .. --data ../../reteco_data_v11 --kit ../../RETECO/starter_kit \
        --out ../research/runs_v13/guid/report.json [--write-config]
"""
import argparse
import copy
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bm25s_run import ndcg_fn  # noqa: E402
from dense_index import T1  # noqa: E402
from hybrid import bootstrap, qrels_for  # noqa: E402
from n1_report import ci_macro, macro  # noqa: E402

R = "research/runs_v13"
SUBS = {"1a": {"main": "1a_rerun", "qcond": "1a", "variant": "1a",
               "cands": {"G1": ("1a__q+r+h+g", "g_1a_G1", False), "G2": ("1a_g__q+r+h+g", "g_1a_G2", True)}},
        "1b": {"main": "1b_rerun", "qcond": "1b_query+step", "variant": "1b",
               "cands": {"G1": ("1b_query+step__q+r+h+g", "g_1b_G1", False),
                         "G2": ("1b_query+step_g__q+r+h+g", "g_1b_G2", True)}}}


def margin_ok(b):
    return bool(b) and b["diff"] >= 0.005 and b["ci95"][0] > 0


def per_topic(a, ndcg, dump, which, sp, qcond):
    out = {}
    for dom in T1:
        if dom not in dump[which].get(sp, {}):
            continue
        gold = qrels_for(a.data, 1, dom, sp, qcond)
        qs = sorted(dump[which][sp][dom])
        out[dom] = [ndcg([d for d, _ in dump[which][sp][dom][q]], gold[q], 10) for q in qs]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--kit", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--write-config", action="store_true")
    a = ap.parse_args()
    ndcg = ndcg_fn(a.kit)
    rr = json.load(open(os.path.join(a.root, R, "reason", "t1_reasonembed-4b.json")))
    rep = {"rule": "LOG 2026-11-23 12:58 (rule 20)", "subtasks": {}}
    conf_path = os.path.join(a.root, "configs", "submission.json")
    conf = json.load(open(conf_path))
    for sub, S in SUBS.items():
        hyb = json.load(open(os.path.join(a.root, R, "guid", "t1", f"hybrid_{sub}.json")))
        main_dump = json.load(open(os.path.join(a.root, R, "scores", f"{S['main']}.json")))
        pt_main = {sp: per_topic(a, ndcg, main_dump, "scores", sp, S["qcond"]) for sp in ("train", "dev")}
        res = {"main": {"name": S["main"], "train": round(macro(pt_main["train"]), 4),
                        "dev": round(macro(pt_main["dev"]), 4), "dev_ci": ci_macro(pt_main["dev"])}}
        pts = {}
        for c, (hcond, name, llm) in S["cands"].items():
            row = rr[name]
            hs = hyb["conditions"][hcond]["systems"]
            tb = row.get("train_bootstrap_best_minus_none")
            use = margin_ok(tb)
            way = row["best_on_train"] if use else "none=0"
            dump = json.load(open(os.path.join(a.root, R, "scores", f"{name}.json")))
            which = "scores" if use else "none"
            pt = {sp: per_topic(a, ndcg, dump, which, sp, S["qcond"]) for sp in ("train", "dev")}
            chk = {sp: round(macro(pt[sp]), 4) for sp in ("train", "dev")}
            assert chk == {sp: row["by_how"][way][sp] for sp in ("train", "dev")}, (name, chk, row["by_how"][way])
            pts[c] = pt
            res[c] = {"name": name, "llm_sees_g": llm, "hybrid_cfg": hs["linear*"]["cfg"],
                      "hybrid_train_full": hs["linear*"]["train_macro"], "hybrid_dev": hs["linear*"]["dev_macro"],
                      "reasonembed_best_on_train": row["best_on_train"], "reasonembed_train_boot": tb,
                      "reasonembed_used": way, "train": chk["train"], "dev": chk["dev"],
                      "dev_ci": ci_macro(pt["dev"]),
                      "minus_main": {sp: bootstrap(pt[sp], pt_main[sp]) for sp in ("train", "dev")},
                      "dev_per_domain_minus_main": {d: round(sum(pt["dev"][d]) / len(pt["dev"][d])
                                                             - sum(pt_main["dev"][d]) / len(pt_main["dev"][d]), 4)
                                                    for d in pt["dev"]},
                      "row": {k: row[k] for k in ("by_how", "docs_encoded", "queries_encoded") if k in row}}
            for k in ("guid_base_cut", "guid_empty"):
                if k in row:
                    res[c][k] = row[k]
        best = max(S["cands"], key=lambda c: (res[c]["train"], c == "G1"))  # tie -> G1 (no LLM change)
        mm = res[best]["minus_main"]["train"]
        res["chosen"] = best
        res["margin_would_be_met_on_train"] = margin_ok(mm)
        res["G2_minus_G1"] = {sp: bootstrap(pts["G2"][sp], pts["G1"][sp]) for sp in ("train", "dev")}
        rep["subtasks"][sub] = res
        print(f"[{sub}] main {res['main']['train']}/{res['main']['dev']} | G1 {res['G1']['train']}/{res['G1']['dev']} "
              f"({res['G1']['reasonembed_used']}) | G2 {res['G2']['train']}/{res['G2']['dev']} ({res['G2']['reasonembed_used']})"
              f" -> {best}; minus main train {mm} dev {res[best]['minus_main']['dev']}", flush=True)
        if a.write_config:
            base = conf["variants"][S["variant"]]
            v = copy.deepcopy(base)
            c = res[best]
            v["run_id"] = f"UA_{sub}_guid"
            v["guidance"] = {"components": ["q", "r", "h", "g"], "llm_input": c["llm_sees_g"], "fallback": S["variant"],
                             "text": "guidance.guidance_text: key_time_anchors, temporal_intent, retrieval_reasoning, "
                                     "retrieval_plan actions (plan gold_ids dropped, gold_passage_annotations never "
                                     "read, ids asserted absent)",
                             "reasonembed_query": "query text + '\\nGuidance: ' + g, query cut first (512 tokens)"}
            if c["llm_sees_g"]:
                v["llm"]["cache"] = f"{R}/guid/llm/t1"
                v["llm"]["input"] = "the main body + '\\n\\nSearch guidance (task annotation): ' + g (question cut, never g)"
            v["variant"] = "q+r+h+g"
            v["bm25"]["text"] = "q \\n r \\n h \\n g"
            v["dense"]["query_vector"] = "normalised sum of e_query(q), e_query(r), e_doc(h), e_query(g)"
            v["hybrid"] = {"kind": "linear", **{k: c["hybrid_cfg"][k] for k in ("kb", "kd", "norm", "alpha")}}
            k_, p_ = c["reasonembed_used"].split("=")
            if k_ == "none":
                v["reasonembed"]["use"] = False
            else:
                v["reasonembed"]["how"] = k_
                v["reasonembed"]["w"] = float(p_) if k_ == "interp" else int(p_)  # submit.py: (how, w); top: w = N
            v["source"] = (f"rule 20 (LOG 2026-11-23): candidate {best} chosen on the train subsample "
                           f"({c['train']} vs main {res['main']['train']}); separate run, the main run is unchanged")
            v["dev_research"] = c["dev"]
            v["train_research"] = c["train"]
            v["role"] = "separate run (rule 20, Track-1 guidance); the supervisor decides"
            conf["variants"][f"{sub}_guid"] = v
            sep = conf.setdefault("_separate_runs", {})
            sep.setdefault(sub, [])
            if f"{sub}_guid" not in sep[sub]:
                sep[sub].append(f"{sub}_guid")
    if a.write_config:
        conf["_separate_runs"]["why"] = conf["_separate_runs"].get("why", "") + (
            "; rule 20 (2026-11-23): 1a_guid / 1b_guid use the Track-1 query-side guidance (a test input since the "
            "organisers' mail of 18.11 / 21.11)")
        json.dump(conf, open(conf_path, "w"), indent=1, ensure_ascii=False)
        print(f"wrote the guidance variants into {conf_path}")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(rep, open(a.out, "w"), indent=1)
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
