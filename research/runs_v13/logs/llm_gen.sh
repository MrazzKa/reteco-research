#!/bin/bash
# Week 5 step 2: LLM query expansions (reason, hyde) for 2a_current, 1a, 1b_query+step; cached + resumable.
export CC=~/semeval-reteco/tools/bin/cc PATH=~/semeval-reteco/tools/bin:$PATH
cd ~/semeval-reteco/reteco-research/scripts
D=../../reteco_data_v11; O=../research/runs_v13/llm; PY=~/semeval-reteco/.venv-llm/bin/python
while pgrep -f tiebreak.sh >/dev/null; do sleep 20; done
gen() {  # GPU memory left by Windows varies: try a large KV budget first, then smaller ones
  for u in 0.75 0.65 0.55 0.485; do
    echo "=== $(date +%H:%M:%S) gpu-util $u: $*"
    $PY llm_expand.py --data $D --gpu-util $u --max-seqs 64 --max-batched 2048 "$@" 2>&1 \
      | grep -E "^\[|/[0-9]+ +chunk|Error|KV cache size" && [ ${PIPESTATUS[0]} -eq 0 ] && return 0
  done
  echo "FAILED $*"
}
gen --track 2 --conditions 2a_current --prompts reason hyde --out $O/t2
gen --track 1 --conditions 1a --prompts reason hyde --out $O/t1
gen --track 1 --conditions 1b_query+step --prompts reason hyde --out $O/t1
echo "=== $(date +%H:%M:%S) ALLDONE"
