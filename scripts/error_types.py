#!/usr/bin/env python3
"""S4 (LOG rule 2026-11-16 14:29): material for the error-type analysis of the main runs on dev.

Per sub-task (1a main `1a`, 1b `1b`, 2a main `2a_history_rr`; submit.py dev files): dev topics with nDCG@10 <= 0.1,
keys (domain, topic id) sorted, 15 drawn with a fresh random.Random(20260921) per sub-task. For each: query / step /
turn, LLM reason + HyDE (start), every gold document's hybrid (first-stage) rank and final rank, the first gold
document's start, the top 3 (starts, gold-of-another-topic marks), and the mechanical label (a) / (b).

    python3 error_types.py --sub ../research/runs_v13/submit/dev_1116 --runs ../research/runs_v13 \
        --data ../../reteco_data_v11 --kit ../../RETECO/starter_kit --out ../research/cases/error_material_dev.json
"""
import argparse
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bm25s_run import ndcg_fn  # noqa: E402
from cases_errors import topic_text  # noqa: E402
from dense_index import T1, T2  # noqa: E402
from gold_categories import fetch  # noqa: E402
from hybrid import qrels_for, read_run  # noqa: E402
from llm_expand import inputs as llm_inputs, key_of  # noqa: E402
from qexp_search import load_gen  # noqa: E402
from reason_rerank import clean  # noqa: E402

SEED = 20260921
N = 15


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sub", required=True)
    ap.add_argument("--runs", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--kit", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    ndcg = ndcg_fn(a.kit)
    R = a.runs
    subs = {"1a": (1, "1a", "1a", f"{R}/foreign/runs/{{pre}}_1a_rerun__none.tsv", "1a"),
            "1b": (1, "1b", "1b_query+step", f"{R}/foreign/runs/{{pre}}_1b_rerun__none.tsv", "1b"),
            "2a": (2, "2a_history_rr", "2a_hist3qa", f"{R}/foreign/runs/{{pre}}_2ah_hybrid__none.tsv", "x")}
    out = {"rule": "LOG 2026-11-16 14:29", "subtasks": {}}
    for sub, (tr, variant, cond, hyb_pat, qk) in subs.items():
        gen = {p: load_gen(os.path.join(R, "llm", f"t{tr}"), p) for p in ("reason", "hyde")}
        body = {(dom, sp, qid): b for dom, sp, qid, b in llm_inputs(a.data, tr, cond) if sp == "dev"}
        doms = T1 if tr == 1 else T2
        pool, runs, hyb, golds, allg = [], {}, {}, {}, {}
        n_topics = 0
        for dom in doms:
            runs[dom] = read_run(os.path.join(a.sub, variant, f"{dom}.txt"))
            hyb[dom] = read_run(hyb_pat.format(pre=f"t{tr}_{dom}_dev"))
            golds[dom] = qrels_for(a.data, tr, dom, "dev", qk)
            ag = {}
            for sp in ("train", "dev"):
                for q, g in qrels_for(a.data, tr, dom, sp, qk).items():
                    for d in g:
                        ag.setdefault(d, set()).add((sp, q))
            allg[dom] = ag
            for q in sorted(golds[dom]):
                n_topics += 1
                if ndcg([d for d, _ in runs[dom].get(q, [])], golds[dom][q], 10) <= 0.1:
                    pool.append((dom, q))
        pick = random.Random(SEED).sample(sorted(pool), N)
        items = []
        for dom, q in pick:
            ranked = [d for d, _ in runs[dom].get(q, [])]
            hranked = [d for d, _ in hyb[dom].get(q, [])]  # hybrid order of the top-50 pool
            g = sorted(golds[dom][q])
            texts = fetch(a.data, tr, dom, set(g) | set(ranked[:3]))
            gr = []
            for d in g:
                fr = ranked.index(d) + 1 if d in ranked else None
                hr = hranked.index(d) + 1 if d in hranked else (fr if fr and fr > 50 else None)
                gr.append({"doc": d, "final_rank": fr, "hybrid_rank": hr, "start": clean(texts.get(d, ""))[:300]})
            best = min([x["final_rank"] for x in gr if x["final_rank"]] or [10 ** 6])
            mech = "a" if best > 100 else "b"
            top3 = []
            for d in ranked[:3]:
                hold = sorted(x for x in allg[dom].get(d, set()) if x != ("dev", q))
                top3.append({"rank": ranked.index(d) + 1, "is_gold": d in g,
                             "gold_of_other_topic": [f"{s}:{t}" for s, t in hold[:3]],
                             "start": clean(texts.get(d, ""))[:300]})
            k = body.get((dom, "dev", q))
            items.append({"domain": dom, "qid": q, "ndcg10": round(ndcg(ranked, set(g), 10), 4),
                          "query": topic_text(a.data, tr, sub, dom, "dev", q),
                          "llm_reason": clean(gen["reason"].get(key_of("reason", k), "") if k else "")[:500],
                          "llm_hyde": clean(gen["hyde"].get(key_of("hyde", k), "") if k else "")[:400],
                          "gold": gr, "best_gold_final_rank": best if best < 10 ** 6 else None,
                          "mechanical_label": mech, "top3": top3})
        out["subtasks"][sub] = {"variant": variant, "eligible": len(pool), "topics": n_topics, "items": items}
        print(f"{sub}: eligible {len(pool)} of {n_topics}; mechanical " +
              str({m: sum(i['mechanical_label'] == m for i in items) for m in 'ab'}), flush=True)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(out, open(a.out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
