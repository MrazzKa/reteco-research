#!/bin/bash
# 2026-11-23: rule-20 submission checks (1a_guid / 1b_guid) and the N6 test-day rehearsal. Waits for queue_1123c and
# for the guidance variants in configs/submission.json (written by g_report.py --write-config).
cd ~/semeval-reteco/reteco-research/scripts
D=../../reteco_data_v11; K=../../RETECO/starter_kit; R=../research/runs_v13; PY=~/semeval-reteco/.venv/bin/python
export CC=~/semeval-reteco/tools/bin/cc
until grep -q "ALLDONE" $R/logs/queue_1123c.log && [ -f $R/guid/config_written ]; do sleep 30; done
T0=$(date +%s)
# ---- rule 20: dev check (official = research), synthetic test with and without the guidance file
$PY submit.py --variants 1a_guid 1b_guid --data $D --split dev --out $R/submit/dev_1123 2>&1 | grep -E "^\[|Error|Traceback|Assertion" | grep -v "\] [a-z]*: {"
$PY score_submission.py --sub $R/submit/dev_1123 --variants 1a_guid 1b_guid --data $D --kit $K --out $R/guid/check_dev.json 2>&1 | tail -3
echo "=== $(date +%H:%M:%S) GUID_DEV_DONE $(( $(date +%s) - T0 )) s"
$PY make_test_release.py --data $D --out $R/guid/rel_g --tracks 1 --keep-guidance
$PY make_test_release.py --data $D --out $R/guid/rel_nog --tracks 1
for X in g nog; do
  $PY submit.py --variants 1a_guid 1b_guid --data $R/guid/rel_$X --split test --out $R/guid/sub_$X 2>&1 | grep -E "Error|Traceback|Assertion|summary"
  $PY score_submission.py --sub $R/guid/sub_$X --variants 1a_guid 1b_guid 1a 1b --data $D --kit $K --out $R/guid/check_rel_$X.json 2>&1 | tail -5
  echo "=== $(date +%H:%M:%S) GUID_REL_${X}_DONE $(( $(date +%s) - T0 )) s"
done
$PY - <<'PY'
import json, os
R = "../research/runs_v13/guid"
out = {}
for x in ("g", "nog"):
    o = {}
    for v, base in (("1a_guid", "1a"), ("1b_guid", "1b")):
        m = json.load(open(f"{R}/sub_{x}/{v}/manifest.json"))
        same = tot = 0
        for dom in m["domains"]:
            a = [l.split()[:4] for l in open(f"{R}/sub_{x}/{v}/{dom}.txt") if l.strip()]
            b = [l.split()[:4] for l in open(f"{R}/sub_{x}/{base}/{dom}.txt") if l.strip()]
            tot += 1; same += a == b
        sc = json.load(open(f"{R}/check_rel_{x}.json"))
        o[v] = {"guidance_summary": m.get("guidance_summary"), "domains_identical_to_main": [same, tot],
                "official": sc[v]["official_macro_ndcg10"], "main_official": sc[base]["official_macro_ndcg10"],
                "format_checker_all_exit0": all(c.get("format_checker_exit") == 0 for c in sc[v]["checks"].values())}
    out[x] = o
json.dump(out, open(f"{R}/submit_check.json", "w"), indent=1)
print(json.dumps(out, indent=1))
PY
echo "=== $(date +%H:%M:%S) GUID_CHECKS_DONE $(( $(date +%s) - T0 )) s"
# ---- N6: test-day rehearsal on a synthetic test release from dev (warm caches)
mkdir -p $R/testday
$PY make_test_release.py --data $D --out $R/testday/rel --keep-sr --keep-guidance
bash run_test.sh $R/testday/rel $R/testday/out
echo "=== $(date +%H:%M:%S) TESTDAY exit $? $(( $(date +%s) - T0 )) s"
echo "=== $(date +%H:%M:%S) ALLDONE $(( $(date +%s) - T0 )) s"
