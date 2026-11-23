#!/bin/bash
# Test day: one command for every submitted run (main + backup runs of configs/submission.json; no SR / guidance /
# other separate runs). Checks disk and GPU, runs submit.py (LLM pre-generation, then retrieval), the official
# format_checker on every file and prints the counters (2a_auto choices, history parser, timings).
#
#   scripts/run_test.sh <test release dir> <out dir> [split, default: test]
#
# The release dir must look like the train/dev release: track1_tempo/<domain>/{documents.jsonl,
# examples_<split>.jsonl, steps_<split>.jsonl} and track2_recor/<domain>/{documents.jsonl, benchmark_<split>.json}.
# Restartable: every LLM generation, ReasonEmbed vector and reranker score is cached as it is computed, so a crashed
# run is simply started again with the same arguments. README, section "Test day".
set -uo pipefail
if [ $# -lt 2 ]; then echo "usage: $0 <test release dir> <out dir> [split]"; exit 2; fi
REL=$(realpath "$1"); OUT=$(realpath -m "$2"); SPLIT=${3:-test}
HERE=$(cd "$(dirname "$0")" && pwd); ROOT=$(dirname "$HERE")
PY=~/semeval-reteco/.venv/bin/python; LPY=~/semeval-reteco/.venv-llm/bin/python
KIT=~/semeval-reteco/RETECO/starter_kit; CONF=$ROOT/configs/submission.json
export CC=~/semeval-reteco/tools/bin/cc
mkdir -p "$OUT"; LOG=$OUT/run_test.log
exec > >(tee -a "$LOG") 2>&1
T0=$(date +%s)
echo "=== $(date '+%F %T') run_test: release $REL split $SPLIT out $OUT"
echo "repo: $(git -C "$ROOT" rev-parse --short HEAD) $(git -C "$ROOT" status --porcelain | wc -l) uncommitted file(s)"

# ---- 1. checks
fail=0
for x in "$PY" "$LPY" "$CC" "$KIT/format_checker.py" "$CONF"; do [ -e "$x" ] || { echo "MISSING: $x"; fail=1; }; done
VARIANTS=$($PY -c "
import json; c = json.load(open('$CONF'))
v = list(c['_main_runs'].values()) + [x for k in sorted(c['_fallback_runs']) for x in c['_fallback_runs'][k]]
print(' '.join(dict.fromkeys(v)))")
echo "runs: $VARIANTS"
for d in $($PY -c "import json; c=json.load(open('$CONF')); print(' '.join(c['variants']['1a']['domains']))"); do
  for f in documents.jsonl examples_$SPLIT.jsonl steps_$SPLIT.jsonl; do
    [ -s "$REL/track1_tempo/$d/$f" ] || { echo "MISSING: track1_tempo/$d/$f"; fail=1; }; done
done
for d in $($PY -c "import json; c=json.load(open('$CONF')); print(' '.join(c['variants']['2a_history_rr']['domains']))"); do
  for f in documents.jsonl benchmark_$SPLIT.json; do
    [ -s "$REL/track2_recor/$d/$f" ] || { echo "MISSING: track2_recor/$d/$f"; fail=1; }; done
done
free_gb=$(df -BG --output=avail "$OUT" | tail -1 | tr -dc 0-9)
echo "free disk at $OUT: ${free_gb} GB"; [ "$free_gb" -ge 20 ] || { echo "LOW DISK: need >= 20 GB"; fail=1; }
free_root=$(df -BG --output=avail "$ROOT" | tail -1 | tr -dc 0-9)
[ "$free_root" -ge 10 ] || { echo "LOW DISK at the repo (caches): ${free_root} GB"; fail=1; }
if ! nvidia-smi > /dev/null 2>&1; then echo "NO GPU (nvidia-smi failed)"; fail=1; else
  read -r used total <<< "$(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits | tr -d ',')"
  echo "GPU memory used ${used} / ${total} MiB"
  [ "$used" -le 3000 ] || echo "WARNING: ${used} MiB of GPU memory already in use (close other GPU programs; vLLM needs ~5 GB)"
  ps -eo pid,args | grep -E "llm_expand|submit.py|reason_rerank|vllm" | grep -v grep | grep -v run_test && \
    echo "WARNING: another GPU job of ours is running"
fi
$PY -c "import torch, bm25s, transformers, bitsandbytes; assert torch.cuda.is_available()" || { echo "main venv broken"; fail=1; }
$LPY -c "import vllm" 2> /dev/null || { echo "LLM venv broken"; fail=1; }
[ $fail -eq 0 ] || { echo "=== checks FAILED — nothing run"; exit 1; }
echo "=== checks passed ($(( $(date +%s) - T0 )) s)"

# ---- 2. all submitted runs (LLM texts first, then retrieval; restartable)
cd "$HERE"
$PY submit.py --config "$CONF" --variants $VARIANTS --data "$REL" --split "$SPLIT" --out "$OUT" 2>&1 \
  | grep -vE "Warning|warn\(|Loading weights|it/s\]|^INFO"
rc=${PIPESTATUS[0]}
echo "=== submit.py exit $rc ($(( $(date +%s) - T0 )) s)"
[ $rc -eq 0 ] || { echo "=== submit.py FAILED — fix and start again with the same arguments (caches are kept)"; exit 1; }

# ---- 3. format check + counters
$PY test_summary.py --release "$REL" --split "$SPLIT" --out "$OUT" --kit "$KIT" --config "$CONF" --variants $VARIANTS
rc=$?
echo "=== $(date '+%F %T') run_test done: exit $rc, $(( ($(date +%s) - T0) / 60 )) min; summary $OUT/test_summary.json"
exit $rc
