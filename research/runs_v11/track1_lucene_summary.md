# Track 1: dev summary

Pure-Python BM25, nDCG@10. The official 1a and 1b references use pyserini.

| domain | n queries / steps | 1a | Query+Step | Step-Only | Query+All | official 1a / 1b |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| bitcoin | 30 / 56 | 0.0362 | 0.0377 | 0.0469 | 0.0527 | 0.0370 / 0.0299 |
| cardano | 15 / 33 | 0.1207 | 0.0912 | 0.1326 | 0.0818 | 0.1027 / 0.0627 |
| economics | 25 / 51 | 0.0328 | 0.0426 | 0.0632 | 0.0319 | 0.0467 / 0.0463 |
| genealogy | 35 / 68 | 0.1491 | 0.1771 | 0.1199 | 0.1736 | 0.1949 / 0.2183 |
| history | 240 / 636 | 0.0615 | 0.0813 | 0.0639 | 0.0833 | 0.0873 / 0.1015 |
| hsm | 45 / 105 | 0.2467 | 0.2459 | 0.1473 | 0.2522 | 0.2489 / 0.2140 |
| iota | 3 / 8 | 0.4316 | 0.4539 | 0.2827 | 0.4539 | 0.3309 / 0.4195 |
| law | 11 / 23 | 0.0304 | 0.0505 | 0.0956 | 0.0521 | 0.0574 / 0.0549 |
| monero | 19 / 28 | 0.0349 | 0.0209 | 0.0168 | 0.0209 | 0.0320 / 0.0113 |
| politics | 45 / 119 | 0.2815 | 0.2652 | 0.1738 | 0.2869 | 0.2625 / 0.2371 |
| quant | 10 / 15 | 0.0000 | 0.0000 | 0.1075 | 0.0000 | 0.0237 / 0.0403 |
| travel | 30 / 52 | 0.0396 | 0.0387 | 0.0691 | 0.0545 | 0.0442 / 0.0645 |
| workplace | 11 / 20 | 0.0000 | 0.0309 | 0.2112 | 0.0433 | 0.0230 / 0.0297 |

Macro averages over available domains: 1a 0.1127, 1b_query+step 0.1181, 1b_step_only 0.1177, 1b_query+all 0.1221.

## Paired bootstrap

10,000 resamples of steps within each domain, seed 0; then macro average across domains.

| contrast | delta | 95% CI | domains |
| --- | ---: | --- | ---: |
| Step-Only - Query+Step | -0.0004 | [-0.0275, +0.0244] | 13 |
| Query+All - Query+Step | +0.0039 | [-0.0020, +0.0099] | 13 |

Query+All assigns the same ranking to every step of a query. The corpus is shared across train and dev; only topics are split.
