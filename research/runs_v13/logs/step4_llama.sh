#!/bin/bash
# 2026-11-02 step 4 (ablation, no choice): retrieval + hybrid grids with the Llama-3.2-3B generations.
source ~/semeval-reteco/.venv/bin/activate
cd ~/semeval-reteco/reteco-research/scripts
D=../../reteco_data_v11; K=../../RETECO/starter_kit; R=../research/runs_v13; E=../research/runs_v12/emb
M=unsloth/Llama-3.2-3B-Instruct
step() { echo "=== $(date +%H:%M:%S) $*"; "$@" 2>&1 | grep -vE "Warning|Loading weights|warn\(|^\s+(train|dev)  "; echo "=== exit ${PIPESTATUS[0]}"; }
while ! grep -q "=== .* ALLDONE" $R/logs/queue_1102.log; do sleep 20; done
step python qexp_search.py --data $D --kit $K --track 2 --cond 2a_current --variants q+r+h --llm $R/llm_llama/t2 --llm-model $M --model bge-base --max-len 512 --emb $E --out $R/llama/t2
step python qexp_search.py --data $D --kit $K --track 1 --cond 1a --variants q+r+h --llm $R/llm_llama/t1 --llm-model $M --model bge-small --max-len 256 --emb $E --out $R/llama/t1
(step python hybrid.py --track 2 --conditions 2a_current__q+r+h --bm25 $R/llama/t2/bm25/runs --dense $R/llama/t2/dense/runs --data $D --kit $K --out $R/llama/t2/hybrid.json > $R/logs/llama_hyb_2a.log 2>&1) &
(step python hybrid.py --track 1 --conditions 1a__q+r+h --bm25 $R/llama/t1/bm25/runs --dense $R/llama/t1/dense/runs --data $D --kit $K --out $R/llama/t1/hybrid.json > $R/logs/llama_hyb_1a.log 2>&1) &
wait
echo "=== $(date +%H:%M:%S) ALLDONE"
