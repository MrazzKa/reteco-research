#!/usr/bin/env python3
"""BM25 runs with a Lucene-style analyzer (bm25s + Snowball stemmer + stopwords).

Why this exists: our week-1 pure-Python BM25 (starter-kit tokeniser: lowercase +
regex, no stemming, no stopwords) scored consistently below the official pyserini
baseline. This script keeps the conditions identical and changes only the
retriever/analyzer, so the difference is attributable.

    python3 bm25s_run.py --data ../../reteco_data_v11 --kit ../../RETECO/starter_kit \
        --split dev --track 1 --domains iota --out ../research/runs_v11/track1

Conditions are the same as week1_run.py. Output layout is the same too
(results.json + runs/*.tsv), so aggregate_week1.py reads it unchanged.
"""
import argparse
import json
import os
import sys
import time
from collections import defaultdict

import bm25s
import Stemmer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from week1_run import REF, load_qrels, read_jsonl, write_run  # noqa: E402

STEMMER = Stemmer.Stemmer("english")


def analyze(texts, analyzer, show=False):
    if analyzer == "lucene":
        return bm25s.tokenize(texts, stopwords="en", stemmer=STEMMER, show_progress=show)
    return bm25s.tokenize(texts, stopwords=None, stemmer=None, show_progress=show)


def build(corpus_path, key, analyzer):
    t0 = time.time()
    ids, texts = [], []
    with open(corpus_path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                d = json.loads(line)
                ids.append(d[key])
                texts.append(d.get("content", "") or "")
    tokens = analyze(texts, analyzer)
    del texts
    retriever = bm25s.BM25(method="lucene", k1=0.9, b=0.4)
    retriever.index(tokens, show_progress=False)
    print(f"    index: {len(ids):,} docs, {time.time() - t0:.0f}s ({analyzer})", flush=True)
    return retriever, ids


def search(retriever, ids, queries, analyzer, label, k=100, threads=-1, tiebreak=True):
    """queries: list of (qid, text). Identical texts are searched once."""
    t0 = time.time()
    uniq = sorted({q for _, q in queries})
    tokens = analyze(uniq, analyzer)
    idx, scores = retriever.retrieve(tokens, k=min(k, retriever.scores["num_docs"]),
                                     n_threads=threads, show_progress=False)
    by_text = {}
    for i, text in enumerate(uniq):
        # Exact score ties are common (duplicate passages, esp. in the non-deduplicated
        # Track-2 corpora) and bm25s orders them arbitrarily, depending on k. Break ties
        # by doc id, as the starter kit does, so a run no longer depends on its depth.
        ranked = [(ids[int(idx[i, j])], float(scores[i, j])) for j in range(idx.shape[1])]
        by_text[text] = sorted(ranked, key=lambda x: (-x[1], x[0])) if tiebreak else ranked
    print(f"    {label:<24} {len(queries):>5} topics ({len(uniq)} unique) "
          f"{time.time() - t0:6.1f}s", flush=True)
    return {qid: by_text[q] for qid, q in queries}


def ndcg_fn(kit):
    sys.path.insert(0, os.path.abspath(kit))
    from ir_metrics import ndcg_at_k
    return ndcg_at_k


def score(run, gold, ndcg):
    per = {qid: ndcg([d for d, _ in run.get(qid, [])], g, 10) for qid, g in gold.items()}
    return (sum(per.values()) / len(per) if per else 0.0), per


def turn_bucket(qid):
    try:
        t = int(qid.rsplit("_turn_", 1)[1])
        return "T5+" if t >= 5 else f"T{t}"
    except (IndexError, ValueError):
        return "T?"


def by_turn(per):
    buckets = defaultdict(list)
    for qid, v in per.items():
        buckets[turn_bucket(qid)].append(v)
    return {k: round(sum(v) / len(v), 4) for k, v in sorted(buckets.items())}


def track1(a, dom, ndcg, runs_dir, results, index=None):
    d = os.path.join(a.data, "track1_tempo", dom)
    print(f"\n[track1 / {dom} / {a.split}]", flush=True)
    recs = read_jsonl(os.path.join(d, f"examples_{a.split}.jsonl"))
    step_recs = read_jsonl(os.path.join(d, f"steps_{a.split}.jsonl"))
    g1a = load_qrels(os.path.join(d, f"qrels_{a.split}.txt"))
    g1b = load_qrels(os.path.join(d, f"qrels_steps_{a.split}.txt"))
    retriever, ids = index or build(os.path.join(d, "documents.jsonl"), "id", a.analyzer)

    plan = [("1a", [(r["id"], r["query"]) for r in recs], g1a)]
    strategies = {
        "1b_query+step": lambda r, s: f"{r['query']}\n\nStep: {s.get('step_instruction', '')}",
        "1b_step_only": lambda r, s: s.get("step_instruction", ""),
        "1b_query+all": lambda r, s: r["query"] + "\n\nSteps:\n" + "\n".join(
            x.get("step_instruction", "") for x in r.get("steps", [])),
    }
    for name, fn in strategies.items():
        plan.append((name, [(s["step_id"], fn(r, s)) for r in step_recs
                            for s in r.get("steps", [])], g1b))
    for name, queries, gold in plan:
        if not queries or (a.conditions and name not in a.conditions):
            continue
        run = search(retriever, ids, queries, a.analyzer, name, k=a.k, threads=a.threads,
                     tiebreak=not a.no_tiebreak)
        write_run(os.path.join(runs_dir, f"t1_{dom}_{a.split}_{name}.tsv"), run, name)
        m, _ = score(run, gold, ndcg)
        ref_key = "1a" if name == "1a" else ("1b" if name == "1b_query+step" else None)
        ref = REF.get(ref_key, {}).get(dom) if ref_key else None
        results.append({"track": 1, "domain": dom, "split": a.split, "run": name,
                        "n": len(gold), "ndcg10": round(m, 4),
                        "official_ref": (ref[0] if a.split == "train" else ref[1]) if ref else None,
                        "system": f"bm25s-{a.analyzer}"})
        print(f"      -> {name} nDCG@10 {m:.4f}"
              + (f"   official {results[-1]['official_ref']}" if results[-1]["official_ref"] else ""),
              flush=True)


def track2(a, dom, ndcg, runs_dir, results, index=None):
    d = os.path.join(a.data, "track2_recor", dom)
    print(f"\n[track2 / {dom} / {a.split}]", flush=True)
    bench = json.load(open(os.path.join(d, f"benchmark_{a.split}.json"), encoding="utf-8"))
    bench = [bench] if isinstance(bench, dict) else bench
    gold = load_qrels(os.path.join(d, f"qrels_{a.split}.txt"))
    retriever, ids = index or build(os.path.join(d, "documents.jsonl"), "doc_id", a.analyzer)
    turns = [(f"{c['id']}_turn_{t['turn_id']}", t) for c in bench for t in c["turns"]]

    def hist(t):
        h = t.get("conversation_history", "") or ""
        return "" if h.lower().startswith("no previous") else h

    def hist_part(t, which):
        keep, cur = [], None
        for ln in hist(t).splitlines():
            s = ln.strip()
            if s.startswith("Q:"):
                cur, s = "Q", s[2:]
            elif s.startswith("A:"):
                cur, s = "A", s[2:]
            if cur == which:
                keep.append(s.strip())
        return " ".join(keep)

    plan = {
        "2a_current": [(q, t["query"]) for q, t in turns],
        "2a_history": [(q, (hist(t) + " " + t["query"]).strip()) for q, t in turns],
        "2a_hist_questions_only": [(q, (hist_part(t, "Q") + " " + t["query"]).strip())
                                   for q, t in turns],
        "2a_hist_answers_only": [(q, (hist_part(t, "A") + " " + t["query"]).strip())
                                 for q, t in turns],
    }
    for name, queries in plan.items():
        if a.conditions and name not in a.conditions:
            continue
        run = search(retriever, ids, queries, a.analyzer, name, k=a.k, threads=a.threads,
                     tiebreak=not a.no_tiebreak)
        write_run(os.path.join(runs_dir, f"t2_{dom}_{a.split}_{name}.tsv"), run, name)
        m, per = score(run, gold, ndcg)
        ref = REF.get(name, {}).get(dom)
        results.append({"track": 2, "domain": dom, "split": a.split, "run": name,
                        "n": len(gold), "ndcg10": round(m, 4),
                        "official_ref": (ref[0] if a.split == "train" else ref[1]) if ref else None,
                        "by_turn": by_turn(per), "system": f"bm25s-{a.analyzer}"})
        print(f"      -> {name} nDCG@10 {m:.4f}"
              + (f"   official {results[-1]['official_ref']}" if results[-1]["official_ref"] else ""),
              flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--kit", required=True)
    ap.add_argument("--split", default="dev", choices=("train", "dev"))
    ap.add_argument("--splits", nargs="+", choices=("train", "dev"),
                    help="several splits from one index build (overrides --split)")
    ap.add_argument("--k", type=int, default=100, help="run depth")
    ap.add_argument("--no-tiebreak", action="store_true",
                    help="keep bm25s's arbitrary order among tied scores (old behaviour)")
    ap.add_argument("--conditions", nargs="*", help="only these condition names")
    ap.add_argument("--track", type=int, required=True, choices=(1, 2))
    ap.add_argument("--domains", nargs="+", required=True)
    ap.add_argument("--analyzer", default="lucene", choices=("lucene", "plain"))
    ap.add_argument("--threads", type=int, default=-1)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    ndcg = ndcg_fn(a.kit)
    runs_dir = os.path.join(a.out, "runs")
    os.makedirs(runs_dir, exist_ok=True)
    results = []
    started = time.time()
    for dom in a.domains:
        index = None
        if a.splits:
            sub, key = ("track1_tempo", "id") if a.track == 1 else ("track2_recor", "doc_id")
            index = build(os.path.join(a.data, sub, dom, "documents.jsonl"), key, a.analyzer)
        for split in (a.splits or [a.split]):
            a.split = split
            (track1 if a.track == 1 else track2)(a, dom, ndcg, runs_dir, results, index)
        del index
        with open(os.path.join(a.out, "results.json"), "w", encoding="utf-8") as f:
            json.dump(results, f, indent=1)
    print(f"\ndone in {time.time() - started:.0f}s -> {a.out}/results.json", flush=True)


if __name__ == "__main__":
    main()
