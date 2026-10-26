#!/bin/bash
# Rule 8 (LOG 13:48, amended 16:07 and 16:21): ReasonEmbed-4B over the top-50 pool, NF4 (bitsandbytes) in-process,
# chunks of 2,000 documents saved after each; restarted automatically after a GPU failure (resumes from the cache).
source ~/semeval-reteco/.venv/bin/activate
cd ~/semeval-reteco/reteco-research/scripts
D=../../reteco_data_v11; K=../../RETECO/starter_kit; R=../research/runs_v13
run() {  # retry up to 20 times
  for i in $(seq 1 20); do
    echo "=== $(date +%H:%M:%S) attempt $i: $*"
    python reason_rerank.py --backend bnb --bits 4 --batch 4 --chunk 2000 --pool 50 --data $D --kit $K --out $R/reason "$@" 2>&1 \
      | grep -vE "Warning|warn\(|Loading weights" && [ ${PIPESTATUS[0]} -eq 0 ] && return 0
    sleep 60
  done
  echo "FAILED $*"
}
run --track 2 --conditions 2a_current__q+r+h --query-cond 2a_current --hybrid $R/maxp/t2/hybrid_2a_current.json --bm25 $R/maxp/t2/bm25/runs --dense $R/maxp/t2/dense/runs
run --track 1 --conditions 1a__q+r+h --query-cond 1a --hybrid $R/qexp/t1/hybrid_1a.json --bm25 $R/qexp/t1/bm25/runs --dense $R/qexp/t1/dense/runs
run --track 1 --conditions 1b_query+step__q+r+h --query-cond 1b_query+step --hybrid $R/qexp/t1/hybrid_1b.json --bm25 $R/qexp/t1/bm25/runs --dense $R/qexp/t1/dense/runs
echo "=== $(date +%H:%M:%S) ALLDONE"
