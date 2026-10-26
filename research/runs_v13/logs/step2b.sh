#!/bin/bash
# Week 5 steps 2-3 (restart after the Track-2 qid fix; 1a from step2.sh is kept): retrieval with LLM expansions (rule 6), hybrids tuned on train, passage index (rule 7).
source ~/semeval-reteco/.venv/bin/activate
cd ~/semeval-reteco/reteco-research/scripts
D=../../reteco_data_v11; K=../../RETECO/starter_kit; R=../research/runs_v13; E=../research/runs_v12/emb
step() { echo "=== $(date +%H:%M:%S) $*"; "$@" 2>&1 | grep -vE "Warning|Loading weights|warn\(|^\s+(train|dev)  "; echo "=== exit ${PIPESTATUS[0]}"; }
V="q q+r r q+h h q+r+h"
conds() { for v in $V; do printf "%s__%s " "$1" "$v"; done; }
while pgrep -f "qexp_search.py.*--cond 1a " >/dev/null; do sleep 15; done
step python qexp_search.py --data $D --kit $K --track 2 --cond 2a_current --llm $R/llm/t2 --model bge-base --max-len 512 --emb $E --out $R/qexp/t2
step python qexp_search.py --data $D --kit $K --track 1 --cond 1b_query+step --llm $R/llm/t1 --model bge-small --max-len 256 --emb $E --out $R/qexp/t1
# hybrids on CPU in parallel while the GPU builds the passage index
(step python hybrid.py --track 2 --conditions $(conds 2a_current) --bm25 $R/qexp/t2/bm25/runs --dense $R/qexp/t2/dense/runs --data $D --kit $K --out $R/qexp/t2/hybrid_2a_current.json > $R/logs/hyb_2a.log 2>&1) &
(step python hybrid.py --track 1 --conditions $(conds 1a) --bm25 $R/qexp/t1/bm25/runs --dense $R/qexp/t1/dense/runs --data $D --kit $K --out $R/qexp/t1/hybrid_1a.json > $R/logs/hyb_1a.log 2>&1) &
(step python hybrid.py --track 1 --conditions $(conds 1b_query+step) --bm25 $R/qexp/t1/bm25/runs --dense $R/qexp/t1/dense/runs --data $D --kit $K --out $R/qexp/t1/hybrid_1b.json > $R/logs/hyb_1b.log 2>&1) &
step python passage_index.py --data $D --track 2 --model bge-base --first $E --out $R/emb
step python passage_index.py --data $D --track 1 --model bge-small --first $E --out $R/emb
wait
echo "=== $(date +%H:%M:%S) ALLDONE"
