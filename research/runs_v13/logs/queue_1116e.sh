#!/bin/bash
# Rule 19, S3 (LOG 2026-11-16 15:12): the LLM sees subquestion_reasoning. After queue_1116c (M0).
cd ~/semeval-reteco/reteco-research/scripts
D=../../reteco_data_v11; K=../../RETECO/starter_kit; R=../research/runs_v13; E=../research/runs_v12/emb; PY=~/semeval-reteco/.venv/bin/python; LPY=~/semeval-reteco/.venv-llm/bin/python
step() { echo "=== $(date +%H:%M:%S) $*"; "$@" 2>&1 | grep -vE "Warning|Loading weights|warn\(|it/s\]|^\s+(train|dev)  "; echo "=== $(date +%H:%M:%S) exit ${PIPESTATUS[0]}"; }
while ! grep -q "ALLDONE" $R/logs/queue_1116c.log; do sleep 15; done
T0=$(date +%s)
export CC=~/semeval-reteco/tools/bin/cc
for u in 0.75 0.65 0.55; do
  echo "=== $(date +%H:%M:%S) gen gpu-util $u"
  $LPY llm_expand.py --data $D --gpu-util $u --max-seqs 64 --max-batched 2048 --track 2 --conditions 2a_hist3qa_sr \
    --chunk 100000 --out $R/llm/t2 2>&1 | grep -E "^\[|/[0-9]+ +chunk|Error|KV cache size|generated|done" && [ ${PIPESTATUS[0]} -eq 0 ] && break
done
echo "=== $(date +%H:%M:%S) GEN_DONE $(( $(date +%s) - T0 )) s"
step $PY qexp_search.py --data $D --kit $K --track 2 --cond 2a_hist3qa_sr --query-cond 2a_history_qfirst --variants q+r+h --llm $R/llm/t2 --model bge-base --max-len 512 --emb $E --out $R/sr/t2
step $PY hybrid.py --track 2 --conditions 2a_hist3qa_sr__q+r+h --bm25 $R/sr/t2/bm25/runs --dense $R/sr/t2/dense/runs --data $D --kit $K --out $R/sr/t2/hybrid_s3.json
step $PY reason_rerank.py --backend bnb --bits 4 --batch 4 --chunk 2000 --pool 50 --track 2 --hybrid $R/sr/t2/hybrid_s3.json --bm25 $R/sr/t2/bm25/runs --dense $R/sr/t2/dense/runs --data $D --kit $K --out $R/reason --conditions 2a_hist3qa_sr__q+r+h --query-cond 2a_hist3qa+sr --name sr_S3 --save-scores $R/scores/sr_sr_S3.json --save-runs $R/sr/runs
echo "=== $(date +%H:%M:%S) RE_S3_DONE $(( $(date +%s) - T0 )) s"
step $PY llm_rerank.py --model qwen3-reranker-0.6b --bits 16 --cond 2a_history_sr --data $D --kit $K --out $R/rerank --save-runs $R/rerank/runs --batch 4 --name sr_S3 --scores $R/scores/sr_sr_S3.json
echo "=== $(date +%H:%M:%S) ALLDONE $(( $(date +%s) - T0 )) s"
