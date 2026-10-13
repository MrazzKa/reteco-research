#!/bin/bash
# Model selection on TRAIN: subset domains, full-corpus dense retrieval, train queries only.
source ~/semeval-reteco/.venv/bin/activate
cd ~/semeval-reteco/reteco-research/scripts
# (indexing finished before this run)
T1S="iota quant law workplace"
T2S="drones law medicalsciences biology psychology economics"
run() {  # model maxlen batch
  python dense_index.py --data ../../reteco_data_v11 --track 1 --domains $T1S --model $1 --max-len $2 --batch $3 --out ../research/runs_v12/emb || echo "FAILED index t1 $1 L$2"
  python dense_index.py --data ../../reteco_data_v11 --track 2 --domains $T2S --model $1 --max-len $2 --batch $3 --out ../research/runs_v12/emb || echo "FAILED index t2 $1 L$2"
  python dense_search.py --data ../../reteco_data_v11 --kit ../../RETECO/starter_kit --track 1 --domains $T1S --splits train --model $1 --max-len $2 --emb ../research/runs_v12/emb --out ../research/runs_v12/select/$1_L$2/t1 || echo "FAILED search t1 $1 L$2"
  python dense_search.py --data ../../reteco_data_v11 --kit ../../RETECO/starter_kit --track 2 --domains $T2S --splits train --model $1 --max-len $2 --emb ../research/runs_v12/emb --out ../research/runs_v12/select/$1_L$2/t2 || echo "FAILED search t2 $1 L$2"
  echo "MODEL DONE $1 L$2"
}
run bge-small 256 64
run bge-small 512 64
run bge-base 512 64
run gte-modernbert 512 64
run qwen3-0.6b 512 16
run e5-large 512 32
run bge-large 512 32
echo ALLDONE
