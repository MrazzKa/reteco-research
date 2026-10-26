#!/usr/bin/env python3
"""BM25 and dense retrieval with LLM query expansions (llm_expand.py caches).

Query variants per topic (q = the original query text of the condition, r = the "reason"
generation, h = the "hyde" generation):

  q        original query (same as the plain runs; recomputed for uniform naming)
  q+r      BM25: q and r concatenated            dense: normalised mean of e(q), e_query(r)
  r        BM25: r alone                          dense: e_query(r)
  q+h      BM25: q and h concatenated            dense: normalised mean of e(q), e_doc(h)
  h        BM25: h alone                          dense: e_doc(h)  (HyDE: a passage, encoded as one)
  q+r+h    BM25: all three concatenated          dense: normalised mean of the three vectors

Dense query vectors are averaged rather than the texts concatenated because the encoders
truncate at 256/512 tokens and Track-1 queries alone often fill that window.

Output: <out>/{bm25,dense}/runs/t<track>_<dom>_<split>_<cond>__<variant>.tsv (depth 1000,
sha1 tie key) and <out>/results.json; hybrid.py then fuses them per variant
(--conditions <cond>__<variant>).

    python3 qexp_search.py --data ../../reteco_data_v11 --kit ../../RETECO/starter_kit --track 2 \
        --cond 2a_current --llm ../research/runs_v13/llm/t2 --model bge-base --max-len 512 \
        --emb ../research/runs_v12/emb --out ../research/runs_v13/qexp/t2
"""
import argparse
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from week1_run import write_run  # noqa: E402
from bm25s_run import build, ndcg_fn, search  # noqa: E402
from dense_index import T1, T2, domain_dir  # noqa: E402
from dense_search import GpuIndex, evaluate, plan  # noqa: E402
from embed_models import load_encoder  # noqa: E402
from llm_expand import inputs as llm_inputs, key_of  # noqa: E402
from passage_index import MaxPIndex, pdir  # noqa: E402
import tiebreak  # noqa: E402

VARIANTS = ("q", "q+r", "r", "q+h", "h", "q+r+h")


def load_gen(llm_dir, prompt):
    out = {}
    p = os.path.join(llm_dir, f"{prompt}.jsonl")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    out[r["key"]] = r["output"]
    return out


def norm(v):
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--kit", required=True)
    ap.add_argument("--track", type=int, required=True, choices=(1, 2))
    ap.add_argument("--cond", required=True, help="1a | 1b_query+step | 2a_current")
    ap.add_argument("--llm", required=True, help="llm_expand.py output dir for this track")
    ap.add_argument("--model", required=True)
    ap.add_argument("--max-len", type=int, required=True)
    ap.add_argument("--emb", required=True)
    ap.add_argument("--domains", nargs="+", default=["all"])
    ap.add_argument("--variants", nargs="+", default=list(VARIANTS))
    ap.add_argument("--k", type=int, default=1000)
    ap.add_argument("--passages", help="passage_index.py root: dense = MaxP over passages "
                    "(first window from --emb at L512) instead of the --max-len cache")
    ap.add_argument("--out", required=True)
    tiebreak.add_arg(ap)
    a = ap.parse_args()
    tiebreak.set_mode(a.tiebreak)
    ndcg = ndcg_fn(a.kit)
    doms = (T1 if a.track == 1 else T2) if a.domains == ["all"] else a.domains
    gen = {p: load_gen(a.llm, p) for p in ("reason", "hyde")}
    # body shown to the LLM per (domain, split, qid) -> generation via the cache key
    # (Track-2 qids such as `2_turn_1` repeat across the BRIGHT domains: the domain is part of the key)
    body = {(dom, sp, qid): b for dom, sp, qid, b in llm_inputs(a.data, a.track, a.cond)}
    sub, key = ("track1_tempo", "id") if a.track == 1 else ("track2_recor", "doc_id")
    bdir, ddir = os.path.join(a.out, "bm25", "runs"), os.path.join(a.out, "dense", "runs")
    os.makedirs(bdir, exist_ok=True)
    os.makedirs(ddir, exist_ok=True)
    rpath = os.path.join(a.out, "results.json")
    results = json.load(open(rpath)) if os.path.exists(rpath) else []
    done = {(r["domain"], r["split"], r["run"], r["system"]) for r in results}
    enc = load_encoder(a.model, a.max_len)
    missing = 0
    for dom in doms:
        d = os.path.join(a.data, sub, dom)
        todo = [(sp, v) for sp in ("train", "dev") for v in a.variants
                if (dom, sp, f"{a.cond}__{v}", "dense") not in done]
        if not todo:
            continue
        t0 = time.time()
        bm, ids = build(os.path.join(d, "documents.jsonl"), key, "lucene")
        gi = (MaxPIndex(domain_dir(a.emb, a.model, 512, a.track, dom), pdir(a.passages, a.model, a.track, dom))
              if a.passages else GpuIndex(domain_dir(a.emb, a.model, a.max_len, a.track, dom)))
        print(f"[t{a.track}/{dom}] indexes ready ({time.time() - t0:.0f}s)", flush=True)
        for sp in ("train", "dev"):
            (_, queries, gold), = [p for p in plan(a.track, d, sp) if p[0] == a.cond]
            texts = {}
            for qid, q in queries:
                k = body.get((dom, sp, qid))
                r = gen["reason"].get(key_of("reason", k), "") if k else ""
                h = gen["hyde"].get(key_of("hyde", k), "") if k else ""
                missing += (not r) + (not h)
                texts[qid] = (q, r, h)
            qids = [qid for qid, _ in queries]
            # dense vectors, one encoding per distinct text
            eq = dict(zip(qids, enc.encode_queries([texts[x][0] for x in qids]).astype(np.float32)))
            er = dict(zip(qids, enc.encode_queries([texts[x][1] for x in qids]).astype(np.float32)))
            eh = dict(zip(qids, enc.encode_docs([texts[x][2] for x in qids]).astype(np.float32)))
            parts = {"q": (eq,), "q+r": (eq, er), "r": (er,), "q+h": (eq, eh), "h": (eh,), "q+r+h": (eq, er, eh)}
            for v in a.variants:
                if (sp, v) not in todo:
                    continue
                name = f"{a.cond}__{v}"
                bq = [(qid, "\n".join(texts[qid][{"q": 0, "r": 1, "h": 2}[c]] for c in v.split("+")))
                      for qid in qids]
                runs = {"bm25": search(bm, ids, bq, "lucene", name, k=a.k, threads=8)}
                mat = norm(sum(np.stack([p[qid] for qid in qids]) for p in parts[v]))
                hits = gi.search(mat.astype(np.float32), a.k)
                runs["dense"] = dict(zip(qids, hits))
                for sysname, run in runs.items():
                    write_run(os.path.join(bdir if sysname == "bm25" else ddir,
                                           f"t{a.track}_{dom}_{sp}_{name}.tsv"), run, f"{sysname}-{v}")
                    mean, _ = evaluate(run, gold, ndcg)
                    results.append({"track": a.track, "domain": dom, "split": sp, "run": name, "variant": v,
                                    "system": sysname, "n": len(gold), "ndcg10": round(mean["ndcg10"], 4),
                                    "r100": round(mean["r100"], 4), "r1000": round(mean["r1000"], 4)})
                print(f"  {sp:<5} {v:<6} bm25 {results[-2]['ndcg10']:.4f}  dense {results[-1]['ndcg10']:.4f}", flush=True)
        gi.free()
        del bm
        json.dump(results, open(rpath, "w"), indent=1)
    print(f"missing generations: {missing}; wrote {rpath}", flush=True)


if __name__ == "__main__":
    main()
