#!/usr/bin/env python3
"""Rule 19 report (LOG 2026-11-16 14:26): `subquestion_reasoning` (SR) as a separate 2a run.

Reads the outputs of queue_1116b.sh (hybrid grid, ReasonEmbed and reranker reports, saved runs), picks the
candidate (S1 = q+r+h+s, S2 = q+s+h) with the better final train-subsample macro as `2a_history_sr`, and reports
its difference to the main run `2a_history_rr` (train subsample and dev; paired bootstrap within domain, 10,000,
seed 20260921), by source (BRIGHT / StackExchange), by turn group and depth (t2_breakdown.py), plus the two
analysis systems (SR without history; SR alone). No adoption: the main run does not change (supervisor).

    python3 sr_report.py --runs ../research/runs_v13 --data ../../reteco_data_v11 --kit ../../RETECO/starter_kit \
        --out ../research/runs_v13/sr/report.json
"""
import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bm25s_run import ndcg_fn  # noqa: E402
from dense_index import T2  # noqa: E402
from hybrid import bootstrap, qrels_for, read_run  # noqa: E402
from week1_run import BRIGHT_DOMAINS  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = "qwen3-reranker-0.6b"


def per_topic(data, pat, split, ndcg, only=None):
    """{dom: [nDCG@10 per topic]} over sorted topic ids (all judged topics, or those in `only`)."""
    out = {}
    for dom in T2:
        run = read_run(pat.format(pre=f"t2_{dom}_{split}", dom=dom))
        gold = qrels_for(data, 2, dom, split, "x")
        qs = sorted(q for q in gold if (only is None or q in only.get(dom, set())))
        out[dom] = [ndcg([d for d, _ in run.get(q, [])], gold[q], 10) for q in qs]
    return out


def macro(pt, doms=None):
    doms = [d for d in (doms or pt) if pt.get(d)]
    return round(sum(sum(pt[d]) / len(pt[d]) for d in doms) / len(doms), 4)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--kit", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    R = a.runs
    ndcg = ndcg_fn(a.kit)
    hyb = json.load(open(os.path.join(R, "sr", "t2", "hybrid.json")))
    rea = json.load(open(os.path.join(R, "reason", "t2_reasonembed-4b.json")))
    rr = {k: json.load(open(os.path.join(R, "rerank", f"rule16_{k}_{MODEL}.json")))
          for k in ("2a_history", "sr_S1", "sr_S2")}
    F, S, RR = f"{R}/foreign/runs", f"{R}/sr/runs", f"{R}/rerank/runs"
    pats = {"2a_history_rr (main)": f"{RR}/{{pre}}_2a_history__rr.tsv",
            "2a_history (no reranker)": f"{F}/{{pre}}_2ah_hybrid__best.tsv",
            "S1 final (q+r+h+s)": f"{RR}/{{pre}}_sr_S1__rr.tsv",
            "S2 final (q+s+h)": f"{RR}/{{pre}}_sr_S2__rr.tsv",
            "S1 before reranker": f"{S}/{{pre}}_sr_S1__best.tsv",
            "S2 before reranker": f"{S}/{{pre}}_sr_S2__best.tsv",
            "B current turn": f"{F}/{{pre}}_2a_nomaxp__best.tsv",
            "B + SR (no history)": f"{S}/{{pre}}_sr_cur__best.tsv",
            "SR only": f"{S}/{{pre}}_sr_only__best.tsv",
            "H0q+RE (no answers)": f"{F}/{{pre}}_2ahq_h0q__best.tsv"}
    # train subsample = the topics of the main run's train file (rule-8 subsample)
    sub = {dom: set(read_run(pats["2a_history_rr (main)"].format(pre=f"t2_{dom}_train"))) for dom in T2}
    pt = {sp: {lab: per_topic(a.data, p, sp, ndcg, sub if sp == "train" else None) for lab, p in pats.items()}
          for sp in ("train", "dev")}
    rows = []
    stage = {"S1": "2a_hist3qa__q+r+h+s", "S2": "2a_hist3qa__q+s+h", "B + SR": "2a_current__q+r+h+s", "SR only": "2a_current__s"}
    for lab in pats:
        r = {"system": lab, "train": macro(pt["train"][lab]), "dev": macro(pt["dev"][lab]),
             "train_bright": macro(pt["train"][lab], sorted(BRIGHT_DOMAINS)),
             "train_se": macro(pt["train"][lab], [d for d in T2 if d not in BRIGHT_DOMAINS]),
             "dev_bright": macro(pt["dev"][lab], sorted(BRIGHT_DOMAINS)),
             "dev_se": macro(pt["dev"][lab], [d for d in T2 if d not in BRIGHT_DOMAINS])}
        rows.append(r)
    cand = {"S1": "S1 final (q+r+h+s)", "S2": "S2 final (q+s+h)"}
    chosen = max(cand, key=lambda k: (next(r["train"] for r in rows if r["system"] == cand[k]), k == "S1"))
    base = "2a_history_rr (main)"
    ch = cand[chosen]

    def diff(x, y, sp, doms=None):
        A = {d: v for d, v in pt[sp][x].items() if (doms is None or d in doms)}
        B = {d: v for d, v in pt[sp][y].items() if (doms is None or d in doms)}
        return bootstrap(A, B)
    se = [d for d in T2 if d not in BRIGHT_DOMAINS]
    diffs = {}
    for sp in ("train", "dev"):
        diffs[sp] = {"all": diff(ch, base, sp), "bright": diff(ch, base, sp, BRIGHT_DOMAINS), "se": diff(ch, base, sp, se),
                     "S1_vs_S2": diff(cand["S1"], cand["S2"], sp),
                     "B+SR_vs_B": diff("B + SR (no history)", "B current turn", sp),
                     "SRonly_vs_B": diff("SR only", "B current turn", sp),
                     "SRonly_vs_main": diff("SR only", base, sp),
                     "S1_before_rr_vs_2a_history": diff("S1 before reranker", "2a_history (no reranker)", sp),
                     "S2_before_rr_vs_2a_history": diff("S2 before reranker", "2a_history (no reranker)", sp)}
    tb = diffs["train"]["all"]
    margin_met = tb["diff"] >= 0.005 and tb["ci95"][0] > 0
    # stage details: fusion (full train), ReasonEmbed way, reranker way
    stages = {}
    for k, cond in stage.items():
        c = hyb["conditions"].get(cond, {})
        lin = c.get("systems", {}).get("linear*", {})
        name = {"S1": "sr_S1", "S2": "sr_S2", "B + SR": "sr_cur", "SR only": "sr_only"}[k]
        re_ = rea.get(name, {})
        st = {"hybrid_cfg": lin.get("cfg"), "hybrid_train_full": lin.get("train_macro"), "hybrid_dev": lin.get("dev_macro"),
              "reasonembed_best_on_train": re_.get("best_on_train"),
              "reasonembed_none": re_.get("by_how", {}).get("none=0"),
              "reasonembed_best": re_.get("by_how", {}).get(re_.get("best_on_train", "")),
              "reasonembed_train_boot_vs_none": re_.get("train_bootstrap_best_minus_none"),
              "reasonembed_query_base_cut": re_.get("sr_base_cut"), "reasonembed_query_empty_sr": re_.get("sr_empty"),
              "new_docs": re_.get("docs_encoded"), "queries": re_.get("queries_encoded"), "encode_s": re_.get("encode_s")}
        if name in rr:
            x = rr[name]
            st.update({"reranker_best_on_train": x["best_on_train"], "reranker_by_how_best": x["by_how"][x["best_on_train"]],
                       "reranker_none": x["by_how"][next(iter(x["by_how"]))],
                       "reranker_train_boot_vs_none": x["train_bootstrap_best_minus_none"],
                       "reranker_pairs": x["pairs"], "reranker_new": x["scored_new"], "reranker_s": x["score_s"]})
        stages[k] = st
    # turn groups / depth (dev all turns; train subsample)
    bd = {}
    for sp in ("dev", "train"):
        tmp = os.path.join(R, "sr", f"breakdown_{sp}.json")
        labs = [base, ch, "2a_history (no reranker)", "B current turn", "B + SR (no history)", "SR only"]
        cmd = [sys.executable, os.path.join(HERE, "t2_breakdown.py"), "--data", a.data, "--kit", a.kit, "--split", sp,
               "--only-run-topics", "--out", tmp] + [x for lab in labs for x in ("--run", f"{lab}={pats[lab]}")]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
        bd[sp] = json.load(open(tmp))
    rep = {"rule": "LOG 2026-11-16 14:26 (rule 19)", "chosen": chosen, "chosen_system": ch, "base": base,
           "rows": rows, "diff": {sp: diffs[sp]["all"] for sp in diffs}, "diffs": diffs,
           "margin_would_be_met_on_train": margin_met, "stages": stages, "breakdown": bd,
           "train_topics": sum(len(v) for v in pt["train"][base].values()),
           "dev_topics": sum(len(v) for v in pt["dev"][base].values()),
           "dev_per_domain": {lab: {d: round(sum(v) / len(v), 4) for d, v in pt["dev"][lab].items()}
                              for lab in (base, ch, "B current turn", "B + SR (no history)", "SR only")}}
    json.dump(rep, open(a.out, "w"), indent=1)
    for r in rows:
        print(f"{r['system']:<28} train {r['train']:.4f}  dev {r['dev']:.4f}  (dev BRIGHT {r['dev_bright']:.4f} SE {r['dev_se']:.4f})")
    print(f"chosen on train: {chosen} ({ch}); {ch} - main: train {diffs['train']['all']} dev {diffs['dev']['all']}; "
          f"margin would be met: {margin_met}")


if __name__ == "__main__":
    main()
