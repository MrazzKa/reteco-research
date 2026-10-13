#!/usr/bin/env python3
"""Exact dense retrieval over a cached corpus embedding (dense_index.py), on the GPU.

For every domain, split and condition: encode the queries, score every document
(fp16 matmul on the GPU, shard by shard), keep the top-k with ties broken by doc id,
write a TREC run (depth k) and report nDCG@10 and recall@k.

Track-2 history conditions for an encoder: `2a_history` is the starter-kit string
(history, then the current question). Encoders truncate on the right, so on long
histories the current question is cut off. `2a_history_qfirst` puts the current
question first; which one to use is decided on train.

    python3 dense_search.py --data ../../reteco_data_v11 --kit ../../RETECO/starter_kit \
        --track 1 --domains iota --splits train dev --model bge-small --max-len 512 \
        --emb ../research/runs_v12/emb --out ../research/runs_v12/dense/bge-small_L512/t1
"""
import argparse
import json
import os
import sys
import time

import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from week1_run import write_run  # noqa: E402
from bm25s_run import by_turn, ndcg_fn  # noqa: E402
from dense_run import plan_track1, plan_track2  # noqa: E402
from dense_index import T1, T2, domain_dir, load_cache  # noqa: E402
from embed_models import load_encoder  # noqa: E402

KS = (10, 20, 50, 100, 200, 500, 1000)


def plan(track, d, split):
    if track == 1:
        return [p for p in plan_track1(d, split) if p[0] in ("1a", "1b_query+step")]
    p = {name: (q, g) for name, q, g in plan_track2(d, split)}
    out = [("2a_current", *p["2a_current"]), ("2a_history", *p["2a_history"])]
    # same text as 2a_history but current question first (survives right truncation)
    cur = dict(p["2a_current"][0])
    hist = dict(p["2a_history"][0])
    qfirst = []
    for qid, _ in p["2a_current"][0]:
        h = hist[qid][: -len(cur[qid])].strip() if hist[qid].endswith(cur[qid]) else ""
        qfirst.append((qid, (cur[qid] + "\n" + h).strip()))
    out.append(("2a_history_qfirst", qfirst, p["2a_current"][1]))
    return out


def recall_at(ranked, gold, k):
    return len(set(ranked[:k]) & gold) / len(gold) if gold else 0.0


def evaluate(run, gold, ndcg):
    """Per-topic nDCG@10 and recall@k for every judged topic (missing topic = 0)."""
    per = {}
    for qid, g in gold.items():
        ranked = [d for d, _ in run.get(qid, [])]
        per[qid] = {"ndcg10": ndcg(ranked, g, 10), **{f"r{k}": recall_at(ranked, g, k) for k in KS}}
    n = len(per)
    mean = {m: (sum(v[m] for v in per.values()) / n if n else 0.0) for m in ["ndcg10"] + [f"r{k}" for k in KS]}
    return mean, per


class GpuIndex:
    """All shards of one domain as a single fp16 tensor on the GPU."""

    def __init__(self, ddir):
        self.ids, shards, self.man = load_cache(ddir)
        self.mat = torch.cat([torch.from_numpy(np.array(s)) for s in shards]).cuda()
        # rank of each id in lexicographic order, for tie-breaking by doc id
        order = sorted(range(len(self.ids)), key=self.ids.__getitem__)
        self.lex = np.empty(len(self.ids), dtype=np.int64)
        self.lex[order] = np.arange(len(self.ids))

    def search(self, qemb, k):
        k = min(k, len(self.ids))
        q = torch.from_numpy(qemb).cuda()
        out = []
        for s in range(0, q.shape[0], 256):
            sims = (q[s:s + 256] @ self.mat.T).float()
            # take a margin beyond k so ties at the cut can be ordered by id
            kk = min(k + 32, sims.shape[1])
            val, idx = torch.topk(sims, kk, dim=1)
            val, idx = val.cpu().numpy(), idx.cpu().numpy()
            for r in range(idx.shape[0]):
                order = np.lexsort((self.lex[idx[r]], -val[r]))[:k]
                out.append([(self.ids[idx[r][j]], float(val[r][j])) for j in order])
        return out

    def free(self):
        del self.mat
        torch.cuda.empty_cache()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--kit", required=True)
    ap.add_argument("--track", type=int, required=True, choices=(1, 2))
    ap.add_argument("--domains", nargs="+", default=["all"])
    ap.add_argument("--splits", nargs="+", default=["train", "dev"])
    ap.add_argument("--model", default="bge-small")
    ap.add_argument("--max-len", type=int, default=512)
    ap.add_argument("--query-len", type=int, help="query window (default: --max-len)")
    ap.add_argument("--k", type=int, default=1000)
    ap.add_argument("--emb", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    doms = (T1 if a.track == 1 else T2) if a.domains == ["all"] else a.domains
    ndcg = ndcg_fn(a.kit)
    runs_dir = os.path.join(a.out, "runs")
    os.makedirs(runs_dir, exist_ok=True)
    rpath = os.path.join(a.out, "results.json")
    results = json.load(open(rpath)) if os.path.exists(rpath) else []
    done = {(r["domain"], r["split"], r["run"]) for r in results}
    enc = load_encoder(a.model, a.query_len or a.max_len)
    sub = "track1_tempo" if a.track == 1 else "track2_recor"
    prefix = f"t{a.track}"
    for dom in doms:
        d = os.path.join(a.data, sub, dom)
        todo = [(s, p) for s in a.splits for p in plan(a.track, d, s)
                if (dom, s, p[0]) not in done]
        if not todo:
            continue
        t0 = time.time()
        index = GpuIndex(domain_dir(a.emb, a.model, a.max_len, a.track, dom))
        print(f"\n[{prefix}/{dom}] {len(index.ids):,} docs on GPU ({time.time() - t0:.0f}s)", flush=True)
        for split, (name, queries, gold) in todo:
            t1 = time.time()
            uniq = sorted({q for _, q in queries})
            qemb = enc.encode_queries(uniq)
            t_enc = time.time() - t1
            t2 = time.time()
            hits = index.search(qemb, a.k)
            t_search = time.time() - t2
            row_of = {q: i for i, q in enumerate(uniq)}
            run = {qid: hits[row_of[q]] for qid, q in queries}
            write_run(os.path.join(runs_dir, f"{prefix}_{dom}_{split}_{name}.tsv"), run,
                      f"dense-{a.model}-L{a.max_len}")
            mean, per = evaluate(run, gold, ndcg)
            row = {"track": a.track, "domain": dom, "split": split, "run": name,
                   "n": len(gold), "ndcg10": round(mean["ndcg10"], 4),
                   "recall": {k: round(mean[f"r{k}"], 4) for k in KS},
                   "system": f"dense-{a.model}-L{a.max_len}", "docs": len(index.ids),
                   "query_encode_s": round(t_enc, 2), "search_s": round(t_search, 2),
                   "ms_per_query_search": round(1000 * t_search / max(len(uniq), 1), 2),
                   "revision": enc.revision}
            if a.track == 2:
                row["by_turn"] = by_turn({q: v["ndcg10"] for q, v in per.items()})
            results.append(row)
            print(f"    {split:<5} {name:<20} nDCG@10 {mean['ndcg10']:.4f}  R@100 {mean['r100']:.4f}  "
                  f"R@1000 {mean['r1000']:.4f}  ({len(uniq)} q, {row['ms_per_query_search']} ms/q)",
                  flush=True)
            with open(rpath, "w") as f:
                json.dump(results, f, indent=1)
        index.free()
    print(f"wrote {rpath}", flush=True)


if __name__ == "__main__":
    main()
