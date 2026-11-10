#!/usr/bin/env python3
"""B5: one ablation table per sub-task, stage by stage, on the same topics (rule-8 train subsample; all dev).

Stages: BM25 (plain query) → + dense, hybrid (plain query) → + LLM reasoning (q+r+h hybrid) → + ReasonEmbed
over the top 50 (final system) → + LLM reranker (only where rule 16 adopted it). For 2a with history the plain
query is the week-4 history text (H0) and the LLM sees the earlier Q/A turns (Hb). Each stage: macro nDCG@10 with
a 95% bootstrap interval, and the paired difference to the previous stage (topics resampled within domain).

    python3 ablation_1110.py --runs ../research/runs_v13 --data ../../reteco_data_v11 --kit ../../RETECO/starter_kit \
        --out ../research/runs_v13/ablation_1110.json
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bm25s_run import ndcg_fn  # noqa: E402
from dense_index import T1, T2  # noqa: E402
from final_1110 import macro_ci  # noqa: E402
from hybrid import Query, bootstrap, qrels_for, read_run  # noqa: E402
from tie_study import fused, order  # noqa: E402
import tiebreak  # noqa: E402


def hyb_cfg(path, cond):
    c = json.load(open(path))["conditions"][cond]
    return c["systems"]["linear*"]["cfg"], c["dense_condition"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--kit", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    tiebreak.set_mode("sha1")
    ndcg = ndcg_fn(a.kit)
    R = a.runs
    F = os.path.join(R, "foreign", "runs")
    RR = os.path.join(R, "rerank", "runs")
    q1, q2 = f"{R}/qexp/t1", f"{R}/qexp/t2"
    # stage: (label, kind, spec); kind "run" = TREC file pattern ({pre}); "hyb" = (report, condition, bm25 dir, dense dir)
    subtasks = {
        "1a": (1, "1a", [("BM25 (query)", "run", f"{q1}/bm25/runs/{{pre}}_1a__q.tsv"),
                         ("+ dense: hybrid (query)", "hyb", (f"{q1}/hybrid_1a.json", "1a__q", f"{q1}/bm25/runs", f"{q1}/dense/runs")),
                         ("+ LLM reasoning (q+r+h hybrid)", "hyb", (f"{q1}/hybrid_1a.json", "1a__q+r+h", f"{q1}/bm25/runs", f"{q1}/dense/runs")),
                         ("+ ReasonEmbed top 50 (final)", "run", f"{F}/{{pre}}_1a_rerun__best.tsv"),
                         ("+ LLM reranker (not adopted)", "run", f"{RR}/{{pre}}_1a__rr.tsv")]),
        "1b": (1, "1b_query+step", [("BM25 (query + step)", "run", f"{q1}/bm25/runs/{{pre}}_1b_query+step__q.tsv"),
                                    ("+ dense: hybrid", "hyb", (f"{q1}/hybrid_1b.json", "1b_query+step__q", f"{q1}/bm25/runs", f"{q1}/dense/runs")),
                                    ("+ LLM reasoning (q+r+h hybrid)", "hyb", (f"{q1}/hybrid_1b.json", "1b_query+step__q+r+h", f"{q1}/bm25/runs", f"{q1}/dense/runs")),
                                    ("+ ReasonEmbed top 50 (final)", "run", f"{F}/{{pre}}_1b_rerun__best.tsv"),
                                    ("+ LLM reranker (not adopted)", "run", f"{RR}/{{pre}}_1b__rr.tsv")]),
        "2a_current": (2, "2a_current", [("BM25 (current turn)", "run", f"{q2}/bm25/runs/{{pre}}_2a_current__q.tsv"),
                                         ("+ dense: hybrid", "hyb", (f"{q2}/hybrid_2a_current.json", "2a_current__q", f"{q2}/bm25/runs", f"{q2}/dense/runs")),
                                         ("+ LLM reasoning (q+r+h hybrid)", "hyb", (f"{q2}/hybrid_2a_current.json", "2a_current__q+r+h", f"{q2}/bm25/runs", f"{q2}/dense/runs")),
                                         ("+ ReasonEmbed top 50 (final B)", "run", f"{F}/{{pre}}_2a_nomaxp__best.tsv"),
                                         ("+ LLM reranker (not adopted)", "run", f"{RR}/{{pre}}_2a_current__rr.tsv")]),
        "2a_history": (2, "2a_current", [("BM25 (history text)", "run", f"{R}/bm25/t2/runs/{{pre}}_2a_history.tsv"),
                                         ("+ dense: hybrid H0", "hyb", (f"{R}/hist/t2/hybrid_h0.json", "2a_history", f"{R}/bm25/t2/runs", f"{R}/dense/bge-base_L512/t2/runs")),
                                         ("+ LLM with earlier Q/A (Hb hybrid)", "hyb", (f"{R}/hist/t2/hybrid.json", "2a_hist3qa__q+r+h", f"{R}/hist/t2/bm25/runs", f"{R}/hist/t2/dense/runs")),
                                         ("+ ReasonEmbed top 50", "run", f"{F}/{{pre}}_2ah_hybrid__best.tsv"),
                                         ("+ LLM reranker (final main)", "run", f"{RR}/{{pre}}_2a_history__rr.tsv")]),
    }
    out = {}
    for name, (tr, gcond, stages) in subtasks.items():
        doms = T1 if tr == 1 else T2
        res = {}
        for sp in ("train", "dev"):
            # topics: those of the final (ReasonEmbed) saved run = train subsample / all dev
            fin = [s for s in stages if "ReasonEmbed" in s[0]][0][2]
            topics = {dom: sorted(read_run(fin.format(pre=f"t{tr}_{dom}_{sp}"))) for dom in doms}
            for lab, kind, spec in stages:
                per = {}
                ok = True
                for dom in doms:
                    pre = f"t{tr}_{dom}_{sp}"
                    gold = qrels_for(a.data, tr, dom, sp, gcond if not gcond.startswith("1b") else "1b")
                    if kind == "run":
                        p = spec.format(pre=pre)
                        if not os.path.exists(p):
                            ok = False
                            break
                        run = read_run(p)
                        ranked = {q: [d for d, _ in run.get(q, [])] for q in topics[dom]}
                    else:
                        rep, cond, bd, dd = spec
                        cfg, dcond = hyb_cfg(rep, cond)
                        bm, de = read_run(os.path.join(bd, f"{pre}_{cond}.tsv")), read_run(os.path.join(dd, f"{pre}_{dcond}.tsv"))
                        ranked = {q: [d for d, _ in order(fused(Query(bm.get(q, []), de.get(q, [])), cfg))] for q in topics[dom]}
                    per[dom] = [ndcg(ranked[q], gold[q], 10) for q in topics[dom]]
                if ok:
                    res.setdefault(lab, {})[sp] = per
        rows, prev = [], None
        for lab, _, _ in stages:
            if lab not in res:
                continue
            row = {"stage": lab}
            for sp in ("train", "dev"):
                m, ci = macro_ci(res[lab][sp])
                row[sp] = m
                row[f"{sp}_ci95"] = ci
                row[f"{sp}_minus_prev"] = bootstrap(res[lab][sp], res[prev][sp]) if prev else None
            rows.append(row)
            prev = lab
            print(f"{name:<11} {lab:<36} train {row['train']:.4f} {row['train_ci95']}  dev {row['dev']:.4f} {row['dev_ci95']}  "
                  f"Δdev {row['dev_minus_prev']['diff'] if row['dev_minus_prev'] else ''}", flush=True)
        out[name] = {"topics": {"train": sum(len(v) for v in res[rows[0]['stage']]["train"].values()),
                                "dev": sum(len(v) for v in res[rows[0]['stage']]["dev"].values())}, "rows": rows}
    json.dump(out, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
