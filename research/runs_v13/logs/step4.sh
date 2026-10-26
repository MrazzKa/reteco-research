#!/bin/bash
# Rule 6 (2a current): cross-encoder over the q+r+h hybrid; then ReasonEmbed speed test (rule 8).
source ~/semeval-reteco/.venv/bin/activate
cd ~/semeval-reteco/reteco-research/scripts
D=../../reteco_data_v11; K=../../RETECO/starter_kit; R=../research/runs_v13
step() { echo "=== $(date +%H:%M:%S) $*"; "$@" 2>&1 | grep -vE "Warning|Loading weights|warn\("; echo "=== exit ${PIPESTATUS[0]}"; }
while ! grep -q "hybrid.py --track" $R/logs/maxp_hyb_2a.log 2>/dev/null; do sleep 20; done   # step-3 GPU part done
mkdir -p $R/ce_final
for f in $R/ce/scores_t2_*_2a_current.json; do b=$(basename $f .json); cp -n $f $R/ce_final/${b}__q+r+h.json; done
step python rerank_ce.py --track 2 --conditions 2a_current__q+r+h --query-cond 2a_current --hybrid $R/qexp/t2/hybrid_2a_current.json --bm25 $R/qexp/t2/bm25/runs --dense $R/qexp/t2/dense/runs --data $D --kit $K --out $R/ce_final
step python reason_rerank.py --track 2 --conditions 2a_current__q+r+h --query-cond 2a_current --hybrid $R/qexp/t2/hybrid_2a_current.json --bm25 $R/qexp/t2/bm25/runs --dense $R/qexp/t2/dense/runs --data $D --kit $K --domains drones --splits dev --out $R/reason_speedtest
echo "=== $(date +%H:%M:%S) ALLDONE"
