#!/bin/bash
# After model selection: window check on full train (rule 1), then cross-encoder (rule 3).
source ~/semeval-reteco/.venv/bin/activate
cd ~/semeval-reteco/reteco-research/scripts
D=../../reteco_data_v11; K=../../RETECO/starter_kit; R=../research/runs_v12
while pgrep -f select_queue.sh >/dev/null; do sleep 30; done
step() { echo "=== $(date +%H:%M:%S) $*"; "$@" 2>&1 | grep -vE "Warning|Loading weights|warn\(" || echo "FAILED: $*"; }
step python dense_index.py --data $D --track 2 --domains all --model bge-small --max-len 256 --batch 64 --out $R/emb
step python dense_index.py --data $D --track 1 --domains all --model bge-small --max-len 256 --batch 64 --out $R/emb
step python dense_search.py --data $D --kit $K --track 2 --splits train --model bge-small --max-len 256 --emb $R/emb --out $R/dense/bge-small_L256/t2
step python dense_search.py --data $D --kit $K --track 1 --splits train --model bge-small --max-len 256 --emb $R/emb --out $R/dense/bge-small_L256/t1
step python rerank_ce.py --track 2 --conditions 2a_current 2a_history --hybrid $R/hybrid/bge-small_L512_t2.json --bm25 $R/bm25/t2/runs --dense $R/dense/bge-small_L512/t2/runs --data $D --kit $K --out $R/ce
step python rerank_ce.py --track 1 --conditions 1a 1b_query+step --hybrid $R/hybrid/bge-small_L512_t1.json --bm25 $R/bm25/t1/runs --dense $R/dense/bge-small_L512/t1/runs --data $D --kit $K --out $R/ce
echo "=== $(date +%H:%M:%S) ALLDONE"
