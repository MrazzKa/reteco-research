#!/bin/bash
# S3 input (2026-11-16): dev breakdown of M0 = the frozen main 2a pipeline (no reranker) on answer-free histories.
cd ~/semeval-reteco/reteco-research/scripts
D=../../reteco_data_v11; K=../../RETECO/starter_kit; R=../research/runs_v13; PY=~/semeval-reteco/.venv/bin/python
while ! grep -q "ALLDONE" $R/logs/queue_1116b.log; do sleep 15; done
T0=$(date +%s)
$PY make_test_release.py --data $D --out $R/sr/rel_noans --tracks 2 --strip-answers
CC=~/semeval-reteco/tools/bin/cc $PY submit.py --variants 2a_history --data $R/sr/rel_noans --split test --out $R/a2/sub_m0dev 2>&1 | grep -E "^\[|Error|Traceback"
$PY t2_breakdown.py --data $D --kit $K --split dev --only-run-topics --out $R/a2/m0_dev_breakdown.json \
  --run "main, reference answers=$R/submit/dev_1116/2a_history/{dom}.txt" \
  --run "main, LLM-written answers=$R/a2/sub_gen/dev/2a_history/{dom}.txt" \
  --run "M0 main pipeline, no answers=$R/a2/sub_m0dev/2a_history/{dom}.txt" \
  --run "no answers (rule 14, H0q+RE)=$R/submit/dev_1116/2a_history_q/{dom}.txt" \
  --run "current turn B=$R/submit/dev_1116/2a_nomaxp/{dom}.txt" | tail -12
echo "=== $(date +%H:%M:%S) ALLDONE $(( $(date +%s) - T0 )) s"
