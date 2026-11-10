#!/bin/bash
# C1 resume (after the user paused C1 on 2026-11-10 23:59): 1a runs are done; 1b, Track 2, scoring. Caches kept, so 1b is no longer fully cold.
cd ~/semeval-reteco/reteco-research/scripts
D=../../reteco_data_v11; K=../../RETECO/starter_kit; R=../research/runs_v13; PY=~/semeval-reteco/.venv/bin/python
C=$R/cold_full  # resume: keep release, caches and finished runs
T0=$(date +%s)
CC=~/semeval-reteco/tools/bin/cc $PY submit.py --config $C/submission_cold.json --variants 1b 1b_noRE --data $C/release --split test --out $C/sub 2>&1 | grep -E "^\[|Error|Traceback"
T1=$(date +%s)
echo "=== $(date +%H:%M:%S) TRACK1_DONE $((T1-T0)) s"
CC=~/semeval-reteco/tools/bin/cc $PY submit.py --config $C/submission_cold.json --variants 2a_auto 2a_history 2a_nomaxp_p100 2a_nomaxp 2a_maxp --data $C/release --split test --out $C/sub 2>&1 | grep -E "^\[|Error|Traceback"
T2=$(date +%s)
echo "=== $(date +%H:%M:%S) COLD track1 $((T1-T0)) s, track2 $((T2-T1)) s"
$PY score_submission.py --sub $C/sub --variants 1a_p100 1a 1a_noRE 1b 1b_noRE 2a_auto 2a_history_rr 2a_history_q 2a_history 2a_nomaxp_p100 2a_nomaxp 2a_maxp --data $D --kit $K --out $C/score.json 2>&1 | tail -40
$PY cold_report.py --cold $C --log $R/logs/queue_1110k_resume.log
echo "=== $(date +%H:%M:%S) ALLDONE"
