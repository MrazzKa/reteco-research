#!/bin/bash
# 2026-11-10 A2 (LLM-written earlier answers, analysis) then the A4 reranker speed test; after queue_1110a.
export CC=~/semeval-reteco/tools/bin/cc PATH=~/semeval-reteco/tools/bin:$PATH
cd ~/semeval-reteco/reteco-research/scripts
D=../../reteco_data_v11; K=../../RETECO/starter_kit; R=../research/runs_v13; PY=~/semeval-reteco/.venv/bin/python; LPY=~/semeval-reteco/.venv-llm/bin/python
step() { echo "=== $(date +%H:%M:%S) $*"; "$@" 2>&1 | grep -vE "Warning|Loading weights|warn\(|it/s\]|^\s*$"; echo "=== exit ${PIPESTATUS[0]}"; }
while ! grep -q "ALLDONE" $R/logs/queue_1110a.log; do sleep 20; done
for i in 1 2 3; do step $LPY gen_answers.py --phase generate --data $D --out $R/a2 --gpu-util 0.6 && grep -q "^round" $R/logs/queue_1110b.log && break; sleep 30; done
step $PY gen_answers.py --phase build --data $D --out $R/a2
step $PY submit.py --variants 2a_history --data $R/a2/data_gen --split trainsub --out $R/a2/sub_gen/trainsub
step $PY submit.py --variants 2a_history --data $R/a2/data_gen --split dev --out $R/a2/sub_gen/dev
step $PY submit.py --variants 2a_history --data $R/a2/data_ref --split trainsub --out $R/a2/sub_ref/trainsub
echo "=== $(date +%H:%M:%S) A2_DONE"
# A1 check: synthetic test releases (dev topics, gold fields removed, split "test"), with / without earlier answers
S=/tmp/claude-1000/-home-timur-rk-semeval-reteco-reteco-research/66c24e1b-08a2-4f47-8e91-486a1a618555/scratchpad
step $PY submit.py --variants 2a_auto --data $S/rel_with --split test --out $S/sub_with
step $PY submit.py --variants 2a_auto --data $S/rel_without --split test --out $S/sub_without
echo "=== $(date +%H:%M:%S) A1_SYNTH_DONE"
step $PY llm_rerank.py --cond 2a_history --scores $R/scores/2ah_hybrid.json --data $D --kit $K --out $R/rerank --limit 200 --batch 4
echo "=== $(date +%H:%M:%S) ALLDONE"
