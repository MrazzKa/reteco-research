#!/usr/bin/env python3
"""Build a chunked, resumable float16 embedding cache for whole domain corpora (GPU).

Layout, per (model, window, track, domain):

    <out>/<model>_L<max_len>/t<track>/<domain>/
        shard_00000.npy        float16 [n, dim], rows in corpus file order
        shard_00000.ids.json   the n document ids of that shard, same order
        ...
        manifest.json          written last: counts, ids checksum, model card, revision,
                               timings, validation result. Its presence = domain complete.

Resumable: a shard is written to a temp name and renamed, so an existing shard is always
complete; a restarted job skips it. Only one shard of text is held in memory at a time.

Validation after the last shard: ids (concatenated over shards) must equal the corpus id
order exactly; every vector must be finite with norm ~1; and 32 randomly chosen documents
(seed 20260921) are re-encoded and must match their cached vectors (cosine > 0.99), which
catches any row/id misalignment.

    python3 dense_index.py --data ../../reteco_data_v11 --track 1 --domains iota quant \
        --model bge-small --max-len 512 --out ../research/runs_v12/emb
"""
import argparse
import hashlib
import json
import os
import random
import resource
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from embed_models import card, load_encoder  # noqa: E402

T1 = ["iota", "quant", "law", "workplace", "cardano", "monero", "economics", "bitcoin",
      "politics", "genealogy", "travel", "hsm", "history"]
T2 = ["drones", "politics", "law", "medicalsciences", "hardware", "economics", "psychology",
      "biology", "sustainable_living", "robotics", "earth_science"]


def domain_dir(out, model, max_len, track, dom):
    return os.path.join(out, f"{model}_L{max_len}", f"t{track}", dom)


def iter_corpus(path, key):
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                d = json.loads(line)
                yield d[key], d.get("content", "") or ""


def ids_sha(ids):
    h = hashlib.sha1()
    for i in ids:
        h.update(i.encode("utf-8") + b"\n")
    return h.hexdigest()


def load_cache(ddir, mmap=True):
    """Return (ids, list of shard arrays). Requires a complete manifest."""
    man = json.load(open(os.path.join(ddir, "manifest.json"), encoding="utf-8"))
    ids, shards = [], []
    for s in range(man["shards"]):
        base = os.path.join(ddir, f"shard_{s:05d}")
        ids += json.load(open(base + ".ids.json", encoding="utf-8"))
        shards.append(np.load(base + ".npy", mmap_mode="r" if mmap else None))
    assert len(ids) == man["n_docs"] and ids_sha(ids) == man["ids_sha1"], ddir
    return ids, shards, man


def build_domain(enc, data, track, dom, a):
    sub, key = ("track1_tempo", "id") if track == 1 else ("track2_recor", "doc_id")
    corpus = os.path.join(data, sub, dom, "documents.jsonl")
    ddir = domain_dir(a.out, a.model, a.max_len, track, dom)
    if os.path.exists(os.path.join(ddir, "manifest.json")):
        print(f"  [t{track}/{dom}] complete, skipping", flush=True)
        return
    os.makedirs(ddir, exist_ok=True)
    import torch
    torch.cuda.reset_peak_memory_stats()
    t0, enc_s, n, s, done_before = time.time(), 0.0, 0, 0, 0
    buf_ids, buf_txt = [], []

    def flush(s, ids, txt):
        nonlocal enc_s
        base = os.path.join(ddir, f"shard_{s:05d}")
        if os.path.exists(base + ".npy") and os.path.exists(base + ".ids.json"):
            prev = json.load(open(base + ".ids.json", encoding="utf-8"))
            assert prev == ids, f"shard {s} ids differ from corpus; delete {ddir} and rebuild"
            return True
        t1 = time.time()
        emb = enc.encode_docs(txt, batch=a.batch)
        enc_s += time.time() - t1
        np.save(base + ".tmp.npy", emb)
        json.dump(ids, open(base + ".ids.tmp.json", "w", encoding="utf-8"))
        os.replace(base + ".tmp.npy", base + ".npy")
        os.replace(base + ".ids.tmp.json", base + ".ids.json")
        return False

    for doc_id, text in iter_corpus(corpus, key):
        buf_ids.append(doc_id)
        buf_txt.append(text)
        if len(buf_ids) == a.shard:
            skipped = flush(s, buf_ids, buf_txt)
            n += len(buf_ids)
            done_before += len(buf_ids) if skipped else 0
            print(f"  [t{track}/{dom}] shard {s} {'(cached)' if skipped else ''} "
                  f"{n:,} docs, {time.time() - t0:.0f}s", flush=True)
            s += 1
            buf_ids, buf_txt = [], []
    if buf_ids:
        skipped = flush(s, buf_ids, buf_txt)
        n += len(buf_ids)
        done_before += len(buf_ids) if skipped else 0
        s += 1
    peak_vram = torch.cuda.max_memory_allocated() / 2**30

    # ---- validation
    all_ids = [i for i, _ in iter_corpus(corpus, key)]
    ids, shards = [], []
    for k in range(s):
        base = os.path.join(ddir, f"shard_{k:05d}")
        ids += json.load(open(base + ".ids.json", encoding="utf-8"))
        shards.append(np.load(base + ".npy", mmap_mode="r"))
    assert ids == all_ids, "concatenated shard ids != corpus order"
    assert sum(x.shape[0] for x in shards) == len(ids)
    bad, nmin, nmax = 0, 9.0, 0.0
    for x in shards:
        xf = np.asarray(x, dtype=np.float32)
        bad += int((~np.isfinite(xf)).any(axis=1).sum())
        norms = np.linalg.norm(xf, axis=1)
        nmin, nmax = min(nmin, float(norms.min())), max(nmax, float(norms.max()))
    rng = random.Random(20260921)
    picks = sorted(rng.sample(range(len(ids)), min(32, len(ids))))
    want = set(picks)
    texts = {i: t for i, (_, t) in enumerate(iter_corpus(corpus, key)) if i in want}
    fresh = enc.encode_docs([texts[i] for i in picks], batch=32).astype(np.float32)
    offs = np.cumsum([0] + [x.shape[0] for x in shards])
    cached = []
    for i in picks:
        k = int(np.searchsorted(offs, i, side="right") - 1)
        cached.append(np.asarray(shards[k][i - offs[k]], dtype=np.float32))
    cos = (fresh * np.stack(cached)).sum(1)
    ok = bad == 0 and nmin > 0.98 and nmax < 1.02 and float(cos.min()) > 0.99
    man = {"track": track, "domain": dom, "corpus": os.path.abspath(corpus),
           "corpus_bytes": os.path.getsize(corpus), "n_docs": len(ids), "dim": int(shards[0].shape[1]),
           "shards": s, "shard_size": a.shard, "ids_sha1": ids_sha(ids), "dtype": "float16",
           **card(a.model, a.max_len), "revision": enc.revision, "batch": a.batch,
           "encode_s": round(enc_s, 1), "wall_s": round(time.time() - t0, 1),
           "docs_encoded_this_run": n - done_before,
           "docs_per_s": round((n - done_before) / enc_s, 1) if enc_s else None,
           "peak_vram_gb": round(peak_vram, 2),
           "peak_rss_gb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2**20, 2),
           "validation": {"nonfinite_rows": bad, "norm_min": round(nmin, 4), "norm_max": round(nmax, 4),
                          "reencode_cos_min": round(float(cos.min()), 5), "ok": ok}}
    if not ok:
        json.dump(man, open(os.path.join(ddir, "manifest.FAILED.json"), "w"), indent=1)
        raise SystemExit(f"validation failed for t{track}/{dom}: {man['validation']}")
    json.dump(man, open(os.path.join(ddir, "manifest.json"), "w"), indent=1)
    print(f"  [t{track}/{dom}] DONE {len(ids):,} docs, encode {enc_s:.0f}s "
          f"({man['docs_per_s']}/s), peak VRAM {peak_vram:.2f} GB, "
          f"validation ok (cos min {cos.min():.4f})", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--track", type=int, required=True, choices=(1, 2))
    ap.add_argument("--domains", nargs="+", default=["all"])
    ap.add_argument("--model", default="bge-small")
    ap.add_argument("--max-len", type=int, default=512)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--shard", type=int, default=20000)
    ap.add_argument("--no-fp16", action="store_true")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    doms = (T1 if a.track == 1 else T2) if a.domains == ["all"] else a.domains
    enc = load_encoder(a.model, a.max_len, fp16=not a.no_fp16)
    t0 = time.time()
    for dom in doms:
        build_domain(enc, a.data, a.track, dom, a)
    print(f"all done in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
