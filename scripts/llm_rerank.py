#!/usr/bin/env python3
"""LOG rule 16: a pointwise LLM reranker (Qwen3-Reranker, yes/no) over the top N of a final system.

Input: a score dump of the final system (reason_rerank.py --save-scores: per split / domain / topic the
pool in final order with the final score) — the rule-8 train subsample and all dev topics. For every topic
the top --depth documents are scored by the reranker: prompt exactly as in the model card (transformers
example, revision 22e6836): system "Judge whether the Document meets the requirements ...", user
"<Instruct>: {instruction}\\n<Query>: {query}\\n<Document>: {doc}", assistant prefix with an empty think
block; score = logit("yes") - logit("no") at the last position (monotone in P(yes)). The document is cut
to 512 tokens, the query to 1,024. Scores are cached by sha1(instruction + query + document text); the
doc id is never shown and never used to rank (ties: sha1 of the id, scripts/tiebreak.py).

Grid (train subsample, rule 16): none; reranker order over the top N; (1 - w) z(final) + w z(reranker)
over the top N, w in 0.1 .. 0.9; N in {10, 20}. Best on train adopted over none with +0.005 and bootstrap
lower bound > 0; dev reported once.

    python3 llm_rerank.py --cond 2a_history --scores R/scores/2ah_hybrid.json --data D --kit K --out R/rerank
    python3 llm_rerank.py ... --limit 200      # speed test on the first 200 pairs
"""
import argparse
import hashlib
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bm25s_run import ndcg_fn  # noqa: E402
from dense_search import plan  # noqa: E402
from gold_categories import fetch  # noqa: E402
from hybrid import bootstrap  # noqa: E402
from reason_rerank import clean, instruction  # noqa: E402
from tie_study import order  # noqa: E402
import tiebreak  # noqa: E402

MODELS = {"qwen3-reranker-4b": ("Qwen/Qwen3-Reranker-4B", "22e683669bc0f0bd69640a1354a6d0aebcfeede5"),
          "qwen3-reranker-0.6b": ("Qwen/Qwen3-Reranker-0.6B", "e61197ed45024b0ed8a2d74b80b4d909f1255473")}
PREFIX = ("<|im_start|>system\nJudge whether the Document meets the requirements based on the Query and the "
          "Instruct provided. Note that the answer can only be \"yes\" or \"no\".<|im_end|>\n<|im_start|>user\n")
SUFFIX = "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
WEIGHTS = [round(0.1 * i, 1) for i in range(1, 10)]
# condition -> (track, plan condition for query text / gold, ReasonEmbed-style instruction condition, qrels)
CONDS = {"1a": (1, "1a", "1a", None), "1b": (1, "1b_query+step", "1b_query+step", None),
         "2a_current": (2, "2a_current", "2a_current", None), "2a_history": (2, "2a_current", "2a_current", "2a_hist3qa"),
         "2a_history_q": (2, "2a_current", "2a_current", "2a_hist3q")}


class Reranker:
    def __init__(self, name, bits, doc_len, query_len, load_model=True):
        from transformers import AutoTokenizer
        self.ckpt, self.rev = MODELS[name]
        self.bits, self.doc_len, self.query_len, self.model = bits, doc_len, query_len, None
        self.tok = AutoTokenizer.from_pretrained(self.ckpt, revision=self.rev, padding_side="left")
        if load_model:
            self.load()
        self.yes = self.tok.convert_tokens_to_ids("yes")
        self.no = self.tok.convert_tokens_to_ids("no")
        self.pre = self.tok.encode(PREFIX, add_special_tokens=False)
        self.suf = self.tok.encode(SUFFIX, add_special_tokens=False)

    def load(self):
        if self.model is not None:
            return
        import torch
        from transformers import AutoModelForCausalLM, BitsAndBytesConfig
        self.torch = torch
        kw = {"dtype": torch.float16, "device_map": "cuda", "revision": self.rev}
        if self.bits == 4:
            kw["quantization_config"] = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                                                           bnb_4bit_compute_dtype=torch.float16)
        self.model = AutoModelForCausalLM.from_pretrained(self.ckpt, **kw).eval()

    def cut(self, text, n):
        ids = self.tok.encode(text, add_special_tokens=False)
        return text if len(ids) <= n else self.tok.decode(ids[:n])

    def score(self, items, batch):
        """items: [(instruction, query, doc)] (already cut) -> logit(yes) - logit(no)"""
        torch = self.torch
        ids = [self.pre + self.tok.encode(f"<Instruct>: {i}\n<Query>: {q}\n<Document>: {d}",
                                          add_special_tokens=False) + self.suf for i, q, d in items]
        out = np.zeros(len(items), dtype=np.float32)
        order_ = sorted(range(len(ids)), key=lambda k: -len(ids[k]))
        for b in range(0, len(order_), batch):
            idx = order_[b:b + batch]
            enc = self.tok.pad({"input_ids": [ids[k] for k in idx]}, padding=True, return_tensors="pt",
                               pad_to_multiple_of=8).to("cuda")
            with torch.inference_mode():
                logits = self.model(**enc, logits_to_keep=1).logits[:, -1, :]
                out[idx] = (logits[:, self.yes] - logits[:, self.no]).float().cpu().numpy()
        return out


def load_cache(path):
    c = {}
    if os.path.exists(path):
        for ln in open(path):
            if ln.strip():
                k, v = ln.split("\t")
                c[k] = float(v)
    return c


def zs(v):
    v = np.asarray(v, dtype=np.float64)
    s = v.std()
    return (v - v.mean()) / s if s > 0 else np.zeros_like(v)


def rerank(lst, how, rs):
    """lst: [(doc, final score)] in final order; rs: reranker score per doc of the top N."""
    kind, n, w = how
    head, tail = lst[:n], [d for d, _ in lst[n:]]
    if kind == "none":
        return [d for d, _ in lst]
    if kind == "only":
        return [d for d, _ in order([(d, rs[d]) for d, _ in head])] + tail
    zf, zr = zs([s for _, s in head]), zs([rs[d] for d, _ in head])
    return [d for d, _ in order([(d, (1 - w) * a + w * b) for (d, _), a, b in zip(head, zf, zr)])] + tail


def query_texts(data, cond, split, dom):
    track, pc, _, hist = CONDS[cond]
    sub = "track1_tempo" if track == 1 else "track2_recor"
    d = os.path.join(data, sub, dom)
    (_, queries, gold), = [p for p in plan(track, d, split) if p[0] == pc]
    qt = dict(queries)
    if hist:
        from llm_expand import history_body
        bench = json.load(open(os.path.join(d, f"benchmark_{split}.json"), encoding="utf-8"))
        bench = [bench] if isinstance(bench, dict) else bench
        qt = {f"{c['id']}_turn_{t['turn_id']}": history_body(t, hist == "2a_hist3qa") for c in bench for t in c["turns"]}
    return qt, gold


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cond", required=True, choices=sorted(CONDS))
    ap.add_argument("--scores", required=True, help="reason_rerank.py --save-scores dump of the final system")
    ap.add_argument("--data", required=True)
    ap.add_argument("--kit", required=True)
    ap.add_argument("--model", default="qwen3-reranker-4b", choices=sorted(MODELS))
    ap.add_argument("--bits", type=int, default=4, choices=(4, 16))
    ap.add_argument("--depth", type=int, default=20)
    ap.add_argument("--doc-len", type=int, default=512)
    ap.add_argument("--query-len", type=int, default=1024)
    ap.add_argument("--batch", type=int, default=4)
    ap.add_argument("--chunk", type=int, default=400, help="pairs per cache flush")
    ap.add_argument("--splits", nargs="+", default=["train", "dev"])
    ap.add_argument("--limit", type=int, help="speed test: score only the first N uncached pairs, no report")
    ap.add_argument("--margin", type=float, default=0.005)
    ap.add_argument("--save-runs", help="write the chosen reranked top-N + rest as TREC runs here")
    ap.add_argument("--out", required=True)
    tiebreak.add_arg(ap)
    a = ap.parse_args()
    tiebreak.set_mode(a.tiebreak)
    track = CONDS[a.cond][0]
    dump = json.load(open(a.scores))
    pools = dump["scores"]
    cdir = os.path.join(a.out, "cache")
    os.makedirs(cdir, exist_ok=True)
    cpath = os.path.join(cdir, f"{a.model}_{a.bits}bit_D{a.doc_len}.tsv")
    cache = load_cache(cpath)
    # phase 1: pairs
    pairs, per, golds = [], {}, {}
    for sp in a.splits:
        for dom, tops in pools[sp].items():
            qt, gold = query_texts(a.data, a.cond, sp, dom)
            golds[(sp, dom)] = gold
            ins = instruction(track, CONDS[a.cond][2], dom, CONDS[a.cond][3])
            docs = fetch(a.data, track, dom, {d for q in tops for d, _ in tops[q][:a.depth]})
            per[(sp, dom)] = {}
            for q, lst in tops.items():
                per[(sp, dom)][q] = []
                for d, _ in lst[:a.depth]:
                    pairs.append((sp, dom, q, d, ins, clean(qt[q]), clean(docs.get(d, ""))[:6000]))
    print(f"[{a.cond}] {len(pairs)} pairs over {sum(len(v) for v in per.values())} topics", flush=True)
    # phase 2: score missing pairs (texts cut to token limits first; the cache key uses the cut texts)
    t0 = time.time()
    rr = Reranker(a.model, a.bits, a.doc_len, a.query_len, load_model=False)
    keyed, cut_q, cut_d, n_new = [], {}, {}, 0
    for c in range(0, len(pairs), a.chunk):
        part = pairs[c:c + a.chunk]
        items, keys = [], []
        for sp, dom, q, d, ins, qx, dx in part:
            if qx not in cut_q:
                cut_q[qx] = rr.cut(qx, a.query_len)
            if (dom, d) not in cut_d:
                cut_d[(dom, d)] = rr.cut(dx, a.doc_len)
            it = (ins, cut_q[qx], cut_d[(dom, d)])
            items.append(it)
            keys.append(hashlib.sha1("\n".join(it).encode("utf-8")).hexdigest())
        keyed += keys
        miss = sorted({k: i for i, k in reversed(list(enumerate(keys))) if k not in cache}.values())
        if a.limit is not None:
            miss = miss[:max(0, a.limit - n_new)]
        if miss:
            rr.load()
            t1 = time.time()
            sc = rr.score([items[i] for i in miss], a.batch)
            with open(cpath, "a") as f:
                for i, s_ in zip(miss, sc):
                    cache[keys[i]] = float(s_)
                    f.write(f"{keys[i]}\t{float(s_):.5f}\n")
            n_new += len(miss)
            print(f"  {c + len(part)}/{len(pairs)} pairs, {len(miss)} scored in {time.time() - t1:.0f}s "
                  f"({len(miss) / max(time.time() - t1, 1e-9):.2f} pairs/s), total {time.time() - t0:.0f}s", flush=True)
        if a.limit is not None and n_new >= a.limit:
            print(f"speed test: {n_new} pairs", flush=True)
            return
    stats = {"pairs": len(pairs), "scored_new": n_new, "score_s": round(time.time() - t0, 1)}
    # phase 3: grid
    rs = {}
    for (sp, dom, q, d, *_), k in zip(pairs, keyed):
        rs.setdefault((sp, dom, q), {})[d] = cache[k]
    ndcg = ndcg_fn(a.kit)
    hows = [("none", a.depth, 0.0)] + [("only", n, 0.0) for n in (10, 20) if n <= a.depth] + \
           [("interp", n, w) for n in (10, 20) if n <= a.depth for w in WEIGHTS]

    def ev(sp, how):
        out = {}
        for dom, tops in pools[sp].items():
            out[dom] = [ndcg(rerank([tuple(x) for x in tops[q]], how, rs[(sp, dom, q)]), golds[(sp, dom)].get(q, set()), 10)
                        for q in sorted(tops)]
        return out

    res = {how: {sp: ev(sp, how) for sp in a.splits} for how in hows}
    mac = {how: {sp: round(sum(sum(v) / len(v) for v in r[sp].values()) / len(r[sp]), 4) for sp in a.splits}
           for how, r in res.items()}
    best = max(hows, key=lambda h: (mac[h]["train"], -hows.index(h)))
    none = hows[0]
    tb = bootstrap(res[best]["train"], res[none]["train"]) if best != none else None
    adopt = best != none and mac[best]["train"] - mac[none]["train"] >= a.margin and tb["ci95"][0] > 0
    lab = lambda h: f"{h[0]}@{h[1]}" + (f"_w{h[2]}" if h[0] == "interp" else "")
    row = {"cond": a.cond, "model": MODELS[a.model], "bits": a.bits, "doc_len": a.doc_len, "depth": a.depth,
           "scores": a.scores, "final_system": dump.get("best"), **stats,
           "by_how": {lab(h): mac[h] for h in hows}, "best_on_train": lab(best), "train_bootstrap_best_minus_none": tb,
           "adopted": adopt,
           "dev_bootstrap_best_minus_none": bootstrap(res[best]["dev"], res[none]["dev"]) if "dev" in a.splits else None,
           "dev_per_topic_best": res[best].get("dev"), "dev_per_topic_none": res[none].get("dev"),
           "train_per_topic_best": res[best]["train"], "train_per_topic_none": res[none]["train"]}
    rpath = os.path.join(a.out, f"rule16_{a.cond}_{a.model}.json")
    json.dump(row, open(rpath, "w"), indent=1)
    for h in hows:
        print(f"   {lab(h):<16} " + "  ".join(f"{sp} {mac[h][sp]:.4f}" for sp in a.splits), flush=True)
    print(f"== {a.cond}: none {mac[none]} | best on train {lab(best)} {mac[best]} | train boot {tb} | adopted={adopt}"
          f" | dev boot {row['dev_bootstrap_best_minus_none']}", flush=True)
    if a.save_runs:
        os.makedirs(a.save_runs, exist_ok=True)
        for sp in a.splits:
            for dom, tops in pools[sp].items():
                with open(os.path.join(a.save_runs, f"t{track}_{dom}_{sp}_{a.cond}__rr.tsv"), "w") as f:
                    for q in sorted(tops):
                        for r, d in enumerate(rerank([tuple(x) for x in tops[q]], best, rs[(sp, dom, q)]), 1):
                            f.write(f"{q} Q0 {d} {r} {1.0 / r:.6f} rr-{lab(best)}\n")


if __name__ == "__main__":
    main()
