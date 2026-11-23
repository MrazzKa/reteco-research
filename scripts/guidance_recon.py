#!/usr/bin/env python3
"""N2a (LOG 2026-11-23 12:58; analysis, no choice): reconnaissance of the Track-1 query-side guidance.

Structure and lengths of `query_guidance` fields, ids in g (= guidance.guidance_text) after stripping, and
"written from gold?": word 8-/5-gram overlap of g with the query's gold documents vs the top-10 non-gold documents of
our main 1a run vs 10 random documents; novel content words of g vs of our LLM reason text. Also the 4 dev examples
of the pre-registered rule. `gold_passage_annotations` is never read (guidance.read_guidance pops it).

    python3 guidance_recon.py --data ../../reteco_data_v11 --runs ../research/runs_v13 \
        --out ../research/runs_v13/guidance/recon.json --cases ../research/cases/track1_guidance_dev.md
"""
import argparse
import json
import os
import random
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dense_index import T1  # noqa: E402
from gold_categories import fetch  # noqa: E402
from guidance import assert_no_ids, corpus_ids, guidance_text, read_guidance  # noqa: E402
from sr_recon import STOP, grams, stats, words  # noqa: E402
from week1_run import load_qrels  # noqa: E402

SEED = 20260921


def all_ids(data, dom):
    out = []
    with open(os.path.join(data, "track1_tempo", dom, "documents.jsonl"), encoding="utf-8") as f:
        for line in f:
            m = re.search(r'"id"\s*:\s*"([^"]+)"', line)
            if m:
                out.append(m.group(1))
    return sorted(out)


def field_text(v):
    if isinstance(v, list):
        return " ".join(field_text(x) for x in v)
    if isinstance(v, dict):
        return " ".join(field_text(x) for k, x in v.items() if k != "gold_ids")
    return str(v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--runs", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cases", required=True)
    a = ap.parse_args()
    from llm_expand import inputs as llm_inputs, key_of
    from qexp_search import load_gen
    gen_r = load_gen(os.path.join(a.runs, "llm", "t1"), "reason")
    body = {(dom, sp, qid): b for dom, sp, qid, b in llm_inputs(a.data, 1, "1a")}
    dump = json.load(open(os.path.join(a.runs, "scores", "1a_rerun.json")))["scores"]
    rep = {"structure": {}, "g": {}, "ids": {}, "ngram": {}, "novel_terms": {}, "steps_vs_plan": {}}
    pres, words_f = defaultdict(Counter), defaultdict(lambda: defaultdict(list))
    glen = defaultdict(list)
    idc = Counter()
    srcs = ("guidance", "query", "llm_reason")
    ng = {sp: {n: {s: {"gold": [], "top10_nongold": [], "random10": []} for s in srcs} for n in (8, 5)}
          for sp in ("train", "dev")}
    nov = {sp: {s: {"n_novel": [], "gold": [], "top10_nongold": [], "random10": []} for s in ("guidance", "llm_reason")}
           for sp in ("train", "dev")}
    examples_pool = []
    steps = Counter()
    rng = random.Random(SEED)
    for dom in T1:
        d = os.path.join(a.data, "track1_tempo", dom)
        ids = corpus_ids(a.data, dom)
        aid = all_ids(a.data, dom)
        for sp in ("train", "dev"):
            rows = read_guidance(os.path.join(d, f"guidance_{sp}.jsonl"))
            ex = {}
            with open(os.path.join(d, f"examples_{sp}.jsonl"), encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        r = json.loads(line)
                        ex[r["id"]] = r["query"]
            gold = load_qrels(os.path.join(d, f"qrels_{sp}.txt"))
            # 1b steps vs plan actions (structure only)
            acts = {q: [st.get("action", "").strip() for st in (qg.get("retrieval_plan") or [])] for q, qg in rows.items()}
            with open(os.path.join(d, f"steps_{sp}.jsonl"), encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        r = json.loads(line)
                        steps[(sp, "queries_with_steps")] += 1
                        steps[(sp, "steps")] += len(r["steps"])
                        steps[(sp, "plan_actions_of_these_queries")] += len(acts.get(r["id"], []))
                        steps[(sp, "step_is_a_plan_action")] += sum(s.get("step_instruction", "").strip() in acts.get(r["id"], [])
                                                                    for s in r["steps"])
            run = dump.get(sp, {}).get(dom, {})
            need = set()
            todo = []
            for q, qg in sorted(rows.items()):
                pres[sp]["rows"] += 1
                for k, v in qg.items():
                    if v not in (None, "", [], {}):
                        pres[sp][k] += 1
                        words_f[sp][k].append(len(field_text(v).split()))
                g = guidance_text(qg)
                assert_no_ids(g, ids, f"{dom}/{sp}/{q}")
                idc[(sp, "g_rows")] += 1
                idc[(sp, "g_with_gold_id")] += any(x.lower() in g.lower() for x in gold.get(q, ()))
                glen[sp].append(len(g.split()))
                if sp == "dev":
                    examples_pool.append(((dom, q), qg, g, ex.get(q, ""), sorted(gold.get(q, ()))))
                if q in run and gold.get(q):
                    gs = gold[q]
                    top = [x for x, _ in run[q][:10] if x not in gs]
                    rnd = rng.sample(aid, 10)
                    need |= set(gs) | set(top) | set(rnd)
                    todo.append((q, g, gs, top, rnd))
            docs = fetch(a.data, 1, dom, need)
            for q, g, gs, top, rnd in todo:
                qtext = ex.get(q, "")
                k = body.get((dom, sp, q))
                rtext = gen_r.get(key_of("reason", k), "") if k else ""
                texts = {"guidance": g, "query": qtext, "llm_reason": rtext}
                for n in (8, 5):
                    pools = {"gold": set().union(*[grams(docs.get(x, ""), n) for x in gs]),
                             "top10_nongold": set().union(*[grams(docs.get(x, ""), n) for x in top]) if top else set(),
                             "random10": set().union(*[grams(docs.get(x, ""), n) for x in rnd])}
                    for s, tx in texts.items():
                        gg = grams(tx, n)
                        if gg:
                            for pk, pg in pools.items():
                                ng[sp][n][s][pk].append(len(gg & pg) / len(gg))
                seen = set(words(qtext))
                wpools = {"gold": set().union(*[words(docs.get(x, "")) for x in gs]),
                          "top10_nongold": set().union(*[words(docs.get(x, "")) for x in top]) if top else set(),
                          "random10": set().union(*[words(docs.get(x, "")) for x in rnd])}
                for s_, tx in (("guidance", g), ("llm_reason", rtext)):
                    nv = {w for w in words(tx) if len(w) >= 4 and w not in STOP and w not in seen and not w.isdigit()}
                    nov[sp][s_]["n_novel"].append(len(nv))
                    if nv:
                        for pk, pw in wpools.items():
                            nov[sp][s_][pk].append(len(nv & pw) / len(nv))
            del docs
        print(f"[{dom}] done", flush=True)
    for sp in ("train", "dev"):
        rep["structure"][sp] = {"rows": pres[sp]["rows"],
                                "present": {k: v for k, v in pres[sp].items() if k != "rows"},
                                "words": {k: stats(v) for k, v in words_f[sp].items()}}
        rep["g"][sp] = {"words": stats(glen[sp]), "empty": sum(1 for x in glen[sp] if x == 0)}
        rep["ids"][sp] = {"rows": idc[(sp, "g_rows")], "g_with_gold_id": idc[(sp, "g_with_gold_id")],
                          "assert_no_ids": "passed for every row"}
        rep["steps_vs_plan"][sp] = {k[1]: v for k, v in steps.items() if k[0] == sp}

        def summ(v):
            return {"queries": len(v), "mean_share": round(sum(v) / len(v), 4) if v else None,
                    "share_queries_any": round(sum(x > 0 for x in v) / len(v), 4) if v else None}
        rep["ngram"][sp] = {str(n): {s: {pk: summ(v) for pk, v in d3.items()} for s, d3 in ng[sp][n].items()}
                            for n in (8, 5)}
        rep["novel_terms"][sp] = {s: {k: (round(sum(v) / len(v), 4) if v else None) for k, v in d.items()}
                                  | {"queries_with_novel": len(d["gold"])} for s, d in nov[sp].items()}
    # ReasonEmbed token length of g (with the 1a instruction format)
    try:
        from transformers import AutoTokenizer
        tok = AutoTokenizer.from_pretrained("hanhainebula/reason-embed-qwen3-4b-0928")
        rep["g"]["dev"]["tokens_reasonembed"] = stats([len(tok(g)["input_ids"]) for _, _, g, _, _ in examples_pool])
    except Exception as e:  # noqa: BLE001
        rep["g"]["dev"]["tokens_reasonembed"] = f"n/a ({e.__class__.__name__})"
    # examples (rule fixed in LOG before viewing)
    keys = sorted(k for k, *_ in examples_pool)
    pick = random.Random(SEED).sample(keys, 4)
    by = {k: rest for k, *rest in examples_pool}
    lines = ["# Track-1 query-side guidance: 4 dev examples (N2a, LOG 2026-11-23 12:58)", "",
             "Rule (fixed before viewing): keys (domain, id) sorted; `random.Random(20260921).sample(keys, 4)`. "
             "g = `guidance.guidance_text` (plan gold ids removed; `gold_passage_annotations` never read). "
             "Shown: query (first 400 chars), g, the other query-side fields (short), the first 300 chars of the "
             "first gold document (qrels order). Not resampled.", ""]
    other = ("query_summary", "expected_granularity", "is_temporal_query", "query_temporal_events",
             "query_temporal_signals", "quality_checks", "temporal_reasoning_class_primary",
             "temporal_reasoning_class_secondary")
    for dom, q in pick:
        qg, g, qtext, gl = by[(dom, q)]
        gd = fetch(a.data, 1, dom, set(gl[:1]))
        lines += [f"## {dom} / {q}", "", "**Query:** " + re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", qtext))[:400], "",
                  "**g:** " + g, "", "**Other query-side fields:**", ""]
        for k in other:
            if k in qg:
                lines.append(f"- {k}: {field_text(qg[k])[:200]}")
        doc = re.sub(r"\s+", " ", gd.get(gl[0], "")) if gl else ""
        lines += ["", f"**First gold document (start, {len(gl)} gold in all):** " + doc[:300], ""]
    os.makedirs(os.path.dirname(os.path.abspath(a.cases)), exist_ok=True)
    open(a.cases, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    rep["examples"] = [list(k) for k in pick]
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(rep, open(a.out, "w"), indent=1)
    print(json.dumps({k: rep[k] for k in ("g", "ids", "ngram", "novel_terms", "steps_vs_plan")}, indent=1))


if __name__ == "__main__":
    main()
