#!/usr/bin/env python3
"""Inspect the official RETECO train/dev release and write a markdown report.

Read-only. Never modifies `reteco_data`.

    python inspect_release.py --data ../../reteco_data --out ../research/data_report.md
    python inspect_release.py --data ../../reteco_data --track1 iota --track2 drones

Reports, per domain: corpus size, doc-length distribution, item counts per
split, gold-per-item distribution, and the share of gold ids that are actually
present in the domain corpus (a silent-failure check worth doing once).
Also dumps a few full examples so you can read them, per PHASE C.
"""
import argparse
import json
import os
import random
import statistics as st

STEP_KEYS = ("steps", "retrieval_steps", "plan")
STEP_TEXT_KEYS = ("step_instruction", "instruction", "step", "text")


def read_jsonl(path, limit=None):
    out = []
    with open(path, encoding="utf-8") as f:
        for ln in f:
            if ln.strip():
                out.append(json.loads(ln))
                if limit and len(out) >= limit:
                    break
    return out


def load_qrels(path):
    gold = {}
    if not os.path.exists(path):
        return gold
    with open(path, encoding="utf-8") as f:
        for ln in f:
            if ln.strip():
                qid, _, docid, rel = ln.split()
                if int(rel) > 0:
                    gold.setdefault(qid, set()).add(docid)
    return gold


def corpus_stats(path):
    """Stream the corpus once: ids + length stats, without holding content."""
    ids, lengths = set(), []
    with open(path, encoding="utf-8") as f:
        for ln in f:
            if not ln.strip():
                continue
            d = json.loads(ln)
            ids.add(d.get("id") or d.get("doc_id"))
            lengths.append(len(d.get("content", "").split()))
    return ids, lengths


def fmt_lengths(lengths):
    if not lengths:
        return "n/a"
    q = sorted(lengths)
    p = lambda f: q[min(len(q) - 1, int(len(q) * f))]
    return (f"n={len(q)} mean={st.mean(q):.0f} p10={p(.10)} p50={p(.50)} "
            f"p90={p(.90)} max={q[-1]}")


def dist(counts):
    if not counts:
        return "n/a"
    return (f"min={min(counts)} mean={st.mean(counts):.2f} "
            f"median={st.median(counts)} max={max(counts)}")


def gold_presence(gold, corpus_ids):
    seen = [d for s in gold.values() for d in s]
    if not seen:
        return "no qrels"
    hit = sum(1 for d in seen if d in corpus_ids)
    return f"{hit}/{len(seen)} gold ids present in corpus ({hit / len(seen):.1%})"


def inspect_track1(root, domain, split, w, sample_n):
    d = os.path.join(root, "track1_tempo", domain)
    corpus = os.path.join(d, "documents.jsonl")
    if not os.path.exists(corpus):
        w(f"- `{domain}`: no documents.jsonl, skipped\n")
        return
    ids, lengths = corpus_stats(corpus)
    ex = read_jsonl(os.path.join(d, f"examples_{split}.jsonl"))
    steps_path = os.path.join(d, f"steps_{split}.jsonl")
    steps = read_jsonl(steps_path) if os.path.exists(steps_path) else []
    qrels = load_qrels(os.path.join(d, f"qrels_{split}.txt"))
    qrels_s = load_qrels(os.path.join(d, f"qrels_steps_{split}.txt"))

    n_steps = 0
    for rec in steps:
        for k in STEP_KEYS:
            if isinstance(rec.get(k), list):
                n_steps += len(rec[k])
                break

    w(f"\n#### track1 / {domain} / {split}\n\n")
    w(f"- corpus: {len(ids):,} docs — words per doc: {fmt_lengths(lengths)}\n")
    w(f"- 1a queries: {len(ex)} — query length (words): "
      f"{fmt_lengths([len(e.get('query', '').split()) for e in ex])}\n")
    w(f"- 1b step records: {len(steps)} ({n_steps} steps total)\n")
    w(f"- qrels 1a: {len(qrels)} topics — gold per query: "
      f"{dist([len(v) for v in qrels.values()])}\n")
    w(f"- qrels 1b: {len(qrels_s)} topics — gold per step: "
      f"{dist([len(v) for v in qrels_s.values()])}\n")
    w(f"- integrity 1a: {gold_presence(qrels, ids)}\n")
    w(f"- integrity 1b: {gold_presence(qrels_s, ids)}\n")
    if ex and sample_n:
        for e in random.sample(ex, min(sample_n, len(ex))):
            w(f"\n<details><summary>example <code>{e.get('id')}</code></summary>\n\n"
              f"```\n{e.get('query', '')[:1200]}\n```\n"
              f"gold_ids: {e.get('gold_ids', [])}\n\n</details>\n")


def inspect_track2(root, domain, split, w, sample_n):
    d = os.path.join(root, "track2_recor", domain)
    corpus = os.path.join(d, "documents.jsonl")
    if not os.path.exists(corpus):
        w(f"- `{domain}`: no documents.jsonl, skipped\n")
        return
    ids, lengths = corpus_stats(corpus)
    bpath = os.path.join(d, f"benchmark_{split}.json")
    bench = json.load(open(bpath, encoding="utf-8")) if os.path.exists(bpath) else []
    if isinstance(bench, dict):
        bench = [bench]
    qrels = load_qrels(os.path.join(d, f"qrels_{split}.txt"))

    turns = [t for c in bench for t in c.get("turns", [])]
    depths = [len(c.get("turns", [])) for c in bench]
    has_reasoning = sum(1 for t in turns if t.get("subquestion_reasoning"))
    hist_words = [len(str(t.get("conversation_history", "")).split()) for t in turns]

    w(f"\n#### track2 / {domain} / {split}\n\n")
    w(f"- corpus: {len(ids):,} docs — words per doc: {fmt_lengths(lengths)}\n")
    w(f"- conversations: {len(bench)} — turns: {len(turns)} — depth: {dist(depths)}\n")
    w(f"- query length (words): "
      f"{fmt_lengths([len(t.get('query', '').split()) for t in turns])}\n")
    w(f"- conversation_history length (words): {fmt_lengths(hist_words)}\n")
    w(f"- turns carrying `subquestion_reasoning`: {has_reasoning}/{len(turns)}"
      f" — NOTE: gold annotation, check availability on the hidden test set\n")
    w(f"- qrels: {len(qrels)} topics — gold per turn: "
      f"{dist([len(v) for v in qrels.values()])}\n")
    w(f"- integrity: {gold_presence(qrels, ids)}\n")
    if bench and sample_n:
        for c in random.sample(bench, min(sample_n, len(bench))):
            lines = []
            for t in c.get("turns", []):
                lines.append(f"[turn {t.get('turn_id')}] Q: {t.get('query', '')[:400]}")
                lines.append(f"            gold: {t.get('gold_doc_ids', [])}")
            w(f"\n<details><summary>conversation <code>{c.get('id')}</code> "
              f"({c.get('task')})</summary>\n\n```\n" + "\n".join(lines)[:2500] +
              "\n```\n\n</details>\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="path to reteco_data")
    ap.add_argument("--out", default=None, help="markdown report path")
    ap.add_argument("--splits", nargs="*", default=["train", "dev"])
    ap.add_argument("--track1", nargs="*", help="domains (default: all)")
    ap.add_argument("--track2", nargs="*", help="domains (default: all)")
    ap.add_argument("--samples", type=int, default=2, help="examples to dump per domain")
    ap.add_argument("--seed", type=int, default=20270101)
    a = ap.parse_args()
    random.seed(a.seed)

    def domains(track, given):
        base = os.path.join(a.data, track)
        if not os.path.isdir(base):
            return []
        all_d = sorted(x for x in os.listdir(base)
                       if os.path.isdir(os.path.join(base, x)))
        return [d for d in (given or all_d) if d in all_d]

    d1, d2 = domains("track1_tempo", a.track1), domains("track2_recor", a.track2)
    buf = []
    w = buf.append
    w(f"# RETECO data inspection report\n\n")
    w(f"- data root: `{os.path.abspath(a.data)}`\n")
    w(f"- track1 domains: {len(d1)} — {', '.join(d1) or 'none found'}\n")
    w(f"- track2 domains: {len(d2)} — {', '.join(d2) or 'none found'}\n")
    w(f"- splits: {', '.join(a.splits)} — seed {a.seed}\n")
    for split in a.splits:
        w(f"\n## split: {split}\n")
        for dom in d1:
            inspect_track1(a.data, dom, split, w, a.samples)
        for dom in d2:
            inspect_track2(a.data, dom, split, w, a.samples)
    text = "".join(buf)
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        open(a.out, "w", encoding="utf-8").write(text)
        print(f"wrote {a.out} ({len(text):,} chars)")
    else:
        print(text)


if __name__ == "__main__":
    main()
