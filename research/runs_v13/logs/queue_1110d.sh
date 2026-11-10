#!/bin/bash
# 2026-11-10 A5 / rule 17: ReasonEmbed over the top 100 of each final hybrid (all four passed the 3% ceiling check),
# after the rule-16 queue. Same NF4 setup as rule 8; chunked, resumable; then rule17_choice.py after each.
cd ~/semeval-reteco/reteco-research/scripts
D=../../reteco_data_v11; K=../../RETECO/starter_kit; R=../research/runs_v13; PY=~/semeval-reteco/.venv/bin/python
while ! grep -q "ALLDONE" $R/logs/queue_1110c.log; do sleep 30; done
rr() {
  for i in $(seq 1 10); do
    echo "=== $(date +%H:%M:%S) attempt $i: $*"
    $PY reason_rerank.py --backend bnb --bits 4 --batch 4 --chunk 2000 --pool 100 \
      --data $D --kit $K --out $R/reason --save-runs $R/foreign/runs "$@" 2>&1 \
      | grep --line-buffered -vE "Warning|warn\(|Loading weights" && [ ${PIPESTATUS[0]} -eq 0 ] && return 0
    sleep 60
  done
  echo "FAILED $*"
}
ch() { $PY rule17_choice.py --runs $R --data $D --kit $K --out $R/select/rule17.json 2>&1 | tail -4; }
rr --track 2 --conditions 2a_hist3qa__q+r+h --query-cond 2a_hist3qa --name 2ah_hybrid_p100 --hybrid $R/hist/t2/hybrid.json --bm25 $R/hist/t2/bm25/runs --dense $R/hist/t2/dense/runs --save-scores $R/scores/2ah_hybrid_p100.json; ch
echo "=== $(date +%H:%M:%S) R17_2AH_DONE"
rr --track 1 --conditions 1a__q+r+h --query-cond 1a --name 1a_rerun_p100 --hybrid $R/qexp/t1/hybrid_1a.json --bm25 $R/qexp/t1/bm25/runs --dense $R/qexp/t1/dense/runs --save-scores $R/scores/1a_rerun_p100.json; ch
echo "=== $(date +%H:%M:%S) R17_1A_DONE"
rr --track 2 --conditions 2a_current__q+r+h --query-cond 2a_current --name 2a_nomaxp_p100 --hybrid $R/qexp/t2/hybrid_2a_current.json --bm25 $R/qexp/t2/bm25/runs --dense $R/qexp/t2/dense/runs --save-scores $R/scores/2a_nomaxp_p100.json; ch
echo "=== $(date +%H:%M:%S) R17_2AC_DONE"
rr --track 1 --conditions 1b_query+step__q+r+h --query-cond 1b_query+step --name 1b_rerun_p100 --hybrid $R/qexp/t1/hybrid_1b.json --bm25 $R/qexp/t1/bm25/runs --dense $R/qexp/t1/dense/runs --save-scores $R/scores/1b_rerun_p100.json; ch
echo "=== $(date +%H:%M:%S) ALLDONE"
