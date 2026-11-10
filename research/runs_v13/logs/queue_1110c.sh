#!/bin/bash
# 2026-11-10 A4 / rule 16: LLM reranker over the top 20 of the four final systems, after queue_1110b (speed test).
# Model: Qwen3-Reranker-4B NF4 if the speed test reached >= 5 pairs/s, else Qwen3-Reranker-0.6B fp16 (rule 16).
cd ~/semeval-reteco/reteco-research/scripts
D=../../reteco_data_v11; K=../../RETECO/starter_kit; R=../research/runs_v13; PY=~/semeval-reteco/.venv/bin/python
while ! grep -q "ALLDONE" $R/logs/queue_1110b.log; do sleep 20; done
SPEED=$(grep -oE "\(([0-9.]+) pairs/s\)" $R/logs/queue_1110b.log | tail -1 | grep -oE "[0-9.]+")
if [ -n "$SPEED" ] && awk "BEGIN{exit !($SPEED >= 5)}"; then M="--model qwen3-reranker-4b --bits 4"; else M="--model qwen3-reranker-0.6b --bits 16"; fi
echo "=== $(date +%H:%M:%S) speed test ${SPEED:-none} pairs/s -> $M"
rr() {
  for i in $(seq 1 6); do
    echo "=== $(date +%H:%M:%S) attempt $i: $*"
    $PY llm_rerank.py $M --data $D --kit $K --out $R/rerank --save-runs $R/rerank/runs --batch 4 "$@" 2>&1 \
      | grep -vE "Warning|warn\(|Loading weights|it/s\]" && [ ${PIPESTATUS[0]} -eq 0 ] && return 0
    sleep 60
  done
  echo "FAILED $*"
}
rr --cond 2a_history --scores $R/scores/2ah_hybrid.json
echo "=== $(date +%H:%M:%S) R16_2AH_DONE"
rr --cond 1a --scores $R/scores/1a_rerun.json
echo "=== $(date +%H:%M:%S) R16_1A_DONE"
rr --cond 2a_current --scores $R/scores/2a_nomaxp.json
echo "=== $(date +%H:%M:%S) R16_2AC_DONE"
rr --cond 1b --scores $R/scores/1b_rerun.json
echo "=== $(date +%H:%M:%S) ALLDONE"
