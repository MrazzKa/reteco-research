# Environment of the submission runs

Two Python virtual environments (both Python 3.14.4); exact package versions from `pip freeze` on 2026-11-23:

| file | venv | used for |
| --- | --- | --- |
| `requirements_main.txt` | `~/semeval-reteco/.venv` | BM25 (bm25s), dense retrieval (sentence-transformers / bge), ReasonEmbed-4B NF4 (transformers + bitsandbytes), Qwen3-Reranker-0.6B, scoring; `scripts/submit.py` and every research script except the LLM |
| `requirements_llm.txt` | `~/semeval-reteco/.venv-llm` | vLLM 0.32.0 for the Qwen3-4B-Instruct-2507 AWQ generations (`scripts/llm_expand.py`, called by `submit.py`) |

Key versions: main — torch 2.14.1+cu130, transformers 5.19.0, bitsandbytes 0.50.2, sentence-transformers 6.1.0,
bm25s 0.3.13, numpy 2.5.4, faiss-cpu 1.15.1; LLM — vllm 0.32.0, torch 2.13.0+cu130, transformers 5.19.0.

Machine: Windows 11 + WSL2 (Ubuntu 26.04.1 LTS, kernel 6.18.58.1-microsoft-standard-WSL2), NVIDIA GeForce RTX 4060
Laptop GPU (8 GB), driver 621.24 (Windows; `nvidia-smi` in WSL reports 620.73.02 / KMD 621.24, CUDA UMD 13.5);
CUDA runtime 13.0 inside both torch wheels (cuDNN 9.24.0 in the main venv); no system CUDA toolkit. vLLM compiles
small kernels at start-up with clang 22.1.8 (`CC=~/semeval-reteco/tools/bin/cc`, set by `submit.py` and
`scripts/run_test.sh`). 7 GB RAM visible to WSL; 20 CPU threads.

Model revisions: `configs/submission.json` (per variant) and RESULTS AF.

Recreate a venv: `python3.14 -m venv <dir> && <dir>/bin/pip install -r requirements_<x>.txt` (torch wheels from the
CUDA 13.0 index: `--extra-index-url https://download.pytorch.org/whl/cu130`).
