#!/bin/bash
# S1 (2026-11-16): dev check of the submission without pool 100 (warm caches).
cd ~/semeval-reteco/reteco-research/scripts
D=../../reteco_data_v11; K=../../RETECO/starter_kit; R=../research/runs_v13; PY=~/semeval-reteco/.venv/bin/python
O=$R/submit/dev_1116
T0=$(date +%s)
CC=~/semeval-reteco/tools/bin/cc $PY submit.py --variants 1a 1a_noRE 1b 1b_noRE --data $D --split dev --out $O 2>&1 | grep -E "^\[|Error|Traceback"
T1=$(date +%s); echo "=== $(date +%H:%M:%S) T1 $((T1-T0)) s"
CC=~/semeval-reteco/tools/bin/cc $PY submit.py --variants 2a_auto 2a_history 2a_nomaxp 2a_maxp --data $D --split dev --out $O 2>&1 | grep -E "^\[|Error|Traceback"
T2=$(date +%s); echo "=== $(date +%H:%M:%S) T2 $((T2-T1)) s"
$PY score_submission.py --sub $O --variants 1a 1a_noRE 1b 1b_noRE 2a_auto 2a_history_rr 2a_history_q 2a_history 2a_nomaxp 2a_maxp --data $D --kit $K --out $R/submit_check_1116.json 2>&1 | tail -30
$PY final_1110.py --sub $O --data $D --kit $K --out $R/final_1116.json
echo "=== $(date +%H:%M:%S) ALLDONE"
