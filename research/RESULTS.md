# Week-1 results (all numbers)

Generated 2026-09-21 from run files by `scripts/aggregate_week1.py` and `scripts/date_quick.py`. Split dev unless stated. See `research/LOG.md` for commands.

## Track 2: dev summary

Pure-Python BM25, nDCG@10. Official references use pyserini. Oracle columns require gold annotations and are not deployable systems.

| domain | source | n | current | questions | answers | history | reasoning oracle | prior-gold oracle | recycled gold | official current/history |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| biology | BRIGHT | 115 | 0.1880 | 0.3360 | 0.5781 | 0.5426 | 0.6306 | 0.6228 | 0.8681 | 0.2034 / 0.6065 |
| drones | StackExchange | 38 | 0.0668 | 0.1362 | 0.2033 | 0.1898 | 0.2358 | 0.4939 | 0.7777 | 0.1695 / 0.2954 |
| earth_science | BRIGHT | 133 | 0.1986 | 0.4466 | 0.6333 | 0.5987 | 0.6491 | 0.6468 | 0.8800 | 0.2195 / 0.6264 |
| economics | BRIGHT | 92 | 0.1387 | 0.2205 | 0.3853 | 0.3705 | 0.4171 | 0.5646 | 0.8226 | 0.1629 / 0.4739 |
| hardware | StackExchange | 58 | 0.1401 | 0.1798 | 0.2566 | 0.2264 | 0.2399 | 0.5110 | 0.7462 | 0.1605 / 0.3378 |
| law | StackExchange | 66 | 0.1149 | 0.2043 | 0.3279 | 0.3187 | 0.3508 | 0.4998 | 0.7196 | 0.1147 / 0.3437 |
| medicalsciences | StackExchange | 44 | 0.0736 | 0.1033 | 0.1295 | 0.1162 | 0.1070 | 0.4622 | 0.6978 | 0.1168 / 0.1730 |
| politics | StackExchange | 54 | 0.0936 | 0.1533 | 0.2768 | 0.2667 | 0.2804 | 0.5249 | 0.7636 | 0.1514 / 0.3219 |
| psychology | BRIGHT | 99 | 0.2066 | 0.2854 | 0.5259 | 0.4983 | 0.5857 | 0.6293 | 0.8686 | 0.2596 / 0.5726 |
| robotics | BRIGHT | 75 | 0.1182 | 0.2432 | 0.4309 | 0.4161 | 0.4710 | 0.5354 | 0.7875 | 0.1574 / 0.5123 |
| sustainable_living | BRIGHT | 84 | 0.2499 | 0.3737 | 0.4909 | 0.4836 | 0.5775 | 0.4040 | 0.6119 | 0.2938 / 0.5531 |

### Macro averages

| group | n domains | 2a_current | 2a_hist_questions_only | 2a_hist_answers_only | 2a_history | 2a_ORACLE_hist+reasoning | 2a_ORACLE_prev_turn_gold | history - current |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| all | 11 | 0.1445 | 0.2438 | 0.3853 | 0.3661 | 0.4132 | 0.5359 | 0.2217 |
| BRIGHT | 6 | 0.1833 | 0.3176 | 0.5074 | 0.4850 | 0.5552 | 0.5671 | 0.3016 |
| StackExchange | 5 | 0.0978 | 0.1554 | 0.2388 | 0.2236 | 0.2428 | 0.4984 | 0.1258 |

Complete source separation: yes (min BRIGHT +0.2318; max StackExchange +0.2038).

### Paired bootstrap

10,000 resamples of turns within each domain, seed 0; then macro average across domains. Turns in one conversation are dependent, so these intervals may be too narrow for new conversations.

| contrast | delta | 95% CI | domains |
| --- | ---: | --- | ---: |
| history - current | +0.2217 | [+0.1994, +0.2442] | 11 |
| answers - questions | +0.1415 | [+0.1232, +0.1605] | 11 |
| history - answers | -0.0192 | [-0.0261, -0.0125] | 11 |

### Turn depth

Each cell is the macro average of available per-domain depth means. Domain counts vary at deeper turns.

| condition | T1 | T2 | T3 | T4 | T5+ |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2a_current | 0.2286 | 0.1375 | 0.1045 | 0.1194 | 0.0915 |
| 2a_hist_questions_only | 0.2286 | 0.2534 | 0.2494 | 0.2454 | 0.2275 |
| 2a_hist_answers_only | 0.2286 | 0.4440 | 0.4379 | 0.4448 | 0.3788 |
| 2a_history | 0.2286 | 0.4180 | 0.4107 | 0.4267 | 0.3571 |
| 2a_ORACLE_hist+reasoning | 0.3452 | 0.4386 | 0.4417 | 0.4454 | 0.3678 |

### Reading

Compare the paired contrasts above before attributing the history gain. Prior answers are reference answers derived from gold passages, and gold recycling is common. These are associations, not proof of a causal mechanism. The hidden-test history and reasoning fields have not been verified.

## Track 1: dev summary

Pure-Python BM25, nDCG@10. The official 1a and 1b references use pyserini.

| domain | n queries / steps | 1a | Query+Step | Step-Only | Query+All | official 1a / 1b |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| cardano | 15 / 33 | 0.1108 | 0.0760 | 0.0984 | 0.0699 | 0.0851 / 0.0554 |
| economics | 25 / 51 | 0.0385 | 0.0312 | 0.0600 | 0.0345 | 0.0480 / 0.0517 |
| iota | 3 / 8 | 0.2346 | 0.2500 | 0.3436 | 0.3125 | 0.2083 / 0.3289 |
| law | 11 / 23 | 0.0293 | 0.0476 | 0.0767 | 0.0623 | 0.0574 / 0.0549 |
| monero | 19 / 28 | 0.0152 | 0.0103 | 0.0065 | 0.0103 | 0.0252 / 0.0103 |
| politics | 45 / 119 | 0.2095 | 0.2047 | 0.1396 | 0.2233 | 0.2550 / 0.2306 |
| quant | 10 / 15 | 0.0000 | 0.0000 | 0.1286 | 0.0000 | 0.0218 / 0.0374 |
| travel | 30 / 52 | 0.0225 | 0.0264 | 0.0522 | 0.0274 | 0.0275 / 0.0492 |
| workplace | 11 / 20 | 0.0184 | 0.0235 | 0.1861 | 0.0735 | 0.0230 / 0.0302 |

Macro averages over available domains: 1a 0.0754, 1b_query+step 0.0744, 1b_step_only 0.1213, 1b_query+all 0.0904.

### Paired bootstrap

10,000 resamples of steps within each domain, seed 0; then macro average across domains.

| contrast | delta | 95% CI | domains |
| --- | ---: | --- | ---: |
| Step-Only - Query+Step | +0.0469 | [+0.0125, +0.0839] | 9 |
| Query+All - Query+Step | +0.0160 | [+0.0032, +0.0333] | 9 |

Query+All assigns the same ranking to every step of a query. The corpus is shared across train and dev; only topics are split.

Step-weighted 1b means (349 steps): Query+Step 0.0965, Step-Only 0.1031, Query+All 0.1082. Skipped for compute: genealogy, bitcoin, hsm, history.

## Track 1: explicit-date feasibility (train)

Regex: years `\b(1[5-9]\d\d|20\d\d)\b`, decades `\b(1[5-9]\d0s|20\d0s)\b`, English month-year. Overlap = a document year within the query's min–max year span ±1, computed only for queries with a year. Contrast = reservoir sample of 2,000 corpus documents per domain (seed 0). Passages counted per query–document pair.

| domain | train queries | queries dated | gold dated | random-corpus dated | median years/query | gold span overlap | random span overlap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| bitcoin | 70 | 21.4% | 21.1% | 27.7% | 0 | 17.5% | 8.3% |
| cardano | 36 | 5.6% | 22.5% | 33.0% | 0 | 0.0% | 9.4% |
| economics | 58 | 53.4% | 61.1% | 45.9% | 1 | 43.9% | 8.0% |
| genealogy | 80 | 93.8% | 85.0% | 63.5% | 2 | 49.8% | 18.1% |
| history | 561 | 48.3% | 55.8% | 47.6% | 0 | 38.9% | 8.4% |
| hsm | 105 | 37.1% | 86.1% | 38.3% | 0 | 60.6% | 8.8% |
| iota | 7 | 0.0% | 31.0% | 22.4% | 0 | n/a | n/a |
| law | 24 | 37.5% | 48.1% | 35.5% | 0 | 26.9% | 5.4% |
| monero | 46 | 39.1% | 16.4% | 23.9% | 0 | 10.0% | 8.7% |
| politics | 105 | 69.5% | 85.9% | 51.1% | 1 | 55.8% | 16.1% |
| quant | 24 | 33.3% | 13.1% | 19.1% | 0 | 0.0% | 4.7% |
| travel | 70 | 30.0% | 19.5% | 39.5% | 0 | 25.8% | 11.7% |
| workplace | 25 | 12.0% | 24.7% | 31.4% | 0 | 40.0% | 4.4% |
| **all (micro)** | 1211 | 46.7% | 54.8% | 36.8% |  | 40.7% | 10.7% |

## Failure-case labels (proposed, unconfirmed)

See `research/cases/pilot_proposed_labels.md`. Track 2 (20 cases, drones + biology): continuation 9, self-contained 6, coreference 5; lexical mismatch 9, history drowns the turn 4, implicit reasoning link 2, gold debatable 1, success/history helps 4. Track 1: 3 iota cases.
