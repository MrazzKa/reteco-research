#!/bin/bash
# Rule 19 (LOG 2026-11-16 14:26): subquestion_reasoning (SR) as a separate 2a run. Waits for the S1 dev check.
cd ~/semeval-reteco/reteco-research/scripts
D=../../reteco_data_v11; K=../../RETECO/starter_kit; R=../research/runs_v13; E=../research/runs_v12/emb; PY=~/semeval-reteco/.venv/bin/python
step() { echo "=== $(date +%H:%M:%S) $*"; "$@" 2>&1 | grep -vE "Warning|Loading weights|warn\(|it/s\]|^\s+(train|dev)  "; echo "=== $(date +%H:%M:%S) exit ${PIPESTATUS[0]}"; }
while ! grep -q ALLDONE $R/logs/queue_1116a.log; do sleep 15; done
T0=$(date +%s)
step $PY qexp_search.py --data $D --kit $K --track 2 --cond 2a_hist3qa --query-cond 2a_history_qfirst --variants q+r+h+s q+s+h --llm $R/llm/t2 --model bge-base --max-len 512 --emb $E --out $R/sr/t2
step $PY qexp_search.py --data $D --kit $K --track 2 --cond 2a_current --variants q+r+h+s s --llm $R/llm/t2 --model bge-base --max-len 512 --emb $E --out $R/sr/t2
echo "=== $(date +%H:%M:%S) SEARCH_DONE $(( $(date +%s) - T0 )) s"
step $PY hybrid.py --track 2 --conditions 2a_hist3qa__q+r+h+s 2a_hist3qa__q+s+h 2a_current__q+r+h+s 2a_current__s --bm25 $R/sr/t2/bm25/runs --dense $R/sr/t2/dense/runs --data $D --kit $K --out $R/sr/t2/hybrid.json
echo "=== $(date +%H:%M:%S) HYBRID_DONE $(( $(date +%s) - T0 )) s"
RE="--backend bnb --bits 4 --batch 4 --chunk 2000 --pool 50 --track 2 --hybrid $R/sr/t2/hybrid.json --bm25 $R/sr/t2/bm25/runs --dense $R/sr/t2/dense/runs --data $D --kit $K --out $R/reason"
step $PY reason_rerank.py $RE --conditions 2a_hist3qa__q+r+h+s 2a_hist3qa__q+s+h --query-cond 2a_hist3qa+sr 2a_hist3qa+sr --name sr_S1 sr_S2 --save-scores $R/scores/sr.json --save-runs $R/sr/runs
echo "=== $(date +%H:%M:%S) RE_HIST_DONE $(( $(date +%s) - T0 )) s"
RR="--model qwen3-reranker-0.6b --bits 16 --cond 2a_history_sr --data $D --kit $K --out $R/rerank --save-runs $R/rerank/runs --batch 4"
step $PY llm_rerank.py $RR --name sr_S1 --scores $R/scores/sr_sr_S1.json
echo "=== $(date +%H:%M:%S) RR_S1_DONE $(( $(date +%s) - T0 )) s"
step $PY llm_rerank.py $RR --name sr_S2 --scores $R/scores/sr_sr_S2.json
echo "=== $(date +%H:%M:%S) RR_S2_DONE $(( $(date +%s) - T0 )) s"
step $PY reason_rerank.py $RE --conditions 2a_current__q+r+h+s 2a_current__s --query-cond 2a_current+sr sr_only --name sr_cur sr_only --save-scores $R/scores/srx.json --save-runs $R/sr/runs
echo "=== $(date +%H:%M:%S) ALLDONE $(( $(date +%s) - T0 )) s"
