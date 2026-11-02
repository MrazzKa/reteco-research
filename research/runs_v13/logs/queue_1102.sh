#!/bin/bash
# 2026-11-02 GPU queue (one job at a time): finish rule-11 history generations, ReasonEmbed runs for step 1 /
# rule 10 (saved runs; query vectors cached), then the step-4 Llama generations.
export CC=~/semeval-reteco/tools/bin/cc PATH=~/semeval-reteco/tools/bin:$PATH
cd ~/semeval-reteco/reteco-research/scripts
D=../../reteco_data_v11; K=../../RETECO/starter_kit; R=../research/runs_v13; PY=~/semeval-reteco/.venv-llm/bin/python
while pgrep -f "llm_expand.py" >/dev/null; do sleep 15; done
gen() {
  for i in 1 2 3; do for u in 0.75 0.65 0.55 0.485; do
    echo "=== $(date +%H:%M:%S) gpu-util $u: $*"
    $PY llm_expand.py --data $D --gpu-util $u --max-seqs 64 --max-batched 2048 "$@" 2>&1 \
      | grep -E "^\[|/[0-9]+ +chunk|Error|KV cache size" && [ ${PIPESTATUS[0]} -eq 0 ] && return 0
  done; sleep 30; done
  echo "FAILED $*"
}
rr() {  # ReasonEmbed NF4, chunked, restartable
  for i in $(seq 1 10); do
    echo "=== $(date +%H:%M:%S) attempt $i: $*"
    ~/semeval-reteco/.venv/bin/python reason_rerank.py --backend bnb --bits 4 --batch 4 --chunk 2000 --pool 50 \
      --data $D --kit $K --out $R/reason --save-runs $R/foreign/runs "$@" 2>&1 \
      | grep -vE "Warning|warn\(|Loading weights" && [ ${PIPESTATUS[0]} -eq 0 ] && return 0
    sleep 60
  done
  echo "FAILED $*"
}
gen --track 2 --conditions 2a_hist3q 2a_hist3qa --prompts reason hyde --out $R/llm/t2
echo "=== $(date +%H:%M:%S) HISTGEN_DONE"
rr --track 2 --conditions 2a_current__q+r+h --query-cond 2a_current --name 2a_maxp --hybrid $R/maxp/t2/hybrid_2a_current.json --bm25 $R/maxp/t2/bm25/runs --dense $R/maxp/t2/dense/runs
rr --track 2 --conditions 2a_current__q+r+h --query-cond 2a_current --name 2a_nomaxp --hybrid $R/qexp/t2/hybrid_2a_current.json --bm25 $R/qexp/t2/bm25/runs --dense $R/qexp/t2/dense/runs
rr --track 1 --conditions 1a__q+r+h --query-cond 1a --name 1a_rerun --hybrid $R/qexp/t1/hybrid_1a.json --bm25 $R/qexp/t1/bm25/runs --dense $R/qexp/t1/dense/runs
rr --track 1 --conditions 1b_query+step__q+r+h --query-cond 1b_query+step --name 1b_rerun --hybrid $R/qexp/t1/hybrid_1b.json --bm25 $R/qexp/t1/bm25/runs --dense $R/qexp/t1/dense/runs
echo "=== $(date +%H:%M:%S) REASON1_DONE"
gen --llm llama3.2-3b --track 2 --conditions 2a_current --prompts reason hyde --out $R/llm_llama/t2
gen --llm llama3.2-3b --track 1 --conditions 1a --prompts reason hyde --out $R/llm_llama/t1
echo "=== $(date +%H:%M:%S) ALLDONE"
