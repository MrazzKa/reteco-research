#!/bin/bash
# 2026-11-02 step 5 / rule 13: several sampled HyDE passages for the rule-12 main 2a condition.
export CC=~/semeval-reteco/tools/bin/cc PATH=~/semeval-reteco/tools/bin:$PATH
cd ~/semeval-reteco/reteco-research/scripts
D=../../reteco_data_v11; K=../../RETECO/starter_kit; R=../research/runs_v13; E=../research/runs_v12/emb
PY=~/semeval-reteco/.venv/bin/python; LPY=~/semeval-reteco/.venv-llm/bin/python
step() { echo "=== $(date +%H:%M:%S) $*"; "$@" 2>&1 | grep -vE "Warning|Loading weights|warn\(|^\s+(train|dev)  "; echo "=== exit ${PIPESTATUS[0]}"; }
while ! grep -qE "ALLDONE" $R/logs/step3b_hist_reason.log; do sleep 15; done
step $PY foreign_gold.py --data $D --kit $K --runs $R --conditions 2a_history --out $R/foreign/report.json
step $PY final_1102.py --runs $R
DEC=$($PY -c "import json;print(json.load(open('$R/select/rule12.json'))['decision'])")
echo "=== rule 12: $DEC"
if [[ "$DEC" == *history* ]]; then C=2a_hist3qa; QC="--query-cond 2a_history_qfirst"; BASE="$R/hist/t2/hybrid.json:2a_hist3qa__q+r+h"
else C=2a_current; QC=""; BASE="$R/qexp/t2/hybrid_2a_current.json:2a_current__q+r+h"; fi
for u in 0.75 0.65 0.55; do
  echo "=== $(date +%H:%M:%S) gen gpu-util $u"
  $LPY llm_expand.py --data $D --gpu-util $u --max-seqs 32 --max-batched 2048 --track 2 --conditions $C --prompts hyde \
    --samples 5 --temperature 0.7 --out $R/llm/t2 2>&1 | grep -E "^\[|/[0-9]+ +chunk|Error|KV cache size" && [ ${PIPESTATUS[0]} -eq 0 ] && break
done
echo "=== $(date +%H:%M:%S) GEN_DONE"
step $PY qexp_search.py --data $D --kit $K --track 2 --cond $C $QC --variants q+r+h1s q+r+h3 q+r+h5 --llm $R/llm/t2 --model bge-base --max-len 512 --emb $E --out $R/hyde5/t2
step $PY hybrid.py --track 2 --conditions ${C}__q+r+h1s ${C}__q+r+h3 ${C}__q+r+h5 --bm25 $R/hyde5/t2/bm25/runs --dense $R/hyde5/t2/dense/runs --data $D --kit $K --out $R/hyde5/t2/hybrid.json
step $PY select_rule.py --rule 13 --cond $C --baseline n1_t0 --cand "n1_t0=$BASE" "n3=$R/hyde5/t2/hybrid.json:${C}__q+r+h3" "n5=$R/hyde5/t2/hybrid.json:${C}__q+r+h5" --out $R/select/rule13_hybrid.json
echo "=== $(date +%H:%M:%S) ALLDONE $C"
