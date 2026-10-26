#!/usr/bin/env python3
"""A reasoning embedder as a second signal over the hybrid pool (LOG rule 8).

The frozen hybrid (`linear*` of a hybrid.py report) gives each topic a ranked pool (top
--pool). A reasoning-oriented embedder (default ReasonEmbed-Qwen3-4B; FP8 through vLLM in
the LLM venv via embed_vllm.py, or 4-bit NF4 through bitsandbytes with --backend bnb;
last-token pooling, instruction on the query side as in its model card) scores every pool
document. Ways of using the score, chosen on TRAIN (N = 0 / w = 0, i.e.
"do not use it", is always a candidate):

  top N reordered by the embedder score (N in 10, 20, 50, 100; the rest keeps hybrid order)
  interpolation over the pool: (1 - w) * minmax(hybrid fused score) + w * minmax(embedder), w in 0.1 .. 0.9

Train is subsampled as for the cross-encoder (<= --train-per-domain topics per domain,
random.Random(20260921) over sorted topic ids); dev uses every topic. Document vectors are
cached per domain (doc id -> vector; the id is only a cache key) and shared by conditions.

    python3 reason_rerank.py --track 2 --conditions 2a_current --hybrid H.json --bm25 B --dense D \
        --data ../../reteco_data_v11 --kit ../../RETECO/starter_kit --out ../research/runs_v13/reason
"""
import argparse
import html
import json
import os
import random
import re
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bm25s_run import ndcg_fn  # noqa: E402
from dense_index import T1, T2  # noqa: E402
from dense_search import plan  # noqa: E402
from gold_categories import fetch  # noqa: E402
from hybrid import Query, bootstrap, read_run  # noqa: E402
from tie_study import fused, order  # noqa: E402
import tiebreak  # noqa: E402

MODELS = {"reasonembed-4b": "hanhainebula/reason-embed-qwen3-4b-0928",
          "diver-4b": "AQ-MedAI/Diver-Retriever-4B"}
DEPTHS = (10, 20, 50, 100)
WEIGHTS = [round(0.1 * i, 1) for i in range(1, 10)]


def instruction(track, cond, dom):
    name = dom.replace("_", " ")
    if cond.startswith("1b"):
        return f"Given a {name} question and one research step, retrieve documents that help with that step."
    return f"Given a {name} question, retrieve documents that help answer the question."


def clean(t):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(t or ""))).strip()


class Embedder:
    def __init__(self, ckpt, bits, max_len):
        import torch
        from transformers import AutoModel, AutoTokenizer, BitsAndBytesConfig
        self.torch, self.max_len = torch, max_len
        self.tok = AutoTokenizer.from_pretrained(ckpt)
        self.tok.padding_side = "left"
        kw = {"dtype": torch.float16, "device_map": "cuda"}
        if bits == 4:
            kw["quantization_config"] = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                                                           bnb_4bit_compute_dtype=torch.float16)
        elif bits == 8:
            kw["quantization_config"] = BitsAndBytesConfig(load_in_8bit=True)
        self.model = AutoModel.from_pretrained(ckpt, **kw).eval()

    def encode(self, texts, batch):
        torch = self.torch
        order_ = sorted(range(len(texts)), key=lambda i: -len(texts[i]))
        out = np.zeros((len(texts), self.model.config.hidden_size), dtype=np.float32)
        for b in range(0, len(order_), batch):
            idx = order_[b:b + batch]
            enc = self.tok([texts[i] for i in idx], max_length=self.max_len, padding=True, truncation=True,
                           return_tensors="pt", pad_to_multiple_of=8).to("cuda")
            with torch.inference_mode():
                h = self.model(**enc).last_hidden_state[:, -1]  # left padding: last token
                h = torch.nn.functional.normalize(h.float(), dim=-1)
            out[idx] = h.cpu().numpy()
        return out


def embed(a, ckpt, texts):
    """L2-normalised float32 vectors for texts, through the chosen backend."""
    if not texts:
        return np.zeros((0, 1), dtype=np.float32)
    if a.backend == "bnb":
        if not hasattr(a, "_emb"):
            a._emb = Embedder(ckpt, a.bits, a.max_len)
        return a._emb.encode(texts, a.batch)
    import subprocess
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        inp, out = os.path.join(tmp, "texts.json"), os.path.join(tmp, "vecs.npy")
        json.dump(texts, open(inp, "w"))
        subprocess.run([os.path.expanduser("~/semeval-reteco/.venv-llm/bin/python"),
                        os.path.join(os.path.dirname(os.path.abspath(__file__)), "embed_vllm.py"),
                        "--model", ckpt, "--inp", inp, "--out", out, "--max-len", str(a.max_len)], check=True)
        return np.load(out)


def load_cache(path):
    if os.path.exists(path + ".npy"):
        ids = json.load(open(path + ".ids.json"))
        return dict(zip(ids, np.load(path + ".npy")))
    return {}


def save_cache(path, cache):
    ids = sorted(cache)
    np.save(path + ".tmp.npy", np.stack([cache[i] for i in ids]).astype(np.float16))
    json.dump(ids, open(path + ".ids.tmp.json", "w"))
    os.replace(path + ".tmp.npy", path + ".npy")
    os.replace(path + ".ids.tmp.json", path + ".ids.json")


def minmax(v):
    lo, hi = min(v), max(v)
    return [(x - lo) / (hi - lo) if hi > lo else 0.0 for x in v]


def rank(lst, how, sc):
    """lst: [(doc, hybrid score)] pool in hybrid order; returns reranked doc list."""
    kind, p = how
    docs = [d for d, _ in lst]
    if kind == "none":
        return docs
    if kind == "top":
        head = [d for d, _ in order([(d, sc[d]) for d in docs[:p]])]
        return head + docs[p:]
    h, r = minmax([s for _, s in lst]), minmax([sc[d] for d in docs])
    return [d for d, _ in order([(d, (1 - p) * a + p * b) for d, a, b in zip(docs, h, r)])]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--track", type=int, required=True)
    ap.add_argument("--conditions", nargs="+", required=True)
    ap.add_argument("--query-cond", nargs="*", help="query text condition per --conditions entry")
    ap.add_argument("--hybrid", required=True)
    ap.add_argument("--bm25", required=True)
    ap.add_argument("--dense", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--kit", required=True)
    ap.add_argument("--model", default="reasonembed-4b", choices=sorted(MODELS))
    ap.add_argument("--backend", default="vllm", choices=("vllm", "bnb"),
                    help="vllm: FP8 through embed_vllm.py in the LLM venv; bnb: bitsandbytes in this process")
    ap.add_argument("--bits", type=int, default=4, choices=(4, 8, 16), help="bnb backend only")
    ap.add_argument("--max-len", type=int, default=512)
    ap.add_argument("--pool", type=int, default=100)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--train-per-domain", type=int, default=30)
    ap.add_argument("--domains", nargs="+", default=["all"])
    ap.add_argument("--splits", nargs="+", default=["train", "dev"])
    ap.add_argument("--out", required=True)
    tiebreak.add_arg(ap)
    a = ap.parse_args()
    tiebreak.set_mode(a.tiebreak)
    ndcg = ndcg_fn(a.kit)
    ckpt = MODELS[a.model]
    hyb = json.load(open(a.hybrid))
    doms = (T1 if a.track == 1 else T2) if a.domains == ["all"] else a.domains
    sub = "track1_tempo" if a.track == 1 else "track2_recor"
    tag = "fp8" if a.backend == "vllm" else f"{a.bits}bit"
    cdir = os.path.join(a.out, "cache", f"{a.model}_{tag}_L{a.max_len}", f"t{a.track}")
    os.makedirs(cdir, exist_ok=True)
    rpath = os.path.join(a.out, f"t{a.track}_{a.model}.json")
    report = json.load(open(rpath)) if os.path.exists(rpath) else {}
    qconds = a.query_cond or [None] * len(a.conditions)
    for cond, qc in zip(a.conditions, qconds):
        hc = hyb["conditions"][cond]
        cfg = hc["systems"]["linear*"]["cfg"]
        dcond = hc["dense_condition"]
        qcond = qc or cond
        stats = {"docs_encoded": 0, "queries_encoded": 0, "encode_s": 0.0, "backend": a.backend}
        # phase 1: pools, missing documents, query texts
        per, caches, jobs = {}, {}, []
        for split in a.splits:
            per[split] = {}
            for dom in doms:
                pre = f"t{a.track}_{dom}_{split}"
                bm = read_run(os.path.join(a.bm25, f"{pre}_{cond}.tsv"))
                de = read_run(os.path.join(a.dense, f"{pre}_{dcond}.tsv"))
                (_, queries, gold), = [p for p in plan(a.track, os.path.join(a.data, sub, dom), split)
                                       if p[0] == qcond]
                qtext = dict(queries)
                qids = sorted(q for q in gold if q in qtext)
                if split == "train" and len(qids) > a.train_per_domain:
                    qids = sorted(random.Random(20260921).sample(qids, a.train_per_domain))
                pools = {q: order(fused(Query(bm.get(q, []), de.get(q, [])), cfg))[:a.pool] for q in qids}
                if dom not in caches:
                    caches[dom] = load_cache(os.path.join(cdir, f"docs_{dom}"))
                ins = instruction(a.track, cond, dom)
                per[split][dom] = (qids, pools, gold, [f"Instruct: {ins}\nQuery: {clean(qtext[q])}" for q in qids])
        need = {dom: sorted({d for sp in per for q in per[sp].get(dom, ([],))[0] for d, _ in per[sp][dom][1][q]}
                            - set(caches[dom])) for dom in caches}
        texts, index = [], []
        for dom, ds in need.items():
            if ds:
                got = fetch(a.data, a.track, dom, set(ds))
                texts += [got.get(d, "")[:4000] for d in ds]
                index += [("doc", dom, d) for d in ds]
        for sp in per:
            for dom, (qids, _, _, qt) in per[sp].items():
                texts += qt
                index += [("q", sp, dom, q) for q in qids]
        # phase 2: embed everything in one call
        t1 = time.time()
        vec = embed(a, ckpt, texts)
        stats["encode_s"] = round(time.time() - t1, 1)
        stats["docs_encoded"] = sum(1 for x in index if x[0] == "doc")
        stats["queries_encoded"] = sum(1 for x in index if x[0] == "q")
        print(f"  [{cond}] {stats['docs_encoded']} docs + {stats['queries_encoded']} queries in "
              f"{stats['encode_s']:.0f}s ({len(texts) / max(stats['encode_s'], 1e-9):.1f}/s)", flush=True)
        qv = {}
        for x, v in zip(index, vec):
            if x[0] == "doc":
                caches[x[1]][x[2]] = v
            else:
                qv[(x[1], x[2], x[3])] = v
        for dom, ds in need.items():
            if ds:
                save_cache(os.path.join(cdir, f"docs_{dom}"), caches[dom])
        # phase 3: scores
        for sp in per:
            for dom, (qids, pools, gold, _) in list(per[sp].items()):
                dc = caches[dom]
                sc = {q: {d: float(np.dot(qv[(sp, dom, q)], dc[d].astype(np.float32))) for d, _ in pools[q]}
                      for q in qids}
                per[sp][dom] = (qids, pools, sc, gold)

        def evaluate(split, how):
            out = {}
            for dom, (qids, pools, sc, gold) in per[split].items():
                out[dom] = [ndcg(rank(pools[q], how, sc[q]), gold[q], 10) for q in qids]
            return out

        hows = [("none", 0)] + [("top", n) for n in DEPTHS if n <= a.pool] + [("interp", w) for w in WEIGHTS]
        res = {}
        for how in hows:
            r = {s: evaluate(s, how) for s in a.splits}
            res[how] = {s: (round(sum(sum(v) / len(v) for v in r[s].values()) / len(r[s]), 4), r[s])
                        for s in a.splits}
        row = {"checkpoint": ckpt, "quant": tag, "max_len": a.max_len, "pool": a.pool, "hybrid_cfg": cfg,
               "query_condition": qcond, "train_topics_per_domain_max": a.train_per_domain, **stats,
               "by_how": {f"{k}={p}": {s: v[0] for s, v in r.items()} for (k, p), r in res.items()}}
        if "train" in a.splits and "dev" in a.splits:
            best = max(hows, key=lambda h: res[h]["train"][0])
            tb = bootstrap(res[best]["train"][1], res[("none", 0)]["train"][1]) if best[0] != "none" else None
            row.update({"best_on_train": f"{best[0]}={best[1]}", "train_bootstrap_best_minus_none": tb,
                        "dev_bootstrap_best_minus_none": bootstrap(res[best]["dev"][1], res[("none", 0)]["dev"][1]),
                        "dev_per_domain_best": {d: round(sum(v) / len(v), 4) for d, v in res[best]["dev"][1].items()},
                        "dev_per_topic_best": res[best]["dev"][1], "dev_per_topic_none": res[("none", 0)]["dev"][1]})
            print(f"== t{a.track} {cond}: none train {res[('none', 0)]['train'][0]} dev {res[('none', 0)]['dev'][0]}"
                  f" | best on train {best}: train {res[best]['train'][0]} dev {res[best]['dev'][0]} "
                  f"train boot {tb}", flush=True)
        for h in hows:
            print(f"   {h[0]}={h[1]}: " + "  ".join(f"{s} {res[h][s][0]}" for s in a.splits), flush=True)
        report[cond] = row
        json.dump(report, open(rpath, "w"), indent=1)


if __name__ == "__main__":
    main()
