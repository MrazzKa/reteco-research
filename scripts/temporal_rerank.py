#!/usr/bin/env python3
"""Temporal signal inside the Track-1 ranking (LOG rule 9).

Over the top --pool of a frozen hybrid (hybrid.py report, `linear*`):
    score(d) = (1 - w) * minmax(hybrid fused score) + w * T(d)
T(d) = share of the query's years y for which document d mentions a year in [y-1, y+1].
Years: 1500-2099 as numbers, decades ("1990s") expanded to their ten years. Query years come
from the query text, or from the query plus the LLM "reason" text (llm_expand.py cache), which
was asked to state the time explicitly. Topics without a year keep the hybrid order.
(source, w) is chosen on all train topics; "none" is always a candidate.

    python3 temporal_rerank.py --conditions 1a__q+r+h --query-cond 1a --hybrid H.json --bm25 B --dense D \
        --llm ../research/runs_v13/llm/t1 --out ../research/runs_v13/temporal/t1.json
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bm25s_run import ndcg_fn  # noqa: E402
from dense_index import T1  # noqa: E402
from dense_search import plan  # noqa: E402
from hybrid import Query, bootstrap, read_run  # noqa: E402
from llm_expand import inputs as llm_inputs, key_of  # noqa: E402
from qexp_search import load_gen  # noqa: E402
from tie_study import fused, order  # noqa: E402

YEAR = re.compile(r"(?<!\d)(1[5-9]\d\d|20\d\d)(s?)(?!\d)")
WEIGHTS = (0.05, 0.1, 0.2, 0.3, 0.5)


def years(text):
    out = set()
    for y, s in YEAR.findall(text or ""):
        y = int(y)
        if s and y % 10 == 0:
            out.update(range(y, y + 10))
        else:
            out.add(y)
    return out


def doc_years(data, dom, wanted, cache_path):
    cache = json.load(open(cache_path)) if os.path.exists(cache_path) else {}
    need = set(wanted) - set(cache)
    if need:
        with open(os.path.join(data, "track1_tempo", dom, "documents.jsonl"), encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    d = json.loads(line)
                    if d["id"] in need:
                        cache[d["id"]] = sorted(years(d.get("content", "")))
        json.dump(cache, open(cache_path, "w"))
    return {d: set(cache.get(d, [])) for d in wanted}


def tscore(qy, dy):
    if not qy:
        return 0.0
    return sum(1 for y in qy if dy & {y - 1, y, y + 1}) / len(qy)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--conditions", nargs="+", required=True)
    ap.add_argument("--query-cond", nargs="+", required=True)
    ap.add_argument("--hybrid", nargs="+", required=True, help="one report per condition")
    ap.add_argument("--bm25", required=True)
    ap.add_argument("--dense", required=True)
    ap.add_argument("--llm", required=True)
    ap.add_argument("--data", default="../../reteco_data_v11")
    ap.add_argument("--kit", default="../../RETECO/starter_kit")
    ap.add_argument("--pool", type=int, default=100)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    ndcg = ndcg_fn(a.kit)
    reason = load_gen(a.llm, "reason")
    cdir = os.path.join(os.path.dirname(os.path.abspath(a.out)), "cache")
    os.makedirs(cdir, exist_ok=True)
    report = {}
    for cond, qcond, hpath in zip(a.conditions, a.query_cond, a.hybrid):
        hc = json.load(open(hpath))["conditions"][cond]
        cfg, dcond = hc["systems"]["linear*"]["cfg"], hc["dense_condition"]
        body = {(dm, sp, q): b for dm, sp, q, b in llm_inputs(a.data, 1, qcond)}
        per = {}
        for split in ("train", "dev"):
            per[split] = {}
            for dom in T1:
                pre = f"t1_{dom}_{split}"
                bm = read_run(os.path.join(a.bm25, f"{pre}_{cond}.tsv"))
                de = read_run(os.path.join(a.dense, f"{pre}_{dcond}.tsv"))
                (_, queries, gold), = [p for p in plan(1, os.path.join(a.data, "track1_tempo", dom), split)
                                       if p[0] == qcond]
                qtext = dict(queries)
                qids = sorted(q for q in gold if q in qtext)
                pools = {q: order(fused(Query(bm.get(q, []), de.get(q, [])), cfg))[:a.pool] for q in qids}
                dy = doc_years(a.data, dom, {d for q in qids for d, _ in pools[q]}, os.path.join(cdir, f"years_{dom}.json"))
                qy = {"q": {q: years(qtext[q]) for q in qids},
                      "q+r": {q: years(qtext[q]) | years(reason.get(key_of("reason", body.get((dom, split, q))), ""))
                              for q in qids}}
                per[split][dom] = (qids, pools, gold, qy, dy)
            print(f"  [{cond}/{split}] pools ready", flush=True)

        def run(split, src, w):
            out = {}
            for dom, (qids, pools, gold, qy, dy) in per[split].items():
                v = []
                for q in qids:
                    lst = pools[q]
                    if w and qy[src][q]:
                        s = [x for _, x in lst]
                        lo, hi = min(s), max(s)
                        lst = order([(d, (1 - w) * ((x - lo) / (hi - lo) if hi > lo else 0.0)
                                      + w * tscore(qy[src][q], dy[d])) for d, x in lst])
                    v.append(ndcg([d for d, _ in lst], gold[q], 10))
                out[dom] = v
            return out

        def mac(d):
            return round(sum(sum(v) / len(v) for v in d.values()) / len(d), 4)

        cands = [("none", 0.0)] + [(s, w) for s in ("q", "q+r") for w in WEIGHTS]
        res = {c: {sp: run(sp, *c) for sp in ("train", "dev")} for c in cands}
        best = max(cands, key=lambda c: mac(res[c]["train"]))
        tb = bootstrap(res[best]["train"], res[("none", 0.0)]["train"]) if best[0] != "none" else None
        adopt = bool(tb and mac(res[best]["train"]) - mac(res[("none", 0.0)]["train"]) >= 0.005 and tb["ci95"][0] > 0)
        cov = {sp: {src: sum(1 for dom in per[sp] for q in per[sp][dom][0] if per[sp][dom][3][src][q])
                    / sum(len(per[sp][dom][0]) for dom in per[sp]) for src in ("q", "q+r")} for sp in per}
        report[cond] = {"hybrid_cfg": cfg, "pool": a.pool, "share_topics_with_years": cov,
                        "by_candidate": {f"{s}|{w}": {sp: mac(res[(s, w)][sp]) for sp in ("train", "dev")} for s, w in cands},
                        "best_on_train": f"{best[0]}|{best[1]}", "train_bootstrap_best_minus_none": tb, "adopted": adopt,
                        "dev_bootstrap_best_minus_none": bootstrap(res[best]["dev"], res[("none", 0.0)]["dev"]),
                        "dev_per_topic_best": res[best]["dev"]}
        print(f"== {cond}: topics with years {cov}")
        for c in cands:
            print(f"   {c[0]}|{c[1]}: train {mac(res[c]['train'])} dev {mac(res[c]['dev'])}")
        print(f"   best on train {best}; train boot {tb}; adopted={adopt}", flush=True)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(report, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
