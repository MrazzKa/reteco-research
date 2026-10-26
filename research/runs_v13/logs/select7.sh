#!/bin/bash
# Rule 7 (LOG 13:37): MaxP vs the rule-6 system, per condition, on train.
source ~/semeval-reteco/.venv/bin/activate
cd ~/semeval-reteco/reteco-research/scripts
R=../research/runs_v13
for x in 2a_current:t2/hybrid_2a_current 1a:t1/hybrid_1a 1b_query+step:t1/hybrid_1b; do
  c=${x%%:*}; h=${x#*:}.json
  python select_rule.py --rule 7 --cond $c --baseline "rule6_q+r+h" --cand "rule6_q+r+h=$R/qexp/$h:${c}__q+r+h" \
    "maxp_q=$R/maxp/$h:${c}__q" "maxp_q+r+h=$R/maxp/$h:${c}__q+r+h" --out $R/select/rule7_$c.json
done
