#!/usr/bin/env python3
"""Cross-encoder reranking of the frozen hybrid (BM25 + dense) list.

The hybrid configuration per (track, condition) is read from hybrid.py's report (chosen
on train). The cross-encoder scores the hybrid top-100 once; the reranking depth N in
{10, 20, 50, 100} is then chosen on TRAIN (the top-N is reordered by the cross-encoder,
everything below N keeps the hybrid order) and frozen for DEV.

Train is subsampled for cost: at most --train-per-domain topics per domain and condition
(random.Random(20260921) over sorted topic ids). Dev uses every topic.

Query text: Track 1 as in the runs; Track 2 history uses the current question first
(`2a_history_qfirst`), because the cross-encoder truncates a (query, passage) pair to 512
tokens.

    python3 rerank_ce.py --track 2 --conditions 2a_current --hybrid ../research/runs_v12/hybrid/bge-small_L512_t2.json \
        --bm25 ../research/runs_v12/bm25/t2/runs --dense ../research/runs_v12/dense/bge-small_L512/t2/runs \
        --data ../../reteco_data_v11 --kit ../../RETECO/starter_kit --out ../research/runs_v12/ce
"""
import argparse
import json
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bm25s_run import ndcg_fn  # noqa: E402
from dense_index import T1, T2  # noqa: E402
from dense_search import plan  # noqa: E402
from gold_categories import fetch  # noqa: E402
from hybrid import Query, bootstrap, read_run, system  # noqa: E402

DEPTHS = (10, 20, 50, 100)
CKPT = "BAAI/bge-reranker-v2-m3"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--track", type=int, required=True)
    ap.add_argument("--conditions", nargs="+", required=True)
    ap.add_argument("--hybrid", required=True)
    ap.add_argument("--bm25", required=True)
    ap.add_argument("--dense", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--kit", required=True)
    ap.add_argument("--train-per-domain", type=int, default=40)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    import torch
    from sentence_transformers import CrossEncoder
    from embed_models import revision
    ndcg = ndcg_fn(a.kit)
    ce = CrossEncoder(CKPT, max_length=512, device="cuda")
    ce.model.half()
    rev = revision(CKPT)
    hyb = json.load(open(a.hybrid))
    doms = T1 if a.track == 1 else T2
    sub = "track1_tempo" if a.track == 1 else "track2_recor"
    os.makedirs(a.out, exist_ok=True)
    rpath = os.path.join(a.out, f"t{a.track}.json")
    report = json.load(open(rpath)) if os.path.exists(rpath) else {}
    for cond in a.conditions:
        hc = hyb["conditions"][cond]
        cfg = hc["systems"]["linear*"]["cfg"]
        dcond = hc["dense_condition"]
        qcond = dcond if a.track == 2 else cond
        per = {}
        for split in ("train", "dev"):
            per[split] = {}
            for dom in doms:
                cache = os.path.join(a.out, f"scores_t{a.track}_{dom}_{split}_{cond}.json")
                pre = f"t{a.track}_{dom}_{split}"
                bm = read_run(os.path.join(a.bm25, f"{pre}_{cond}.tsv"))
                de = read_run(os.path.join(a.dense, f"{pre}_{dcond}.tsv"))
                (_, queries, gold), = [p for p in plan(a.track, os.path.join(a.data, sub, dom), split)
                                       if p[0] == qcond]
                qtext = dict(queries)
                qids = sorted(q for q in gold if q in qtext)
                if split == "train" and len(qids) > a.train_per_domain:
                    qids = sorted(random.Random(20260921).sample(qids, a.train_per_domain))
                hyb_lists = {q: system(Query(bm.get(q, []), de.get(q, [])), cfg)[:100] for q in qids}
                scores = json.load(open(cache)) if os.path.exists(cache) else {}
                todo = [q for q in qids if q not in scores]
                if todo:
                    texts = fetch(a.data, a.track, dom, {d for q in todo for d in hyb_lists[q]})
                    t0 = time.time()
                    pairs = [(qtext[q], texts.get(d, "")) for q in todo for d in hyb_lists[q]]
                    with torch.inference_mode():
                        s = ce.predict(pairs, batch_size=a.batch, show_progress_bar=False)
                    i = 0
                    for q in todo:
                        scores[q] = {d: float(s[i + j]) for j, d in enumerate(hyb_lists[q])}
                        i += len(hyb_lists[q])
                    json.dump(scores, open(cache, "w"))
                    print(f"  [{cond}/{split}/{dom}] {len(pairs)} pairs, {time.time() - t0:.0f}s "
                          f"({len(pairs) / max(time.time() - t0, 1e-9):.0f}/s)", flush=True)
                per[split][dom] = (qids, hyb_lists, scores, gold)

        def evaluate(split, n):
            out = {}
            for dom, (qids, hl, sc, gold) in per[split].items():
                v = []
                for q in qids:
                    head = sorted(hl[q][:n], key=lambda d: (-sc[q][d], d)) if n else hl[q]
                    v.append(ndcg(head + hl[q][n:], gold[q], 10))
                out[dom] = v
            return out

        res = {}
        for n in (0,) + DEPTHS:
            tr, dv = evaluate("train", n), evaluate("dev", n)
            res[n] = {"train_macro": round(sum(sum(v) / len(v) for v in tr.values()) / len(tr), 4),
                      "dev_macro": round(sum(sum(v) / len(v) for v in dv.values()) / len(dv), 4),
                      "dev": dv}
        best = max(DEPTHS, key=lambda n: res[n]["train_macro"])
        boot = bootstrap(res[best]["dev"], res[0]["dev"])
        report[cond] = {"checkpoint": CKPT, "revision": rev, "hybrid_cfg": cfg, "query_condition": qcond,
                        "train_topics_per_domain_max": a.train_per_domain, "chosen_depth_on_train": best,
                        "by_depth": {str(n): {k: v for k, v in r.items() if k != "dev"} for n, r in res.items()},
                        "dev_per_domain_chosen": {d: round(sum(v) / len(v), 4) for d, v in res[best]["dev"].items()},
                        "dev_per_domain_hybrid": {d: round(sum(v) / len(v), 4) for d, v in res[0]["dev"].items()},
                        "dev_bootstrap_ce_minus_hybrid": boot}
        print(f"== t{a.track} {cond}: " + "  ".join(
            f"N={n}: train {r['train_macro']:.4f} dev {r['dev_macro']:.4f}" for n, r in res.items())
              + f"  -> chosen N={best} on train; dev CE-hybrid {boot}", flush=True)
        json.dump(report, open(rpath, "w"), indent=1)


if __name__ == "__main__":
    main()
