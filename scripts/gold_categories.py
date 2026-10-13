#!/usr/bin/env python3
"""Who finds which gold document? BM25-only / dense-only / both / neither, on DEV.

For every (topic, gold document) pair of a condition, the gold document is classed at
depth k (10 and 100) by whether it appears in the BM25 top-k, the dense top-k, both or
neither. Counts are reported per domain and track. This is diagnosis only: nothing here
feeds back into model or parameter choices.

Descriptive features are computed for ALL pairs (not just the examples), so hypotheses
about the categories can be checked on the whole population:
  * overlap      share of the query's content stems that occur in the gold document
  * overlap_win  same, but only in the part of the document an encoder with a W-token window
                 sees (first ~0.75*W words, a rough words-per-token conversion)
  * q_nums       query contains a number/year; nums_hit = share of those found in the gold
  * gold_words / query_words  lengths in words (beyond the window = truncated for the encoder)

Example selection (fixed before any example was read; seed 20260921):
  for each category at k=100, conditions 1a (Track 1) and 2a_current (Track 2) only;
  pairs sorted by (track, domain, qid, doc); shuffled with random.Random(20260921);
  take pairs in that order, skipping a pair whose query was already used, until there
  are `--per-track` examples per track. No other filtering.

    python3 gold_categories.py --data ../../reteco_data_v11 --bm25 ../research/runs_v12/bm25 \
        --dense ../research/runs_v12/dense/bge-small_L512 --out ../research/runs_v12/categories
"""
import argparse
import html
import json
import os
import random
import re
import sys
from collections import defaultdict

import Stemmer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from week1_run import load_qrels, read_jsonl  # noqa: E402
from dense_index import T1, T2  # noqa: E402
from hybrid import read_run  # noqa: E402

SEED = 20260921
CATS = ("bm25_only", "dense_only", "both", "neither")
COND = {1: [("1a", "1a"), ("1b_query+step", "1b_query+step")],
        2: [("2a_current", "2a_current"), ("2a_history", "2a_history_qfirst")]}
EXAMPLE_COND = {1: "1a", 2: "2a_current"}
STEM = Stemmer.Stemmer("english")
WORD = re.compile(r"[a-z0-9]+")
NUM = re.compile(r"\b\d[\d,.]*\b")
TAG = re.compile(r"<[^>]+>")


def stopwords():
    try:
        from bm25s.stopwords import STOPWORDS_EN
        return set(STOPWORDS_EN)
    except Exception:  # noqa: BLE001
        return {"the", "a", "an", "of", "and", "or", "in", "on", "to", "is", "are", "was", "for"}


STOP = stopwords()


def clean(text):
    return " ".join(html.unescape(TAG.sub(" ", text or "")).split())


def stems(text):
    return [STEM.stemWord(w) for w in WORD.findall(text.lower()) if w not in STOP]


def topics(data, track, dom, split, cond):
    sub = "track1_tempo" if track == 1 else "track2_recor"
    d = os.path.join(data, sub, dom)
    if track == 1:
        recs = read_jsonl(os.path.join(d, f"examples_{split}.jsonl"))
        if cond == "1a":
            return ({r["id"]: {"query": r["query"]} for r in recs},
                    load_qrels(os.path.join(d, f"qrels_{split}.txt")))
        out = {}
        for r in read_jsonl(os.path.join(d, f"steps_{split}.jsonl")):
            for s in r.get("steps", []):
                out[s["step_id"]] = {"query": f"{r['query']}\n\nStep: {s.get('step_instruction', '')}"}
        return out, load_qrels(os.path.join(d, f"qrels_steps_{split}.txt"))
    bench = json.load(open(os.path.join(d, f"benchmark_{split}.json"), encoding="utf-8"))
    bench = [bench] if isinstance(bench, dict) else bench
    out = {}
    for c in bench:
        for t in c["turns"]:
            h = t.get("conversation_history", "") or ""
            h = "" if h.lower().startswith("no previous") else h
            out[f"{c['id']}_turn_{t['turn_id']}"] = {"query": t["query"], "history": h,
                                                     "turn": t["turn_id"]}
    return out, load_qrels(os.path.join(d, f"qrels_{split}.txt"))


def fetch(data, track, dom, wanted):
    sub, key = ("track1_tempo", "id") if track == 1 else ("track2_recor", "doc_id")
    got = {}
    with open(os.path.join(data, sub, dom, "documents.jsonl"), encoding="utf-8") as f:
        for line in f:
            if wanted and line.strip():
                d = json.loads(line)
                if d[key] in wanted:
                    got[d[key]] = d.get("content", "") or ""
    return got


def features(query, doc, window_words):
    qs = set(stems(clean(query)))
    dwords = clean(doc).split()
    ds_all = set(stems(" ".join(dwords)))
    ds_win = set(stems(" ".join(dwords[:window_words])))
    qnums = set(NUM.findall(clean(query)))
    return {"overlap": len(qs & ds_all) / len(qs) if qs else 0.0,
            "overlap_win": len(qs & ds_win) / len(qs) if qs else 0.0,
            "q_nums": bool(qnums),
            "nums_hit": (len({n for n in qnums if n in doc}) / len(qnums)) if qnums else None,
            "gold_words": len(dwords), "query_words": len(clean(query).split())}


def rank_of(lst, doc):
    for r, (d, _) in enumerate(lst, 1):
        if d == doc:
            return r
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--bm25", required=True, help="dir with t1/ and t2/ BM25 run dirs")
    ap.add_argument("--dense", required=True, help="dir with t1/ and t2/ dense run dirs")
    ap.add_argument("--split", default="dev")
    ap.add_argument("--window", type=int, default=512, help="encoder window in tokens")
    ap.add_argument("--per-track", type=int, default=2)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    win_words = int(0.75 * a.window)
    os.makedirs(a.out, exist_ok=True)
    pairs, counts = [], {}
    for track, doms in ((1, T1), (2, T2)):
        for dom in doms:
            per_cond = []
            for cond, dcond in COND[track]:
                pre = f"t{track}_{dom}_{a.split}"
                bp = os.path.join(a.bm25, f"t{track}", "runs", f"{pre}_{cond}.tsv")
                dp = os.path.join(a.dense, f"t{track}", "runs", f"{pre}_{dcond}.tsv")
                if not (os.path.exists(bp) and os.path.exists(dp)):
                    print(f"  missing runs for t{track}/{dom}/{cond}", flush=True)
                    continue
                per_cond.append((cond, read_run(bp), read_run(dp), *topics(a.data, track, dom, a.split, cond)))
            wanted = {g for *_, gold in per_cond for gs in gold.values() for g in gs}
            texts = fetch(a.data, track, dom, wanted)
            for cond, bm, de, tops, gold in per_cond:
                for qid in sorted(gold):
                    if qid not in tops:
                        continue
                    for g in sorted(gold[qid]):
                        rb, rd = rank_of(bm.get(qid, []), g), rank_of(de.get(qid, []), g)
                        row = {"track": track, "domain": dom, "cond": cond, "qid": qid, "doc": g,
                               "bm25_rank": rb, "dense_rank": rd, "n_gold": len(gold[qid])}
                        for k in (10, 100):
                            inb, ind = rb is not None and rb <= k, rd is not None and rd <= k
                            row[f"cat{k}"] = ("both" if inb and ind else "bm25_only" if inb else
                                              "dense_only" if ind else "neither")
                        row.update(features(tops[qid]["query"], texts.get(g, ""), win_words))
                        if track == 2:
                            row["turn"] = tops[qid]["turn"]
                        pairs.append(row)
            print(f"  t{track}/{dom}: {sum(1 for p in pairs if p['domain'] == dom and p['track'] == track)} pairs",
                  flush=True)

    # ---- counts by (track, cond, domain, k)
    for p in pairs:
        for k in (10, 100):
            for key in ((p["track"], p["cond"], p["domain"], k), (p["track"], p["cond"], "ALL", k)):
                c = counts.setdefault("|".join(map(str, key)), {c: 0 for c in CATS})
                c[p[f"cat{k}"]] += 1

    # ---- feature means per category (k=100), per track/condition
    feat = {}
    for p in pairs:
        key = f"{p['track']}|{p['cond']}|{p['cat100']}"
        f = feat.setdefault(key, defaultdict(list))
        for m in ("overlap", "overlap_win", "gold_words", "query_words"):
            f[m].append(p[m])
        f["q_nums"].append(1.0 if p["q_nums"] else 0.0)
        if p["nums_hit"] is not None:
            f["nums_hit"].append(p["nums_hit"])
        f["gold_beyond_window"].append(1.0 if p["gold_words"] > win_words else 0.0)
        f["match_only_beyond_window"].append(1.0 if p["overlap"] > p["overlap_win"] + 0.1 else 0.0)
        if "turn" in p:
            f["turn"].append(p["turn"])
    feat_mean = {k: {m: (round(sum(v) / len(v), 3) if v else None) for m, v in f.items()} | {"n": len(f["overlap"])}
                 for k, f in feat.items()}

    # ---- example selection (rule in the docstring)
    examples = {}
    for cat in CATS:
        pool = sorted([p for p in pairs if p["cond"] == EXAMPLE_COND[p["track"]] and p["cat100"] == cat],
                      key=lambda p: (p["track"], p["domain"], p["qid"], p["doc"]))
        random.Random(SEED).shuffle(pool)
        chosen, used = [], set()
        for track in (1, 2):
            n = 0
            for p in pool:
                if p["track"] == track and (p["track"], p["domain"], p["qid"]) not in used and n < a.per_track:
                    chosen.append(p)
                    used.add((p["track"], p["domain"], p["qid"]))
                    n += 1
        examples[cat] = chosen

    json.dump({"window": a.window, "seed": SEED, "counts": counts, "features_k100": feat_mean,
               "examples": examples}, open(os.path.join(a.out, "categories.json"), "w"), indent=1)
    with open(os.path.join(a.out, "pairs.jsonl"), "w") as f:
        for p in pairs:
            f.write(json.dumps(p) + "\n")
    print(f"wrote {a.out}/categories.json ({len(pairs)} pairs)")


if __name__ == "__main__":
    main()
