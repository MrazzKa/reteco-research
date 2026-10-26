#!/usr/bin/env python3
"""Passage embeddings for long documents (MaxP), on top of an existing first-window cache.

A document of L content tokens is split into windows of 510 tokens (512 with [CLS]/[SEP])
with an overlap of 128: starts 0, 382, 764, ... The first window (start 0) is exactly what
the dense_index.py cache at --max-len 512 already holds, so only windows 2+ are encoded
here, i.e. only documents longer than 510 tokens get extra passages. At most
--max-passages windows per document (the cap is recorded in the manifest).

Windows are encoded from token ids directly (no decode / re-tokenise), through the
sentence-transformers model (same pooling and normalisation as the cache). Validation:
32 random documents (seed 20260921) have their first window encoded by this code path
and compared with the cached vector (cosine > 0.99), which checks the code path and the
row alignment.

Layout: <out>/<model>_P510s382/t<track>/<domain>/shard_XXXXX.npy (float16 [p, dim]),
shard_XXXXX.map.npy (int32 corpus row of each passage), manifest.json written last.
Resumable per shard of --shard documents.

    python3 passage_index.py --data ../../reteco_data_v11 --track 1 --domains iota \
        --model bge-small --first ../research/runs_v12/emb --out ../research/runs_v13/emb
"""
import argparse
import json
import os
import random
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dense_index import T1, T2, domain_dir, iter_corpus, load_cache  # noqa: E402
from embed_models import load_encoder  # noqa: E402

WIN, STRIDE = 510, 382  # 510 content tokens, overlap 128


def pdir(out, model, track, dom):
    return os.path.join(out, f"{model}_P{WIN}s{STRIDE}", f"t{track}", dom)


def windows(ids, max_passages):
    """Token-id windows 2+ of one document (first window is in the cache)."""
    out = []
    s = STRIDE
    while s + 128 < len(ids) and len(out) < max_passages - 1:
        out.append(ids[s:s + WIN])
        s += STRIDE
    return out


class WindowEncoder:
    def __init__(self, enc):
        import torch
        self.torch, self.st = torch, enc.model
        tok = self.st.tokenizer
        self.tok, self.cls, self.sep, self.pad = tok, tok.cls_token_id, tok.sep_token_id, tok.pad_token_id

    def encode(self, wins, batch):
        torch = self.torch
        order = sorted(range(len(wins)), key=lambda i: -len(wins[i]))
        out = np.zeros((len(wins), self.st.get_sentence_embedding_dimension()), dtype=np.float16)
        for b in range(0, len(order), batch):
            idx = order[b:b + batch]
            seqs = [[self.cls] + wins[i] + [self.sep] for i in idx]
            m = max(len(x) for x in seqs)
            ii = torch.full((len(seqs), m), self.pad, dtype=torch.long)
            am = torch.zeros((len(seqs), m), dtype=torch.long)
            for r, x in enumerate(seqs):
                ii[r, :len(x)] = torch.tensor(x)
                am[r, :len(x)] = 1
            feats = {"input_ids": ii.cuda(), "attention_mask": am.cuda(),
                     "token_type_ids": torch.zeros_like(ii).cuda()}
            with torch.inference_mode():
                e = self.st(feats)["sentence_embedding"].float()
                e = torch.nn.functional.normalize(e, dim=-1)
            out[idx] = e.half().cpu().numpy()
        return out


def build(a, enc, wenc, dom):
    sub, key = ("track1_tempo", "id") if a.track == 1 else ("track2_recor", "doc_id")
    corpus = os.path.join(a.data, sub, dom, "documents.jsonl")
    ddir = pdir(a.out, a.model, a.track, dom)
    if os.path.exists(os.path.join(ddir, "manifest.json")):
        print(f"  [t{a.track}/{dom}] complete, skipping", flush=True)
        return
    os.makedirs(ddir, exist_ok=True)
    t0, enc_s, tok_s = time.time(), 0.0, 0.0
    cap_chars = (a.max_passages * STRIDE + WIN) * 12
    row, s, n_pass, n_long, n_capped = 0, 0, 0, 0, 0
    buf = []

    def flush(s, buf, row0):
        nonlocal enc_s, tok_s, n_pass, n_long, n_capped
        base = os.path.join(ddir, f"shard_{s:05d}")
        if os.path.exists(base + ".npy") and os.path.exists(base + ".map.npy"):
            mp = np.load(base + ".map.npy")
            n_pass += len(mp)
            n_long += len(set(mp.tolist()))
            return
        t1 = time.time()
        toks = wenc.tok([t[:cap_chars] for t in buf], add_special_tokens=False, truncation=False,
                        return_attention_mask=False)["input_ids"]
        wins, mp = [], []
        for j, ids in enumerate(toks):
            w = windows(ids, a.max_passages)
            n_capped += int(len(ids) > (a.max_passages - 1) * STRIDE + WIN + 128)
            wins += w
            mp += [row0 + j] * len(w)
        tok_s += time.time() - t1
        t1 = time.time()
        emb = wenc.encode(wins, a.batch) if wins else np.zeros((0, enc.dim), dtype=np.float16)
        enc_s += time.time() - t1
        np.save(base + ".tmp.npy", emb)
        np.save(base + ".map.tmp.npy", np.array(mp, dtype=np.int32))
        os.replace(base + ".tmp.npy", base + ".npy")
        os.replace(base + ".map.tmp.npy", base + ".map.npy")
        n_pass += len(mp)
        n_long += len(set(mp))

    for _, text in iter_corpus(corpus, key):
        buf.append(text)
        if len(buf) == a.shard:
            flush(s, buf, row)
            row += len(buf)
            s += 1
            buf = []
            print(f"  [t{a.track}/{dom}] shard {s - 1}: {row:,} docs, {n_pass:,} passages, "
                  f"{time.time() - t0:.0f}s", flush=True)
    if buf:
        flush(s, buf, row)
        row += len(buf)
        s += 1

    # validation: first window through this code path vs the cached L512 vector
    fids, fshards, _ = load_cache(domain_dir(a.first, a.model, 512, a.track, dom))
    assert len(fids) == row, (len(fids), row)
    first = np.concatenate([np.asarray(x) for x in fshards])
    picks = sorted(random.Random(20260921).sample(range(row), min(32, row)))
    want = set(picks)
    texts = {i: t for i, (_, t) in enumerate(iter_corpus(corpus, key)) if i in want}
    toks = wenc.tok([texts[i][:cap_chars] for i in picks], add_special_tokens=False)["input_ids"]
    fresh = wenc.encode([t[:WIN] for t in toks], 32).astype(np.float32)
    cos = (fresh * first[picks].astype(np.float32)).sum(1)
    ok = float(cos.min()) > 0.99
    man = {"track": a.track, "domain": dom, "model": a.model, "revision": enc.revision, "n_docs": row,
           "shards": s, "shard_size": a.shard, "window_tokens": WIN, "stride": STRIDE, "overlap": WIN - STRIDE,
           "max_passages_per_doc": a.max_passages, "docs_capped": n_capped,
           "extra_passages": n_pass, "docs_with_extra_passages": n_long,
           "encode_s": round(enc_s, 1), "tokenize_s": round(tok_s, 1), "wall_s": round(time.time() - t0, 1),
           "validation": {"first_window_cos_min": round(float(cos.min()), 5), "ok": ok}}
    if not ok:
        json.dump(man, open(os.path.join(ddir, "manifest.FAILED.json"), "w"), indent=1)
        raise SystemExit(f"validation failed t{a.track}/{dom}: {man['validation']}")
    json.dump(man, open(os.path.join(ddir, "manifest.json"), "w"), indent=1)
    print(f"  [t{a.track}/{dom}] DONE {row:,} docs, {n_pass:,} extra passages ({n_long:,} docs), "
          f"encode {enc_s:.0f}s, tokenize {tok_s:.0f}s, cos min {cos.min():.4f}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--track", type=int, required=True, choices=(1, 2))
    ap.add_argument("--domains", nargs="+", default=["all"])
    ap.add_argument("--model", required=True)
    ap.add_argument("--first", required=True, help="dense_index.py cache root holding <model>_L512")
    ap.add_argument("--max-passages", type=int, default=200)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--shard", type=int, default=20000)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    doms = (T1 if a.track == 1 else T2) if a.domains == ["all"] else a.domains
    enc = load_encoder(a.model, 512)
    wenc = WindowEncoder(enc)
    for dom in doms:
        build(a, enc, wenc, dom)


if __name__ == "__main__":
    main()


class MaxPIndex:
    """Document score = max over its passages (first window from the L512 cache, windows 2+
    from this index); same search() interface and tie key as dense_search.GpuIndex."""

    def __init__(self, first_dir, pass_dir):
        import torch
        import tiebreak
        self.torch = torch
        self.ids, shards, _ = load_cache(first_dir)
        self.first = torch.cat([torch.from_numpy(np.array(x)) for x in shards]).cuda().float()
        man = json.load(open(os.path.join(pass_dir, "manifest.json")))
        assert man["n_docs"] == len(self.ids), pass_dir
        ps, ms = [], []
        for s in range(man["shards"]):
            base = os.path.join(pass_dir, f"shard_{s:05d}")
            ps.append(np.load(base + ".npy"))
            ms.append(np.load(base + ".map.npy"))
        self.pas = torch.from_numpy(np.concatenate(ps)).cuda().float()
        self.map = torch.from_numpy(np.concatenate(ms).astype(np.int64)).cuda()
        order = sorted(range(len(self.ids)), key=lambda i: tiebreak.key(self.ids[i]))
        self.lex = np.empty(len(self.ids), dtype=np.int64)
        self.lex[order] = np.arange(len(self.ids))

    def search(self, qemb, k, batch=64):
        torch = self.torch
        k = min(k, len(self.ids))
        q = torch.from_numpy(qemb).cuda().float()
        out = []
        for s in range(0, q.shape[0], batch):
            sims = q[s:s + batch] @ self.first.T
            if self.pas.shape[0]:
                ps = q[s:s + batch] @ self.pas.T
                sims.scatter_reduce_(1, self.map.expand(ps.shape[0], -1), ps, reduce="amax")
            kk = min(k + 32, sims.shape[1])
            val, idx = torch.topk(sims, kk, dim=1)
            val, idx = val.cpu().numpy(), idx.cpu().numpy()
            for r in range(idx.shape[0]):
                o = np.lexsort((self.lex[idx[r]], -val[r]))[:k]
                out.append([(self.ids[idx[r][j]], float(val[r][j])) for j in o])
        return out

    def free(self):
        del self.first, self.pas, self.map
        self.torch.cuda.empty_cache()
