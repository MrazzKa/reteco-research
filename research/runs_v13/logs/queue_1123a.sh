#!/bin/bash
# 2026-11-23 N1: query variants through the final system (analysis, no choice). GPU jobs one at a time.
cd ~/semeval-reteco/reteco-research/scripts
D=../../reteco_data_v11; K=../../RETECO/starter_kit; R=../research/runs_v13; E=../research/runs_v12/emb; PY=~/semeval-reteco/.venv/bin/python
step() { echo "=== $(date +%H:%M:%S) $*"; "$@" 2>&1 | grep -vE "Warning|Loading weights|warn\(|^\s+(train|dev)  "; echo "=== exit ${PIPESTATUS[0]}"; }
rr() {  # ReasonEmbed NF4, chunked, restartable
  for i in $(seq 1 10); do
    echo "=== $(date +%H:%M:%S) attempt $i: $*"
    $PY reason_rerank.py --backend bnb --bits 4 --batch 4 --chunk 2000 --pool 50 \
      --data $D --kit $K --out $R/reason "$@" 2>&1 \
      | grep -vE "Warning|warn\(|Loading weights" && [ ${PIPESTATUS[0]} -eq 0 ] && return 0
    sleep 60
  done
  echo "FAILED $*"
}
# history q+r and q+h (Hb generations), then their hybrids
step $PY qexp_search.py --data $D --kit $K --track 2 --cond 2a_hist3qa --query-cond 2a_history_qfirst --variants q+r q+h --llm $R/llm/t2 --model bge-base --max-len 512 --emb $E --out $R/hist/t2
step $PY hybrid.py --track 2 --conditions 2a_hist3qa__q+r 2a_hist3qa__q+h --bm25 $R/hist/t2/bm25/runs --dense $R/hist/t2/dense/runs --data $D --kit $K --out $R/hist/t2/hybrid_n1.json
echo "=== $(date +%H:%M:%S) N1_HYBRID_DONE"
rr --track 2 --conditions 2a_hist3qa__q+r --query-cond 2a_hist3qa --name n1_2ah_qr --hybrid $R/hist/t2/hybrid_n1.json --bm25 $R/hist/t2/bm25/runs --dense $R/hist/t2/dense/runs --save-scores $R/scores/n1_2ah_qr.json
rr --track 2 --conditions 2a_hist3qa__q+h --query-cond 2a_hist3qa --name n1_2ah_qh --hybrid $R/hist/t2/hybrid_n1.json --bm25 $R/hist/t2/bm25/runs --dense $R/hist/t2/dense/runs --save-scores $R/scores/n1_2ah_qh.json
rr --track 2 --conditions 2a_current__q+r --query-cond 2a_current --name n1_2a_qr --hybrid $R/qexp/t2/hybrid_2a_current.json --bm25 $R/qexp/t2/bm25/runs --dense $R/qexp/t2/dense/runs --save-scores $R/scores/n1_2a_qr.json
rr --track 2 --conditions 2a_current__q+h --query-cond 2a_current --name n1_2a_qh --hybrid $R/qexp/t2/hybrid_2a_current.json --bm25 $R/qexp/t2/bm25/runs --dense $R/qexp/t2/dense/runs --save-scores $R/scores/n1_2a_qh.json
echo "=== $(date +%H:%M:%S) N1_T2_DONE"
for v in q q+r q+h; do
  n=$(echo $v | sed 's/+//g')
  rr --track 1 --conditions 1a__$v --query-cond 1a --name n1_1a_$n --hybrid $R/qexp/t1/hybrid_1a.json --bm25 $R/qexp/t1/bm25/runs --dense $R/qexp/t1/dense/runs --save-scores $R/scores/n1_1a_$n.json
done
echo "=== $(date +%H:%M:%S) N1_1A_DONE"
for v in q q+r q+h; do
  n=$(echo $v | sed 's/+//g')
  rr --track 1 --conditions 1b_query+step__$v --query-cond 1b_query+step --name n1_1b_$n --hybrid $R/qexp/t1/hybrid_1b.json --bm25 $R/qexp/t1/bm25/runs --dense $R/qexp/t1/dense/runs --save-scores $R/scores/n1_1b_$n.json
done
echo "=== $(date +%H:%M:%S) ALLDONE"
