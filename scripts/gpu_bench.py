#!/usr/bin/env python3
"""Encoding throughput benchmark: one model, one corpus sample, several batch sizes.

Reports docs/s, peak VRAM and wall time per (precision, batch) so the indexing jobs
can pick a setting. Sample = the first N documents of a domain corpus (deterministic).

    python3 gpu_bench.py --corpus ../../reteco_data_v11/track1_tempo/history/documents.jsonl \
        --model bge-small --n 4000 --max-len 256 --batches 32 64 128 256
"""
import argparse
import json
import os
import platform
import sys
import time

import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from embed_models import load_encoder  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--model", default="bge-small")
    ap.add_argument("--n", type=int, default=4000)
    ap.add_argument("--max-len", type=int, default=256)
    ap.add_argument("--batches", type=int, nargs="+", default=[32, 64, 128, 256])
    ap.add_argument("--precisions", nargs="+", default=["fp16", "fp32"])
    ap.add_argument("--out")
    a = ap.parse_args()

    texts = []
    with open(a.corpus, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                texts.append(json.loads(line).get("content", "") or "")
            if len(texts) >= a.n:
                break
    info = {"python": platform.python_version(), "torch": torch.__version__,
            "cuda": torch.version.cuda, "gpu": torch.cuda.get_device_name(0),
            "vram_total_gb": round(torch.cuda.get_device_properties(0).total_memory / 2**30, 2),
            "corpus": a.corpus, "n": len(texts), "max_len": a.max_len, "model": a.model}
    print(json.dumps(info), flush=True)
    rows = []
    for prec in a.precisions:
        enc = load_encoder(a.model, a.max_len, fp16=(prec == "fp16"))
        enc.encode_docs(texts[:256], batch=64)  # warm-up
        for b in a.batches:
            torch.cuda.synchronize()
            torch.cuda.reset_peak_memory_stats()
            t0 = time.time()
            try:
                enc.encode_docs(texts, batch=b)
            except torch.OutOfMemoryError:
                print(f"  {prec} batch {b}: OOM", flush=True)
                torch.cuda.empty_cache()
                continue
            torch.cuda.synchronize()
            dt = time.time() - t0
            row = {"precision": prec, "batch": b, "seconds": round(dt, 2),
                   "docs_per_s": round(len(texts) / dt, 1),
                   "peak_vram_gb": round(torch.cuda.max_memory_allocated() / 2**30, 2)}
            rows.append(row)
            print("  " + json.dumps(row), flush=True)
        del enc
        torch.cuda.empty_cache()
    if a.out:
        json.dump({"info": info, "rows": rows}, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
