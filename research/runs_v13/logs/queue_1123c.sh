#!/bin/bash
# 2026-11-23 N3 checks, then N4 (several LLM draws). Waits for queue_1123b (rule 20). GPU jobs one at a time.
cd ~/semeval-reteco/reteco-research/scripts
D=../../reteco_data_v11; K=../../RETECO/starter_kit; R=../research/runs_v13; PY=~/semeval-reteco/.venv/bin/python
LPY=~/semeval-reteco/.venv-llm/bin/python; export CC=~/semeval-reteco/tools/bin/cc
until grep -q "ALLDONE" $R/logs/queue_1123b.log; do sleep 30; done
T0=$(date +%s)
# ---- N3
mkdir -p $R/n3
$PY submit.py --variants 2a_history_noans --data $D --split dev --out $R/submit/dev_1123 2>&1 | grep -E "^\[|Error|Traceback|Assertion"
$PY score_submission.py --sub $R/submit/dev_1123 --variants 2a_history_noans --data $D --kit $K --out $R/n3/check_dev.json 2>&1 | tail -3
$PY make_test_release.py --data $D --out $R/n3/rel_noans --tracks 2 --strip-answers
$PY submit.py --variants 2a_history_noans --data $R/n3/rel_noans --split test --out $R/n3/sub_noans 2>&1 | grep -E "^\[|Error|Traceback|Assertion"
$PY score_submission.py --sub $R/n3/sub_noans --variants 2a_history_noans --data $D --kit $K --out $R/n3/check_rel_noans.json 2>&1 | tail -3
$PY t2_breakdown.py --data $D --kit $K --split dev --out $R/n3/m0_vs_h0q_dev.json \
  --run "M0 (2a_history_noans)=$R/submit/dev_1123/2a_history_noans/{dom}.txt" \
  --run "H0q+RE (2a_history_q)=$R/submit/dev_1116/2a_history_q/{dom}.txt" \
  --run "main, reference answers (2a_history)=$R/submit/dev_1116/2a_history/{dom}.txt" | tail -6
$PY - <<'PY'
import json, os
R = "../research/runs_v13"
same = tot = 0
for dom in sorted(os.listdir(f"{R}/a2/sub_m0dev/2a_history")):
    if not dom.endswith(".txt"):
        continue
    a = [l.split()[:4] for l in open(f"{R}/submit/dev_1123/2a_history_noans/{dom}") if l.strip()]
    b = [l.split()[:4] for l in open(f"{R}/a2/sub_m0dev/2a_history/{dom}") if l.strip()]
    tot += 1; same += a == b
print(json.dumps({"domains_identical_to_m0_1116": [same, tot]}))
json.dump({"domains_identical_to_m0_1116": [same, tot]}, open(f"{R}/n3/identical.json", "w"))
PY
echo "=== $(date +%H:%M:%S) N3_DONE $(( $(date +%s) - T0 )) s"
# ---- N4
sub() {  # seed, label, data, split, variants...
  local s=$1 lab=$2 data=$3 split=$4; shift 4
  $PY submit.py --config $R/n4/configs/s$s.json --stages --variants "$@" --data $data --split $split --out $R/n4/sub/s$s/$lab 2>&1 | grep -E "^\[|Error|Traceback|Assertion" | grep -v "^\[2a_auto\]"
}
for s in 0 1 2 3; do
  $PY n4_prepare.py --root .. --data $D --seed $s
  if [ $s -gt 0 ]; then
    for t in 1 2; do
      echo "=== $(date +%H:%M:%S) N4 s$s LLM t$t"
      $LPY llm_expand.py --track $t --bodies $R/n4/llm/s$s/bodies_t$t.json --shuffle-seed $s --prompts reason hyde --chunk 100000 --gpu-util 0.6 --max-seqs 64 --max-batched 2048 --out $R/n4/llm/s$s/t$t 2>&1 | grep -vE "Warning|warn\(|INFO|it/s\]" | tail -4
    done
  fi
  echo "=== $(date +%H:%M:%S) N4 s$s retrieval"
  sub $s t1_dev $D dev 1a 1b
  sub $s t1_trainsub $R/n4/rel/t1 trainsub 1a 1b
  sub $s t2_dev $D dev 2a_history_rr 2a_history_noans
  sub $s t2_trainsub $R/a2/data_ref trainsub 2a_history_rr 2a_history_noans
  sub $s gen_dev $R/a2/data_gen dev 2a_history
  sub $s gen_trainsub $R/a2/data_gen trainsub 2a_history
  echo "=== $(date +%H:%M:%S) N4_S${s}_DONE $(( $(date +%s) - T0 )) s"
done
echo "=== $(date +%H:%M:%S) ALLDONE $(( $(date +%s) - T0 )) s"
