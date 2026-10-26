#!/bin/bash
# Week 5 step 1: final systems re-run with the sha1(doc id) tie key (LOG 2026-10-26 13:45).
source ~/semeval-reteco/.venv/bin/activate
cd ~/semeval-reteco/reteco-research/scripts
D=../../reteco_data_v11; K=../../RETECO/starter_kit; R=../research/runs_v13; E=../research/runs_v12/emb
step() { echo "=== $(date +%H:%M:%S) $*"; "$@" 2>&1 | grep -vE "Warning|Loading weights|warn\("; echo "=== exit ${PIPESTATUS[0]}"; }
step python bm25s_run.py --data $D --kit $K --splits train dev --track 2 --domains biology drones earth_science economics hardware law medicalsciences politics psychology robotics sustainable_living --k 1000 --conditions 2a_current 2a_history --threads 8 --out $R/bm25/t2
step python bm25s_run.py --data $D --kit $K --splits train dev --track 1 --domains iota quant law workplace cardano monero economics bitcoin politics genealogy travel hsm history --k 1000 --conditions 1a 1b_query+step --threads 8 --out $R/bm25/t1
step python dense_search.py --data $D --kit $K --track 2 --model bge-base --max-len 512 --emb $E --out $R/dense/bge-base_L512/t2
step python dense_search.py --data $D --kit $K --track 1 --model bge-small --max-len 256 --emb $E --out $R/dense/bge-small_L256/t1
step python hybrid.py --track 2 --conditions 2a_current 2a_history --dense-cond 2a_current 2a_history_qfirst --bm25 $R/bm25/t2/runs --dense $R/dense/bge-base_L512/t2/runs --data $D --kit $K --out $R/hybrid/bge-base_L512_t2.json
step python hybrid.py --track 1 --conditions 1a 1b_query+step --bm25 $R/bm25/t1/runs --dense $R/dense/bge-small_L256/t1/runs --data $D --kit $K --out $R/hybrid/bge-small_L256_t1.json
mkdir -p $R/ce; cp -n ../research/runs_v12/ce_bge-base/scores_*.json $R/ce/
step python rerank_ce.py --track 2 --conditions 2a_current --hybrid $R/hybrid/bge-base_L512_t2.json --bm25 $R/bm25/t2/runs --dense $R/dense/bge-base_L512/t2/runs --data $D --kit $K --out $R/ce
echo "=== $(date +%H:%M:%S) ALLDONE"
