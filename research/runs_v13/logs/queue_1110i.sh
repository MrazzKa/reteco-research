#!/bin/bash
# 2026-11-10 B4 / rule 13 for 1b, second stage: ReasonEmbed over the top 50 of the n = 5 HyDE hybrid.
cd ~/semeval-reteco/reteco-research/scripts
D=../../reteco_data_v11; K=../../RETECO/starter_kit; R=../research/runs_v13; PY=~/semeval-reteco/.venv/bin/python
for i in $(seq 1 6); do
  echo "=== $(date +%H:%M:%S) attempt $i"
  $PY reason_rerank.py --backend bnb --bits 4 --batch 4 --chunk 2000 --pool 50 --track 1 \
    --conditions 1b_query+step__q+r+h5 --query-cond 1b_query+step --name 1b_h5 --hybrid $R/hyde5/t1/hybrid_1b.json \
    --bm25 $R/hyde5/t1/bm25/runs --dense $R/hyde5/t1/dense/runs --data $D --kit $K --out $R/reason \
    --save-runs $R/foreign/runs --save-scores $R/scores/1b_h5.json 2>&1 | grep --line-buffered -vE "Warning|warn\(|Loading weights" \
    && [ ${PIPESTATUS[0]} -eq 0 ] && break
  sleep 60
done
echo "=== $(date +%H:%M:%S) ALLDONE"
