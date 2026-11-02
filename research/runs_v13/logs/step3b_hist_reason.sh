#!/bin/bash
# 2026-11-02 step 3 / rule 11, second stage: ReasonEmbed over the top 50 of the rule-11 hybrid (GPU, after the queue).
cd ~/semeval-reteco/reteco-research/scripts
D=../../reteco_data_v11; K=../../RETECO/starter_kit; R=../research/runs_v13; PY=~/semeval-reteco/.venv/bin/python
while ! grep -q ALLDONE $R/logs/step3_hist.log; do sleep 20; done
[ -f $R/select/rule11.json ] || $PY rule11_choice.py --runs $R --out $R/select/rule11.json > $R/logs/rule11_choice.log 2>&1
CH=$($PY -c "import json;print(json.load(open('$R/select/rule11.json'))['chosen'])")
echo "=== $(date +%H:%M:%S) rule 11 hybrid choice: $CH"
case $CH in
  H0) ARGS="--conditions 2a_history --query-cond 2a_hist3q --hybrid $R/hybrid/bge-base_L512_t2.json --bm25 $R/bm25/t2/runs --dense $R/dense/bge-base_L512/t2/runs";;
  Ha) ARGS="--conditions 2a_hist3q__q+r+h --query-cond 2a_hist3q --hybrid $R/hist/t2/hybrid.json --bm25 $R/hist/t2/bm25/runs --dense $R/hist/t2/dense/runs";;
  Hb) ARGS="--conditions 2a_hist3qa__q+r+h --query-cond 2a_hist3qa --hybrid $R/hist/t2/hybrid.json --bm25 $R/hist/t2/bm25/runs --dense $R/hist/t2/dense/runs";;
esac
while ! grep -q "=== .* ALLDONE" $R/logs/queue_1102.log; do sleep 20; done
for i in $(seq 1 10); do
  echo "=== $(date +%H:%M:%S) attempt $i: $ARGS"
  $PY reason_rerank.py --backend bnb --bits 4 --batch 4 --chunk 2000 --pool 50 --track 2 --name 2ah_hybrid \
    --data $D --kit $K --out $R/reason --save-runs $R/foreign/runs $ARGS 2>&1 \
    | grep -vE "Warning|warn\(|Loading weights" && [ ${PIPESTATUS[0]} -eq 0 ] && break
  sleep 60
done
echo "=== $(date +%H:%M:%S) ALLDONE"
