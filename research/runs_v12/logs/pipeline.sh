#!/bin/bash
# Everything downstream of the bge-small L512 caches, float32 scoring.
source ~/semeval-reteco/.venv/bin/activate
cd ~/semeval-reteco/reteco-research/scripts
D=../../reteco_data_v11; K=../../RETECO/starter_kit; R=../research/runs_v12
step() { echo "=== $(date +%H:%M:%S) $*"; "$@" 2>&1 | grep -vE "Warning|Loading weights|warn\(" || echo "FAILED: $*"; }
step python dense_search.py --data $D --kit $K --track 2 --model bge-small --max-len 512 --emb $R/emb --out $R/dense/bge-small_L512/t2
step python hybrid.py --track 2 --conditions 2a_current 2a_history --dense-cond 2a_current 2a_history_qfirst --bm25 $R/bm25/t2/runs --dense $R/dense/bge-small_L512/t2/runs --data $D --kit $K --out $R/hybrid/bge-small_L512_t2.json
step python history_leak.py --data $D --kit $K --bm25 $R/bm25/t2/runs --dense $R/dense/bge-small_L512/t2/runs --out $R/history_leak.json
step python order_study.py --data $D --kit $K --track 2 --domains biology drones earth_science economics hardware law medicalsciences politics psychology robotics sustainable_living --emb $R/emb --perms 5 --ann-domains drones biology earth_science --out $R/order/t2.json
step python ann_eval.py --data $D --kit $K --track 2 --emb $R/emb --out $R/ann/bge-small_L512_t2.json
while kill -0 5205 2>/dev/null; do sleep 20; done
step python dense_search.py --data $D --kit $K --track 1 --model bge-small --max-len 512 --emb $R/emb --out $R/dense/bge-small_L512/t1
step python dense_search.py --data $D --kit $K --track 1 --domains iota --model bge-small --max-len 256 --emb $R/emb --out $R/dense/bge-small_L256/t1
step python hybrid.py --track 1 --conditions 1a 1b_query+step --bm25 $R/bm25/t1/runs --dense $R/dense/bge-small_L512/t1/runs --data $D --kit $K --out $R/hybrid/bge-small_L512_t1.json
step python gold_categories.py --data $D --bm25 $R/bm25 --dense $R/dense/bge-small_L512 --out $R/categories
step python order_study.py --data $D --kit $K --track 1 --domains iota quant law workplace cardano --emb $R/emb --perms 5 --ann-domains law cardano --out $R/order/t1.json
step python ann_eval.py --data $D --kit $K --track 1 --emb $R/emb --out $R/ann/bge-small_L512_t1.json
echo "=== $(date +%H:%M:%S) ALLDONE"
