#!/bin/bash
# 2026-11-02 step 5 / rule 13 for 1a (after the 2a retrieval, while the 2a hybrid grid runs on the CPU).
export CC=~/semeval-reteco/tools/bin/cc PATH=~/semeval-reteco/tools/bin:$PATH
cd ~/semeval-reteco/reteco-research/scripts
D=../../reteco_data_v11; K=../../RETECO/starter_kit; R=../research/runs_v13; E=../research/runs_v12/emb
PY=~/semeval-reteco/.venv/bin/python; LPY=~/semeval-reteco/.venv-llm/bin/python
step() { echo "=== $(date +%H:%M:%S) $*"; "$@" 2>&1 | grep -vE "Warning|Loading weights|warn\(|^\s+(train|dev)  "; echo "=== exit ${PIPESTATUS[0]}"; }
while ! grep -q "hybrid.py --track 2" $R/logs/step5_hyde.log; do sleep 15; done
for u in 0.75 0.65 0.55; do
  echo "=== $(date +%H:%M:%S) gen gpu-util $u"
  $LPY llm_expand.py --data $D --gpu-util $u --max-seqs 32 --max-batched 2048 --track 1 --conditions 1a --prompts hyde \
    --samples 5 --temperature 0.7 --out $R/llm/t1 2>&1 | grep -E "^\[|/[0-9]+ +chunk|Error|KV cache size" && [ ${PIPESTATUS[0]} -eq 0 ] && break
done
echo "=== $(date +%H:%M:%S) GEN_DONE"
step $PY qexp_search.py --data $D --kit $K --track 1 --cond 1a --variants q+r+h1s q+r+h3 q+r+h5 --llm $R/llm/t1 --model bge-small --max-len 256 --emb $E --out $R/hyde5/t1
step $PY hybrid.py --track 1 --conditions 1a__q+r+h1s 1a__q+r+h3 1a__q+r+h5 --bm25 $R/hyde5/t1/bm25/runs --dense $R/hyde5/t1/dense/runs --data $D --kit $K --out $R/hyde5/t1/hybrid.json
step $PY select_rule.py --rule 13 --cond 1a --baseline n1_t0 --cand "n1_t0=$R/qexp/t1/hybrid_1a.json:1a__q+r+h" "n3=$R/hyde5/t1/hybrid.json:1a__q+r+h3" "n5=$R/hyde5/t1/hybrid.json:1a__q+r+h5" --out $R/select/rule13_hybrid_1a.json
echo "=== $(date +%H:%M:%S) ALLDONE 1a"
