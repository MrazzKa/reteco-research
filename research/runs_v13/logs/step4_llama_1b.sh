#!/bin/bash
# 2026-11-02 step 4 extension (ablation, no choice): Llama-3.2-3B generations + retrieval + hybrid for 1b.
export CC=~/semeval-reteco/tools/bin/cc PATH=~/semeval-reteco/tools/bin:$PATH
cd ~/semeval-reteco/reteco-research/scripts
D=../../reteco_data_v11; K=../../RETECO/starter_kit; R=../research/runs_v13; E=../research/runs_v12/emb
PY=~/semeval-reteco/.venv/bin/python; LPY=~/semeval-reteco/.venv-llm/bin/python; M=unsloth/Llama-3.2-3B-Instruct
step() { echo "=== $(date +%H:%M:%S) $*"; "$@" 2>&1 | grep -vE "Warning|Loading weights|warn\(|^\s+(train|dev)  "; echo "=== exit ${PIPESTATUS[0]}"; }
while pgrep -f "submit.py --variants|score_submission.py" >/dev/null; do sleep 10; done
for u in 0.75 0.65 0.55; do
  echo "=== $(date +%H:%M:%S) gen gpu-util $u"
  $LPY llm_expand.py --llm llama3.2-3b --data $D --gpu-util $u --max-seqs 64 --max-batched 2048 --track 1 --conditions 1b_query+step \
    --prompts reason hyde --out $R/llm_llama/t1 2>&1 | grep -E "^\[|/[0-9]+ +chunk|Error|KV cache size" && [ ${PIPESTATUS[0]} -eq 0 ] && break
done
echo "=== $(date +%H:%M:%S) GEN_DONE"
step $PY qexp_search.py --data $D --kit $K --track 1 --cond 1b_query+step --variants q+r+h --llm $R/llm_llama/t1 --llm-model $M --model bge-small --max-len 256 --emb $E --out $R/llama/t1b
step $PY hybrid.py --track 1 --conditions 1b_query+step__q+r+h --bm25 $R/llama/t1b/bm25/runs --dense $R/llama/t1b/dense/runs --data $D --kit $K --out $R/llama/t1b/hybrid.json
echo "=== $(date +%H:%M:%S) ALLDONE"
