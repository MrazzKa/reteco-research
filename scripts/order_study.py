#!/usr/bin/env python3
"""Does the order in which documents are indexed change the results? (Steve's question)

Per domain, on DEV:
  1. duplicates  — documents with identical text (whitespace-collapsed); how many gold
                   documents have a non-gold twin (an exact tie for any lexical scorer).
  2. bm25        — index the corpus in file order and in R random permutations
                   (seeds 0..R-1); nDCG@10 with bm25s's native order among ties
                   (`raw`) and with ties broken by doc id (`tiebreak`).
  3. dense       — permute the rows of the cached embedding matrix; exact GPU search with
                   and without the doc-id tie-break.
  4. ann         — NGT graph built with the vectors inserted in file order vs permuted
                   order; nDCG@10 and recall@10 against exact search.

    python3 order_study.py --data ../../reteco_data_v11 --kit ../../RETECO/starter_kit \
        --track 2 --domains biology drones --emb ../research/runs_v12/emb --model bge-small \
        --max-len 512 --perms 5 --out ../research/runs_v12/order/t2.json
"""
import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
import time
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bm25s_run import analyze, ndcg_fn  # noqa: E402
from dense_search import plan  # noqa: E402
from dense_index import domain_dir, load_cache  # noqa: E402

CONDS = {1: ("1a", "1b_query+step"), 2: ("2a_current", "2a_history")}


def corpus(path, key):
    ids, texts = [], []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                d = json.loads(line)
                ids.append(d[key])
                texts.append(d.get("content", "") or "")
    return ids, texts


def duplicates(ids, texts, gold_all):
    groups, h_of = defaultdict(list), {}
    for i, t in zip(ids, texts):
        h_of[i] = hashlib.md5(" ".join(t.split()).encode()).hexdigest()
        groups[h_of[i]].append(i)
    dup_groups = [g for g in groups.values() if len(g) > 1]
    gold_with_twin = sum(1 for g in gold_all if g in h_of
                         and any(x not in gold_all for x in groups[h_of[g]]))
    return {"docs": len(ids), "dup_groups": len(dup_groups),
            "docs_in_dup_groups": sum(len(g) for g in dup_groups),
            "share_docs_duplicated": round(sum(len(g) for g in dup_groups) / len(ids), 4),
            "gold_docs": len(gold_all), "gold_with_nongold_twin": gold_with_twin}


def mean_ndcg(run, gold, ndcg):
    v = [ndcg(run.get(q, []), g, 10) for q, g in gold.items()]
    return sum(v) / len(v) if v else 0.0


def bm25_runs(ids, texts, perm, plans, k=100):
    """One index per permutation; returns {cond: (raw_run, tiebreak_run)}."""
    import bm25s
    order = perm if perm is not None else np.arange(len(ids))
    pids = [ids[i] for i in order]
    r = bm25s.BM25(method="lucene", k1=0.9, b=0.4)
    r.index(analyze([texts[i] for i in order], "lucene"), show_progress=False)
    out = {}
    for c, queries in plans.items():
        uniq = sorted({q for _, q in queries})
        idx, sc = r.retrieve(analyze(uniq, "lucene"), k=min(k, len(ids)), show_progress=False,
                             n_threads=4)
        raw, tb = {}, {}
        for i, q in enumerate(uniq):
            lst = [(pids[int(idx[i, j])], float(sc[i, j])) for j in range(idx.shape[1])]
            raw[q] = [d for d, _ in lst]
            tb[q] = [d for d, _ in sorted(lst, key=lambda x: (-x[1], x[0]))]
        out[c] = ({qid: raw[q] for qid, q in queries}, {qid: tb[q] for qid, q in queries})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--kit", required=True)
    ap.add_argument("--track", type=int, required=True)
    ap.add_argument("--domains", nargs="+", required=True)
    ap.add_argument("--emb", required=True)
    ap.add_argument("--model", default="bge-small")
    ap.add_argument("--max-len", type=int, default=512)
    ap.add_argument("--perms", type=int, default=5)
    ap.add_argument("--ann-domains", nargs="*", default=[])
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    ndcg = ndcg_fn(a.kit)
    sub, key = ("track1_tempo", "id") if a.track == 1 else ("track2_recor", "doc_id")
    report = json.load(open(a.out)) if os.path.exists(a.out) else {}
    for dom in a.domains:
        if dom in report:
            continue
        t0 = time.time()
        d = os.path.join(a.data, sub, dom)
        ids, texts = corpus(os.path.join(d, "documents.jsonl"), key)
        pl = {name: (q, g) for name, q, g in plan(a.track, d, "dev")}
        gold_all = {x for c in CONDS[a.track] for g in pl[c][1].values() for x in g}
        rep = {"duplicates": duplicates(ids, texts, gold_all), "bm25": {}, "dense": {}}
        perms = [None] + [np.random.default_rng(s).permutation(len(ids)) for s in range(a.perms)]
        per_perm = [bm25_runs(ids, texts, p, {c: pl[c][0] for c in CONDS[a.track]}) for p in perms]
        for c in CONDS[a.track]:
            gold = pl[c][1]
            raw = [mean_ndcg(r[c][0], gold, ndcg) for r in per_perm]
            tb = [mean_ndcg(r[c][1], gold, ndcg) for r in per_perm]
            rep["bm25"][c] = {"raw_file_order": round(raw[0], 4), "raw_perms": [round(x, 4) for x in raw[1:]],
                              "raw_range": round(max(raw) - min(raw), 4),
                              "tiebreak_file_order": round(tb[0], 4),
                              "tiebreak_range": round(max(tb) - min(tb), 4)}
            print(f"  [{dom}] bm25 {c}: raw {min(raw):.4f}..{max(raw):.4f}  "
                  f"tiebreak {min(tb):.4f}..{max(tb):.4f}", flush=True)
        del texts
        # ---- dense: permuted rows, exact search
        import torch
        from embed_models import load_encoder
        enc = load_encoder(a.model, a.max_len)
        cids, shards, _ = load_cache(domain_dir(a.emb, a.model, a.max_len, a.track, dom))
        mat = np.concatenate([np.asarray(s) for s in shards])
        for c in CONDS[a.track]:
            name = "2a_history_qfirst" if c == "2a_history" else c
            queries, gold = pl[name]
            uniq = sorted({q for _, q in queries})
            qemb = torch.from_numpy(enc.encode_queries(uniq)).cuda()
            vals = {"raw": [], "tiebreak": []}
            for p in perms:
                order = p if p is not None else np.arange(len(cids))
                pid = [cids[i] for i in order]
                m = torch.from_numpy(mat[order]).cuda()
                sims = (qemb @ m.T).float()
                v, ix = torch.topk(sims, 132, dim=1)
                v, ix = v.cpu().numpy(), ix.cpu().numpy()
                rr, rt = {}, {}
                for i, q in enumerate(uniq):
                    lst = [(pid[j], float(s)) for j, s in zip(ix[i], v[i])]
                    rr[q] = [x for x, _ in lst[:100]]
                    rt[q] = [x for x, _ in sorted(lst, key=lambda x: (-x[1], x[0]))[:100]]
                vals["raw"].append(mean_ndcg({qid: rr[q] for qid, q in queries}, gold, ndcg))
                vals["tiebreak"].append(mean_ndcg({qid: rt[q] for qid, q in queries}, gold, ndcg))
                del m, sims
            rep["dense"][c] = {k: {"file_order": round(v[0], 4), "range": round(max(v) - min(v), 4)}
                               for k, v in vals.items()}
            print(f"  [{dom}] dense {c}: raw range {rep['dense'][c]['raw']['range']:.4f}  "
                  f"tiebreak range {rep['dense'][c]['tiebreak']['range']:.4f}", flush=True)
        # ---- ANN insertion order
        if dom in a.ann_domains:
            import ngtpy
            c = CONDS[a.track][0]
            queries, gold = pl[c]
            uniq = sorted({q for _, q in queries})
            qe = enc.encode_queries(uniq).astype(np.float32)
            ex = torch.topk((torch.from_numpy(qe).cuda() @ torch.from_numpy(mat.astype(np.float32)).cuda().T), 10, dim=1)[1].cpu().numpy()
            ann = []
            for p in perms[:3]:
                order = p if p is not None else np.arange(len(cids))
                tmp = tempfile.mkdtemp()
                path = os.path.join(tmp, "idx").encode()
                ngtpy.create(path, mat.shape[1], distance_type="Cosine")
                idx = ngtpy.Index(path)
                idx.batch_insert(mat[order].astype(np.float32), num_threads=8)
                runs, rec = {}, []
                for i, q in enumerate(uniq):
                    hits = [int(order[h]) for h, _ in idx.search(qe[i], size=100, epsilon=0.1)]
                    runs[q] = [cids[h] for h in hits]
                    rec.append(len(set(hits[:10]) & set(ex[i].tolist())) / 10)
                ann.append({"ndcg10": round(mean_ndcg({qid: runs[q] for qid, q in queries}, gold, ndcg), 4),
                            "recall10_vs_exact": round(sum(rec) / len(rec), 4)})
                idx.close()
                shutil.rmtree(tmp)
            rep["ann"] = {"condition": c, "insertion_orders": ann}
            print(f"  [{dom}] ann {c}: {ann}", flush=True)
        del mat, enc
        torch.cuda.empty_cache()
        rep["seconds"] = round(time.time() - t0, 1)
        report[dom] = rep
        with open(a.out, "w") as f:
            json.dump(report, f, indent=1)
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
