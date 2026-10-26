#!/bin/bash
# Rule 8 (LOG 13:48, amended 16:07): ReasonEmbed-4B (FP8, vLLM) over the top-50 pool of the adopted systems.
source ~/semeval-reteco/.venv/bin/activate
export CC=~/semeval-reteco/tools/bin/cc PATH=~/semeval-reteco/tools/bin:$PATH
cd ~/semeval-reteco/reteco-research/scripts
D=../../reteco_data_v11; K=../../RETECO/starter_kit; R=../research/runs_v13
step() { echo "=== $(date +%H:%M:%S) $*"; "$@" 2>&1 | grep -vE "Warning|warn\(|INFO|Loading weights"; echo "=== exit ${PIPESTATUS[0]}"; }
step python reason_rerank.py --track 2 --conditions 2a_current__q+r+h --query-cond 2a_current --hybrid $R/maxp/t2/hybrid_2a_current.json --bm25 $R/maxp/t2/bm25/runs --dense $R/maxp/t2/dense/runs --data $D --kit $K --pool 50 --out $R/reason
step python reason_rerank.py --track 1 --conditions 1a__q+r+h --query-cond 1a --hybrid $R/qexp/t1/hybrid_1a.json --bm25 $R/qexp/t1/bm25/runs --dense $R/qexp/t1/dense/runs --data $D --kit $K --pool 50 --out $R/reason
step python reason_rerank.py --track 1 --conditions 1b_query+step__q+r+h --query-cond 1b_query+step --hybrid $R/qexp/t1/hybrid_1b.json --bm25 $R/qexp/t1/bm25/runs --dense $R/qexp/t1/dense/runs --data $D --kit $K --pool 50 --out $R/reason
echo "=== $(date +%H:%M:%S) ALLDONE"
