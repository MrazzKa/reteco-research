# Week-1 results

split: `dev` · BM25 k1=0.9 b=0.4 · pure-Python (FastBM25 ≡ starter_kit/bm25.py) · nDCG@10 via starter_kit/ir_metrics.py

`official_ref` is the pyserini baseline from BASELINE_RESULTS.md. Tokenisation differs, so a small gap is expected; a large one is a finding to investigate, not to patch.

| track | domain | run | n | nDCG@10 | official ref | Δ |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| 1 | iota | 1a | 3 | 0.2346 | 0.2083 | +0.0263 |
| 1 | iota | 1b_query+step | 8 | 0.2500 | 0.3289 | -0.0789 |
| 1 | iota | 1b_step_only | 8 | 0.3436 |  |  |
| 1 | iota | 1b_query+all | 8 | 0.3125 |  |  |
| 2 | drones | DIAG_gold_recycling | 27 | 0.7777 |  |  |
| 2 | drones | 2a_ORACLE_prev_turn_gold | 38 | 0.4939 |  |  |
| 2 | drones | 2a_current | 38 | 0.0668 | 0.1695 | -0.1027 |
| 2 | drones | 2a_history | 38 | 0.1898 | 0.2954 | -0.1056 |
| 2 | drones | 2a_hist_questions_only | 38 | 0.1362 |  |  |
| 2 | drones | 2a_hist_answers_only | 38 | 0.2033 |  |  |
| 2 | drones | 2a_ORACLE_hist+reasoning | 38 | 0.2358 |  |  |
| 2 | biology | DIAG_gold_recycling | 89 | 0.8681 |  |  |
| 2 | biology | 2a_ORACLE_prev_turn_gold | 115 | 0.6228 |  |  |
| 2 | biology | 2a_current | 115 | 0.1880 | 0.2034 | -0.0154 |
| 2 | biology | 2a_history | 115 | 0.5426 | 0.6065 | -0.0639 |
| 2 | biology | 2a_hist_questions_only | 115 | 0.3360 |  |  |
| 2 | biology | 2a_hist_answers_only | 115 | 0.5781 |  |  |
| 2 | biology | 2a_ORACLE_hist+reasoning | 115 | 0.6306 |  |  |

## Track 2 by turn depth

| domain | run | T1 | T2 | T3 | T4 | T5+ |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| drones (StackExchange) | 2a_current | 0.087 | 0.120 | 0.024 | 0.000 | 0.000 |
| drones (StackExchange) | 2a_history | 0.087 | 0.210 | 0.233 | 0.347 | 0.000 |
| drones (StackExchange) | 2a_hist_questions_only | 0.087 | 0.136 | 0.174 | 0.202 | 0.000 |
| drones (StackExchange) | 2a_hist_answers_only | 0.087 | 0.240 | 0.249 | 0.347 | 0.000 |
| drones (StackExchange) | 2a_ORACLE_hist+reasoning | 0.178 | 0.248 | 0.246 | 0.393 | 0.000 |
| biology (BRIGHT) | 2a_current | 0.309 | 0.169 | 0.142 | 0.127 | 0.165 |
| biology (BRIGHT) | 2a_history | 0.309 | 0.518 | 0.533 | 0.690 | 0.761 |
| biology (BRIGHT) | 2a_hist_questions_only | 0.309 | 0.275 | 0.307 | 0.356 | 0.465 |
| biology (BRIGHT) | 2a_hist_answers_only | 0.309 | 0.607 | 0.590 | 0.695 | 0.771 |
| biology (BRIGHT) | 2a_ORACLE_hist+reasoning | 0.523 | 0.583 | 0.603 | 0.701 | 0.803 |

Notes:
- `2a_ORACLE_*` pastes the GOLD reasoning annotation into the query. It is a ceiling for BM25, not a system.
- `2a_ORACLE_prev_turn_gold` ranks ONLY the gold passages of earlier turns (needs hidden qrels, never a system). It measures how much of +history's gain could come from re-finding what was already relevant.
- `DIAG_gold_recycling`: the value column is the mean share of a later turn's gold that was already gold in an earlier turn — not an nDCG.
- `2a_hist_questions_only` / `2a_hist_answers_only` split the history into prior questions vs prior REFERENCE answers (written from gold passages).
- `1b_step_only` and `1b_query+all` are the two strategies the task proposal permits but the baseline does not report.
- Small domains give unstable numbers (see iota: official 1a train 0.0199 vs dev 0.2083). Report n next to every score.