# Track 2: dev summary

Pure-Python BM25, nDCG@10. Official references use pyserini. Oracle columns require gold annotations and are not deployable systems.

| domain | source | n | current | questions | answers | history | reasoning oracle | prior-gold oracle | recycled gold | official current/history |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| biology | BRIGHT | 115 | 0.1962 | 0.3198 | 0.5710 | 0.5509 |  |  |  | 0.2034 / 0.6065 |
| drones | StackExchange | 38 | 0.1235 | 0.2280 | 0.2767 | 0.2590 |  |  |  | 0.1695 / 0.2954 |
| earth_science | BRIGHT | 133 | 0.2070 | 0.4302 | 0.6123 | 0.6061 |  |  |  | 0.2195 / 0.6264 |
| economics | BRIGHT | 92 | 0.1783 | 0.2781 | 0.4573 | 0.4322 |  |  |  | 0.1629 / 0.4739 |
| hardware | StackExchange | 58 | 0.1559 | 0.2110 | 0.3136 | 0.2899 |  |  |  | 0.1605 / 0.3378 |
| law | StackExchange | 66 | 0.1356 | 0.2712 | 0.3687 | 0.3508 |  |  |  | 0.1147 / 0.3437 |
| medicalsciences | StackExchange | 44 | 0.0973 | 0.0965 | 0.1446 | 0.1282 |  |  |  | 0.1168 / 0.1730 |
| politics | StackExchange | 54 | 0.1458 | 0.2015 | 0.3147 | 0.3016 |  |  |  | 0.1514 / 0.3219 |
| psychology | BRIGHT | 99 | 0.2369 | 0.3490 | 0.5419 | 0.5226 |  |  |  | 0.2596 / 0.5726 |
| robotics | BRIGHT | 75 | 0.1628 | 0.3078 | 0.4941 | 0.4709 |  |  |  | 0.1574 / 0.5123 |
| sustainable_living | BRIGHT | 84 | 0.2959 | 0.3861 | 0.5334 | 0.5257 |  |  |  | 0.2938 / 0.5531 |

## Macro averages

| group | n domains | 2a_current | 2a_hist_questions_only | 2a_hist_answers_only | 2a_history | 2a_ORACLE_hist+reasoning | 2a_ORACLE_prev_turn_gold | history - current |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| all | 11 | 0.1759 | 0.2799 | 0.4208 | 0.4034 | 0.0000 | 0.0000 | 0.2275 |
| BRIGHT | 6 | 0.2128 | 0.3452 | 0.5350 | 0.5181 | 0.0000 | 0.0000 | 0.3052 |
| StackExchange | 5 | 0.1316 | 0.2016 | 0.2837 | 0.2659 | 0.0000 | 0.0000 | 0.1343 |

Complete source separation: yes (min BRIGHT +0.2298; max StackExchange +0.2152).

## Paired bootstrap

10,000 resamples of turns within each domain, seed 0; then macro average across domains. Turns in one conversation are dependent, so these intervals may be too narrow for new conversations.

| contrast | delta | 95% CI | domains |
| --- | ---: | --- | ---: |
| history - current | +0.2275 | [+0.2051, +0.2507] | 11 |
| answers - questions | +0.1408 | [+0.1233, +0.1590] | 11 |
| history - answers | -0.0173 | [-0.0234, -0.0114] | 11 |

## Turn depth

Each cell is the macro average of available per-domain depth means. Domain counts vary at deeper turns.

| condition | T1 | T2 | T3 | T4 | T5+ |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2a_current | 0.2554 | 0.1787 | 0.1452 | 0.1294 | 0.0991 |
| 2a_hist_questions_only | 0.2554 | 0.2923 | 0.2977 | 0.2742 | 0.2420 |
| 2a_hist_answers_only | 0.2554 | 0.4800 | 0.4805 | 0.4824 | 0.4354 |
| 2a_history | 0.2554 | 0.4564 | 0.4588 | 0.4572 | 0.3774 |
| 2a_ORACLE_hist+reasoning |  |  |  |  |  |

## Reading

Compare the paired contrasts above before attributing the history gain. Prior answers are reference answers derived from gold passages, and gold recycling is common. These are associations, not proof of a causal mechanism. The hidden-test history and reasoning fields have not been verified.
