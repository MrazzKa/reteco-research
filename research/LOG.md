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
