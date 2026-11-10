#!/bin/bash
# 2026-11-10 B2 / rule 18: Qwen3-Embedding-4B over the same top-50 pools, ensemble with ReasonEmbed; after queue_1110d.
cd ~/semeval-reteco/reteco-research/scripts
D=../../reteco_data_v11; K=../../RETECO/starter_kit; R=../research/runs_v13; PY=~/semeval-reteco/.venv/bin/python
while ! grep -q "ALLDONE" $R/logs/queue_1110d.log; do sleep 30; done
rr() {  # $1 = model, rest = args
  m=$1; shift
  for i in $(seq 1 10); do
    echo "=== $(date +%H:%M:%S) attempt $i: $m $*"
    $PY reason_rerank.py --model $m --backend bnb --bits 4 --batch 4 --chunk 2000 --pool 50 \
      --data $D --kit $K --out $R/reason "$@" 2>&1 \
      | grep --line-buffered -vE "Warning|warn\(|Loading weights" && [ ${PIPESTATUS[0]} -eq 0 ] && return 0
    sleep 60
  done
  echo "FAILED $*"
}
one() {  # cond track hybrid-cond query-cond name hybrid bm25 dense
  c=$1; t=$2; hc=$3; qc=$4; n=$5; H=$6; B=$7; DD=$8
  rr reasonembed-4b --track $t --conditions $hc --query-cond $qc --name $n --hybrid $H --bm25 $B --dense $DD --save-scores $R/scores/${n}.json
  rr qwen3-emb-4b --track $t --conditions $hc --query-cond $qc --name ${n}_q3e --hybrid $H --bm25 $B --dense $DD --save-scores $R/scores/${n}_q3e.json
  $PY ensemble_embed.py --cond $c --a $R/scores/${n}.json --b $R/scores/${n}_q3e.json --data $D --kit $K --out $R/ensemble/rule18_${c}.json 2>&1 | tail -30
  echo "=== $(date +%H:%M:%S) R18_${c}_DONE"
}
one 2a_history 2 2a_hist3qa__q+r+h 2a_hist3qa 2ah_hybrid $R/hist/t2/hybrid.json $R/hist/t2/bm25/runs $R/hist/t2/dense/runs
one 1a 1 1a__q+r+h 1a 1a_rerun $R/qexp/t1/hybrid_1a.json $R/qexp/t1/bm25/runs $R/qexp/t1/dense/runs
one 2a_current 2 2a_current__q+r+h 2a_current 2a_nomaxp $R/qexp/t2/hybrid_2a_current.json $R/qexp/t2/bm25/runs $R/qexp/t2/dense/runs
one 1b 1 1b_query+step__q+r+h 1b_query+step 1b_rerun $R/qexp/t1/hybrid_1b.json $R/qexp/t1/bm25/runs $R/qexp/t1/dense/runs
echo "=== $(date +%H:%M:%S) ALLDONE"
