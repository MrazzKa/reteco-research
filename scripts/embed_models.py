"""Embedding-model registry and a thin GPU encoder (fp16, length-sorted batches).

Every entry follows its model card: query/document prefixes or instructions,
pooling (taken from the checkpoint's sentence-transformers config), L2 normalisation,
and the maximum context. Changing a prefix silently costs several nDCG points, so
they live in one place and are recorded with every cache (see `card()`).

`max_len` is the truncation window in tokens; text beyond it is dropped (right
truncation, the sentence-transformers default). The model's native limit is kept in
`native_len` for the record.
"""
import os
import time

import numpy as np

BGE_Q = "Represent this sentence for searching relevant passages: "
QWEN_TASK = "Given a web search query, retrieve relevant passages that answer the query"

# name -> dict(ckpt, q, d, native_len, trust, dim, notes)
MODELS = {
    "minilm": dict(ckpt="sentence-transformers/all-MiniLM-L6-v2", q="", d="", native_len=256),
    "bge-small": dict(ckpt="BAAI/bge-small-en-v1.5", q=BGE_Q, d="", native_len=512),
    "bge-base": dict(ckpt="BAAI/bge-base-en-v1.5", q=BGE_Q, d="", native_len=512),
    "bge-large": dict(ckpt="BAAI/bge-large-en-v1.5", q=BGE_Q, d="", native_len=512),
    "e5-small": dict(ckpt="intfloat/e5-small-v2", q="query: ", d="passage: ", native_len=512),
    "e5-base": dict(ckpt="intfloat/e5-base-v2", q="query: ", d="passage: ", native_len=512),
    "e5-large": dict(ckpt="intfloat/e5-large-v2", q="query: ", d="passage: ", native_len=512),
    "gte-small": dict(ckpt="thenlper/gte-small", q="", d="", native_len=512),
    "arctic-s": dict(ckpt="Snowflake/snowflake-arctic-embed-s", q=BGE_Q, d="", native_len=512),
    # Arctic v2.0: query prefix "query: ", no document prefix (model card).
    # Model card: without xformers, disable memory-efficient attention and unpadding.
    "arctic-m-v2": dict(ckpt="Snowflake/snowflake-arctic-embed-m-v2.0", q="query: ", d="",
                        native_len=8192, trust=True,
                        config_kwargs={"use_memory_efficient_attention": False,
                                       "unpad_inputs": False}),
    # GTE ModernBERT: no prefixes, CLS pooling, 8192 context (model card).
    "gte-modernbert": dict(ckpt="Alibaba-NLP/gte-modernbert-base", q="", d="", native_len=8192),
    # Nomic v1.5: task prefixes are mandatory.
    "nomic-v1.5": dict(ckpt="nomic-ai/nomic-embed-text-v1.5", q="search_query: ",
                       d="search_document: ", native_len=8192, trust=True),
    # Qwen3-Embedding: instruction on the query side only, last-token pooling, 32k context.
    "qwen3-0.6b": dict(ckpt="Qwen/Qwen3-Embedding-0.6B",
                       q=f"Instruct: {QWEN_TASK}\nQuery:", d="", native_len=32768),
}


def card(name, max_len):
    m = MODELS[name]
    return {"model": name, "checkpoint": m["ckpt"], "query_prefix": m["q"],
            "doc_prefix": m["d"], "native_len": m["native_len"], "max_len": max_len,
            "normalize": True, "truncation": "right, at max_len tokens"}


def revision(ckpt):
    """Commit hash of the locally cached snapshot (recorded with every result)."""
    from huggingface_hub.constants import HF_HUB_CACHE
    ref = os.path.join(HF_HUB_CACHE, "models--" + ckpt.replace("/", "--"), "refs", "main")
    try:
        return open(ref).read().strip()
    except OSError:
        return "unknown"


class Encoder:
    def __init__(self, name, max_len, fp16=True, device="cuda"):
        import torch
        from sentence_transformers import SentenceTransformer
        m = MODELS[name]
        kw = {"trust_remote_code": True} if m.get("trust") else {}
        if m.get("config_kwargs"):
            kw["config_kwargs"] = m["config_kwargs"]
        self.name, self.max_len = name, max_len
        self.qp, self.dp = m["q"], m["d"]
        self.model = SentenceTransformer(m["ckpt"], device=device, **kw)
        self.model.max_seq_length = max_len
        if fp16 and device == "cuda":
            self.model.half()
        self.dim = (getattr(self.model, "get_embedding_dimension", None)
                    or self.model.get_sentence_embedding_dimension)()
        self.revision = revision(m["ckpt"])
        self.torch = torch

    def _enc(self, texts, prefix, batch):
        # sentence-transformers sorts inputs by length internally, so each batch holds
        # similar-length texts (little padding); output order is restored. On CUDA OOM
        # the batch is halved and the call retried (the halved size is kept).
        while True:
            try:
                with self.torch.inference_mode():
                    emb = self.model.encode([prefix + t for t in texts], batch_size=batch,
                                            normalize_embeddings=True, convert_to_tensor=True,
                                            show_progress_bar=False)
                return emb.to(self.torch.float16).cpu().numpy()
            except self.torch.OutOfMemoryError:
                self.torch.cuda.empty_cache()
                if batch <= 1:
                    raise
                batch //= 2
                self.oom_batch = batch
                print(f"    CUDA OOM -> batch {batch}", flush=True)

    def encode_docs(self, texts, batch=128):
        return self._enc(texts, self.dp, min(batch, getattr(self, "oom_batch", batch)))

    def encode_queries(self, texts, batch=64):
        return self._enc(texts, self.qp, min(batch, getattr(self, "oom_batch", batch)))


def load_encoder(name, max_len, fp16=True, device="cuda"):
    t0 = time.time()
    enc = Encoder(name, max_len, fp16=fp16, device=device)
    print(f"    model {MODELS[name]['ckpt']} rev {enc.revision[:10]} dim {enc.dim} "
          f"max_len {max_len} fp16={fp16} ({time.time() - t0:.0f}s)", flush=True)
    return enc


