#!/bin/bash
source ~/semeval-reteco/.venv/bin/activate
cd ~/semeval-reteco/reteco-research/scripts
/usr/bin/time -v python bm25s_run.py --data ../../reteco_data_v11 --kit ../../RETECO/starter_kit --splits train dev --track 2 --domains biology drones earth_science economics hardware law medicalsciences politics psychology robotics sustainable_living --analyzer lucene --k 1000 --conditions 2a_current 2a_history --threads 8 --out ../research/runs_v12/bm25/t2 || echo "FAILED t2"
/usr/bin/time -v python bm25s_run.py --data ../../reteco_data_v11 --kit ../../RETECO/starter_kit --splits train dev --track 1 --domains iota quant law workplace cardano monero economics bitcoin politics genealogy travel hsm history --analyzer lucene --k 1000 --conditions 1a 1b_query+step --threads 8 --out ../research/runs_v12/bm25/t1 || echo "FAILED t1"
echo ALLDONE
