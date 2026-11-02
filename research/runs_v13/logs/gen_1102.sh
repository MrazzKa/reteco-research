#!/bin/bash
# 2026-11-02: step 3 (rule 11) history generations with Qwen3-4B, then step 4 generations with Llama-3.2-3B.
export CC=~/semeval-reteco/tools/bin/cc PATH=~/semeval-reteco/tools/bin:$PATH
cd ~/semeval-reteco/reteco-research/scripts
D=../../reteco_data_v11; R=../research/runs_v13; PY=~/semeval-reteco/.venv-llm/bin/python
gen() {  # GPU memory left by Windows varies: try a large KV budget first, then smaller ones (resumable cache)
  for i in 1 2 3; do for u in 0.75 0.65 0.55 0.485; do
    echo "=== $(date +%H:%M:%S) gpu-util $u: $*"
    $PY llm_expand.py --data $D --gpu-util $u --max-seqs 64 --max-batched 2048 "$@" 2>&1 \
      | grep -E "^\[|/[0-9]+ +chunk|Error|KV cache size" && [ ${PIPESTATUS[0]} -eq 0 ] && return 0
  done; sleep 30; done
  echo "FAILED $*"
}
gen --track 2 --conditions 2a_hist3q 2a_hist3qa --prompts reason hyde --out $R/llm/t2
while pgrep -f "hf download unsloth" >/dev/null; do sleep 15; done
gen --llm llama3.2-3b --track 2 --conditions 2a_current --prompts reason hyde --out $R/llm_llama/t2
gen --llm llama3.2-3b --track 1 --conditions 1a --prompts reason hyde --out $R/llm_llama/t1
echo "=== $(date +%H:%M:%S) ALLDONE"
