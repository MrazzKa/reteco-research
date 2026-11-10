#!/bin/bash
# 2026-11-10 A1 (rule 14) and A3 (rule 15) queue, GPU jobs one at a time.
cd ~/semeval-reteco/reteco-research/scripts
D=../../reteco_data_v11; K=../../RETECO/starter_kit; R=../research/runs_v13; E=../research/runs_v12/emb; PY=~/semeval-reteco/.venv/bin/python
step() { echo "=== $(date +%H:%M:%S) $*"; "$@" 2>&1 | grep -vE "Warning|Loading weights|warn\(|^\s+(train|dev)  "; echo "=== exit ${PIPESTATUS[0]}"; }
rr() {  # ReasonEmbed NF4, chunked, restartable
  for i in $(seq 1 10); do
    echo "=== $(date +%H:%M:%S) attempt $i: $*"
    $PY reason_rerank.py --backend bnb --bits 4 --batch 4 --chunk 2000 --pool 50 \
      --data $D --kit $K --out $R/reason --save-runs $R/foreign/runs "$@" 2>&1 \
      | grep -vE "Warning|warn\(|Loading weights" && [ ${PIPESTATUS[0]} -eq 0 ] && return 0
    sleep 60
  done
  echo "FAILED $*"
}
# A1: answer-free history text, plain (q) and with the 2a_hist3q generations (q+r+h)
step $PY qexp_search.py --data $D --kit $K --track 2 --cond 2a_hist3q --query-cond 2a_history_qonly_qfirst --variants q q+r+h --llm $R/llm/t2 --model bge-base --max-len 512 --emb $E --out $R/histq/t2
step $PY hybrid.py --track 2 --conditions 2a_hist3q__q 2a_hist3q__q+r+h --bm25 $R/histq/t2/bm25/runs --dense $R/histq/t2/dense/runs --data $D --kit $K --out $R/histq/t2/hybrid.json
echo "=== $(date +%H:%M:%S) A1_HYBRID_DONE"
rr --track 2 --conditions 2a_hist3q__q+r+h --query-cond 2a_hist3q --name 2ahq_haq --hybrid $R/histq/t2/hybrid.json --bm25 $R/histq/t2/bm25/runs --dense $R/histq/t2/dense/runs --save-scores $R/scores/2ahq_haq.json
rr --track 2 --conditions 2a_hist3q__q --query-cond 2a_hist3q --name 2ahq_h0q --hybrid $R/histq/t2/hybrid.json --bm25 $R/histq/t2/bm25/runs --dense $R/histq/t2/dense/runs --save-scores $R/scores/2ahq_h0q.json
echo "=== $(date +%H:%M:%S) A1_RE_DONE"
# A3: q-systems (plain query hybrid + ReasonEmbed) for 2a current and 2a history (H0 with answers)
rr --track 2 --conditions 2a_current__q --query-cond 2a_current --name 2a_cur_q --hybrid $R/qexp/t2/hybrid_2a_current.json --bm25 $R/qexp/t2/bm25/runs --dense $R/qexp/t2/dense/runs --save-scores $R/scores/2a_cur_q.json
rr --track 2 --conditions 2a_history --query-cond 2a_hist3qa --name 2ah_h0 --hybrid $R/hist/t2/hybrid_h0.json --bm25 $R/bm25/t2/runs --dense $R/dense/bge-base_L512/t2/runs --save-scores $R/scores/2ah_h0.json
echo "=== $(date +%H:%M:%S) A3_RE_DONE"
# final-system score dumps for A4 (all vectors cached: no model load)
rr --track 2 --conditions 2a_current__q+r+h --query-cond 2a_current --name 2a_nomaxp --hybrid $R/qexp/t2/hybrid_2a_current.json --bm25 $R/qexp/t2/bm25/runs --dense $R/qexp/t2/dense/runs --save-scores $R/scores/2a_nomaxp.json
rr --track 2 --conditions 2a_hist3qa__q+r+h --query-cond 2a_hist3qa --name 2ah_hybrid --hybrid $R/hist/t2/hybrid.json --bm25 $R/hist/t2/bm25/runs --dense $R/hist/t2/dense/runs --save-scores $R/scores/2ah_hybrid.json
rr --track 1 --conditions 1a__q+r+h --query-cond 1a --name 1a_rerun --hybrid $R/qexp/t1/hybrid_1a.json --bm25 $R/qexp/t1/bm25/runs --dense $R/qexp/t1/dense/runs --save-scores $R/scores/1a_rerun.json
rr --track 1 --conditions 1b_query+step__q+r+h --query-cond 1b_query+step --name 1b_rerun --hybrid $R/qexp/t1/hybrid_1b.json --bm25 $R/qexp/t1/bm25/runs --dense $R/qexp/t1/dense/runs --save-scores $R/scores/1b_rerun.json
echo "=== $(date +%H:%M:%S) ALLDONE"
