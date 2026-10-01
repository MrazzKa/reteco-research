# Research log

One entry per run. If it is not here, it did not happen and cannot be reported.

Template:

```
## YYYY-MM-DD HH:MM — <short name>
commit:      <research repo sha> | upstream: <RETECO sha>
split:       train | dev        domains: <...>
command:     <exact command>
system:      <retriever / model / strategy>
params:      <k1, b, top-k, seed, ...>
metric:      nDCG@10 (pytrec_eval)
result:      <number>           expected: <number>   delta: <...>
runtime:     <...>              peak RAM: <...>
notes:       <...>
conclusion:  <one sentence>
```

---

## 2026-09-14 17:18 — upstream checkout
upstream: `23093c30e568a337c6293de4c58ffcccddbded5b` (2026-08-30, "Add icons and an entrance to the News list")
Repo contents: `starter_kit/` (official + pure-Python baselines, scorer, format
checker, dataset card, baseline results) and `docs/` (task site + curated sample
data: 5 TEMPO examples / 26 gold docs, 4 RECOR conversations / 13 turns / 15 docs).
conclusion: Official baseline numbers in the handoff notes match
`BASELINE_RESULTS.md` exactly — 1a 0.0967, 1b 0.1063, 2a 0.1827, 2a+hist 0.4379 (dev).

## 2026-09-14 17:20 — pipeline smoke test on curated sample
command: `python scripts/smoke_sample.py ./RETECO`
system:  starter-kit pure-Python BM25 (k1=0.9, b=0.4) + starter-kit scorer, no deps
result:  1a nDCG@10 0.7821 · 2a current 0.7331 · 2a +history 0.7824
expected: **not comparable** — the sample corpus contains only gold passages
(26 and 15 docs), so these are plumbing checks, not retrieval scores.
notes:
- Sample Track-2 qrels use `ex_111149#turn1`; `bm25_baseline.py` emits
  `ex_111149_turn_1`. Unnormalised, every topic scores 0.0 with no error raised.
  32 qids rewritten by the script.
- Turn-depth breakdown moved in the expected direction when history was added:
  T1 0.9165 → 0.9165 (unchanged, correct — no history exists at T1),
  T2 0.7144 → 0.8137, T3 0.5322 → 0.5789, T4 0.8773 → 0.9349.
  Directionally consistent with RECOR, on 13 turns — worth nothing statistically.
- Sample `steps.jsonl` records carry no nested `steps` field; the release is
  documented to nest them. Verify after download before trusting any 1b run.
conclusion: Read → BM25 → TREC run → official scorer works end to end. Safe to
download the release.

## 2026-09-14 17:21 — inspection script dry run
command: `python scripts/inspect_release.py --data fake_data --splits dev --samples 0`
notes: run against a release-shaped tree assembled from the curated sample, to
exercise the code path without the 4.5 GB download. Reported corpus/query length
distributions, gold-per-item counts, and 100% gold-id-in-corpus integrity.
conclusion: Script runs; **not yet validated against the real release.**

## [ ] next — download release, then PHASE C/D

## 2026-09-21 — selected-domain release download (user run)
upstream: `23093c30e568a337c6293de4c58ffcccddbded5b`
split: train and dev    domains: iota (Track 1), drones and biology (Track 2)
command: `& $py reteco-research\scripts\get_data.py --track1 iota --track2 drones biology`
system: Hugging Face release downloader
result: 23 files fetched; data root `D:\dev\semeval-reteco\reteco_data`
runtime: not separately measured    peak RAM: not measured
notes: User-supplied terminal output; listing showed 13 Track-1 and 11 Track-2 domains.
conclusion: Selected release domains are available locally.

## 2026-09-21 — release structure and integrity (user run)
split: train and dev    domains: iota, drones, biology
command: `& $py reteco-research\scripts\check_open_questions.py --data reteco_data`; `& $py reteco-research\scripts\inspect_release.py --data reteco_data --out reteco-research\research\data_report.md`
system: field inventory and corpus/qrels inspection
result: iota train `excluded_ids` non-empty 0/10; steps nested under `steps`; Track-2 `subquestion_reasoning` present in 504/504 inspected turns; all reported gold IDs present in the selected corpora.
runtime: not measured    peak RAM: not measured
notes: The hidden test field inventory remains unknown.
conclusion: Selected release data matches the expected schema and passes gold-ID integrity checks.

## 2026-09-21 — first selected-domain dev runs (user run)
upstream: `23093c30e568a337c6293de4c58ffcccddbded5b`
split: dev    domains: iota, drones, biology
command: `& $py reteco-research\scripts\week1_run.py --data reteco_data --kit RETECO\starter_kit --split dev --track1 iota --track2 drones biology --cases 8 --out reteco-research\research\week1`
system: FastBM25, k1=0.9, b=0.4, top 100; nDCG@10 via starter-kit ir_metrics
result: iota 1a 0.2346 (n=3), 1b query+step 0.2500 (n=8); drones 2a current 0.0668, history 0.1898 (n=38); biology 2a current 0.1880, history 0.5426 (n=115). All other conditions are recorded in `week1/results.md`.
runtime: 240 s total    peak RAM: not measured
notes: Differences from official pyserini dev references exceed 0.05 for iota 1b (-0.0789), drones current (-0.1027) and history (-0.1056), and biology history (-0.0639). Implementations use different analyzers; no causal explanation established. Fixed-seed case sheets were generated but not hand-labelled.
conclusion: History gains are positive in both Track-2 domains, and prior-answer-only queries outscore prior-question-only queries; full-domain confirmation is pending.

## 2026-09-21 06:06 — local curated-sample smoke test
upstream: `23093c30e568a337c6293de4c58ffcccddbded5b`
split: curated sample (not train or dev)    domains: sample Track 1 and Track 2
command: `$env:PYTHONUTF8='1'; & 'D:\dev\semeval-reteco\.venv\Scripts\python.exe' 'reteco-research\scripts\smoke_sample.py' 'RETECO'` from `D:\dev\semeval-reteco`
system: starter-kit pure-Python BM25 and official sample scorer
result: 1a 0.7821; 2a current 0.7331; 2a history 0.7824 nDCG@10
runtime: under 1 second after startup    peak RAM: not measured
notes: Resolved the RETECO argument to an absolute path in `smoke_sample.py`. The first retry without `PYTHONUTF8` failed on Windows cp1251 decoding; rerunning with it passed. Sample corpus contains only gold passages.
conclusion: Sample pipeline works locally; these scores do not measure retrieval quality.

## 2026-09-14 17:45 — upstream TEMPO + RECOR code read
pinned: Tempo `8731487` (2026-02-16) · RECOR `ba05460` (2026-01-14)
notes: see `notes/upstream_code_findings.md`. Three things that change how we
plan: (a) TEMPO's `retrieval_bm25` applies `excluded_ids`, RETECO's starter kit
never mentions the field — check after download; (b) RECOR's "+Reasoning"
condition is literal concatenation of the gold `subquestion_reasoning` string
onto the query, i.e. an oracle, and a stronger untested condition
(history+reasoning+metadata) exists upstream; (c) 6 of 11 RECOR domains are
BRIGHT-derived, so a BRIGHT-vs-StackExchange per-domain split is a free diagnostic.
conclusion: The interesting Track-2 question is generating the reasoning string,
not consuming it. Confirmed RETECO pin contains the latest starter_kit commit `877522b`.

## 2026-09-14 17:55 — accepted task proposal read (6 pp. PDF from the repo)
notes: `notes/proposal_findings.md`. Material facts: hidden test is ~350 Track-1
queries and ~200 Track-2 turns (small — plan significance testing, not point
estimates); 1b permits Step-Only / Query+Step / Query+All, and only Query+Step
has published numbers; official error taxonomies already exist (TEMPO 10 temporal
reasoning classes, RECOR 6 discourse-dependency types with `self-contained` at
24%); 2a is defined as prior turns + current question, with no reasoning field.
conclusion: First cheap experiment identified — the three permitted 1b query
strategies, one variable, official metric, no new model. Track-1 case strengthened:
Bethard's time-normalization line attacks TEMPO's named failure (Temporal
Coverage@10 = 71.4%) directly.

## 2026-09-20 22:40 — pre-meeting analysis (no local data yet)
source: official `BASELINE_RESULTS.md` + curated sample.
- +History gain by RECOR source, dev: BRIGHT-derived (6) +0.341 vs StackExchange
  (5) +0.152; complete separation (min BRIGHT +0.259 > max SE +0.229), same on
  train (+0.295 > +0.281). Exact rank-test p = 2/462 ≈ 0.004 two-sided. n=11
  domains, source confounded with construction pipeline.
- `conversation_history` = `Q:`/`A:` blocks; the A: lines are prior turns'
  reference answers verbatim (sample: 13/13). Later turns reuse earlier gold:
  8/9 any, 6/9 all, mean share 0.83 (sample, n=9 — direction only).
- Sample-only ablation (drones-like sample, n=13, meaningless statistically):
  current 0.7331 · +questions 0.7554 · +answers 0.8095 · +full history 0.7824.
- Official iota: 1a train 0.0199 vs dev 0.2083; 1b 0.0000 vs 0.3289 → small-domain noise.
code: `scripts/week1_run.py` (FastBM25 = starter-kit BM25 with inverted index;
randomised self-test: identical top-100 on 200 queries × 3000 docs; synthetic
benchmark 50k docs: ~0.14 s/query short, ~0.9 s/query with history).
conclusion: History-composition ablation and gold-recycling rate added to the
week-1 run; verify on real dev data (drones, biology) before claiming anything.

## 2026-09-21 06:35 США - горное время (зима) — Track 2 economics dev run
split: dev    domains: economics
command: `D:\dev\semeval-reteco\.venv\Scripts\python.exe D:\dev\semeval-reteco\reteco-research\scripts\week1_run.py --data reteco_data --kit RETECO\starter_kit --split dev --track2 economics --cases 5 --seed 20260921 --out reteco-research\research\week1_t2\economics`
system: FastBM25 k1=0.9 b=0.4, top 100; fixed seed 20260921
result: FAILED (see error.log)
runtime: 95s    peak RAM: not measured
notes: console and errors in `reteco-research\research\week1_t2\economics`; exit code 1.
conclusion: No result; investigate failure.

## 2026-09-21 — full-release download and inspection
split: train and dev    domains: all 13 Track-1 and 11 Track-2 domains
command: `& .\.venv\Scripts\python.exe reteco-research\scripts\get_data.py --all --out reteco_data`; `& .\.venv\Scripts\python.exe reteco-research\scripts\check_open_questions.py --data reteco_data`; `& .\.venv\Scripts\python.exe reteco-research\scripts\inspect_release.py --data reteco_data --samples 0 --out reteco-research\research\data_report.md`
system: release downloader and integrity checks
result: 201 release files fetched; 0/1730 Track-1 records have non-empty `excluded_ids`; 2971/2971 Track-2 turns carry `subquestion_reasoning`; all reported train/dev gold IDs are in their domain corpora.
runtime: download 212s; inspection runtime not measured    peak RAM: not measured
notes: Exact data inventory and per-domain integrity counts are in `research/data_report.md`. Hidden-test fields remain unknown.
conclusion: Full train/dev release is available and structurally consistent with the research scripts.

## 2026-09-21 — correction to nine Track-2 process statuses
split: dev    domains: earth_science, economics, hardware, law, medicalsciences, politics, psychology, robotics, sustainable_living
command: `python scripts/aggregate_week1.py --track 2 --runs research/week1_t2 --initial research/week1 --data ../reteco_data --kit ../RETECO/starter_kit --out research/week1_t2/summary.md`
system: re-score the saved top-10 run files against each domain's dev qrels
result: all nine domains completed their retrieval and wrote valid run files, `results.json`, and case sheets. Together with biology and drones, the summary covers 11/11 domains; macro current 0.1445, history 0.3661.
runtime: aggregation 9s    peak RAM: not measured
notes: The nine Track-2 `FAILED` statuses in this log refer only to a Windows cp1251 `UnicodeEncodeError` while printing the finished report. Retrieval had finished before that exception. The scores were independently re-scored from the run files and matched `results.json`; no rerun or case resampling was done.
conclusion: The nine Track-2 runs are valid despite process exit code 1 at final console printing.

## 2026-09-21 06:36 США - горное время (зима) — Track 2 hardware dev run
split: dev    domains: hardware
command: `D:\dev\semeval-reteco\.venv\Scripts\python.exe D:\dev\semeval-reteco\reteco-research\scripts\week1_run.py --data reteco_data --kit RETECO\starter_kit --split dev --track2 hardware --cases 5 --seed 20260921 --out reteco-research\research\week1_t2\hardware`
system: FastBM25 k1=0.9 b=0.4, top 100; fixed seed 20260921
result: FAILED (see error.log)
runtime: 76s    peak RAM: not measured
notes: console and errors in `reteco-research\research\week1_t2\hardware`; exit code 1.
conclusion: No result; investigate failure.

## 2026-09-21 06:38 США - горное время (зима) — Track 2 earth_science dev run
split: dev    domains: earth_science
command: `D:\dev\semeval-reteco\.venv\Scripts\python.exe D:\dev\semeval-reteco\reteco-research\scripts\week1_run.py --data reteco_data --kit RETECO\starter_kit --split dev --track2 earth_science --cases 5 --seed 20260921 --out reteco-research\research\week1_t2\earth_science`
system: FastBM25 k1=0.9 b=0.4, top 100; fixed seed 20260921
result: FAILED (see error.log)
runtime: 241s    peak RAM: not measured
notes: console and errors in `reteco-research\research\week1_t2\earth_science`; exit code 1.
conclusion: No result; investigate failure.

## 2026-09-21 06:38 США - горное время (зима) — Track 2 law dev run
split: dev    domains: law
command: `D:\dev\semeval-reteco\.venv\Scripts\python.exe D:\dev\semeval-reteco\reteco-research\scripts\week1_run.py --data reteco_data --kit RETECO\starter_kit --split dev --track2 law --cases 5 --seed 20260921 --out reteco-research\research\week1_t2\law`
system: FastBM25 k1=0.9 b=0.4, top 100; fixed seed 20260921
result: FAILED (see error.log)
runtime: 83s    peak RAM: not measured
notes: console and errors in `reteco-research\research\week1_t2\law`; exit code 1.
conclusion: No result; investigate failure.

## 2026-09-21 06:38 США - горное время (зима) — Track 2 medicalsciences dev run
split: dev    domains: medicalsciences
command: `D:\dev\semeval-reteco\.venv\Scripts\python.exe D:\dev\semeval-reteco\reteco-research\scripts\week1_run.py --data reteco_data --kit RETECO\starter_kit --split dev --track2 medicalsciences --cases 5 --seed 20260921 --out reteco-research\research\week1_t2\medicalsciences`
system: FastBM25 k1=0.9 b=0.4, top 100; fixed seed 20260921
result: FAILED (see error.log)
runtime: 50s    peak RAM: not measured
notes: console and errors in `reteco-research\research\week1_t2\medicalsciences`; exit code 1.
conclusion: No result; investigate failure.

## 2026-09-21 06:39 США - горное время (зима) — Track 2 politics dev run
split: dev    domains: politics
command: `D:\dev\semeval-reteco\.venv\Scripts\python.exe D:\dev\semeval-reteco\reteco-research\scripts\week1_run.py --data reteco_data --kit RETECO\starter_kit --split dev --track2 politics --cases 5 --seed 20260921 --out reteco-research\research\week1_t2\politics`
system: FastBM25 k1=0.9 b=0.4, top 100; fixed seed 20260921
result: FAILED (see error.log)
runtime: 57s    peak RAM: not measured
notes: console and errors in `reteco-research\research\week1_t2\politics`; exit code 1.
conclusion: No result; investigate failure.

## 2026-09-21 06:41 США - горное время (зима) — Track 2 robotics dev run
split: dev    domains: robotics
command: `D:\dev\semeval-reteco\.venv\Scripts\python.exe D:\dev\semeval-reteco\reteco-research\scripts\week1_run.py --data reteco_data --kit RETECO\starter_kit --split dev --track2 robotics --cases 5 --seed 20260921 --out reteco-research\research\week1_t2\robotics`
system: FastBM25 k1=0.9 b=0.4, top 100; fixed seed 20260921
result: FAILED (see error.log)
runtime: 128s    peak RAM: not measured
notes: console and errors in `reteco-research\research\week1_t2\robotics`; exit code 1.
conclusion: No result; investigate failure.

## 2026-09-21 06:42 США - горное время (зима) — Track 2 psychology dev run
split: dev    domains: psychology
command: `D:\dev\semeval-reteco\.venv\Scripts\python.exe D:\dev\semeval-reteco\reteco-research\scripts\week1_run.py --data reteco_data --kit RETECO\starter_kit --split dev --track2 psychology --cases 5 --seed 20260921 --out reteco-research\research\week1_t2\psychology`
system: FastBM25 k1=0.9 b=0.4, top 100; fixed seed 20260921
result: FAILED (see error.log)
runtime: 185s    peak RAM: not measured
notes: console and errors in `reteco-research\research\week1_t2\psychology`; exit code 1.
conclusion: No result; investigate failure.

## 2026-09-21 06:43 США - горное время (зима) — Track 2 sustainable_living dev run
split: dev    domains: sustainable_living
command: `D:\dev\semeval-reteco\.venv\Scripts\python.exe D:\dev\semeval-reteco\reteco-research\scripts\week1_run.py --data reteco_data --kit RETECO\starter_kit --split dev --track2 sustainable_living --cases 5 --seed 20260921 --out reteco-research\research\week1_t2\sustainable_living`
system: FastBM25 k1=0.9 b=0.4, top 100; fixed seed 20260921
result: FAILED (see error.log)
runtime: 96s    peak RAM: not measured
notes: console and errors in `reteco-research\research\week1_t2\sustainable_living`; exit code 1.
conclusion: No result; investigate failure.

## 2026-09-21 07:04 США - горное время (зима) — Track 1 quant dev run
split: dev    domains: quant
command: `D:\dev\semeval-reteco\.venv\Scripts\python.exe D:\dev\semeval-reteco\reteco-research\scripts\week1_run.py --data reteco_data --kit RETECO\starter_kit --split dev --track1 quant --cases 5 --seed 20260921 --out reteco-research\research\week1_t1\quant`
system: FastBM25 k1=0.9 b=0.4, top 100; fixed seed 20260921
result: 1a=0.0000 (n=10); 1b_query+step=0.0000 (n=15); 1b_step_only=0.1286 (n=15); 1b_query+all=0.0000 (n=15)
runtime: 63s    peak RAM: not measured
notes: console and errors in `reteco-research\research\week1_t1\quant`; exit code 0.
conclusion: Completed fixed dev conditions.

## 2026-09-21 07:09 США - горное время (зима) — Track 1 cardano dev run
split: dev    domains: cardano
command: `D:\dev\semeval-reteco\.venv\Scripts\python.exe D:\dev\semeval-reteco\reteco-research\scripts\week1_run.py --data reteco_data --kit RETECO\starter_kit --split dev --track1 cardano --cases 5 --seed 20260921 --out reteco-research\research\week1_t1\cardano`
system: FastBM25 k1=0.9 b=0.4, top 100; fixed seed 20260921
result: 1a=0.1108 (n=15); 1b_query+step=0.0760 (n=33); 1b_step_only=0.0984 (n=33); 1b_query+all=0.0699 (n=33)
runtime: 281s    peak RAM: not measured
notes: console and errors in `reteco-research\research\week1_t1\cardano`; exit code 0.
conclusion: Completed fixed dev conditions.

## 2026-09-21 07:11 США - горное время (зима) — Track 1 law dev run
split: dev    domains: law
command: `D:\dev\semeval-reteco\.venv\Scripts\python.exe D:\dev\semeval-reteco\reteco-research\scripts\week1_run.py --data reteco_data --kit RETECO\starter_kit --split dev --track1 law --cases 5 --seed 20260921 --out reteco-research\research\week1_t1\law`
system: FastBM25 k1=0.9 b=0.4, top 100; fixed seed 20260921
result: 1a=0.0293 (n=11); 1b_query+step=0.0476 (n=23); 1b_step_only=0.0767 (n=23); 1b_query+all=0.0623 (n=23)
runtime: 99s    peak RAM: not measured
notes: console and errors in `reteco-research\research\week1_t1\law`; exit code 0.
conclusion: Completed fixed dev conditions.

## 2026-09-21 07:14 США - горное время (зима) — Track 1 monero dev run
split: dev    domains: monero
command: `D:\dev\semeval-reteco\.venv\Scripts\python.exe D:\dev\semeval-reteco\reteco-research\scripts\week1_run.py --data reteco_data --kit RETECO\starter_kit --split dev --track1 monero --cases 5 --seed 20260921 --out reteco-research\research\week1_t1\monero`
system: FastBM25 k1=0.9 b=0.4, top 100; fixed seed 20260921
result: 1a=0.0152 (n=19); 1b_query+step=0.0103 (n=28); 1b_step_only=0.0065 (n=28); 1b_query+all=0.0103 (n=28)
runtime: 185s    peak RAM: not measured
notes: console and errors in `reteco-research\research\week1_t1\monero`; exit code 0.
conclusion: Completed fixed dev conditions.

## 2026-09-21 07:16 США - горное время (зима) — Track 1 workplace dev run
split: dev    domains: workplace
command: `D:\dev\semeval-reteco\.venv\Scripts\python.exe D:\dev\semeval-reteco\reteco-research\scripts\week1_run.py --data reteco_data --kit RETECO\starter_kit --split dev --track1 workplace --cases 5 --seed 20260921 --out reteco-research\research\week1_t1\workplace`
system: FastBM25 k1=0.9 b=0.4, top 100; fixed seed 20260921
result: 1a=0.0184 (n=11); 1b_query+step=0.0235 (n=20); 1b_step_only=0.1861 (n=20); 1b_query+all=0.0735 (n=20)
runtime: 97s    peak RAM: not measured
notes: console and errors in `reteco-research\research\week1_t1\workplace`; exit code 0.
conclusion: Completed fixed dev conditions.

## 2026-09-21 06:35–07:14 — Track 1 politics dev run (started directly, not via run_remaining)
split: dev    domains: politics
command: `week1_run.py --data reteco_data --kit RETECO\starter_kit --split dev --track1 politics --cases 5 --seed 20260921 --out reteco-research\research\week1_t1\politics`
system: FastBM25 k1=0.9 b=0.4, top 100; fixed seed 20260921
result: 1a=0.2095 (n=45, ref 0.2550); 1b_query+step=0.2047 (n=119, ref 0.2306); 1b_step_only=0.1396; 1b_query+all=0.2233
runtime: 1a 238s; query+step 876s; step_only 103s; query+all ~18 min (started before the query cache was added)
notes: timing drove the Track-1 subset decision: all 13 domains did not fit the ~90 min budget. Subset = every corpus < 300 MB plus politics (timed); skipped genealogy, bitcoin, hsm, history. Chosen by cost before seeing scores.
conclusion: Completed; on the largest dev domain run, Step-Only is worse than Query+Step, opposite to the small domains.

## 2026-09-21 07:15 — Track 1 explicit-date feasibility, fast version (train)
split: train    domains: all 13 Track-1
command: `python3 scripts/date_quick.py --data ../reteco_data --out research/results/date_feasibility_quick.md --workers 5` (WSL)
system: regex only (years, decades, month-year; same patterns as date_feasibility.py); contrast = reservoir sample of 2,000 corpus docs/domain, seed 0
result: queries dated 46.7%; gold dated 54.8%; random dated 36.8%; span overlap gold 40.7% vs random 10.7% (micro, 1,211 queries)
runtime: 125s
notes: date_feasibility.py (BM25 non-gold top-10 contrast) was still running on `history` on Windows at the time and had not produced output. Random documents are an easier contrast than BM25 negatives.
conclusion: Explicit dates carry a gold-vs-random signal for about half of the queries; E2 is worth a first version, strongly domain-dependent.

## 2026-09-21 07:15 — aggregate_week1.py fix
notes: Track-1 per-topic re-scoring used step qrels for 1a as well; fixed to use qrels_dev.txt for 1a and qrels_steps_dev.txt for 1b. The run-file vs results.json consistency check now passes for all Track-1 domains. Track-2 aggregation unaffected.

## 2026-09-21 07:19 MST — Track 1 economics dev run
split: dev    domains: economics
command: `/usr/bin/python3 /mnt/d/dev/semeval-reteco/reteco-research/scripts/week1_run.py --data reteco_data --kit RETECO/starter_kit --split dev --track1 economics --cases 5 --seed 20260921 --out reteco-research/research/week1_t1/economics`
system: FastBM25 k1=0.9 b=0.4, top 100; fixed seed 20260921
result: 1a=0.0385 (n=25); 1b_query+step=0.0312 (n=51); 1b_step_only=0.0600 (n=51); 1b_query+all=0.0345 (n=51)
runtime: 249s    peak RAM: not measured
notes: console and errors in `reteco-research/research/week1_t1/economics`; exit code 0.
conclusion: Completed fixed dev conditions.

## 2026-09-21 07:22 MST — Track 1 travel dev run
split: dev    domains: travel
command: `/usr/bin/python3 /mnt/d/dev/semeval-reteco/reteco-research/scripts/week1_run.py --data reteco_data --kit RETECO/starter_kit --split dev --track1 travel --cases 5 --seed 20260921 --out reteco-research/research/week1_t1/travel`
system: FastBM25 k1=0.9 b=0.4, top 100; fixed seed 20260921
result: 1a=0.0225 (n=30); 1b_query+step=0.0264 (n=52); 1b_step_only=0.0522 (n=52); 1b_query+all=0.0274 (n=52)
runtime: 443s    peak RAM: not measured
notes: console and errors in `reteco-research/research/week1_t1/travel`; exit code 0.
conclusion: Completed fixed dev conditions.

## 2026-09-21 — repository restructure (no new runs)
notes: Folders renamed; paths in earlier entries refer to the old names:
`research/week1` -> `research/runs/pilot`, `research/week1_t1` -> `research/runs/track1`,
`research/week1_t2` -> `research/runs/track2`. Case sheets moved to `research/cases/`
(per-domain sheets merged into `wide_track{1,2}.md`, unchanged content). Per-domain
`results.md` removed (same numbers in `results.json`). Notes, handoff and meeting brief moved
out of the repo. Codex's `date_feasibility.py` process on Windows was stopped before finishing
(no output); `date_quick.py` results stand. Verified after the move: `--selftest` OK; both
aggregations re-run from the new paths reproduce every table row in `research/RESULTS.md`.

## 2026-09-28 — data v1.1 downloaded and verified
split: n/a    domains: all 13 Track-1
command: `python3 scripts/get_data.py --out reteco_data_v11 --track1 <all 13>` (WSL)
result: 1,167,159 Track-1 documents, matching the organisers' announcement exactly (v1.0 had 1,654,055). Per-domain reduction 7% (iota) to 50% (bitcoin). `duplicate_map.json` present in every domain. Track 2 unchanged, still read from `reteco_data/`.
notes: v1.0 kept at `reteco_data/` for comparison. Official v1.1 references (1a dev 0.1147, 1b dev 0.1177) were copied into `scripts/week1_run.py` REF from the updated starter-kit BASELINE_RESULTS.md; our REF macro reproduces both exactly.
conclusion: All Track-1 numbers from here on are v1.1; week-1 Track-1 numbers are v1.0 and are not comparable.

## 2026-09-28 — BM25 reproduction with a Lucene-style analyzer (bm25s)
split: dev    domains: all 13 Track-1 (v1.1), all 11 Track-2
command: `python3 scripts/bm25s_run.py --data <root> --kit RETECO/starter_kit --split dev --track {1,2} --domains <all> --analyzer {lucene,plain} --out research/runs_v11/...`
system: bm25s, method="lucene", k1=0.9, b=0.4, top-100; `lucene` = Snowball English stemmer + English stopwords, `plain` = no stemming/stopwords
result: Track 1 macro 1a 0.1127 (official 0.1147), 1b_query+step 0.1181 (official 0.1177). Track 2 macro current 0.1759 (official 0.1827), +history 0.4034 (official 0.4379).
runtime: Track 1 dev 1087s (lucene) / 477s (plain); Track 2 dev 50s / 57s
notes: Track 2 attribution of the week-1 gap: kit pure-Python 0.1445 -> bm25s-plain 0.1490 (BM25 variant) -> bm25s-lucene 0.1759 (stemming + stopwords) -> official 0.1827. Stemming accounts for most of it; ~0.007 (current) and ~0.035 (history) remain unexplained.
conclusion: The macro-level reproduction gap is essentially closed on Track 1 and mostly closed on Track 2; per-domain differences of up to 0.04 remain, so per-domain claims still need the official pipeline.

## 2026-09-28 — E1 revisited on all 13 Track-1 domains (v1.1, lucene analyzer)
split: dev    domains: all 13
result: macro 1a 0.1127; 1b Query+Step 0.1181, Step-Only 0.1177, Query+All 0.1221. Step-weighted (1,214 steps): 0.1124 / 0.0902 / 0.1168. Paired bootstrap: Step-Only - Query+Step -0.0004 [-0.0275, +0.0244]; Query+All - Query+Step +0.0039 [-0.0020, +0.0099].
notes: This overturns the week-1 reading (Step-Only +0.047 on 9 domains, pure-Python BM25, v1.0). That advantage came from small domains and a weaker analyzer.
conclusion: Negative result for E1: with a proper analyzer and all 13 domains, the three permitted 1b query strategies are indistinguishable.

## 2026-09-28 — dense encoder selection (TRAIN only)
split: train    domains: iota, quant, law (Track 1); conditions 1a and 1b_query+step
command: `python3 scripts/dense_rerank.py --split train --track 1 --domains iota quant law --model {bge-small,e5-small,minilm,arctic-s} --runs research/runs_v11/sel_track1_train/runs --max-len 256 --depth 100`
system: sentence-transformers on CPU, reranking the BM25 top-100; RRF variant fuses the dense order with the BM25 order
result: macro over the 6 (domain, condition) cells — BM25 0.0704; rerank: bge-small 0.2139, arctic-s 0.1940, minilm 0.1742, e5-small 0.1686; rrf is worse than rerank for every model (best 0.1724). Recall ceiling of the BM25 top-100: 0.3736.
notes: Selection was done on train precisely so that dev stays untouched; the dev numbers below use the selected model (bge-small, plain rerank) without further choices.
conclusion: bge-small chosen. Dense reranking roughly triples BM25 on train; RRF with BM25 hurts.

## 2026-09-28 — dense reranking on dev, Track 1 (11 of 13 domains at time of writing)
split: dev    domains: 11 Track-1 domains (genealogy, hsm still running)
result: macro 1a — BM25 0.0972 -> rerank 0.2326 (RRF 0.1630), recall cap 0.4161. macro 1b_query+step — BM25 0.1012 -> rerank 0.2437 (RRF 0.1757), cap 0.4741.
notes: Same 11 domains in every column. The official v1.1 BM25 baseline is 0.1147 (1a) / 0.1177 (1b) over all 13. Dense reranking is limited by BM25 recall: it reaches roughly 56% of the top-100 ceiling on 1a.
conclusion: A 33M-parameter off-the-shelf encoder reranking BM25's top-100 more than doubles nDCG@10 on CPU, with no training.

## 2026-09-28 — E2 explicit-date reranking: negative result (train)
split: train    domains: all 13 Track-1
command: `python3 scripts/date_rerank.py --split train --runs research/runs_v11/track1_train_lucene/runs --out research/runs_v11/e2_dates_train.json`
system: four fixed variants over the BM25 top-100 — promote date-matching documents over the whole list (`hard`), inside the top 20 / top 10, or fuse the two orders with RRF
result: macro base 0.1005; hard 0.0909 (-0.0096), top20 0.0945 (-0.0060), top10 0.0971 (-0.0034), rrf 0.0946 (-0.0059). No domain improved by more than +0.002; several lose 0.02-0.04.
notes: Last week's feasibility analysis compared gold with RANDOM corpus documents (41% vs 11% year overlap). Among BM25's top-100 — topically similar documents — the year signal no longer separates gold from non-gold, which is why every variant loses.
conclusion: E2 as specified is dead in this form. Reported as a negative result; a date-aware system would need the date signal inside the ranking function (or a recall stage), not as a post-hoc reorder of BM25's top-100.

## 2026-09-28 — dense reranking on dev, Track 2 (all 11 domains)
split: dev    domains: all 11
result: 2a_current — BM25 0.1759 -> rerank 0.2117, RRF 0.2172 (RRF beats BM25 in 11/11 domains), recall cap 0.5546. 2a_history — BM25 0.4034 -> rerank 0.3664, RRF 0.3981 (RRF beats BM25 in only 5/11), cap 0.8251.
notes: The loss is concentrated in the BRIGHT domains, where `conversation_history` carries the previous turns' reference answers (week-1 Finding 2): biology 0.5509 -> 0.4192, earth_science 0.6061 -> 0.3721. In the StackExchange domains reranking still helps (drones 0.2590 -> 0.3019, politics 0.3016 -> 0.4668).
conclusion: Dense reranking helps the current-turn condition everywhere and hurts the +history condition exactly where near-verbatim gold text sits in the query.

## 2026-09-28 — is the Track-2 history loss caused by the encoder's 256-token window? (train)
split: train    domains: drones, biology
command: `dense_rerank.py --split train --track 2 --domains drones biology --model bge-small --max-len {256,512}`
result: drones 2a_history — BM25 0.2546, @256 0.3701, @512 0.3603. biology 2a_history — BM25 0.5908, @256 0.4224, @512 0.4742. Current-turn: drones 0.1319 / 0.2662 / 0.2592; biology 0.2015 / 0.2213 / 0.2582.
conclusion: Truncation explains part of it (biology +0.05 from the longer window) but not the effect: at 512 tokens the reranker is still 0.12 below BM25 on biology history. The leakage explanation stands — where the query paraphrases the gold, lexical matching is close to optimal.

## 2026-09-28 — hsm dense reranking killed, rerun
notes: The hsm Track-1 reranking died without a traceback while five encoder jobs ran concurrently (7 GB RAM in WSL) — an out-of-memory kill. `results.json` for that batch therefore holds only genealogy, history and politics. Rerun alone as `dev_rerank/t1d`.
conclusion: Run at most 3 encoder processes at a time on this machine.

## 2026-10-01 — dense retrieval with an ANN index (Steve's week-2 direction)
plan: Steve asked to move the encoders from reranking to retrieval, with an ANN index over the
embedding vectors (ann-benchmarks: NGT-QG / Descartes). `scripts/ann_index.py` embeds a domain's
corpus once (vectors cached under `research/runs_v11/ann/emb/`), then runs (a) exact brute-force
cosine as the quality reference and (b) NGT (ANNG graph, cosine) over the same vectors, reporting
nDCG@10 for both, recall@10 of ANN against exact, index build time and per-query latency.
system: bge-small-en-v1.5, 256-token window, CPU; NGT via `ngtpy` (Linux wheels available).
notes: `hnswlib` has no wheels for this Python; faiss-cpu does, kept as a cross-check. NGT-QG
(the quantized variant, "qsgngt" in ann-benchmarks) is the next refinement after the plain graph.

## 2026-10-01 — measured embedding throughput (the binding constraint)
command: bge-small, 256-token window, 18 threads, 2,000 documents from the `history` corpus
result: **8 documents/second**, i.e. about 38 h for the 1,167,159 Track-1 documents and 17 h for
Track 2 on this machine. Vector storage is small: 1.7 GB float32 / 0.8 GB float16 for Track 1.
conclusion: For a full dense index the cost is embedding the corpus, not the ANN index or the
search. Scaling plan is therefore smallest-domains-first, plus an int8/ONNX export test.

## 2026-10-01 — dense retrieval + ANN on iota (first full-corpus dense index)
split: dev    domain: iota (9,680 docs, Track 1 v1.1)
command: `python3 scripts/ann_index.py --data ../../reteco_data_v11 --kit ../../RETECO/starter_kit --split dev --track 1 --domains iota --model bge-small --conditions 1a 1b_query+step --out ../research/runs_v11/ann`
system: bge-small-en-v1.5, 256-token window, CPU; exact brute-force cosine vs NGT (ANNG graph, cosine, epsilon 0.1)
result: 1a — exact 0.5581 (19.0 ms/query), ANN 0.5581 (3.4 ms/query), recall@10 vs exact 1.000, index build 3s.
        1b_query+step — exact 0.4984 (9.1 ms/query), ANN 0.4984 (2.5 ms/query), recall@10 1.000, build 3s.
        For comparison on the same domain: BM25 1a 0.4316; BM25 + bge rerank 0.6951; oracle over BM25 top-100 0.9440.
runtime: corpus embedding 1,034s for 9,680 docs (9 docs/s, CPU, shared machine); index build 3s
notes: At this corpus size the ANN approximation is free — identical rankings, 5x lower latency. Dense
retrieval alone beats BM25 (+0.127) but stays below BM25 + dense reranking (-0.137), so the pipeline
still wins over dense-only here. One small domain, 3 dev queries for 1a: not generalisable yet.
conclusion: The retrieval path works end to end. The open cost is embedding, not indexing or search.
