#!/usr/bin/env python3
"""Embed a list of texts with a decoder embedding model through vLLM (pooling runner, FP8).

Runs in the LLM venv (`~/semeval-reteco/.venv-llm`); reason_rerank.py calls it as a
subprocess. Input: a JSON list of strings. Each text is tokenised, cut to max_len - 1 tokens
and the tokenizer's end-of-text token is appended (the last-token pooling position, as the
model card's transformers code produces). Output: float32 [n, dim], L2-normalised.

    ~/semeval-reteco/.venv-llm/bin/python embed_vllm.py --model hanhainebula/reason-embed-qwen3-4b-0928 \
        --inp texts.json --out vecs.npy
"""
import argparse
import json
import time

import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--inp", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-len", type=int, default=512)
    ap.add_argument("--quant", default="fp8")
    ap.add_argument("--gpu-util", type=float, default=0.75)
    a = ap.parse_args()
    from vllm import LLM
    from vllm.inputs import TokensPrompt
    texts = json.load(open(a.inp))
    llm = LLM(model=a.model, runner="pooling", quantization=a.quant, max_model_len=a.max_len,
              gpu_memory_utilization=a.gpu_util, enforce_eager=True, seed=0)
    tok = llm.get_tokenizer()
    end = tok("x")["input_ids"][-1]  # the appended end-of-text id (151643 for Qwen3)
    ids = tok(texts, add_special_tokens=False)["input_ids"]
    prompts = [TokensPrompt(prompt_token_ids=x[:a.max_len - 1] + [end]) for x in ids]
    t0 = time.time()
    out = llm.embed(prompts, use_tqdm=False)
    e = np.array([o.outputs.embedding for o in out], dtype=np.float32)
    e /= np.linalg.norm(e, axis=1, keepdims=True)
    np.save(a.out, e)
    print(f"embedded {len(e)} texts in {time.time() - t0:.0f}s ({len(e) / max(time.time() - t0, 1e-9):.1f}/s)",
          flush=True)


if __name__ == "__main__":
    main()
