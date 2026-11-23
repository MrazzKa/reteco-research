#!/bin/bash
# 2026-11-23 N2b / rule 20: Track-1 guidance G1 (no LLM change) and G2 (the LLM sees g). Waits for queue_1123a.
cd ~/semeval-reteco/reteco-research/scripts
D=../../reteco_data_v11; K=../../RETECO/starter_kit; R=../research/runs_v13; E=../research/runs_v12/emb; PY=~/semeval-reteco/.venv/bin/python
LPY=~/semeval-reteco/.venv-llm/bin/python; export CC=~/semeval-reteco/tools/bin/cc
until grep -q "ALLDONE" $R/logs/queue_1123a.log; do sleep 30; done
step() { echo "=== $(date +%H:%M:%S) $*"; "$@" 2>&1 | grep -vE "Warning|Loading weights|warn\(|^\s+(train|dev)  "; echo "=== exit ${PIPESTATUS[0]}"; }
rr() {
  for i in $(seq 1 10); do
    echo "=== $(date +%H:%M:%S) attempt $i: $*"
    $PY reason_rerank.py --backend bnb --bits 4 --batch 4 --chunk 2000 --pool 50 \
      --data $D --kit $K --out $R/reason "$@" 2>&1 \
      | grep -vE "Warning|warn\(|Loading weights" && [ ${PIPESTATUS[0]} -eq 0 ] && return 0
    sleep 60
  done
  echo "FAILED $*"
}
G=$R/guid
# G2 generations first (vLLM needs the whole GPU): all 1a + 1b train/dev inputs with g, one generate() per prompt
step $LPY llm_expand.py --data $D --track 1 --conditions 1a_g 1b_query+step_g --merge-conditions --prompts reason hyde --chunk 100000 --gpu-util 0.6 --max-seqs 64 --max-batched 2048 --out $G/llm/t1
echo "=== $(date +%H:%M:%S) G2_LLM_DONE"
# G1: main generations + g
step $PY qexp_search.py --data $D --kit $K --track 1 --cond 1a --variants q+r+h+g --llm $R/llm/t1 --model bge-small --max-len 256 --emb $E --out $G/t1
step $PY qexp_search.py --data $D --kit $K --track 1 --cond 1b_query+step --variants q+r+h+g --llm $R/llm/t1 --model bge-small --max-len 256 --emb $E --out $G/t1
# G2: new generations + g
step $PY qexp_search.py --data $D --kit $K --track 1 --cond 1a_g --query-cond 1a --variants q+r+h+g --llm $G/llm/t1 --model bge-small --max-len 256 --emb $E --out $G/t1
step $PY qexp_search.py --data $D --kit $K --track 1 --cond 1b_query+step_g --query-cond 1b_query+step --variants q+r+h+g --llm $G/llm/t1 --model bge-small --max-len 256 --emb $E --out $G/t1
echo "=== $(date +%H:%M:%S) G_QEXP_DONE"
step $PY hybrid.py --track 1 --conditions 1a__q+r+h+g 1a_g__q+r+h+g --bm25 $G/t1/bm25/runs --dense $G/t1/dense/runs --data $D --kit $K --out $G/t1/hybrid_1a.json
step $PY hybrid.py --track 1 --conditions 1b_query+step__q+r+h+g 1b_query+step_g__q+r+h+g --bm25 $G/t1/bm25/runs --dense $G/t1/dense/runs --data $D --kit $K --out $G/t1/hybrid_1b.json
echo "=== $(date +%H:%M:%S) G_HYBRID_DONE"
rr --track 1 --conditions 1a__q+r+h+g --query-cond 1a+g --name g_1a_G1 --hybrid $G/t1/hybrid_1a.json --bm25 $G/t1/bm25/runs --dense $G/t1/dense/runs --save-scores $R/scores/g_1a_G1.json
rr --track 1 --conditions 1a_g__q+r+h+g --query-cond 1a+g --name g_1a_G2 --hybrid $G/t1/hybrid_1a.json --bm25 $G/t1/bm25/runs --dense $G/t1/dense/runs --save-scores $R/scores/g_1a_G2.json
rr --track 1 --conditions 1b_query+step__q+r+h+g --query-cond 1b_query+step+g --name g_1b_G1 --hybrid $G/t1/hybrid_1b.json --bm25 $G/t1/bm25/runs --dense $G/t1/dense/runs --save-scores $R/scores/g_1b_G1.json
rr --track 1 --conditions 1b_query+step_g__q+r+h+g --query-cond 1b_query+step+g --name g_1b_G2 --hybrid $G/t1/hybrid_1b.json --bm25 $G/t1/bm25/runs --dense $G/t1/dense/runs --save-scores $R/scores/g_1b_G2.json
echo "=== $(date +%H:%M:%S) ALLDONE"
