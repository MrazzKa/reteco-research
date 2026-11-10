#!/bin/bash
# 2026-11-10 phase B, reordered at 14:30: B3b (LLM nondeterminism on dev) -> rule 18 for 1a, 2a current, 1b ->
# B4 (rule 13 for 1b). Replaces the tails of queue_1110g.sh / queue_1110f.sh (stopped by PID; ReasonEmbed / Qwen3-Emb
# document vectors are cached per 2,000 and resume).
export CC=~/semeval-reteco/tools/bin/cc PATH=~/semeval-reteco/tools/bin:$PATH
cd ~/semeval-reteco/reteco-research/scripts
D=../../reteco_data_v11; K=../../RETECO/starter_kit; R=../research/runs_v13; E=../research/runs_v12/emb
PY=~/semeval-reteco/.venv/bin/python; LPY=~/semeval-reteco/.venv-llm/bin/python
step() { echo "=== $(date +%H:%M:%S) $*"; "$@" 2>&1 | grep --line-buffered -vE "Warning|Loading weights|warn\(|^\s+(train|dev)  "; echo "=== exit ${PIPESTATUS[0]}"; }
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
# B3b: LLM nondeterminism on dev (fresh LLM cache, shared ReasonEmbed / reranker caches)
N=$R/nondet; mkdir -p $N
$PY - <<'PYEOF'
import json
c = json.load(open("../configs/submission.json"))
for v in c["variants"].values():
    if "llm" in v:
        v["llm"]["cache"] = f"research/runs_v13/nondet/llm/t{v['track']}"
json.dump(c, open("../research/runs_v13/nondet/submission_freshllm.json", "w"), indent=1)
PYEOF
step $PY submit.py --config $N/submission_freshllm.json --variants 1a_p100 1b --data $D --split dev --out $N/sub
step $PY submit.py --config $N/submission_freshllm.json --variants 2a_history_rr 2a_nomaxp_p100 --data $D --split dev --out $N/sub
step $PY nondet_report.py --runs $R --data $D --kit $K
echo "=== $(date +%H:%M:%S) B3B_DONE"
one 1a 1 1a__q+r+h 1a 1a_rerun $R/qexp/t1/hybrid_1a.json $R/qexp/t1/bm25/runs $R/qexp/t1/dense/runs
one 2a_current 2 2a_current__q+r+h 2a_current 2a_nomaxp $R/qexp/t2/hybrid_2a_current.json $R/qexp/t2/bm25/runs $R/qexp/t2/dense/runs
one 1b 1 1b_query+step__q+r+h 1b_query+step 1b_rerun $R/qexp/t1/hybrid_1b.json $R/qexp/t1/bm25/runs $R/qexp/t1/dense/runs
echo "=== $(date +%H:%M:%S) R18_ALL_DONE"
C=1b_query+step
for u in 0.75 0.65 0.55; do
  echo "=== $(date +%H:%M:%S) gen gpu-util $u"
  $LPY llm_expand.py --data $D --gpu-util $u --max-seqs 32 --max-batched 2048 --track 1 --conditions $C --prompts hyde \
    --samples 5 --temperature 0.7 --out $R/llm/t1 2>&1 | grep --line-buffered -E "^\[|/[0-9]+ +chunk|Error|KV cache size" && [ ${PIPESTATUS[0]} -eq 0 ] && break
done
echo "=== $(date +%H:%M:%S) GEN_DONE"
step $PY qexp_search.py --data $D --kit $K --track 1 --cond $C --variants q+r+h1s q+r+h3 q+r+h5 --llm $R/llm/t1 --model bge-small --max-len 256 --emb $E --out $R/hyde5/t1
step $PY hybrid.py --track 1 --conditions ${C}__q+r+h1s ${C}__q+r+h3 ${C}__q+r+h5 --bm25 $R/hyde5/t1/bm25/runs --dense $R/hyde5/t1/dense/runs --data $D --kit $K --out $R/hyde5/t1/hybrid_1b.json
step $PY select_rule.py --rule 13 --cond $C --baseline n1_t0 --cand "n1_t0=$R/qexp/t1/hybrid_1b.json:${C}__q+r+h" "n3=$R/hyde5/t1/hybrid_1b.json:${C}__q+r+h3" "n5=$R/hyde5/t1/hybrid_1b.json:${C}__q+r+h5" --out $R/select/rule13_1b_hybrid.json
echo "=== $(date +%H:%M:%S) ALLDONE"
