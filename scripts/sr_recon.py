#!/usr/bin/env python3
"""S2a (LOG 2026-11-16 14:24): reconnaissance of the Track-2 fields `subquestion_reasoning` (SR) and
`subquestion_reasoning_metadata` (SRM). Analysis only; reads gold only to measure leakage.

  1. structure: presence, type, length in words (first turn vs later), SRM keys / value types / lengths;
  2. identifiers: gold doc id, doc-id-like strings, BRIGHT page title / question slug as a phrase, against chance
     (the gold ids of a random other conversation of the same domain);
  3. "written from gold?": share of word 8-grams of SR (and SRM, the reference answer, the current query) found
     verbatim in the turn's gold documents vs the top-10 non-gold documents of the main run vs 10 random documents;
  4. Track 1: fields of examples / steps / guidance;
  5. examples file (rule fixed in LOG before viewing).

    python3 sr_recon.py --data ../../reteco_data_v11 --runs ../research/runs_v13 \
        --out ../research/runs_v13/sr/recon.json --cases ../research/cases/subquestion_reasoning_dev.md
"""
import argparse
import json
import os
import random
import re
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dense_index import T1, T2  # noqa: E402
from week1_run import BRIGHT_DOMAINS  # noqa: E402

SEED = 20260921
STOP = set("""about above after again against also among another anything because been before being below
between both could does doing documents document during each either especially explain explicitly focus focused
focusing from further have having here into itself just like many might more most much must only other others over
same select should since some such than that their them then there these they this those through under until upon
very what when where whether which while whom whose will with within without would your avoid retrieve sources
discuss discussing discusses related specific specifically information unrelated general solely topics""".split())
TOK = re.compile(r"[a-z0-9]+")
IDLIKE = re.compile(r"[a-z_]+_ex_\d+_doc_\d+|\bex_\d+\b|\.txt\b|_doc_\d+", re.I)


def words(t):
    return TOK.findall((t or "").lower())


def grams(t, n):
    w = words(t)
    return {tuple(w[i:i + n]) for i in range(len(w) - n + 1)}


def srm_text(m):
    if not isinstance(m, dict):
        return str(m or "")
    parts = []
    for v in m.values():
        parts += v if isinstance(v, list) else [v]
    return "\n".join(str(x) for x in parts)


def read_run(path):
    run = {}
    if os.path.exists(path):
        for ln in open(path):
            p = ln.split()
            if len(p) >= 3:
                run.setdefault(p[0], []).append(p[2])
    return run


def bright_phrases(doc_id):
    """BRIGHT ids: '<question slug>/<page title>_<n>.txt' -> (title phrase, slug phrase)."""
    if "/" not in doc_id:
        return None, None
    slug, fn = doc_id.split("/", 1)
    stem = re.sub(r"(_\d+)?\.txt$", "", fn)
    return " ".join(words(stem.replace("_", " "))), " ".join(words(slug.replace("_", " ")))


def contains_phrase(text_words, phrase):
    if not phrase:
        return False
    return f" {phrase} " in f" {' '.join(text_words)} "


def stats(v):
    v = sorted(v)
    if not v:
        return None
    return {"n": len(v), "mean": round(sum(v) / len(v), 1), "median": statistics.median(v),
            "p90": v[int(0.9 * (len(v) - 1))], "min": v[0], "max": v[-1]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--runs", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cases", required=True)
    a = ap.parse_args()
    rep = {"structure": {}, "ids": {}, "ngram": {}, "conversation_fields": {}, "track1": {}}
    agg = {sp: {"turns": 0, "sr_present": 0, "sr_present_first": 0, "first": 0, "sr_type": {}, "srm_type": {},
                "sr_words_first": [], "sr_words_later": [], "srm_keys": {}, "srm_value_types": {},
                "srm_words": {}, "srm_list_len": {}} for sp in ("train", "dev")}
    idc = {sp: {k: 0 for k in ("turns", "sr_gold_id", "srm_gold_id", "sr_idlike", "srm_idlike",
                               "bright_turns", "sr_gold_title", "sr_gold_slug", "srm_gold_title", "srm_gold_slug",
                               "sr_chance_title", "sr_chance_slug", "srm_chance_title", "srm_chance_slug",
                               "answer_gold_title", "answer_chance_title", "query_gold_title", "query_gold_slug",
                               "history_gold_title", "history_gold_slug", "srm_idlike_examples")} | {"srm_idlike_examples": None} for sp in ("train", "dev")}
    srcs = ("sr", "srm", "answer", "query")
    ng = {sp: {grp: {n: {s: {"gold": [], "top10_nongold": [], "random10": []} for s in srcs} for n in (8, 5)}
               for grp in ("all", "bright", "se")} for sp in ("train", "dev")}
    examples_pool = {"bright": [], "se": []}
    # novel terms: content words (>= 4 letters, not stop words) of a text absent from the current question and the
    # released history; where do they occur? SR vs our LLM reason text (Hb input, generated without documents)
    from llm_expand import inputs as llm_inputs, key_of
    from qexp_search import load_gen
    gen_r = load_gen(os.path.join(a.runs, "llm", "t2"), "reason")
    body = {(dom, sp, qid): b for dom, sp, qid, b in llm_inputs(a.data, 2, "2a_hist3qa")}
    nov = {sp: {grp: {s: {"n_novel": [], "gold": [], "top10_nongold": [], "random10": []} for s in ("sr", "llm_reason")}
                for grp in ("all", "bright", "se")} for sp in ("train", "dev")}
    conv_fields = {}
    rng = random.Random(SEED)
    for dom in T2:
        d = os.path.join(a.data, "track2_recor", dom)
        grp = "bright" if dom in BRIGHT_DOMAINS else "se"
        docs = {}
        with open(os.path.join(d, "documents.jsonl"), encoding="utf-8") as f:
            for ln in f:
                r = json.loads(ln)
                docs[r["doc_id"]] = r.get("content", "")
        all_ids = sorted(docs)
        for sp in ("train", "dev"):
            bench = json.load(open(os.path.join(d, f"benchmark_{sp}.json"), encoding="utf-8"))
            bench = [bench] if isinstance(bench, dict) else bench
            for c in bench:
                for k, v in c.items():
                    if k != "turns":
                        conv_fields.setdefault(k, {"type": type(v).__name__, "example": None})
                        if k == "metadata" and isinstance(v, dict):
                            conv_fields[k]["keys"] = sorted(set(conv_fields[k].get("keys", [])) | set(v))
            if sp == "dev":
                run = read_run(os.path.join(a.runs, "submit", "dev", "2a_history_rr", f"{dom}.txt"))
            else:
                run = read_run(os.path.join(a.runs, "rerank", "runs", f"t2_{dom}_train_2a_history__rr.tsv"))
            convs = sorted(bench, key=lambda c: c["id"])
            for ci, c in enumerate(convs):
                other = convs[(ci + 1 + rng.randrange(max(1, len(convs) - 1))) % len(convs)] if len(convs) > 1 else c
                other_gold = sorted({g for t in other["turns"] for g in t.get("gold_doc_ids", [])})
                for t in c["turns"]:
                    qid = f"{c['id']}_turn_{t['turn_id']}"
                    A = agg[sp]
                    A["turns"] += 1
                    sr, srm = t.get("subquestion_reasoning"), t.get("subquestion_reasoning_metadata")
                    A["sr_type"][type(sr).__name__] = A["sr_type"].get(type(sr).__name__, 0) + 1
                    A["srm_type"][type(srm).__name__] = A["srm_type"].get(type(srm).__name__, 0) + 1
                    first = t["turn_id"] == 1
                    A["first"] += first
                    has = isinstance(sr, str) and bool(sr.strip())
                    A["sr_present"] += has
                    A["sr_present_first"] += has and first
                    if has:
                        A["sr_words_first" if first else "sr_words_later"].append(len(sr.split()))
                    if isinstance(srm, dict):
                        for k, v in srm.items():
                            A["srm_keys"][k] = A["srm_keys"].get(k, 0) + 1
                            tn = type(v).__name__
                            A["srm_value_types"].setdefault(k, {})
                            A["srm_value_types"][k][tn] = A["srm_value_types"][k].get(tn, 0) + 1
                            txt = " ".join(v) if isinstance(v, list) else str(v)
                            A["srm_words"].setdefault(k, []).append(len(txt.split()))
                            if isinstance(v, list):
                                A["srm_list_len"].setdefault(k, []).append(len(v))
                    gold = list(t.get("gold_doc_ids", []))
                    srt, smt = sr or "", srm_text(srm)
                    I = idc[sp]
                    I["turns"] += 1
                    low_sr, low_sm = srt.lower(), smt.lower()
                    I["sr_gold_id"] += any(g.lower() in low_sr for g in gold)
                    I["srm_gold_id"] += any(g.lower() in low_sm for g in gold)
                    I["sr_idlike"] += bool(IDLIKE.search(srt))
                    I["srm_idlike"] += bool(IDLIKE.search(smt))
                    if IDLIKE.search(smt):
                        I["srm_idlike_examples"] = (I["srm_idlike_examples"] or []) + [[dom, qid, IDLIKE.search(smt).group(0)]]
                    if grp == "bright":
                        I["bright_turns"] += 1
                        w_sr, w_sm, w_an = words(srt), words(smt), words(t.get("answer", ""))
                        gp = [bright_phrases(g) for g in gold]
                        op = [bright_phrases(g) for g in other_gold]
                        I["sr_gold_title"] += any(contains_phrase(w_sr, p[0]) for p in gp)
                        I["sr_gold_slug"] += any(contains_phrase(w_sr, p[1]) for p in gp)
                        I["srm_gold_title"] += any(contains_phrase(w_sm, p[0]) for p in gp)
                        I["srm_gold_slug"] += any(contains_phrase(w_sm, p[1]) for p in gp)
                        I["sr_chance_title"] += any(contains_phrase(w_sr, p[0]) for p in op)
                        I["sr_chance_slug"] += any(contains_phrase(w_sr, p[1]) for p in op)
                        I["srm_chance_title"] += any(contains_phrase(w_sm, p[0]) for p in op)
                        I["srm_chance_slug"] += any(contains_phrase(w_sm, p[1]) for p in op)
                        I["answer_gold_title"] += any(contains_phrase(w_an, p[0]) for p in gp)
                        I["answer_chance_title"] += any(contains_phrase(w_an, p[0]) for p in op)
                        w_q, w_h = words(t.get("query", "")), words(t.get("conversation_history", ""))
                        I["query_gold_title"] += any(contains_phrase(w_q, p[0]) for p in gp)
                        I["query_gold_slug"] += any(contains_phrase(w_q, p[1]) for p in gp)
                        I["history_gold_title"] += any(contains_phrase(w_h, p[0]) for p in gp)
                        I["history_gold_slug"] += any(contains_phrase(w_h, p[1]) for p in gp)
                    # n-gram overlap (only turns of the run: dev all, train the subsample)
                    if qid in run and gold:
                        gs = set(gold)
                        top = [x for x in run[qid][:10] if x not in gs]
                        rnd = rng.sample(all_ids, 10)
                        texts = {"sr": srt, "srm": smt, "answer": t.get("answer", ""), "query": t.get("query", "")}
                        seen = set(words(t.get("query", "")) + words(t.get("conversation_history", "")))
                        kk = body.get((dom, sp, qid))
                        rtext = gen_r.get(key_of("reason", kk), "") if kk else ""
                        wpools = {"gold": set().union(*[words(docs.get(x, "")) for x in gold]),
                                  "top10_nongold": set().union(*[words(docs.get(x, "")) for x in top]) if top else set(),
                                  "random10": set().union(*[words(docs.get(x, "")) for x in rnd])}
                        for s_, tx in (("sr", srt), ("llm_reason", rtext)):
                            nv = {w for w in words(tx) if len(w) >= 4 and w not in STOP and w not in seen and not w.isdigit()}
                            for G in ("all", grp):
                                nov[sp][G][s_]["n_novel"].append(len(nv))
                                if nv:
                                    for pk, pw in wpools.items():
                                        nov[sp][G][s_][pk].append(len(nv & pw) / len(nv))
                        for n in (8, 5):
                            pools = {"gold": set().union(*[grams(docs.get(x, ""), n) for x in gold]),
                                     "top10_nongold": set().union(*[grams(docs.get(x, ""), n) for x in top]) if top else set(),
                                     "random10": set().union(*[grams(docs.get(x, ""), n) for x in rnd])}
                            for s, tx in texts.items():
                                g = grams(tx, n)
                                if not g:
                                    continue
                                for pk, pg in pools.items():
                                    v = len(g & pg) / len(g)
                                    ng[sp]["all"][n][s][pk].append(v)
                                    ng[sp][grp][n][s][pk].append(v)
                    if sp == "dev":
                        examples_pool[grp].append(((dom, qid), t, gold, docs.get(gold[0], "") if gold else ""))
        del docs
        print(f"[{dom}] done", flush=True)
    for sp, A in agg.items():
        rep["structure"][sp] = {
            "turns": A["turns"], "first_turns": A["first"], "sr_present": A["sr_present"],
            "sr_present_first": A["sr_present_first"], "sr_type": A["sr_type"], "srm_type": A["srm_type"],
            "sr_words_first": stats(A["sr_words_first"]), "sr_words_later": stats(A["sr_words_later"]),
            "sr_words_all": stats(A["sr_words_first"] + A["sr_words_later"]),
            "srm_keys": A["srm_keys"], "srm_value_types": A["srm_value_types"],
            "srm_words": {k: stats(v) for k, v in A["srm_words"].items()},
            "srm_list_len": {k: stats(v) for k, v in A["srm_list_len"].items()}}
    rep["ids"] = idc

    def summ(v):
        return {"turns": len(v), "mean_share": round(sum(v) / len(v), 4) if v else None,
                "share_turns_any": round(sum(x > 0 for x in v) / len(v), 4) if v else None}
    rep["ngram"] = {sp: {grp: {str(n): {s: {pk: summ(v) for pk, v in d3.items()} for s, d3 in d2.items()}
                               for n, d2 in d1.items()} for grp, d1 in d0.items()} for sp, d0 in ng.items()}
    rep["conversation_fields"] = conv_fields
    rep["novel_terms"] = {sp: {grp: {s_: {k: (round(sum(v) / len(v), 4) if v else None) for k, v in d.items()}
                                     | {"turns_with_novel": len(d["gold"])} for s_, d in g.items()}
                               for grp, g in x.items()} for sp, x in nov.items()}
    # Track 1 fields
    t1 = {}
    for fn in ("examples_dev.jsonl", "steps_dev.jsonl", "guidance_dev.jsonl"):
        p = os.path.join(a.data, "track1_tempo", "iota", fn)
        x = json.loads(open(p, encoding="utf-8").readline())
        t1[fn] = {k: type(v).__name__ for k, v in x.items()}
        if fn == "steps_dev.jsonl":
            t1["step_keys"] = {k: type(v).__name__ for k, v in x["steps"][0].items()}
        if fn == "guidance_dev.jsonl":
            t1["query_guidance_keys"] = sorted(x["query_guidance"])
            t1["gold_passage_annotation_keys"] = sorted(x["gold_passage_annotations"][0])
            t1["guidance_example"] = {"query_guidance": x["query_guidance"]}
    # Track 1 guidance: does query_guidance name a gold doc id? (gold_passage_annotations do by construction)
    g_hits, g_n = 0, 0
    for dom in T1:
        p = os.path.join(a.data, "track1_tempo", dom, "guidance_dev.jsonl")
        gold = {}
        for ln in open(os.path.join(a.data, "track1_tempo", dom, "examples_dev.jsonl"), encoding="utf-8"):
            r = json.loads(ln)
            gold[r["id"]] = r["gold_ids"]
        for ln in open(p, encoding="utf-8"):
            r = json.loads(ln)
            txt = json.dumps(r.get("query_guidance", {})).lower()
            g_n += 1
            g_hits += any(g.lower() in txt or g.split("/")[-1].lower() in txt for g in gold.get(r["id"], []))
    t1["dev_query_guidance_with_gold_id"] = [g_hits, g_n]
    rep["track1"] = t1
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(rep, open(a.out, "w"), indent=1)
    # examples (rule: LOG 2026-11-16 14:24)
    rng2 = random.Random(SEED)
    pick = rng2.sample(sorted(examples_pool["bright"], key=lambda x: x[0]), 2) + \
        rng2.sample(sorted(examples_pool["se"], key=lambda x: x[0]), 2)
    L = ["# `subquestion_reasoning` on dev: four examples", "",
         "Rule (LOG 2026-11-16 14:24, fixed before viewing): dev turns keyed (domain, qid), sorted; "
         "rng = random.Random(20260921); two from the BRIGHT domains, then two from the StackExchange domains "
         "(`rng.sample`). Generated by `scripts/sr_recon.py`. SR = `subquestion_reasoning`, SRM = "
         "`subquestion_reasoning_metadata`.", ""]
    for (dom, qid), t, gold, gtext in pick:
        L += [f"## {dom} / {qid} ({'BRIGHT' if dom in BRIGHT_DOMAINS else 'StackExchange'}, turn {t['turn_id']})", "",
              f"**Current question:** {t.get('query', '').strip()}", "",
              f"**SR (first 500 chars):** {(t.get('subquestion_reasoning') or '')[:500]}", "",
              "**SRM:**", ""]
        for k, v in (t.get("subquestion_reasoning_metadata") or {}).items():
            L.append(f"- `{k}`: {json.dumps(v, ensure_ascii=False)[:300]}")
        L += ["", f"**First gold document (first 300 chars):** "
              f"{re.sub(chr(10) + '+', ' ', gtext[:300]).strip()}", ""]
    open(a.cases, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(json.dumps({"structure": rep["structure"], "ids": idc}, indent=1)[:6000])


if __name__ == "__main__":
    main()
