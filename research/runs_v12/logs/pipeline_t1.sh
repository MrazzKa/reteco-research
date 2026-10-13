#!/bin/bash
# Everything downstream of the bge-small L512 caches, float32 scoring.
source ~/semeval-reteco/.venv/bin/activate
cd ~/semeval-reteco/reteco-research/scripts
D=../../reteco_data_v11; K=../../RETECO/starter_kit; R=../research/runs_v12
step() { echo "=== $(date +%H:%M:%S) $*"; "$@" 2>&1 | grep -vE "Warning|Loading weights|warn\(" || echo "FAILED: $*"; }
step python dense_search.py --data $D --kit $K --track 1 --model bge-small --max-len 512 --emb $R/emb --out $R/dense/bge-small_L512/t1
step python dense_search.py --data $D --kit $K --track 1 --domains iota --model bge-small --max-len 256 --emb $R/emb --out $R/dense/bge-small_L256/t1
step python hybrid.py --track 1 --conditions 1a 1b_query+step --bm25 $R/bm25/t1/runs --dense $R/dense/bge-small_L512/t1/runs --data $D --kit $K --out $R/hybrid/bge-small_L512_t1.json
step python gold_categories.py --data $D --bm25 $R/bm25 --dense $R/dense/bge-small_L512 --out $R/categories
step python order_study.py --data $D --kit $K --track 1 --domains iota quant law workplace cardano --emb $R/emb --perms 5 --ann-domains law cardano --out $R/order/t1.json
step python ann_eval.py --data $D --kit $K --track 1 --emb $R/emb --out $R/ann/bge-small_L512_t1.json
echo "=== $(date +%H:%M:%S) ALLDONE"
