#!/bin/bash
source ~/semeval-reteco/.venv/bin/activate
cd ~/semeval-reteco/reteco-research/scripts
for L in 512 256; do
  for T in 2 1; do
    python dense_index.py --data ../../reteco_data_v11 --track $T --domains all --model bge-small --max-len $L --batch 64 --out ../research/runs_v12/emb || echo "FAILED track $T L$L"
  done
done
echo ALLDONE
