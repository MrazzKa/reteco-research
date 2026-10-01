#!/usr/bin/env python3
"""Week-1 runner: everything for the first Bethard meeting in one command.

    python week1_run.py --data ..\\..\\reteco_data --kit ..\\..\\RETECO\\starter_kit ^
        --track1 iota --track2 drones biology --split dev

Per domain it runs, with the starter kit's BM25 settings (k1=0.9, b=0.4):

  Track 1   1a  whole query                         (reproduction)
            1b  Query+Step   -- the official baseline   (reproduction)
            1b  Step-Only    -- permitted by the proposal, unpublished
            1b  Query+All    -- permitted by the proposal, unpublished
  Track 2   2a  current turn                        (reproduction)
            2a  + history (starter-kit construction) (reproduction)
            2a  + history + GOLD reasoning           (ORACLE ceiling, not a system)

and writes, under --out:
  runs/*.tsv                  TREC run files (re-scorable with the official scorer.py)
  results.md / results.json   nDCG@10 table next to the official reference numbers
  cases_track1.md             sampled failure cases, ready to label by hand
  cases_track2.md

Retrieval uses FastBM25 below: the SAME tokenizer, idf, scoring expression and
tie-breaking as starter_kit/bm25.py, but with an inverted index so a query only
touches documents that contain its terms. Rankings are identical to bm25.py
(checked with --selftest); it just does not score every document for every query.
The official, pyserini-based numbers still need official_baseline.py.
"""
import argparse
import json
import os
import random
import sys
import time
from array import array
from collections import defaultdict
from math import log

# ---------------------------------------------------------------- reference --
# From starter_kit/BASELINE_RESULTS.md (official pyserini baseline). Pure-Python
# BM25 tokenises differently, so expect small gaps, not equality.
# Official pyserini BM25 references (train, dev), from starter_kit/BASELINE_RESULTS.md.
# Track 1 numbers are data **v1.1** (deduplicated corpora, 25 Sep 2026); Track 2 is unchanged.
# v1.0 Track-1 macro was 1a 0.0879/0.0967 and 1b 0.0852/0.1063 (train/dev); v1.1 is 1a
# 0.1075/0.1147 and 1b 0.1024/0.1177. Our own v1.0 runs are kept in research/RESULTS_v10.md.
REF = {
    "1a": {"bitcoin": (.0856, .0370), "cardano": (.1848, .1027), "economics": (.0382, .0467),
           "genealogy": (.1242, .1949), "history": (.0654, .0873), "hsm": (.1736, .2489),
           "iota": (.1563, .3309), "law": (.0946, .0574), "monero": (.0382, .0320),
           "politics": (.2810, .2625), "quant": (.0255, .0237), "travel": (.0506, .0442),
           "workplace": (.0798, .0230)},
    "1b": {"bitcoin": (.0888, .0299), "cardano": (.1655, .0627), "economics": (.0300, .0463),
           "genealogy": (.1181, .2183), "history": (.0614, .1015), "hsm": (.1729, .2140),
           "iota": (.1403, .4195), "law": (.0854, .0549), "monero": (.0622, .0113),
           "politics": (.2403, .2371), "quant": (.0085, .0403), "travel": (.0423, .0645),
           "workplace": (.1162, .0297)},
    "2a_current": {"biology": (.2250, .2034), "drones": (.1400, .1695), "earth_science": (.2757, .2195),
                   "economics": (.1573, .1629), "hardware": (.1472, .1605), "law": (.1047, .1147),
                   "medicalsciences": (.1188, .1168), "politics": (.1609, .1514),
                   "psychology": (.2208, .2596), "robotics": (.1847, .1574),
                   "sustainable_living": (.2851, .2938)},
    "2a_history": {"biology": (.6369, .6065), "drones": (.3162, .2954), "earth_science": (.6324, .6264),
                   "economics": (.4593, .4739), "hardware": (.2935, .3378), "law": (.2721, .3437),
                   "medicalsciences": (.2267, .1730), "politics": (.4423, .3219),
                   "psychology": (.5558, .5726), "robotics": (.5773, .5123),
                   "sustainable_living": (.5801, .5531)},
}
BRIGHT_DOMAINS = {"biology", "earth_science", "economics", "psychology", "robotics",
                  "sustainable_living"}

TEMPO_CLASSES = "event analysis/localization · time-period contextualization · " \
                "other TEMPO class (write it in) · not temporal at all"
RECOR_TYPES = "continuation · coreference · self-contained · topic-shift · other"
FAILURE_MODES_T1 = "right topic, wrong period · period partly covered · " \
                   "lexical mismatch · gold looks wrong/debatable · other"
FAILURE_MODES_T2 = "needs history, not given · history drowns the turn · " \
                   "implicit reasoning link · lexical mismatch · gold looks wrong/debatable · other"


# ------------------------------------------------------------------ BM25 -----
def _load_kit(kit):
    sys.path.insert(0, os.path.abspath(kit))
    import bm25 as kit_bm25          # noqa: E402  (tokenizer, reference class)
    import ir_metrics as kit_metrics  # noqa: E402  (official starter nDCG)
    return kit_bm25, kit_metrics


class FastBM25:
    """Inverted-index twin of starter_kit/bm25.py::BM25. Same scores, same order."""

    def __init__(self, tokenize, k1=0.9, b=0.4):
        self.tokenize, self.k1, self.b = tokenize, k1, b
        self.doc_ids, self.doc_len = [], []
        self.post_doc = defaultdict(lambda: array("I"))
        self.post_tf = defaultdict(lambda: array("I"))

    def add(self, doc_id, text):
        i = len(self.doc_ids)
        self.doc_ids.append(doc_id)
        toks = self.tokenize(text)
        self.doc_len.append(len(toks))
        counts = {}
        for w in toks:
            counts[w] = counts.get(w, 0) + 1
        for w, f in counts.items():
            self.post_doc[w].append(i)
            self.post_tf[w].append(f)

    def finalize(self):
        self.N = len(self.doc_ids)
        self.avgdl = (sum(self.doc_len) / self.N) if self.N else 0.0
        N = self.N
        self.idf = {w: log(1 + (N - len(p) + 0.5) / (len(p) + 0.5))
                    for w, p in self.post_doc.items()}
        self.post_doc, self.post_tf = dict(self.post_doc), dict(self.post_tf)
        self._by_id = None

    def search(self, query, top_k=100):
        k1, b, avg = self.k1, self.b, (self.avgdl or 1)
        acc = {}
        # outer loop over query terms (duplicates kept, same order) so each
        # document's score is summed in exactly the order bm25.py sums it
        for w in self.tokenize(query):
            docs = self.post_doc.get(w)
            if docs is None:
                continue
            idf = self.idf.get(w, 0.0)
            tfs = self.post_tf[w]
            dl = self.doc_len
            for i, f in zip(docs, tfs):
                denom = f + k1 * (1 - b + b * dl[i] / avg)
                acc[i] = acc.get(i, 0.0) + idf * (f * (k1 + 1)) / denom
        scored = sorted(((self.doc_ids[i], s) for i, s in acc.items()),
                        key=lambda x: (-x[1], x[0]))[:top_k]
        if len(scored) < top_k:  # bm25.py pads with zero-score docs by doc id
            if self._by_id is None:
                self._by_id = sorted(self.doc_ids)
            hit = {d for d, _ in scored}
            for d in self._by_id:
                if len(scored) >= top_k:
                    break
                if d not in hit:
                    scored.append((d, 0.0))
        return scored


# ----------------------------------------------------------------- helpers ---
def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(ln) for ln in f if ln.strip()]


def load_qrels(path):
    gold = defaultdict(set)
    if not os.path.exists(path):
        return gold
    with open(path, encoding="utf-8") as f:
        for ln in f:
            if ln.strip():
                qid, _, docid, rel = ln.split()
                if int(rel) > 0:
                    gold[qid].add(docid)
    return gold


def build_index(corpus_path, key, tokenize):
    t0 = time.time()
    ix = FastBM25(tokenize)
    with open(corpus_path, encoding="utf-8") as f:
        for n, ln in enumerate(f, 1):
            if ln.strip():
                d = json.loads(ln)
                ix.add(d[key], d.get("content", ""))
            if n % 50000 == 0:
                print(f"      indexed {n:,} docs ...", flush=True)
    ix.finalize()
    print(f"    index: {ix.N:,} docs, {len(ix.idf):,} terms, {time.time() - t0:.0f}s",
          flush=True)
    return ix


def run_queries(ix, queries, label):
    t0 = time.time()
    out = {}
    cache = {}
    for n, (qid, q) in enumerate(queries, 1):
        if q not in cache:
            cache[q] = ix.search(q, 100)
        out[qid] = cache[q]
        if n % 100 == 0:
            print(f"      {label}: {n}/{len(queries)}", flush=True)
    print(f"    {label:<22} {len(queries):>5} topics  {time.time() - t0:6.1f}s", flush=True)
    return out


def write_run(path, run, tag):
    with open(path, "w", encoding="utf-8") as f:
        for qid, ranked in run.items():
            for r, (d, s) in enumerate(ranked, 1):
                f.write(f"{qid}\tQ0\t{d}\t{r}\t{s:.6f}\t{tag}\n")


def score(run, gold, ndcg):
    """Mean nDCG@10 over judged topics; unanswered judged topics score 0."""
    per = {qid: ndcg([d for d, _ in run.get(qid, [])], g, 10) for qid, g in gold.items()}
    return (sum(per.values()) / len(per) if per else 0.0), per


def turn_bucket(qid):
    try:
        t = int(qid.rsplit("_turn_", 1)[1])
        return "T5+" if t >= 5 else f"T{t}"
    except (IndexError, ValueError):
        return "T?"


def snippet(text, n=260):
    t = " ".join((text or "").split())
    return t if len(t) <= n else t[:n] + " …"


def fetch_docs(corpus_path, key, wanted):
    got = {}
    if not wanted:
        return got
    with open(corpus_path, encoding="utf-8") as f:
        for ln in f:
            if ln.strip():
                d = json.loads(ln)
                if d[key] in wanted:
                    got[d[key]] = d.get("content", "")
                    if len(got) == len(wanted):
                        break
    return got


def sample_cases(per_run, n_fail, n_ok, rng):
    """Reproducible random sample, fixed BEFORE reading any case text.
    Failures are nDCG@10 == 0; a few clear successes are kept for contrast."""
    fails = sorted(q for q, v in per_run.items() if v == 0.0)
    oks = sorted(q for q, v in per_run.items() if v >= 0.5)
    return (rng.sample(fails, min(n_fail, len(fails))),
            rng.sample(oks, min(n_ok, len(oks))))


# ----------------------------------------------------------------- tracks ----
def do_track1(a, dom, tokenize, ndcg, runs_dir, results, cases, rng):
    d = os.path.join(a.data, "track1_tempo", dom)
    print(f"\n[track1 / {dom}]", flush=True)
    recs = read_jsonl(os.path.join(d, f"examples_{a.split}.jsonl"))
    steps_path = os.path.join(d, f"steps_{a.split}.jsonl")
    step_recs = read_jsonl(steps_path) if os.path.exists(steps_path) else []
    g1a = load_qrels(os.path.join(d, f"qrels_{a.split}.txt"))
    g1b = load_qrels(os.path.join(d, f"qrels_steps_{a.split}.txt"))
    ix = build_index(os.path.join(d, "documents.jsonl"), "id", tokenize)

    q1a = [(r["id"], r["query"]) for r in recs]
    strategies = {
        # official baseline: TEMPO run_step.py, verbatim format
        "1b_query+step": lambda r, s: f"{r['query']}\n\nStep: {s.get('step_instruction', '')}",
        "1b_step_only": lambda r, s: s.get("step_instruction", ""),
        "1b_query+all": lambda r, s: r["query"] + "\n\nSteps:\n" + "\n".join(
            x.get("step_instruction", "") for x in r.get("steps", [])),
    }
    n_steps = sum(len(r.get("steps", [])) for r in step_recs)
    if step_recs and n_steps == 0:
        print("    !! steps file has no nested 'steps' — 1b skipped; check the schema")

    plan = [("1a", q1a, g1a)]
    for name, fn in strategies.items():
        if n_steps:
            plan.append((name, [(s["step_id"], fn(r, s)) for r in step_recs
                                for s in r.get("steps", [])], g1b))
    per_by = {}
    for name, queries, gold in plan:
        run = run_queries(ix, queries, name)
        write_run(os.path.join(runs_dir, f"t1_{dom}_{a.split}_{name}.tsv"), run, name)
        m, per = score(run, gold, ndcg)
        per_by[name] = (run, per)
        ref_key = "1a" if name == "1a" else ("1b" if name == "1b_query+step" else None)
        ref = REF.get(ref_key, {}).get(dom) if ref_key else None
        ref_v = (ref[0] if a.split == "train" else ref[1]) if ref else None
        results.append({"track": 1, "domain": dom, "split": a.split, "run": name,
                        "n": len(gold), "ndcg10": round(m, 4), "official_ref": ref_v})

    # failure cases (1a)
    run, per = per_by["1a"]
    fails, oks = sample_cases(per, a.cases, 2, rng)
    step_by_q = {r["id"]: r for r in step_recs}
    by_q = {r["id"]: r for r in recs}
    wanted = set()
    for q in fails + oks:
        wanted |= set(g1a[q]) | {x for x, _ in run[q][:5]}
    docs = fetch_docs(os.path.join(d, "documents.jsonl"), "id", wanted)
    for q in fails + oks:
        r = by_q[q]
        lines = [f"### {dom} · `{q}` · 1a nDCG@10 = {per[q]:.3f}"
                 f"{'  (success, for contrast)' if q in oks else ''}\n",
                 f"**Query:** {snippet(r['query'], 900)}\n"]
        st = step_by_q.get(q, {}).get("steps", [])
        if st:
            lines.append("**Steps:**")
            for s in st:
                sid = s["step_id"]
                sc = {k: per_by[k][1].get(sid) for k in strategies if k in per_by}
                sc_txt = ", ".join(f"{k.split('_', 1)[1]} {v:.2f}" for k, v in sc.items()
                                   if v is not None)
                lines.append(f"- {snippet(s.get('step_instruction', ''), 220)}  "
                             f"_(nDCG@10: {sc_txt})_")
            lines.append("")
        lines.append("**Gold passages:**")
        for gd in sorted(g1a[q]):
            lines.append(f"- `{gd}` — {snippet(docs.get(gd, '(not in corpus!)'))}")
        lines.append("\n**BM25 top 5:**")
        for rank, (x, s) in enumerate(run[q][:5], 1):
            mark = "✅ GOLD" if x in g1a[q] else ""
            lines.append(f"{rank}. `{x}` {mark} — {snippet(docs.get(x, ''))}")
        lines += ["", f"- [ ] TEMPO class: {TEMPO_CLASSES}",
                  f"- [ ] Failure mode: {FAILURE_MODES_T1}",
                  "- Note: ", "\n---\n"]
        cases["t1"].append("\n".join(lines))


def do_track2(a, dom, tokenize, ndcg, runs_dir, results, cases, rng):
    d = os.path.join(a.data, "track2_recor", dom)
    print(f"\n[track2 / {dom}]", flush=True)
    bench = json.load(open(os.path.join(d, f"benchmark_{a.split}.json"), encoding="utf-8"))
    bench = [bench] if isinstance(bench, dict) else bench
    gold = load_qrels(os.path.join(d, f"qrels_{a.split}.txt"))
    ix = build_index(os.path.join(d, "documents.jsonl"), "doc_id", tokenize)

    turns = [(f"{c['id']}_turn_{t['turn_id']}", c, t) for c in bench for t in c["turns"]]

    def hist(t):
        h = t.get("conversation_history", "") or ""
        return "" if h.lower().startswith("no previous") else h

    def hist_part(t, which):
        """conversation_history is 'Q: ...\\nA: ...' blocks; keep only Q or only A."""
        keep, cur = [], None
        for ln in hist(t).splitlines():
            s = ln.strip()
            if s.startswith("Q:"):
                cur = "Q"
                s = s[2:]
            elif s.startswith("A:"):
                cur = "A"
                s = s[2:]
            if cur == which:
                keep.append(s.strip())
        return " ".join(keep)

    plan = {
        "2a_current": [(q, t["query"]) for q, _, t in turns],
        # identical to starter_kit/bm25_baseline.py --strategy history
        "2a_history": [(q, (hist(t) + " " + t["query"]).strip()) for q, _, t in turns],
        # one-variable ablations of what "history" contributes
        "2a_hist_questions_only": [(q, (hist_part(t, "Q") + " " + t["query"]).strip())
                                   for q, _, t in turns],
        "2a_hist_answers_only": [(q, (hist_part(t, "A") + " " + t["query"]).strip())
                                 for q, _, t in turns],
        "2a_ORACLE_hist+reasoning": [
            (q, (hist(t) + " " + t["query"] + " " +
                 (t.get("subquestion_reasoning", "") or "")).strip()) for q, _, t in turns],
    }
    has_reason = sum(1 for _, _, t in turns if t.get("subquestion_reasoning"))
    if has_reason == 0:
        plan.pop("2a_ORACLE_hist+reasoning")
        print("    (no subquestion_reasoning in this split — oracle run skipped)")
    has_qa = sum(1 for _, _, t in turns if hist_part(t, "A"))
    if has_qa == 0:
        plan.pop("2a_hist_questions_only")
        plan.pop("2a_hist_answers_only")
        print("    (history has no 'Q:'/'A:' structure — Q/A ablations skipped)")

    # gold recycling: how much of a turn's gold was already gold in earlier turns
    recycled, later_turns = [], 0
    prev_gold_rank = {}
    for c in bench:
        seen = []  # earlier turns' gold, most recent turn first
        for t in sorted(c["turns"], key=lambda x: x["turn_id"]):
            q = f"{c['id']}_turn_{t['turn_id']}"
            g = gold.get(q, set())
            if seen and g:
                later_turns += 1
                prior = {d for block in seen for d in block}
                recycled.append(len(g & prior) / len(g))
            ranked, dup = [], set()
            for block in seen:
                for doc in sorted(block):
                    if doc not in dup:
                        ranked.append((doc, 1.0))
                        dup.add(doc)
            prev_gold_rank[q] = ranked
            seen.insert(0, g)
    if recycled:
        full = sum(1 for r in recycled if r == 1.0)
        some = sum(1 for r in recycled if r > 0)
        print(f"    gold recycling: {some}/{later_turns} later turns reuse earlier gold; "
              f"{full}/{later_turns} reuse ALL of it; mean share {sum(recycled)/len(recycled):.2f}")
        results.append({"track": 2, "domain": dom, "split": a.split, "run": "DIAG_gold_recycling",
                        "n": later_turns, "ndcg10": round(sum(recycled) / len(recycled), 4),
                        "official_ref": None,
                        "source": "BRIGHT" if dom in BRIGHT_DOMAINS else "StackExchange",
                        "by_turn": {}, "any_reuse": some, "full_reuse": full})

    per_by = {}
    # ORACLE: rank = earlier turns' gold, nothing else. Needs hidden qrels, so it is
    # never a system; it measures how far "look up what was relevant before" goes.
    m, per = score(prev_gold_rank, gold, ndcg)
    results.append({"track": 2, "domain": dom, "split": a.split,
                    "run": "2a_ORACLE_prev_turn_gold", "n": len(gold), "ndcg10": round(m, 4),
                    "official_ref": None,
                    "source": "BRIGHT" if dom in BRIGHT_DOMAINS else "StackExchange",
                    "by_turn": {}})
    print(f"    {'2a_ORACLE_prev_turn_gold':<22}  nDCG@10 {m:.4f} (earlier turns' gold only)")

    for name, queries in plan.items():
        run = run_queries(ix, queries, name)
        write_run(os.path.join(runs_dir, f"t2_{dom}_{a.split}_{name}.tsv"), run, name)
        m, per = score(run, gold, ndcg)
        per_by[name] = (run, per)
        ref = REF.get(name, {}).get(dom)
        ref_v = (ref[0] if a.split == "train" else ref[1]) if ref else None
        buckets = defaultdict(list)
        for q, v in per.items():
            buckets[turn_bucket(q)].append(v)
        results.append({"track": 2, "domain": dom, "split": a.split, "run": name,
                        "n": len(gold), "ndcg10": round(m, 4), "official_ref": ref_v,
                        "source": "BRIGHT" if dom in BRIGHT_DOMAINS else "StackExchange",
                        "by_turn": {k: round(sum(v) / len(v), 4)
                                    for k, v in sorted(buckets.items())}})

    run_c, per_c = per_by["2a_current"]
    run_h, per_h = per_by["2a_history"]
    fails, oks = sample_cases(per_h, a.cases, 2, rng)  # failures of the STRONGER run
    info = {q: (c, t) for q, c, t in turns}
    wanted = set()
    for q in fails + oks:
        wanted |= set(gold[q]) | {x for x, _ in run_h[q][:5]}
    docs = fetch_docs(os.path.join(d, "documents.jsonl"), "doc_id", wanted)
    for q in fails + oks:
        c, t = info[q]
        lines = [f"### {dom} · `{q}` · current {per_c.get(q, 0):.3f} → "
                 f"+history {per_h[q]:.3f}"
                 f"{'  (success, for contrast)' if q in oks else ''}\n"]
        h = hist(t)
        if h:
            lines.append(f"**History:** {snippet(h, 700)}\n")
        lines.append(f"**Current turn:** {snippet(t['query'], 400)}\n")
        lines.append("**Gold passages:**")
        for gd in sorted(gold[q]):
            lines.append(f"- `{gd}` — {snippet(docs.get(gd, '(not in corpus!)'))}")
        lines.append("\n**BM25 +history top 5:**")
        for rank, (x, s) in enumerate(run_h[q][:5], 1):
            mark = "✅ GOLD" if x in gold[q] else ""
            lines.append(f"{rank}. `{x}` {mark} — {snippet(docs.get(x, ''))}")
        lines += ["", f"- [ ] Discourse type: {RECOR_TYPES}",
                  f"- [ ] Failure mode: {FAILURE_MODES_T2}",
                  "- Note: ", "\n---\n"]
        cases["t2"].append("\n".join(lines))


# ------------------------------------------------------------------- report --
def write_report(a, results):
    rows = ["# Week-1 results\n",
            f"split: `{a.split}` · BM25 k1=0.9 b=0.4 · pure-Python (FastBM25 ≡ "
            f"starter_kit/bm25.py) · nDCG@10 via starter_kit/ir_metrics.py\n",
            "`official_ref` is the pyserini baseline from BASELINE_RESULTS.md. "
            "Tokenisation differs, so a small gap is expected; a large one is a "
            "finding to investigate, not to patch.\n",
            "| track | domain | run | n | nDCG@10 | official ref | Δ |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: |"]
    for r in results:
        ref = r["official_ref"]
        ref_txt = "" if ref is None else f"{ref:.4f}"
        delta_txt = "" if ref is None else f"{r['ndcg10'] - ref:+.4f}"
        rows.append(f"| {r['track']} | {r['domain']} | {r['run']} | {r['n']} | "
                    f"{r['ndcg10']:.4f} | {ref_txt} | {delta_txt} |")
    t2 = [r for r in results if r["track"] == 2]
    if t2:
        rows += ["", "## Track 2 by turn depth", "",
                 "| domain | run | " + " | ".join(["T1", "T2", "T3", "T4", "T5+"]) + " |",
                 "| --- | --- |" + " ---: |" * 5]
        for r in t2:
            b = r["by_turn"]
            if not b:
                continue
            rows.append(f"| {r['domain']} ({r['source']}) | {r['run']} | " +
                        " | ".join(f"{b[k]:.3f}" if k in b else "" for k in
                                   ["T1", "T2", "T3", "T4", "T5+"]) + " |")
    rows += ["", "Notes:",
             "- `2a_ORACLE_hist+reasoning` appends GOLD reasoning to the query. "
             "It is a diagnostic, not a deployable system or guaranteed ceiling.",
             "- `2a_ORACLE_prev_turn_gold` ranks ONLY the gold passages of earlier turns "
             "(needs hidden qrels, never a system). It measures how much of +history's "
             "gain could come from re-finding what was already relevant.",
             "- `DIAG_gold_recycling`: the value column is the mean share of a later "
             "turn's gold that was already gold in an earlier turn — not an nDCG.",
             "- `2a_hist_questions_only` / `2a_hist_answers_only` split the history "
             "into prior questions vs prior REFERENCE answers (written from gold passages).",
             "- `1b_step_only` and `1b_query+all` are the two strategies the task "
             "proposal permits but the baseline does not report.",
             "- Small domains give unstable numbers (see iota: official 1a train "
             "0.0199 vs dev 0.2083). Report n next to every score."]
    open(os.path.join(a.out, "results.md"), "w", encoding="utf-8").write("\n".join(rows))
    json.dump(results, open(os.path.join(a.out, "results.json"), "w", encoding="utf-8"),
              indent=2)


def selftest(kit_bm25):
    """FastBM25 must rank exactly like starter_kit/bm25.py."""
    rng = random.Random(0)
    vocab = [f"w{i}" for i in range(400)] + ["the", "and", "2013", "2017", "bitcoin"]
    docs = [(f"d{i:05d}", " ".join(rng.choice(vocab) for _ in range(rng.randint(5, 120))))
            for i in range(3000)]
    ref = kit_bm25.BM25([d for d, _ in docs], [t for _, t in docs])
    fast = FastBM25(kit_bm25.tokenize)
    for d, t in docs:
        fast.add(d, t)
    fast.finalize()
    for _ in range(200):
        q = " ".join(rng.choice(vocab) for _ in range(rng.randint(1, 60)))
        if ref.search(q, 100) != fast.search(q, 100):
            sys.exit("SELFTEST FAILED: rankings differ from starter_kit/bm25.py")
    q = "zzz_no_such_term"
    if ref.search(q, 100) != fast.search(q, 100):
        sys.exit("SELFTEST FAILED on zero-match padding")
    print("selftest OK: FastBM25 == starter_kit BM25 on 200 random queries x 3000 docs")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=None)
    ap.add_argument("--kit", required=True, help="path to RETECO/starter_kit")
    ap.add_argument("--split", default="dev", choices=["train", "dev"])
    ap.add_argument("--track1", nargs="*", default=[])
    ap.add_argument("--track2", nargs="*", default=[])
    ap.add_argument("--cases", type=int, default=10, help="failures to sample per domain")
    ap.add_argument("--seed", type=int, default=20260921)
    ap.add_argument("--out", default="week1_out")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    kit_bm25, kit_metrics = _load_kit(a.kit)
    if a.selftest:
        selftest(kit_bm25)
        return
    if not a.data:
        sys.exit("--data is required")
    runs_dir = os.path.join(a.out, "runs")
    os.makedirs(runs_dir, exist_ok=True)
    rng = random.Random(a.seed)
    results, cases = [], {"t1": [], "t2": []}
    t0 = time.time()
    for dom in a.track1:
        do_track1(a, dom, kit_bm25.tokenize, kit_metrics.ndcg_at_k, runs_dir, results, cases, rng)
        write_report(a, results)
    for dom in a.track2:
        do_track2(a, dom, kit_bm25.tokenize, kit_metrics.ndcg_at_k, runs_dir, results, cases, rng)
        write_report(a, results)
    head = (f"_seed {a.seed}; cases were sampled at random from nDCG@10 = 0 before "
            f"reading them. Label each one; do not re-sample._\n\n")
    for k, title in (("t1", "Track 1 failure cases (1a)"),
                     ("t2", "Track 2 failure cases (2a +history)")):
        if cases[k]:
            open(os.path.join(a.out, f"cases_track{k[1]}.md"), "w", encoding="utf-8").write(
                f"# {title}\n\n{head}" + "\n".join(cases[k]))
    print(f"\ndone in {time.time() - t0:.0f}s -> {os.path.abspath(a.out)}")
    print(open(os.path.join(a.out, "results.md"), encoding="utf-8").read())


if __name__ == "__main__":
    main()
