#!/bin/bash
# Rule 2 (LOG 16:35): bge-base won the train selection (section G) -> full index, dense, hybrid tuned on train, dev once.
source ~/semeval-reteco/.venv/bin/activate
cd ~/semeval-reteco/reteco-research/scripts
D=../../reteco_data_v11; K=../../RETECO/starter_kit; R=../research/runs_v12
while pgrep -f queue2.sh >/dev/null; do sleep 30; done
step() { echo "=== $(date +%H:%M:%S) $*"; "$@" 2>&1 | grep -vE "Warning|Loading weights|warn\("; echo "=== exit ${PIPESTATUS[0]}"; }
step python dense_index.py --data $D --track 2 --domains all --model bge-base --max-len 512 --batch 64 --out $R/emb
step python dense_index.py --data $D --track 1 --domains all --model bge-base --max-len 512 --batch 64 --out $R/emb
step python dense_search.py --data $D --kit $K --track 2 --model bge-base --max-len 512 --emb $R/emb --out $R/dense/bge-base_L512/t2
step python dense_search.py --data $D --kit $K --track 1 --model bge-base --max-len 512 --emb $R/emb --out $R/dense/bge-base_L512/t1
step python hybrid.py --track 2 --conditions 2a_current 2a_history --dense-cond 2a_current 2a_history_qfirst --bm25 $R/bm25/t2/runs --dense $R/dense/bge-base_L512/t2/runs --data $D --kit $K --out $R/hybrid/bge-base_L512_t2.json
step python hybrid.py --track 1 --conditions 1a 1b_query+step --bm25 $R/bm25/t1/runs --dense $R/dense/bge-base_L512/t1/runs --data $D --kit $K --out $R/hybrid/bge-base_L512_t1.json
echo "=== $(date +%H:%M:%S) ALLDONE"
