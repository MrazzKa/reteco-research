#!/usr/bin/env python3
"""B3: a copy of configs/submission.json whose LLM / ReasonEmbed / reranker caches point into an empty folder, so
that submit.py runs cold (corpus embeddings and BM25 are not caches: the dense corpus index and the MaxP passage
index are the prebuilt corpus artefacts, BM25 indexes are always rebuilt).

    python3 cold_config.py --out /path/cold/submission_cold.json --cache-root /path/cold/cache
"""
import argparse
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=os.path.join(os.path.dirname(HERE), "configs", "submission.json"))
    ap.add_argument("--cache-root", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    c = json.load(open(a.config))
    root = os.path.abspath(a.cache_root)
    for name, v in c["variants"].items():
        if "llm" in v:
            v["llm"]["cache"] = os.path.join(root, "llm", f"t{v['track']}")
        v["reasonembed"]["cache"] = os.path.join(root, "reason")
        if "llm_rerank" in v:
            v["llm_rerank"]["cache"] = os.path.join(root, "rerank", "scores.tsv")
        # corpus artefacts stay absolute paths into the repo
        for k in ("emb", "passages"):
            if k in v["dense"] and not os.path.isabs(v["dense"][k]):
                v["dense"][k] = os.path.join(os.path.dirname(HERE), v["dense"][k])
    os.makedirs(os.path.join(root, "rerank"), exist_ok=True)
    json.dump(c, open(a.out, "w"), indent=1)
    print(f"wrote {a.out}; caches under {root}")


if __name__ == "__main__":
    main()
