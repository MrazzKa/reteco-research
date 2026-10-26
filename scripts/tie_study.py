#!/usr/bin/env python3
"""How much did the doc-id tie-break help? Gold in the top 10 that sat on an exact score tie.

For each final system (BM25, dense, hybrid, hybrid + cross-encoder) and each tie key
(`id`: weeks 1-4, `sha1`: week 5) count, over all judged dev and train topics:

  gold_top10        gold documents ranked in the top 10
  gold_tied         ... of which share their exact score with >= 1 non-gold document of the
                    same list (depth 1000 for BM25/dense, the fusion pool for the hybrid, the
                    reranked top N for the cross-encoder)
  gold_tied_first   ... of which are ranked above every non-gold document they are tied with

Scores per (system, key) come from the run files written with that key (runs_v12 = id,
runs_v13 = sha1); hybrid and cross-encoder lists are recomputed from them with the frozen
configurations of the corresponding hybrid / rerank_ce reports.

    python3 tie_study.py --data ../../reteco_data_v11 --out ../research/runs_v13/tiebreak/ties.json
"""
import argparse
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dense_index import T1, T2  # noqa: E402
from hybrid import Query, qrels_for, read_run  # noqa: E402
import tiebreak  # noqa: E402

R12, R13 = "../research/runs_v12", "../research/runs_v13"
# (track, condition, dense condition, bm25 dir, dense dir, hybrid report, ce dir) per tie key
SYSTEMS = {
    "id": {
        "t1": ("bm25/t1/runs", "dense/bge-small_L256/t1/runs", "hybrid/bge-small_L256_t1.json", None),
        "t2": ("bm25/t2/runs", "dense/bge-base_L512/t2/runs", "hybrid/bge-base_L512_t2.json", "ce_bge-base"),
    },
    "sha1": {
        "t1": ("bm25/t1/runs", "dense/bge-small_L256/t1/runs", "hybrid/bge-small_L256_t1.json", None),
        "t2": ("bm25/t2/runs", "dense/bge-base_L512/t2/runs", "hybrid/bge-base_L512_t2.json", "ce"),
    },
}
CONDS = [(1, "1a", "1a"), (1, "1b_query+step", "1b_query+step"),
         (2, "2a_current", "2a_current"), (2, "2a_history", "2a_history_qfirst")]


def fused(q, cfg):
    """(doc, fused score) for the pool, as hybrid.system ranks it."""
    pool = q.pool(cfg["kb"], cfg["kd"])
    if cfg["kind"] == "linear":
        al, how = cfg["alpha"], cfg["norm"]
        return [(d, al * q.norm(d, "de", how) + (1 - al) * q.norm(d, "bm", how)) for d in pool]
    c = cfg["c"]
    return [(d, (1.0 / (c + q.bm_rank[d]) if d in q.bm_rank else 0.0)
             + (1.0 / (c + q.de_rank[d]) if d in q.de_rank else 0.0)) for d in pool]


def order(scored):
    return sorted(scored, key=lambda x: (-x[1], tiebreak.key(x[0])))


def count(ranked, gold, acc):
    """ranked: [(doc, score)] in final order; ties counted within this list."""
    by_score = defaultdict(list)
    for d, s in ranked:
        by_score[s].append(d)
    for r, (d, s) in enumerate(ranked[:10]):
        if d not in gold:
            continue
        acc["gold_top10"] += 1
        twins = [x for x in by_score[s] if x not in gold]
        if twins:
            acc["gold_tied"] += 1
            pos = {x: i for i, (x, _) in enumerate(ranked)}
            if all(pos[t] > r for t in twins):
                acc["gold_tied_first"] += 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = {}
    for key, systems in SYSTEMS.items():
        tiebreak.set_mode(key)
        root = R12 if key == "id" else R13
        for track, cond, dcond in CONDS:
            bdir, ddir, hrep, cedir = systems[f"t{track}"]
            hyb = json.load(open(os.path.join(root, hrep)))["conditions"][cond]
            cfg = hyb["systems"]["linear*"]["cfg"]
            ce = None
            if cedir and cond == "2a_current":
                cer = json.load(open(os.path.join(root, cedir, "t2.json")))[cond]
                ce = int(cer["chosen_depth_on_train"])
            for split in ("train", "dev"):
                for dom in (T1 if track == 1 else T2):
                    pre = f"t{track}_{dom}_{split}"
                    bm = read_run(os.path.join(root, bdir, f"{pre}_{cond}.tsv"))
                    de = read_run(os.path.join(root, ddir, f"{pre}_{dcond}.tsv"))
                    gold = qrels_for(a.data, track, dom, split, cond)
                    scores = {}
                    if ce:
                        p = os.path.join(root, cedir, f"scores_t2_{dom}_{split}_{cond}.json")
                        scores = json.load(open(p)) if os.path.exists(p) else {}
                    for qid, g in gold.items():
                        acc = out.setdefault(f"{key}|{cond}|{split}|{dom}", {})
                        for sysname in ("bm25", "dense", "hybrid", "ce"):
                            acc.setdefault(sysname, defaultdict(int))
                        q = Query(bm.get(qid, []), de.get(qid, []))
                        count(order(q.bm), g, acc["bm25"])
                        count(order(q.de), g, acc["dense"])
                        h = order(fused(q, cfg))
                        count(h, g, acc["hybrid"])
                        if ce and qid in scores:
                            sc = scores[qid]
                            head = order([(d, sc[d]) for d, _ in h[:ce]])
                            # tail keeps hybrid scores; offset so they never tie with the head
                            count(head + [(d, s - 1e9) for d, s in h[ce:]], g, acc["ce"])
            print(f"done {key} {cond}", flush=True)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(out, open(a.out, "w"), indent=1)
    # summary: per (key, cond, split, system), summed over domains
    summ = defaultdict(lambda: defaultdict(int))
    for k, systems in out.items():
        key, cond, split, _ = k.split("|")
        for s, c in systems.items():
            for m, v in c.items():
                summ[f"{key}|{cond}|{split}|{s}"][m] += v
    for k in sorted(summ):
        c = summ[k]
        if c["gold_top10"]:
            print(f"{k:<40} top10 {c['gold_top10']:>5}  tied {c['gold_tied']:>4}  tied&first {c['gold_tied_first']:>4}")


if __name__ == "__main__":
    main()
