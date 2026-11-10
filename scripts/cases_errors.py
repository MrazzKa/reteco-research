#!/usr/bin/env python3
"""B5 error examples (LOG rule 2026-11-10 10:12): 3 dev topics per sub-task with nDCG@10 < 0.2 under the main run,
drawn with random.Random(20260921) over sorted (domain, topic id); written to research/cases/errors_main_dev.md.

    python3 cases_errors.py --runs ../research/runs_v13 --data ../../reteco_data_v11 --kit ../../RETECO/starter_kit \
        --out ../research/cases/errors_main_dev.md
"""
import argparse
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bm25s_run import ndcg_fn  # noqa: E402
from dense_index import T1, T2  # noqa: E402
from gold_categories import fetch  # noqa: E402
from hybrid import qrels_for, read_run  # noqa: E402
from reason_rerank import clean  # noqa: E402


def topic_text(data, tr, sub, dom, split, qid):
    d = os.path.join(data, "track1_tempo" if tr == 1 else "track2_recor", dom)
    if tr == 1:
        name = "examples" if sub == "1a" else "steps"
        for ln in open(os.path.join(d, f"{name}_{split}.jsonl"), encoding="utf-8"):
            r = json.loads(ln)
            if sub == "1a" and r["id"] == qid:
                return clean(r["query"])[:400]
            for s in r.get("steps", []):
                if s["step_id"] == qid:
                    return (clean(r["query"])[:300] + " || STEP: " + clean(s.get("step_instruction", "")))[:400]
    else:
        bench = json.load(open(os.path.join(d, f"benchmark_{split}.json"), encoding="utf-8"))
        for c in bench:
            for t in c["turns"]:
                if f"{c['id']}_turn_{t['turn_id']}" == qid:
                    return (f"CURRENT: {clean(t['query'])}\n\nHISTORY: {clean(t.get('conversation_history', ''))[:300]}")
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--kit", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    ndcg = ndcg_fn(a.kit)
    R = a.runs
    mains = {"1a": (1, f"{R}/foreign/runs/{{pre}}_1a_rerun__best.tsv", "1a final (hybrid q+r+h + ReasonEmbed w 0.8)"),
             "1b": (1, f"{R}/foreign/runs/{{pre}}_1b_rerun__best.tsv", "1b final (hybrid q+r+h + ReasonEmbed w 0.7)"),
             "2a": (2, f"{R}/rerank/runs/{{pre}}_2a_history__rr.tsv", "2a main (history, Hb + ReasonEmbed w 0.9 + reranker w 0.4)")}
    L = ["# Error examples of the main runs (dev)", "",
         "Selection rule (LOG 2026-11-10 10:12, written before viewing): dev topics with nDCG@10 < 0.2 under the main run, "
         "sorted by (domain, topic id), 3 per sub-task drawn with `random.Random(20260921)`; no resampling. Ranks are in "
         "the main run's reranked top 50 (\"> 50\" = not there). Foreign = gold for another train/dev topic of the domain.", ""]
    for sub, (tr, pat, desc) in mains.items():
        doms = T1 if tr == 1 else T2
        pool, runs, golds, others = [], {}, {}, {}
        for dom in doms:
            pre = f"t{tr}_{dom}_dev"
            run = read_run(pat.format(pre=pre))
            gold = qrels_for(a.data, tr, dom, "dev", "1b" if sub == "1b" else "x")
            runs[dom], golds[dom] = run, gold
            allg = {}
            for sp in ("train", "dev"):
                for q, g in qrels_for(a.data, tr, dom, sp, "1b" if sub == "1b" else "x").items():
                    for d in g:
                        allg.setdefault(d, set()).add((sp, q))
            others[dom] = allg
            for q in sorted(gold):
                if ndcg([d for d, _ in run.get(q, [])], gold[q], 10) < 0.2:
                    pool.append((dom, q))
        pick = random.Random(20260921).sample(sorted(pool), 3)
        L += [f"## {sub}: {desc}", "", f"Eligible dev topics (nDCG@10 < 0.2): {len(pool)} of "
              f"{sum(len(g) for g in golds.values())}.", ""]
        for i, (dom, q) in enumerate(pick, 1):
            ranked = [d for d, _ in runs[dom].get(q, [])]
            g = golds[dom][q]
            texts = fetch(a.data, tr, dom, set(g) | set(ranked[:1]))
            L += [f"### {sub}.{i} — {dom} `{q}` (nDCG@10 {ndcg(ranked, g, 10):.3f})", "", "Query:", "",
                  "> " + topic_text(a.data, tr, sub, dom, "dev", q).replace("\n", "\n> "), ""]
            for d in sorted(g):
                rk = ranked.index(d) + 1 if d in ranked else "> 50"
                L += [f"- gold (rank {rk}): {clean(texts.get(d, ''))[:250]}"]
            top = ranked[0] if ranked else None
            if top:
                grp = lambda t: t.rsplit("_step", 1)[0] if sub == "1b" else (t.rsplit("_turn_", 1)[0] if tr == 2 else t)
                hold = sorted(x for x in others[dom].get(top, set()) if x != ("dev", q))
                same = [x for x in hold if x[0] == "dev" and grp(x[1]) == grp(q)]
                foreign = [x for x in hold if x not in same]
                if top in g:
                    lab = "gold"
                elif foreign:
                    lab = "FOREIGN gold of " + ", ".join(f"{s}:{t}" for s, t in foreign[:2])
                elif same:
                    lab = "not gold here; gold of another " + ("step of the same query" if sub == "1b" else "turn of the same conversation") + \
                          " (" + ", ".join(t for _, t in same[:2]) + ")"
                else:
                    lab = "not gold"
                L += [f"- rank 1 ({lab}): {clean(texts.get(top, ''))[:250]}"]
            L += ["", "Reading (written after viewing): _to fill_", ""]
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    open(a.out, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
