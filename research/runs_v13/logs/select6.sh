#!/bin/bash
# Rule 6 (LOG 13:37): choose the query variant per condition on train.
source ~/semeval-reteco/.venv/bin/activate
cd ~/semeval-reteco/reteco-research/scripts
R=../research/runs_v13
sel() {  # cond, hybrid report
  args=""; for v in q q+r r q+h h q+r+h; do args="$args $v=$2:$1__$v"; done
  python select_rule.py --rule 6 --cond $1 --baseline q --cand $args --out $R/select/rule6_$1.json
}
sel 2a_current $R/qexp/t2/hybrid_2a_current.json
sel 1a $R/qexp/t1/hybrid_1a.json
sel 1b_query+step $R/qexp/t1/hybrid_1b.json
