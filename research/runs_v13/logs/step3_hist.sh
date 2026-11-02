#!/bin/bash
# 2026-11-02 step 3 / rule 11: week-5 pipeline for 2a with history (retrieval + hybrid grids + choice).
source ~/semeval-reteco/.venv/bin/activate
cd ~/semeval-reteco/reteco-research/scripts
D=../../reteco_data_v11; K=../../RETECO/starter_kit; R=../research/runs_v13; E=../research/runs_v12/emb
step() { echo "=== $(date +%H:%M:%S) $*"; "$@" 2>&1 | grep -vE "Warning|Loading weights|warn\(|^\s+(train|dev)  "; echo "=== exit ${PIPESTATUS[0]}"; }
while ! grep -q HISTGEN_DONE $R/logs/queue_1102.log; do sleep 20; done
step python qexp_search.py --data $D --kit $K --track 2 --cond 2a_hist3q --query-cond 2a_history_qfirst --variants q q+r+h --llm $R/llm/t2 --model bge-base --max-len 512 --emb $E --out $R/hist/t2
step python qexp_search.py --data $D --kit $K --track 2 --cond 2a_hist3qa --query-cond 2a_history_qfirst --variants q+r+h --llm $R/llm/t2 --model bge-base --max-len 512 --emb $E --out $R/hist/t2
step python hybrid.py --track 2 --conditions 2a_hist3q__q 2a_hist3q__q+r+h 2a_hist3qa__q+r+h --bm25 $R/hist/t2/bm25/runs --dense $R/hist/t2/dense/runs --data $D --kit $K --out $R/hist/t2/hybrid.json
step python select_rule.py --rule 11 --cond 2a_history --baseline H0 --cand "H0=$R/hybrid/bge-base_L512_t2.json:2a_history" "Ha=$R/hist/t2/hybrid.json:2a_hist3q__q+r+h" "Hb=$R/hist/t2/hybrid.json:2a_hist3qa__q+r+h" --out $R/select/rule11_hybrid.json
step python select_rule.py --rule 11 --cond 2a_history --baseline Ha --cand "Ha=$R/hist/t2/hybrid.json:2a_hist3q__q+r+h" "Hb=$R/hist/t2/hybrid.json:2a_hist3qa__q+r+h" --out $R/select/rule11_a_vs_b.json
echo "=== $(date +%H:%M:%S) ALLDONE"
