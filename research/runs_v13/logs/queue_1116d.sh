#!/bin/bash
# S2c (2026-11-16): checks of the separate run 2a_history_sr (rule 19). Needs the 2a_history_sr block in configs/submission.json.
cd ~/semeval-reteco/reteco-research/scripts
D=../../reteco_data_v11; K=../../RETECO/starter_kit; R=../research/runs_v13; PY=~/semeval-reteco/.venv/bin/python
while ! grep -q "ALLDONE" $R/logs/queue_1116c.log; do sleep 15; done
T0=$(date +%s)
# 1. dev check (research caches): official scorer = research number
CC=~/semeval-reteco/tools/bin/cc $PY submit.py --variants 2a_history_sr --data $D --split dev --out $R/submit/dev_1116 2>&1 | grep -E "^\[|Error|Traceback"
$PY score_submission.py --sub $R/submit/dev_1116 --variants 2a_history_sr 2a_history_rr --data $D --kit $K --out $R/sr/submit_check_dev.json 2>&1 | tail -8
echo "=== $(date +%H:%M:%S) DEV_DONE $(( $(date +%s) - T0 )) s"
# 2. synthetic test releases from dev: with SR (as announced) and with the field removed
$PY make_test_release.py --data $D --out $R/sr/rel_sr --tracks 2 --keep-sr
$PY make_test_release.py --data $D --out $R/sr/rel_nosr --tracks 2
for X in sr nosr; do
  CC=~/semeval-reteco/tools/bin/cc $PY submit.py --variants 2a_history_sr 2a_auto --data $R/sr/rel_$X --split test --out $R/sr/sub_$X 2>&1 | grep -E "^\[|Error|Traceback" | grep -vE "^\[2a_history_sr\] [a-z_]+: \{"
  $PY score_submission.py --sub $R/sr/sub_$X --variants 2a_history_sr 2a_history_rr 2a_auto --data $D --kit $K --out $R/sr/submit_check_$X.json 2>&1 | tail -8
  echo "=== $(date +%H:%M:%S) REL_${X}_DONE $(( $(date +%s) - T0 )) s"
done
$PY - <<'PY'
import json
R = "../research/runs_v13/sr"
out = {}
for x in ("sr", "nosr"):
    m = json.load(open(f"{R}/sub_{x}/2a_history_sr/manifest.json"))
    sc = json.load(open(f"{R}/submit_check_{x}.json"))
    same = 0
    tot = 0
    import os
    for dom in m["domains"]:
        a = open(f"{R}/sub_{x}/2a_history_sr/{dom}.txt").read().split("\n")
        b = open(f"{R}/sub_{x}/2a_history_rr/{dom}.txt").read().split("\n")
        tot += 1
        same += [l.split()[:4] for l in a if l] == [l.split()[:4] for l in b if l]
    out[x] = {"sr_summary": m.get("sr_summary"), "domains_identical_to_2a_history_rr": [same, tot],
              "scores": {v: s.get("official_macro_ndcg10") for v, s in sc.items()},
              "format_checker_all_exit0": all(c.get("format_checker_exit") == 0 for s in sc.values() for c in s.get("checks", {}).values())}
json.dump(out, open(f"{R}/s2c_check.json", "w"), indent=1)
print(json.dumps(out, indent=1))
PY
echo "=== $(date +%H:%M:%S) ALLDONE $(( $(date +%s) - T0 )) s"
