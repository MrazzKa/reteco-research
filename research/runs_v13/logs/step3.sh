#!/bin/bash
# Week 5 step 3 (rule 7): MaxP dense (first window + passages) with every query variant; hybrids tuned on train.
source ~/semeval-reteco/.venv/bin/activate
cd ~/semeval-reteco/reteco-research/scripts
D=../../reteco_data_v11; K=../../RETECO/starter_kit; R=../research/runs_v13; E=../research/runs_v12/emb
step() { echo "=== $(date +%H:%M:%S) $*"; "$@" 2>&1 | grep -vE "Warning|Loading weights|warn\(|^\s+(train|dev)  "; echo "=== exit ${PIPESTATUS[0]}"; }
V="q q+r r q+h h q+r+h"
conds() { for v in $V; do printf "%s__%s " "$1" "$v"; done; }
while ! grep -q ALLDONE $R/logs/step2b.log; do sleep 30; done
step python qexp_search.py --data $D --kit $K --track 2 --cond 2a_current --llm $R/llm/t2 --model bge-base --max-len 512 --emb $E --passages $R/emb --out $R/maxp/t2
step python qexp_search.py --data $D --kit $K --track 1 --cond 1a --llm $R/llm/t1 --model bge-small --max-len 512 --emb $E --passages $R/emb --out $R/maxp/t1
step python qexp_search.py --data $D --kit $K --track 1 --cond 1b_query+step --llm $R/llm/t1 --model bge-small --max-len 512 --emb $E --passages $R/emb --out $R/maxp/t1
(step python hybrid.py --track 2 --conditions $(conds 2a_current) --bm25 $R/maxp/t2/bm25/runs --dense $R/maxp/t2/dense/runs --data $D --kit $K --out $R/maxp/t2/hybrid_2a_current.json > $R/logs/maxp_hyb_2a.log 2>&1) &
(step python hybrid.py --track 1 --conditions $(conds 1a) --bm25 $R/maxp/t1/bm25/runs --dense $R/maxp/t1/dense/runs --data $D --kit $K --out $R/maxp/t1/hybrid_1a.json > $R/logs/maxp_hyb_1a.log 2>&1) &
(step python hybrid.py --track 1 --conditions $(conds 1b_query+step) --bm25 $R/maxp/t1/bm25/runs --dense $R/maxp/t1/dense/runs --data $D --kit $K --out $R/maxp/t1/hybrid_1b.json > $R/logs/maxp_hyb_1b.log 2>&1) &
wait
echo "=== $(date +%H:%M:%S) ALLDONE"
