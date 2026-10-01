#!/usr/bin/env python3
"""Readable side-by-side view of what two systems retrieve for the same queries.

Not a scoring tool: it prints the query, the gold passages and each system's top-5
with gold marked, so a human can see *why* a query works or fails.

Cases are sampled with a fixed seed before anything is read: `--mode` picks
`fixed` (random sample of judged queries), `wins` (dense beats BM25 most),
`losses` (BM25 beats dense most) or `zero` (both fail).

    python3 query_view.py --data ../../reteco_data_v11 --kit ../../RETECO/starter_kit \
        --split dev --track 1 --domain politics \
        --a "BM25=../research/runs_v11/track1_lucene/runs/t1_politics_dev_1a.tsv" \
        --b "BM25+bge rerank=../research/runs_v11/rerank/runs/t1_politics_dev_1a_rerank.tsv" \
        --n 6 --out ../research/cases/query_view_politics.md
"""
import argparse
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from week1_run import load_qrels, read_jsonl, snippet  # noqa: E402
from bm25s_run import ndcg_fn  # noqa: E402


def read_run(path):
    out = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                qid, _, doc, *_ = line.split()
                out.setdefault(qid, []).append(doc)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--kit", required=True)
    ap.add_argument("--split", default="dev")
    ap.add_argument("--track", type=int, required=True)
    ap.add_argument("--domain", required=True)
    ap.add_argument("--a", required=True, help="label=run.tsv")
    ap.add_argument("--b", required=True, help="label=run.tsv")
    ap.add_argument("--qrels", default=None, help="override qrels file name")
    ap.add_argument("--mode", default="fixed", choices=("fixed", "wins", "losses", "zero"))
    ap.add_argument("--n", type=int, default=6)
    ap.add_argument("--seed", type=int, default=20260928)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    ndcg = ndcg_fn(a.kit)
    la, pa = a.a.split("=", 1)
    lb, pb = a.b.split("=", 1)
    ra, rb = read_run(pa), read_run(pb)
    sub = "track1_tempo" if a.track == 1 else "track2_recor"
    d = os.path.join(a.data, sub, a.domain)
    gold = load_qrels(os.path.join(d, a.qrels or f"qrels_{a.split}.txt"))

    if a.track == 1:
        texts = {r["id"]: r["query"] for r in read_jsonl(os.path.join(d, f"examples_{a.split}.jsonl"))}
        ctx = {}
    else:
        bench = json.load(open(os.path.join(d, f"benchmark_{a.split}.json"), encoding="utf-8"))
        bench = [bench] if isinstance(bench, dict) else bench
        texts, ctx = {}, {}
        for c in bench:
            for t in c["turns"]:
                q = f"{c['id']}_turn_{t['turn_id']}"
                texts[q] = t["query"]
                h = t.get("conversation_history", "") or ""
                ctx[q] = "" if h.lower().startswith("no previous") else h

    judged = [q for q in gold if q in texts]
    sa = {q: ndcg(ra.get(q, [])[:10], gold[q], 10) for q in judged}
    sb = {q: ndcg(rb.get(q, [])[:10], gold[q], 10) for q in judged}
    if a.mode == "fixed":
        picked = random.Random(a.seed).sample(sorted(judged), min(a.n, len(judged)))
    elif a.mode == "wins":
        picked = sorted(judged, key=lambda q: sb[q] - sa[q], reverse=True)[:a.n]
    elif a.mode == "losses":
        picked = sorted(judged, key=lambda q: sa[q] - sb[q], reverse=True)[:a.n]
    else:
        picked = sorted([q for q in judged if sa[q] == 0 and sb[q] == 0])[:a.n]

    wanted = set()
    for q in picked:
        wanted |= set(gold[q]) | set(ra.get(q, [])[:5]) | set(rb.get(q, [])[:5])
    docs = {}
    key = "id" if a.track == 1 else "doc_id"
    with open(os.path.join(d, "documents.jsonl"), encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rec = json.loads(line)
                if rec[key] in wanted:
                    docs[rec[key]] = rec.get("content", "") or ""

    out = [f"# Query view — {a.domain} (track {a.track}, {a.split}, mode `{a.mode}`)", "",
           f"Systems: **A = {la}**, **B = {lb}**. Gold marked ✅. "
           f"Sampling is by fixed seed ({a.seed}) or by the mode's rule, before reading.", ""]
    for q in picked:
        out += [f"## `{q}` — A {sa[q]:.3f} · B {sb[q]:.3f}", ""]
        if ctx.get(q):
            out += [f"**Conversation so far:** {snippet(ctx[q], 700)}", ""]
        out += [f"**Query:** {snippet(texts[q], 700)}", "", "**Gold:**"]
        for g in sorted(gold[q]):
            out.append(f"- `{g}` — {snippet(docs.get(g, '(missing)'), 200)}")
        for label, run in ((la, ra), (lb, rb)):
            out += ["", f"**{label} top 5:**"]
            for rank, doc in enumerate(run.get(q, [])[:5], 1):
                mark = " ✅" if doc in gold[q] else ""
                out.append(f"{rank}. `{doc}`{mark} — {snippet(docs.get(doc, ''), 180)}")
        out += ["", "- Reading: ", "", "---", ""]
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"wrote {a.out}: {len(picked)} queries; mean A {sum(sa[q] for q in picked)/len(picked):.3f}, "
          f"B {sum(sb[q] for q in picked)/len(picked):.3f}")


if __name__ == "__main__":
    main()
