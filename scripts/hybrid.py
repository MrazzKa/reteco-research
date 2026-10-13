#!/usr/bin/env python3
"""Hybrid BM25 + dense retrieval: fusion tuned on TRAIN, frozen, then measured on DEV.

Inputs are two depth-1000 run directories (bm25s_run.py --k 1000 and dense_search.py)
for one track. Candidate pool = BM25 top-kb  UNION  dense top-kd. Systems compared:

  bm25            BM25 order
  dense           dense order
  rerank          BM25 top-100 reordered by dense score (the week-2 pipeline)
  pool_rerank     the union pool reordered by dense score
  rrf             reciprocal rank fusion, 1/(c + rank_bm25) + 1/(c + rank_dense)
  linear          alpha * norm(dense) + (1 - alpha) * norm(bm25), norm in {minmax, zscore}

Missing scores. Every score is looked up in the depth-1000 runs, so a pool document is
scored exactly by both systems whenever it is inside the other system's top-1000. If it
is not, it gets that system's 1000th score (an upper bound on its true score — we do not
know the exact value, only that it is no higher) and, for RRF, contributes nothing from
that system (rank treated as infinite). Normalisation statistics (min/max, mean/std) are
computed over each system's own top-1000 list for the query.

Tuning: one configuration per (track, condition), chosen by train macro nDCG@10 (domain
macro), over the grid below. Dev is scored once with the frozen configuration.

    python3 hybrid.py --track 1 --conditions 1a 1b_query+step \
        --bm25 ../research/runs_v12/bm25/t1/runs --dense ../research/runs_v12/dense/bge-small_L512/t1/runs \
        --data ../../reteco_data_v11 --kit ../../RETECO/starter_kit --out ../research/runs_v12/hybrid/t1.json
"""
import argparse
import itertools
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from week1_run import load_qrels  # noqa: E402
from bm25s_run import ndcg_fn  # noqa: E402
from dense_index import T1, T2  # noqa: E402

KS = (10, 20, 50, 100, 200, 500, 1000)
DEPTHS = (50, 100, 200, 500)
ALPHAS = [round(0.1 * i, 1) for i in range(11)]
RRF_C = (10, 30, 60, 100)


def read_run(path):
    out = defaultdict(list)
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                qid, _, doc, _, sc, *_ = line.split()
                out[qid].append((doc, float(sc)))
    return out


def qrels_for(data, track, dom, split, cond):
    sub = "track1_tempo" if track == 1 else "track2_recor"
    name = f"qrels_steps_{split}.txt" if cond.startswith("1b") else f"qrels_{split}.txt"
    return load_qrels(os.path.join(data, sub, dom, name))


class Query:
    """Both depth-1000 lists for one topic, with rank/score lookups and norm stats."""

    def __init__(self, bm, de):
        self.bm, self.de = bm, de
        self.bm_rank = {d: r for r, (d, _) in enumerate(bm, 1)}
        self.de_rank = {d: r for r, (d, _) in enumerate(de, 1)}
        self.bm_sc = dict(bm)
        self.de_sc = dict(de)
        self.bm_floor = bm[-1][1] if bm else 0.0
        self.de_floor = de[-1][1] if de else 0.0
        self.stats = {}
        for key, lst in (("bm", bm), ("de", de)):
            v = [s for _, s in lst] or [0.0]
            mn, mx = min(v), max(v)
            mu = sum(v) / len(v)
            sd = (sum((x - mu) ** 2 for x in v) / len(v)) ** 0.5 or 1.0
            self.stats[key] = (mn, mx, mu, sd)

    def pool(self, kb, kd):
        seen, out = set(), []
        for d, _ in self.bm[:kb] + self.de[:kd]:
            if d not in seen:
                seen.add(d)
                out.append(d)
        return out

    def score(self, d, which):
        if which == "bm":
            return self.bm_sc.get(d, self.bm_floor)
        return self.de_sc.get(d, self.de_floor)

    def norm(self, d, which, how):
        s = self.score(d, which)
        mn, mx, mu, sd = self.stats[which]
        if how == "minmax":
            return (s - mn) / (mx - mn) if mx > mn else 0.0
        return (s - mu) / sd


def rank_by(docs, key):
    return [d for d in sorted(docs, key=lambda d: (-key(d), d))]


def system(q, cfg):
    kind = cfg["kind"]
    if kind == "bm25":
        return [d for d, _ in q.bm]
    if kind == "dense":
        return [d for d, _ in q.de]
    if kind == "rerank":
        return rank_by([d for d, _ in q.bm[:100]], lambda d: q.score(d, "de"))
    pool = q.pool(cfg["kb"], cfg["kd"])
    if kind == "pool_rerank":
        return rank_by(pool, lambda d: q.score(d, "de"))
    if kind == "rrf":
        c = cfg["c"]
        return rank_by(pool, lambda d: (1.0 / (c + q.bm_rank[d]) if d in q.bm_rank else 0.0)
                       + (1.0 / (c + q.de_rank[d]) if d in q.de_rank else 0.0))
    if kind == "linear":
        al, how = cfg["alpha"], cfg["norm"]
        return rank_by(pool, lambda d: al * q.norm(d, "de", how) + (1 - al) * q.norm(d, "bm", how))
    raise ValueError(kind)


def grid():
    yield {"kind": "pool_rerank", "kb": 100, "kd": 100}
    for kb, kd in itertools.product(DEPTHS, DEPTHS):
        for c in RRF_C:
            yield {"kind": "rrf", "kb": kb, "kd": kd, "c": c}
    for kb, kd in [(100, 100), (200, 200), (500, 500), (100, 500), (500, 100)]:
        for how in ("minmax", "zscore"):
            for al in ALPHAS:
                yield {"kind": "linear", "kb": kb, "kd": kd, "norm": how, "alpha": al}


def cfg_name(cfg):
    return "|".join(f"{k}={v}" for k, v in cfg.items())


def load_split(a, track, cond, split, doms, dense_cond):
    """{domain: [(Query, gold set)]} for judged topics; missing run topic -> empty list."""
    out = {}
    for dom in doms:
        pre = f"t{track}_{dom}_{split}"
        bp = os.path.join(a.bm25, f"{pre}_{cond}.tsv")
        dp = os.path.join(a.dense, f"{pre}_{dense_cond}.tsv")
        if not (os.path.exists(bp) and os.path.exists(dp)):
            continue
        bm, de = read_run(bp), read_run(dp)
        gold = qrels_for(a.data, track, dom, split, cond)
        out[dom] = [(Query(bm.get(q, []), de.get(q, [])), g) for q, g in sorted(gold.items())]
    return out


def evaluate(data, cfg, ndcg, with_recall=False):
    per_dom = {}
    for dom, items in data.items():
        nd, rec = [], defaultdict(list)
        for q, g in items:
            ranked = system(q, cfg)
            nd.append(ndcg(ranked, g, 10))
            if with_recall:
                for k in KS:
                    rec[k].append(len(set(ranked[:k]) & g) / len(g))
        row = {"ndcg10": sum(nd) / len(nd), "n": len(nd), "per_topic": nd}
        if with_recall:
            row["recall"] = {k: sum(v) / len(v) for k, v in rec.items()}
        per_dom[dom] = row
    macro = sum(r["ndcg10"] for r in per_dom.values()) / len(per_dom)
    return macro, per_dom


def bootstrap(a_dom, b_dom, n=10000, seed=20260921):
    """Paired bootstrap of macro(A) - macro(B): resample topics within each domain."""
    import random
    rng = random.Random(seed)
    doms = sorted(a_dom)
    obs = sum(sum(a_dom[d]) / len(a_dom[d]) - sum(b_dom[d]) / len(b_dom[d]) for d in doms) / len(doms)
    diffs = []
    for _ in range(n):
        tot = 0.0
        for d in doms:
            x, y = a_dom[d], b_dom[d]
            idx = [rng.randrange(len(x)) for _ in x]
            tot += sum(x[i] - y[i] for i in idx) / len(idx)
        diffs.append(tot / len(doms))
    diffs.sort()
    return {"diff": round(obs, 4), "ci95": [round(diffs[int(0.025 * n)], 4), round(diffs[int(0.975 * n)], 4)],
            "p_le_0": round(sum(1 for x in diffs if x <= 0) / n, 4)}


def depth_analysis(data):
    """Recall of BM25, dense and their union by depth; unique gold contributions; budgets."""
    rows = {}
    for dom, items in data.items():
        r = defaultdict(list)
        cnt = defaultdict(int)
        for q, g in items:
            bml, del_ = [d for d, _ in q.bm], [d for d, _ in q.de]
            for k in KS:
                b, d = set(bml[:k]) & g, set(del_[:k]) & g
                r[f"bm25@{k}"].append(len(b) / len(g))
                r[f"dense@{k}"].append(len(d) / len(g))
                r[f"union_each@{k}"].append(len(b | d) / len(g))
                r[f"union_size@{k}"].append(len(set(bml[:k]) | set(del_[:k])))
                # budget-matched: k unique candidates in total, half from each list
                half = []
                seen = set()
                for x in itertools.chain.from_iterable(itertools.zip_longest(bml, del_)):
                    if x is not None and x not in seen:
                        seen.add(x)
                        half.append(x)
                    if len(half) == k:
                        break
                r[f"union_budget@{k}"].append(len(set(half) & g) / len(g))
                cnt[f"gold@{k}"] += len(g)
                cnt[f"both@{k}"] += len(b & d)
                cnt[f"bm25_only@{k}"] += len(b - d)
                cnt[f"dense_only@{k}"] += len(d - b)
                cnt[f"neither@{k}"] += len(g - b - d)
        rows[dom] = {"n_topics": len(items), **{k: sum(v) / len(v) for k, v in r.items()}, **cnt}
    return rows


def allocation(data, budgets=(100, 200, 500, 1000), fracs=(0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0)):
    """Union recall when a total depth budget B is split kb = f*B, kd = (1-f)*B."""
    out = {}
    for B in budgets:
        for f in fracs:
            kb, kd = int(round(f * B)), B - int(round(f * B))
            vals = []
            for dom, items in data.items():
                v = [len(({d for d, _ in q.bm[:kb]} | {d for d, _ in q.de[:kd]}) & g) / len(g)
                     for q, g in items]
                vals.append(sum(v) / len(v))
            out[f"B={B}|bm25_frac={f}"] = {"kb": kb, "kd": kd, "macro_recall": sum(vals) / len(vals)}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--track", type=int, required=True)
    ap.add_argument("--conditions", nargs="+", required=True)
    ap.add_argument("--dense-cond", nargs="*",
                    help="dense run condition per --conditions entry (default: same name)")
    ap.add_argument("--bm25", required=True)
    ap.add_argument("--dense", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--kit", required=True)
    ap.add_argument("--domains", nargs="+", default=["all"])
    ap.add_argument("--boot", type=int, default=10000)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    ndcg = ndcg_fn(a.kit)
    doms = (T1 if a.track == 1 else T2) if a.domains == ["all"] else a.domains
    dconds = a.dense_cond or a.conditions
    report = {"track": a.track, "bm25": a.bm25, "dense": a.dense, "conditions": {}}
    for cond, dcond in zip(a.conditions, dconds):
        tr = load_split(a, a.track, cond, "train", doms, dcond)
        dv = load_split(a, a.track, cond, "dev", doms, dcond)
        print(f"\n== track {a.track} {cond} (dense: {dcond}) — train {len(tr)} dom, dev {len(dv)} dom",
              flush=True)
        tuned = []
        for cfg in grid():
            m, _ = evaluate(tr, cfg, ndcg)
            tuned.append((m, cfg))
        tuned.sort(key=lambda x: -x[0])
        best = {}
        for m, cfg in tuned:
            best.setdefault(cfg["kind"], (m, cfg))
        frozen = {k: v[1] for k, v in best.items()}
        systems = {"bm25": {"kind": "bm25"}, "dense": {"kind": "dense"},
                   "rerank": {"kind": "rerank"}, **{f"{k}*": v for k, v in frozen.items()},
                   # fixed, untuned reference points
                   "rrf_c60_100+100": {"kind": "rrf", "kb": 100, "kd": 100, "c": 60}}
        res = {}
        for label, cfg in systems.items():
            mt, pt = evaluate(tr, cfg, ndcg, with_recall=True)
            md, pd = evaluate(dv, cfg, ndcg, with_recall=True)
            res[label] = {"cfg": cfg, "train_macro": round(mt, 4), "dev_macro": round(md, 4),
                          "train": pt, "dev": pd}
            print(f"  {label:<16} train {mt:.4f}  dev {md:.4f}   {cfg_name(cfg)}", flush=True)
        dev_pt = {lab: {d: r["dev"][d].pop("per_topic") for d in r["dev"]} for lab, r in res.items()}
        for r in res.values():
            for d in r["train"]:
                r["train"][d].pop("per_topic", None)
        boots = {}
        for x, y in [("linear*", "bm25"), ("rrf*", "bm25"), ("linear*", "rerank"), ("dense", "bm25"),
                     ("rerank", "bm25"), ("linear*", "dense")]:
            boots[f"{x} - {y}"] = bootstrap(dev_pt[x], dev_pt[y], n=a.boot)
            print(f"  dev {x} - {y}: {boots[f'{x} - {y}']}", flush=True)
        report["conditions"][cond] = {
            "dev_bootstrap": boots,
            "dev_per_topic": dev_pt,
            "dense_condition": dcond, "systems": res,
            "grid_top10_train": [(round(m, 4), c) for m, c in tuned[:10]],
            "grid_size": len(tuned),
            "linear_alpha_curve_train": {
                f"{c['norm']}|{c['kb']}+{c['kd']}|a={c['alpha']}": round(m, 4)
                for m, c in tuned if c["kind"] == "linear"},
            "depth": {"train": depth_analysis(tr), "dev": depth_analysis(dv)},
            "allocation": {"train": allocation(tr), "dev": allocation(dv)},
        }
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        with open(a.out, "w") as f:
            json.dump(report, f, indent=1)
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
