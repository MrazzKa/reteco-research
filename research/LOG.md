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

---

# Week 4 — GPU machine (2026-10-13, autonomous overnight session)

All runs below on the new laptop: RTX 4060 Laptop 8 GB, WSL2 Ubuntu, ~12 GB RAM visible,
i7-13650HX (20 threads), Python 3.14.4, torch 2.14.1+cu130, sentence-transformers 6.1.0,
transformers 5.19.0, bm25s 0.3.13, faiss-cpu 1.15.1, ngt 2.8.0.post1, numpy 2.5.4.
Data: `reteco_data_v11/` for **both** tracks. The local official repo `RETECO/` is now at
`eebd377` ("Open registration"), two commits after the earlier pin `23093c3`; the new
commits touch the website/news only (v1.1 announcement, registration link).
Run outputs: `research/runs_v12/` (embeddings, TREC runs and ANN indexes are git-ignored).
Seed for every sample and bootstrap: 20260921.

## 2026-10-13 15:27 — environment check and Track-2 data version
command: `nvidia-smi`; `python -c "import torch; ..."`; `free -g`; counts of `documents.jsonl`
result: CUDA available, 8,188 MiB VRAM, 11.7 GB RAM, 940 GB free disk. `reteco_data/` (v1.0)
  is not on this machine. Track 2 in v1.1: per-domain document, conversation, turn and qrels
  counts in `split_manifest.json` match `research/data_report.md` (made from v1.0) for every
  domain, and the task website states Track 2 is unchanged in v1.1. BM25 on Track-2 dev
  reproduces the week-2 numbers (below).
conclusion: Track 2 v1.1 = v1.0 for our purposes; README now points both tracks to `reteco_data_v11/`.

## 2026-10-13 15:30 — GPU encoding benchmark (bge-small)
command: `python3 gpu_bench.py --corpus ../../reteco_data_v11/track1_tempo/history/documents.jsonl --model bge-small --n 4000 --max-len {256,512} --batches ...`
system: `BAAI/bge-small-en-v1.5` rev 5c38ec7c, sentence-transformers (length-sorted batches), first 4,000 `history` documents
result: 256 tokens — fp16: 1,141 / 1,257 / 1,243 / 1,189 / 1,092 docs/s at batch 32/64/128/256/512
  (peak VRAM 0.15–1.24 GB); fp32: 507 / 485 / 404 / 360 / 350 docs/s. 512 tokens, fp16: 822 / 753 / 648
  docs/s at batch 64/128/256 (0.37–1.27 GB).
notes: batch 64 fp16 is best; larger batches are slower (padding inside a length-sorted batch grows).
  Previous CPU machine: 8 docs/s → ~150× faster.
outputs: `research/runs_v12/bench/bge-small_{256,512}.json`
conclusion: The whole release (1.67M docs) is ~30–40 min of encoding with bge-small; the 38-hour bottleneck is gone.

## 2026-10-13 15:35 — BM25 depth-1000, train+dev, both tracks; tie-breaking bug found
command: `python3 bm25s_run.py --data ../../reteco_data_v11 --kit ../../RETECO/starter_kit --splits train dev --track {1,2} --domains <all> --analyzer lucene --k 1000 --conditions <1a 1b_query+step | 2a_current 2a_history> --threads 8 --out ../research/runs_v12/bm25/t{1,2}`
system: bm25s-lucene (k1=0.9, b=0.4, Snowball + stopwords) as week 2; new options: `--k` depth, `--splits` (one index for both splits), `--conditions`.
result (first attempt, before the fix): Track-2 dev 2a_history macro 0.4032 instead of 0.4034; per domain
  biology 0.5509 → 0.5478 and robotics 0.4709 → 0.4711, everything else identical.
diagnosis: biology dev 2a_history with k=100 gives 0.5509, with k=1000 gives 0.5478; the thread count does
  not matter. 29/115 topics have a different top 10, always among documents with **exactly equal scores**
  (e.g. `dealing-with-fear-of-the-dark_6_6 / _7_6 / _8_6`, identical passages). bm25s returns tied
  documents in an order that depends on k.
fix: `search()` now sorts each list by (−score, doc id) — the starter kit's rule; `--no-tiebreak` keeps the old
  behaviour. With the fix, k=100 and k=1000 both give 0.5529 on biology. The aborted run's log is kept
  (`logs/bm25_deep_untiebroken_aborted.log`).
result (final): Track 1 dev macro 1a **0.1127**, 1b_query+step **0.1181** — identical to week 2 in all 13
  domains. Track 1 train 1a 0.1005, 1b 0.1101 (monero +0.0006 vs week 2, a tie effect). Track 2 dev
  2a_current **0.1758** (week 2 0.1759), 2a_history **0.4034**; train 0.1667 / 0.4082.
runtime: Track 2 50 s (peak RSS 0.4 GB); Track 1 7 min 18 s (peak RSS 3.2 GB), both splits, both conditions.
conclusion: Baseline reproduced; scores are now independent of run depth. Ties matter only where corpora hold duplicate passages (see the order study).

## 2026-10-13 15:37–17:10 — full dense index, bge-small, 512 tokens, all 24 domains
command: `python3 dense_index.py --data ../../reteco_data_v11 --track {2,1} --domains all --model bge-small --max-len 512 --batch 64 --out ../research/runs_v12/emb`
system: float16 vectors in shards of 20,000 docs (`shard_*.npy` + `shard_*.ids.json`), written atomically,
  skipped on restart; `manifest.json` last. Validation per domain: shard ids concatenated == corpus order,
  no non-finite rows, norms in [0.98, 1.02], 32 random documents (seed 20260921) re-encoded and compared
  with the cache (cosine > 0.99).
result: 24/24 domains validated (minimum re-encode cosine 0.99915). Track 2: 507,141 docs, 363 s of
  encoding (1,398 docs/s). Track 1: 1,167,159 docs; 11 domains in 1,293 s (617 docs/s), then hsm + history
  after the crash below (410 s). Cache 1.2 GB on disk (git-ignored). Peak VRAM 0.38 GB.
failure: the Track-1 job was killed without a traceback in `hsm` shard 4 (4 shards done). RAM was free
  afterwards; the job's peak RSS had reached 5.4 GB and an NGT/FAISS build (`ann_eval.py`, earth_science)
  ran at the same time → most likely the OOM killer. Cause of the 5.4 GB: the tokenizer materialises
  very long documents in full (Track-1 corpora contain documents of >1M words) before truncating.
fix: `Encoder.encode_docs` cuts each text at 200 × max_len characters before tokenisation (512 tokens
  never span 102k characters of real text, so the first 512 tokens are unchanged). Resumed alone:
  hsm reused shards 0–3, history built from scratch; peak RSS 3.3 GB, 7 min 8 s.
conclusion: Full dense index for the whole release in ~35 min of GPU time. Large jobs now run alone.

## 2026-10-13 15:45 — precision problem in the first dense runs (fixed)
notes: `ann_eval.py` showed GPU "exact" search (fp16 matmul) and FAISS IndexFlatIP (float32) disagreeing
  on drones: nDCG@10 0.1665 vs 0.1689, recall@10 between the two exact lists 0.982. fp16 accumulation
  flips near-ties. `dense_search.py` and `order_study.py` now keep vectors in fp16 on disk but score in
  float32 (TF32 off). After the fix GPU exact == FAISS flat (drones R@10 1.000; biology 0.999, a tie between
  duplicates). All dense results below were re-run with float32 scoring; the fp16-scored Track-2 order
  study is kept as `order/t2_fp16scoring_superseded.json`. Hybrid conclusions did not change (Track 2
  current 0.2435 → 0.2441, history 0.4238 → 0.4242).

## 2026-10-13 16:18 — dense retrieval (whole corpus), train + dev, both tracks
command: `python3 dense_search.py --data ../../reteco_data_v11 --kit ../../RETECO/starter_kit --track {1,2} --model bge-small --max-len 512 --emb ../research/runs_v12/emb --out ../research/runs_v12/dense/bge-small_L512/t{1,2}`
system: exact cosine (float32 on GPU) over the full corpus, top 1000, ties by doc id; query instruction from the model card
result (dev, macro nDCG@10): 1a **0.2806**, 1b_query+step **0.2787**, 2a_current **0.2081**,
  2a_history 0.3726 (history then question) / **0.3816** (question then history).
  Recall@100 dev: 1a 0.633, 1b 0.719, 2a_current 0.612, 2a_history 0.843.
query-string choice (train, decided before looking at dev): `2a_history_qfirst` 0.4142 vs 0.4029 (R@100 0.8388 vs 0.8261) → question first.
runtime: 0.4–13 ms per query for search (GPU); whole dense_search for both splits of Track 1 ~40 s.
reproduction: bge-small, **256 tokens**, iota dev: 1a **0.5581**, 1b 0.4984 — exactly the 2026-10-01 CPU numbers
  (metric: binary nDCG@10, starter-kit `ir_metrics.ndcg_at_k`, mean over iota's 3 dev queries; 256-token
  window; exact cosine). At 512 tokens iota dev 1a is 0.7157 (3 queries — not interpretable alone).
conclusion: On Track 1, dense retrieval alone is 2.5× BM25 and already above week 2's BM25 + rerank pipeline; on Track 2 it beats BM25 on the current turn, not with history.

## 2026-10-13 16:19 — hybrid BM25 + dense: tuned on train, frozen, measured on dev
command: `python3 hybrid.py --track {1,2} --conditions <...> [--dense-cond 2a_current 2a_history_qfirst] --bm25 ../research/runs_v12/bm25/t{1,2}/runs --dense ../research/runs_v12/dense/bge-small_L512/t{1,2}/runs --data ../../reteco_data_v11 --kit ../../RETECO/starter_kit --out ../research/runs_v12/hybrid/bge-small_L512_t{1,2}.json`
system: pool = BM25 top-kb ∪ dense top-kd; RRF (kb, kd ∈ {50,100,200,500}, c ∈ {10,30,60,100}) and linear
  fusion alpha·norm(dense) + (1−alpha)·norm(BM25), norm ∈ {min-max, z-score}, alpha ∈ {0,…,1} in 0.1 steps,
  (kb, kd) ∈ {(100,100),(200,200),(500,500),(100,500),(500,100)}; 175 configurations. Missing score =
  that system's 1000th score (upper bound); missing RRF rank contributes 0. One configuration per
  sub-track chosen by train macro nDCG@10; dev scored once. Paired bootstrap (10,000, topics within domain).
result (dev macro nDCG@10; hybrid = linear, configuration from train):
  | sub-track | BM25 | dense | BM25 top-100 + dense rerank | RRF* | hybrid* |
  | 1a | 0.1127 | 0.2806 | 0.2562 | 0.2588 | 0.2956 |
  | 1b_query+step | 0.1181 | 0.2787 | 0.2685 | 0.2814 | 0.2966 |
  | 2a_current | 0.1758 | 0.2081 | 0.2224 | 0.2390 | 0.2441 |
  | 2a_history | 0.4034 | 0.3816 | 0.3864 | 0.4221 | 0.4242 |
  hybrid − BM25: +0.1829 [0.1445, 0.2257], +0.1784 [0.1472, 0.2118], +0.0683 [0.0515, 0.0851], +0.0208 [0.0027, 0.0387].
  hybrid − rerank: +0.0395 [0.0204, 0.0594], +0.0281 [0.0093, 0.0483], +0.0217 [0.0102, 0.0334], +0.0377 [0.0256, 0.0497].
  hybrid − dense: +0.0151 [−0.0021, 0.0316], +0.0179 [0.0045, 0.0312], +0.0360 [0.0241, 0.0477], +0.0426 [0.0305, 0.0548].
  chosen: linear (100+100) z-score alpha 0.6 (1a), min-max 0.7 (1b), z-score 0.7 (both Track-2 conditions).
  hybrid > BM25 in 13/13, 13/13, 10/11 and 6/11 domains.
runtime: Track 1 3 min 20 s, Track 2 4 min (pure Python, CPU).
notes: dev was used once per sub-track with the frozen configuration. Week 2's CPU rerank used a 256-token window and 12 domains; the `rerank` column here is re-run at 512 tokens on all 13 domains.
conclusion: Fusing BM25 and dense scores beats every single system on all four sub-tracks; over dense alone the gain is small on Track 1 (about +0.015) and larger on Track 2.

## 2026-10-13 16:22 — retrieval depth and unique contributions (dev)
source: `depth` and `allocation` blocks of the hybrid reports (same command as above).
result: recall@100 (macro) BM25 / dense / union of the two top-100 lists (mean 179–186 docs):
  1a 0.402 / 0.633 / 0.683; 1b 0.482 / 0.719 / 0.767; 2a_current 0.531 / 0.612 / 0.710; 2a_history 0.807 / 0.843 / 0.917.
  At equal budget (k unique docs alternating between lists) the union beats both single systems on
  Track 2 at every k, and is between them on Track 1 below k=200 (dense alone is better there).
  Unique gold at k=100 (pairs): Track 1 1a — dense adds 606 to BM25's 454 (+133%), BM25 adds 57 to dense's
  1,003 (+6%). Track 2 current — dense adds 302 to 824 (+37%), BM25 adds 178 to 948 (+19%).
  Best BM25 share of a 100-doc budget (train): 0 on Track 1, 0.25 on Track 2 (same on dev).
conclusion: On Track 1, recall comes from the dense side; BM25 contributes a few percent. On Track 2 both contribute and a 25/75 BM25/dense split is the most efficient allocation.

## 2026-10-13 16:22 — BM25-only / dense-only / both / neither (dev) — meeting deliverable
command: `python3 gold_categories.py --data ../../reteco_data_v11 --bm25 ../research/runs_v12/bm25 --dense ../research/runs_v12/dense/bge-small_L512 --out ../research/runs_v12/categories`; `python3 case_study.py ... --readings ../research/cases/readings_dev.json --intro ../research/cases/src/categories_intro.md --outro ../research/cases/src/categories_outro.md --out ../research/cases/retrieval_categories_dev.md`; `python3 label_sample.py ... --category {neither,bm25_only,dense_only}`
system: every (topic, gold) pair of dev, conditions 1a, 1b_query+step, 2a_current, 2a_history; k=10 and 100.
result (k=100; BM25-only / dense-only / both / neither): 1a 3.2 / 34.0 / 22.3 / 40.5%; 1b 4.1 / 38.8 / 31.2 / 25.9%;
  2a_current 10.7 / 18.1 / 38.8 / 32.4%; 2a_history 8.0 / 10.8 / 71.8 / 9.4%. At k=10 "neither" is 70% (1a)
  and 64% (2a_current).
  Features (all pairs, Track 1 1a): BM25-only golds average 1,279 words, 68% longer than the window,
  44% match the query only beyond the window (dense-only: 234 words, 8%, 2%); lexical overlap dense-only
  0.18 vs 0.36–0.40 for BM25-found pairs.
  Example rule fixed in code before reading (seed 20260921, k=100, 1a/2a_current, 2 per track per category);
  16 examples rendered with hand readings; 52 more pairs labelled with the same rule (preliminary labels):
  neither — 6/20 instance needing world knowledge, 6/20 abstract inferential link, 3/20 weak/debatable
  judgement, 2 context-dependent turns, 2 near-copy crowding, 1 fragment; BM25-only — 11/16 exact rare
  term/name/identifier, 5/16 match beyond the window; dense-only — 10/16 paraphrase, 5/16 verbose query
  dilutes BM25, 1 inferential.
notes: diagnosis only; nothing fed back into any configuration. Labels are the assistant's, not human-validated.
conclusion: BM25's unique contribution is exact terms and text the encoder never sees (truncation); the dense side's is paraphrase; what neither finds mostly needs an inference step.

## 2026-10-13 16:20 — data note: Track-2 document ids reveal gold documents
command: `python3 id_artifact.py --data ../../reteco_data_v11 --out ../research/runs_v12/id_artifact.json`
result: in drones, hardware, law, medicalsciences and politics, 100% of train+dev gold documents are named
  `<question>_doc_<n>`; only 1.1–1.5% of the corpus has that form and 64–76% of those are gold; most
  negatives are `<question>_google_neg_<n>`. BRIGHT domains use `<question-folder>/<page>` ids.
notes: no system here reads ids. To be reported to Steve (and possibly the organisers) — if the hidden test
  set is built the same way, an id-reading system would gain an illegitimate advantage.

## 2026-10-13 15:58 — Track 2: history gain vs recycled gold (dev and train)
command: `python3 history_leak.py --data ../../reteco_data_v11 --kit ../../RETECO/starter_kit --bm25 ../research/runs_v12/bm25/t2/runs --dense ../research/runs_v12/dense/bge-small_L512/t2/runs --out ../research/runs_v12/history_leak.json`
result (dev): 89% (BRIGHT) / 86% (StackExchange) of later turns reuse ≥1 gold document of an earlier turn.
  Recycled-gold turns (568): BM25 0.163 → 0.556 with history; hybrid 0.222 → 0.534. New-gold turns (79):
  BM25 0.178 → 0.197; hybrid 0.245 → 0.208 (history hurts). First turns (211) are unaffected by construction.
  Train shows the same pattern (recycled 1,455 turns: BM25 0.151 → 0.539; new 162: 0.172 → 0.180).
conclusion: Most of the "+history" gain is re-finding documents whose content is already in the history (prior reference answers); it says little about finding new evidence. Track-2 current-turn results are the cleaner measure of retrieval.

## 2026-10-13 15:59–16:26 — does indexing order matter? (Steve's question)
command: `python3 order_study.py --data ../../reteco_data_v11 --kit ../../RETECO/starter_kit --track 2 --domains <all 11> --perms 5 --ann-domains drones biology earth_science --emb ../research/runs_v12/emb --out ../research/runs_v12/order/t2.json`; same for Track 1 with iota quant law workplace cardano, ANN on law and cardano.
system: corpus in file order + 5 random permutations (seeds 0–4); BM25 index rebuilt per order; dense = rows
  of the cached matrix permuted; NGT graph built with 3 insertion orders.
result: Track 2 — BRIGHT domains have 4.9–41.7% of documents in exact-duplicate groups (robotics 41.7%);
  StackExchange domains 0%. Gold documents with a non-gold exact twin: biology 3, earth_science 2, else 0.
  nDCG@10 range over the 6 orders: BM25 with bm25s's native tie order ≤ 0.0031 (biology history);
  dense ≤ 0.0114 (biology history), > 0 only in biology and earth_science; with doc-id tie-break 0.0000
  everywhere. NGT: nDCG@10 varies ≤ 0.0036 across insertion orders (biology), recall@10 vs exact 0.987–0.995.
  Track 1 (v1.1 deduplicated, 5 small domains): no duplicates, every range 0.0000; NGT range 0.
conclusion: Document order changes results only through exact ties between duplicate documents, by at most ~1 point on one domain (≈0.1 on the macro). The ~10-point week-1 differences came from the analyzer (stemming: Track 2 current 0.1490 → 0.1759) and from v1.0 → v1.1 deduplication, not from order.

## 2026-10-13 16:03–16:30 — ANN (NGT, FAISS HNSW) vs exact search, all 24 domains
command: `python3 ann_eval.py --data ../../reteco_data_v11 --kit ../../RETECO/starter_kit --track {1,2} --emb ../research/runs_v12/emb --out ../research/runs_v12/ann/bge-small_L512_t{1,2}.json`
system: dev 1a / 2a_current; exact = GPU float32; FAISS IndexFlatIP (CPU, independent exact); FAISS HNSW (M 32, efC 200, efS 128); NGT ANNG (cosine, epsilon 0.1).
result: see RESULTS.md section H (per domain: nDCG@10, recall@10 vs exact, build time, latency).
  Over 24 domains: NGT recall@10 vs exact 0.960–1.000 (recall@100 ≥ 0.959), mean |ΔnDCG@10| 0.0021,
  build ≤ 19 s, ≤ 2.8 ms/query; HNSW recall@10 0.960–1.000 (recall@100 ≥ 0.931), mean |ΔnDCG@10| 0.0027,
  build ≤ 34 s, ≤ 0.7 ms/query. history (200,252 docs): exact 0.2603, NGT 0.2612 (R@10 0.987), HNSW 0.2603
  (R@10 0.993). FAISS flat R@10 ≥ 0.975 — below 1 only through duplicate ties.
  Largest per-domain changes: NGT −0.0178 (Track-2 economics) and −0.0159 (sustainable_living), both
  BRIGHT domains with ~25% exact duplicates (presumably the ANN returning a non-gold twin of a gold
  passage — not checked per query). HNSW: worst −0.0613 on Track-1 quant (10 dev queries, R@10 0.960).
conclusion: At RETECO's scale (≤ 200k docs per domain) ANN costs ~0.002 nDCG on average (worst domain −0.018 for NGT, −0.061 for HNSW on a 10-query domain) and a few seconds of build; exact GPU search (≤ 13 ms/query) is also affordable, so ANN is a convenience here, not a necessity.

## 2026-10-13 16:35 — pre-registered decision rules (written before the runs they govern)
1. **Window (256 vs 512 tokens, bge-small).** On the 4+6-domain selection subset, train nDCG@10 favoured
   256 on Track 1 and 512 on Track 2, recall@100 favoured 512 on both (see section G of RESULTS). The
   subset has ~80 Track-1 train queries, too few to decide. Rule: build L256 for all 24 domains, run
   dense retrieval on **train only**, and per track choose the window with the higher mean train macro
   nDCG@10 over that track's two conditions. If a track switches to 256, its hybrid is re-tuned on train
   with the L256 runs and dev is scored once; the L512 numbers stay in the record.
2. **Encoder.** Choose the model with the highest mean train nDCG@10 over the four sub-track cells of the
   selection subset (section G). If it is not bge-small and a full index costs ≤ 3 h of GPU time, build it
   for all domains and run the same pipeline (dense, hybrid tuned on train, dev once).
3. **Cross-encoder depth.** bge-reranker-v2-m3 scores the frozen hybrid top 100; N ∈ {10, 20, 50, 100}
   chosen on a train subsample (≤ 40 topics per domain and condition, seed 20260921); dev once.
   Amendment (16:37, before any full cross-encoder run): measured 32 pairs/s while the GPU is shared;
   to fit the night the cross-encoder scores the hybrid **top 50**, N ∈ {10, 20, 50}, train subsample ≤ 30
   topics per domain and condition. Smoke test on drones only (not reported as a result).

## 2026-10-13 16:55 — week-2 hsm rerank completed (13/13 domains), and a second OOM kill
command: `python3 dense_rerank.py --data ../../reteco_data_v11 --kit ../../RETECO/starter_kit --split dev --track 1 --domains hsm --model bge-small --runs ../research/runs_v12/bm25/t1/runs --depth 100 --max-len 256 --conditions 1a 1b_query+step --out ../research/runs_v11/dev_rerank/t1d_hsm_gpu`
system: the week-2 configuration (BM25 top-100 reranked by bge-small, 256 tokens, fp32), now on the GPU. The
  BM25 input is the week-4 depth-1000 run, whose top 100 equals week 2's on Track 1 dev (identical scores in
  all 13 domains).
failure: first attempt killed by signal 9 after 10 min, peak RSS 11.0 GB — the week-2 encoder path had no
  length cap and tokenised hsm's very long documents in full (same cause as the indexer crash). The model-
  selection job running at the same time survived. Fix: `dense_run.encode` now cuts texts at 200 × window
  characters before tokenisation.
result: hsm dev 1a — rerank **0.3932**, RRF 0.3728, recall cap 0.6977; 1b_query+step — rerank **0.3234**,
  RRF 0.3452, cap 0.6189. 35 s, peak RSS 2.1 GB.
conclusion: The week-2 table (RESULTS, "Weeks 1–3", section 2) now covers all 13 Track-1 domains.

## 2026-10-13 15:10–20:21 — encoder selection on train (subset), rule 2 applied
command: `research/runs_v12/logs/select_queue.sh` (per model: `dense_index.py` on the subset domains, then
  `dense_search.py --splits train`; outputs `research/runs_v12/select/<model>_L<len>/t{1,2}/results.json`).
data: Track 1 iota, quant, law, workplace; Track 2 drones, law, medicalsciences (StackExchange), biology,
  psychology, economics (BRIGHT). Train queries only, retrieval over each full domain corpus. Dev not touched.
system: fp16 encoding, exact float32 search; prefixes/instructions from each model card (bge: query
  instruction; e5: "query: "/"passage: "; Qwen3: retrieval instruct prompt; gte-modernbert: none); every
  model cut at 512 tokens. Revisions recorded in the results files and RESULTS section G.
result (mean of 1a, 1b, 2a current, 2a history-qfirst train macro nDCG@10):
  bge-base 0.2913 · bge-small L256 0.2861 · gte-modernbert 0.2806 · bge-small L512 0.2794 ·
  Qwen3-Embedding-0.6B 0.2744 · bge-large 0.2739 · e5-large-v2 0.2280.
  Throughput Track 1 / Track 2 docs/s: bge-small 654/1439 (L512), bge-base 288/429, bge-large 94/180,
  e5-large 94/179, gte-modernbert 78/255, Qwen3-0.6B 39/77 (peak VRAM 2.2 GB, batch 16).
  Qwen3 has the best recall@100 (0.758) but lower nDCG@10 on Track 1; e5-large is weak on Track 1
  (1a 0.133) — prefixes were applied as in the card; not investigated further.
failed: snowflake-arctic-embed-m-v2.0 and nomic-embed-text-v1.5 (remote code incompatible with transformers 5.19).
conclusion: Bigger is not better here: no 335M–600M model beats bge-base at 512 tokens, and the spread
  between the top four (0.279–0.291) is small for ~80 Track-1 train queries. Rule 2: bge-base wins; full
  index estimated ≈1.5 h (1.17M docs at 288/s + 0.51M at 429/s) ≤ 3 h → full pipeline queued
  (`research/runs_v12/logs/queue3.sh`, after queue2).

## 2026-10-13 20:24–20:44 — rule 1 (window 256 vs 512), full train
command: `research/runs_v12/logs/queue2.sh` (bge-small L256 index for all 24 domains, `dense_search.py --splits train`);
  then for Track 1 only (switch triggered): `dense_search.py --track 1 --splits dev --model bge-small --max-len 256`
  and `hybrid.py --track 1 --conditions 1a 1b_query+step --dense ../research/runs_v12/dense/bge-small_L256/t1/runs
  --out ../research/runs_v12/hybrid/bge-small_L256_t1.json` (log `runs_v12/logs/rule1_t1_L256.log`).
data: index validation ok in all 24 domains (re-encode cos min ≥ 0.9992); L256 encoding 1,100–2,900 docs/s.
  The L256 Track-1 results file also holds the 16:19 iota dev reproduction (0.5581/0.4984), not new dev scoring.
result (train macro nDCG@10 over all domains, dense alone):
  Track 1: L256 1a 0.2271, 1b 0.2407 (mean 0.2339) vs L512 0.2219, 0.2387 (0.2303) → switch to 256 (+0.0036).
  Track 2: L256 current 0.2197, history-qfirst 0.3901 (0.3049) vs L512 0.2333, 0.4142 (0.3237) → stay at 512.
  Track 1 with L256, hybrid re-tuned on train (chosen: linear 100+100, z-score, α 0.6 for both conditions):
    1a  train hybrid 0.2479 · dev: BM25 0.1127, dense 0.2429, rerank 0.2467, hybrid **0.2834** (CI vs BM25 +0.1707 [0.1367, 0.2075])
    1b  train hybrid 0.2694 · dev: BM25 0.1181, dense 0.2417, rerank 0.2531, hybrid **0.2865** (+0.1684 [0.1379, 0.2014])
  For comparison, the L512 system scored dev 1a 0.2956 / 1b 0.2966 (dense 0.2806 / 0.2787).
conclusion (negative): the rule picked 256 on a +0.0036 train difference, and on dev the 256 system is lower
  (hybrid −0.012/−0.010, dense −0.038/−0.037). Train and dev disagree about the window by more than the train
  margin, so the window choice is within noise on train and the decision rule was too sensitive (no minimum
  margin). Per the rule, the Track-1 frozen system is the L256 one; the L512 numbers stay in the record and are
  NOT re-selected on the basis of dev. Lesson for next time: require a margin (or a bootstrap over train topics)
  before switching.

## 2026-10-13 20:46 — rule 4 (written before any bge-base result exists): final system per track
After queue3, the submitted-style system per track is the hybrid with the higher **train** macro nDCG@10
(mean of the track's two conditions) of: bge-small at the rule-1 window (Track 1 L256, Track 2 L512) and
bge-base L512. Dev numbers of both are reported; dev is not used to choose.
Disclosure: this rule was written after the Track-1 L256 dev scores above had been seen. bge-small L512 is
deliberately *not* a candidate on Track 1 (its train hybrid mean, 0.2590, ties L256's 0.2587; re-admitting it
now would amount to choosing on dev).

## 2026-10-13 20:40–21:40 — cross-encoder (bge-reranker-v2-m3) over the hybrid list (rule 3)
command: `research/runs_v12/logs/queue2.sh`, last two steps: `rerank_ce.py --track {2,1} --conditions ... --hybrid
  ../research/runs_v12/hybrid/bge-small_L512_t{2,1}.json ... --out ../research/runs_v12/ce` (report `ce/t{1,2}.json`).
system: BAAI/bge-reranker-v2-m3 (rev 953dc6f6), fp16, max 512 tokens per (query, passage) pair, documents cut at
  4,000 characters; scores the hybrid top 50; top N ∈ {10, 20, 50} reordered by the cross-encoder, the rest keep the
  hybrid order; N chosen on a train subsample (≤ 30 topics per domain and condition, seed 20260921); dev once.
  Track-2 history query = current question first. Input hybrid = bge-small **L512** (prepared before rule 1 moved
  Track 1 to L256; the Track-1 L256 hybrid was not cross-encoded).
cost: 241,750 pairs in ~60 min, 58–61 pairs/s with the GPU to itself.
result (train → chosen N; dev hybrid → hybrid + CE; dev CE − hybrid, paired bootstrap):
  2a current  train 0.2839 → 0.3375 (N=50) · dev 0.2441 → **0.2900**, +0.0459 [+0.0311, +0.0610]; better in 11/11 domains
              (BRIGHT 0.258 → 0.308, StackExchange 0.227 → 0.268).
  2a history  train 0.4645 → 0.4327 (N=10, the least harmful) · dev 0.4242 → 0.3777, −0.0465 [−0.0630, −0.0300];
              worse in 6/6 BRIGHT domains (0.504 → 0.403), better in 4/5 StackExchange domains (0.329 → 0.348).
  1a          train 0.2383 → 0.2181 (N=10) · dev 0.2956 → 0.2786, −0.0170 [−0.0373, +0.0031].
  1b          train 0.2861 → 0.2498 (N=10) · dev 0.2966 → 0.2519, −0.0446 [−0.0659, −0.0237].
  On Track 1 and Track-2 history every N lowers train and dev, monotonically in N (1a dev N=50: 0.2180).
failure of the rule: N = 0 ("do not rerank") was not an allowed choice, so where the cross-encoder hurts on train the
  rule still had to apply it. With N=0 allowed, train would have kept the plain hybrid on Track 1 and Track-2 history.
  Reported as run; this is a design flaw in rule 3, not a reason to re-select on dev.
conclusion: A general-purpose cross-encoder helps where the query is a short, self-contained question (Track-2
  current turn, +4.6 points, the largest single gain on Track 2 this week) and hurts where the query is long or the
  relevance is not a "does this passage answer this question" judgement: Track-1 queries/steps (temporal and
  inferential relevance) and Track-2 history queries (which fill most of the 512-token pair budget). Hypotheses, not
  tested: (a) truncation of query+passage at 512 tokens; (b) on BRIGHT history, BM25 re-finds gold through the prior
  answers (LOG 2026-10-13 15:58 entry) while the cross-encoder judges answer-relevance to the current question only.

## 2026-10-13 21:40–23:03 — rule 2: bge-base full pipeline; rule 4: final system per track
command: `research/runs_v12/logs/queue3.sh` (`dense_index.py --model bge-base --max-len 512` all 24 domains,
  `dense_search.py` train+dev, `hybrid.py` as for bge-small → `research/runs_v12/hybrid/bge-base_L512_t{1,2}.json`).
cost: Track 1 1,167,159 docs 73.5 min (233–291 docs/s), Track 2 507,141 docs 16.9 min; peak VRAM 0.82 GB; cache 2.5 GB;
  re-encode validation ok in all 24 domains (cos min ≥ 0.9991). (The four Track-1 and six Track-2 subset domains were
  encoded during selection and reused.)
result (macro nDCG@10, train / dev):
  1a  BM25 0.1005/0.1127 · dense 0.2103/0.2488 · rerank 0.1856/0.2415 · RRF* 0.2140/0.2470 · hybrid* 0.2345/**0.2734**
  1b  BM25 0.1101/0.1181 · dense 0.2304/0.2579 · rerank 0.2139/0.2623 · RRF* 0.2426/0.2571 · hybrid* 0.2632/**0.2824**
  2a current  BM25 0.1667/0.1758 · dense 0.2573/0.2350 · rerank 0.2524/0.2398 · RRF* 0.2632/0.2448 · hybrid* 0.2803/**0.2540**
  2a history  BM25 0.4082/0.4034 · dense 0.4387/0.3838 · rerank 0.4445/0.3866 · RRF* 0.4692/0.4265 · hybrid* 0.4806/**0.4342**
  dev hybrid* − BM25: 1a +0.1607 [0.1285, 0.1929]; 1b +0.1643 [0.1337, 0.1974]; 2a current +0.0782 [0.0609, 0.0960];
  2a history +0.0307 [0.0155, 0.0458]. Hybrid* − dense: +0.0245, +0.0245, +0.0190, +0.0503 (all CIs > 0).
  Hybrid configs (train): linear 100+100, min-max α 0.7 (1a, 1b, 2a current), z-score α 0.6 (2a history).
rule 4 (train hybrid mean over the two conditions): Track 1 bge-small L256 0.2586 vs bge-base 0.2488 → **bge-small L256**;
  Track 2 bge-small L512 0.3613 vs bge-base 0.3805 → **bge-base L512**.
final frozen systems (dev): Track 1 1a **0.2834**, 1b **0.2865** (bge-small L256 hybrid); Track 2 current **0.2540**,
  +history **0.4342** (bge-base hybrid). The cross-encoder result on Track-2 current (0.2900) was obtained over the
  bge-small L512 hybrid and has not been run over the bge-base hybrid.
conclusion: The subset selection (4 Track-1 domains, ~80 train queries) did not carry over to Track 1 as a whole:
  over all 13 domains bge-base is below bge-small on train (−0.010) and dev (1a 0.2734 vs 0.2956 at L512). On Track 2
  the larger model is better on train and dev (+0.010 / +0.010). Encoder differences in the 0.01 range are about as
  large as the selection noise we can measure with this much train data; the hybrid's gain over BM25 is not.

## 2026-10-13 23:06 — rule 5 (before running): cross-encoder over the bge-base Track-2 current-turn hybrid
`rerank_ce.py` as in rule 3 (top 50, N ∈ {10, 20, 50}, train subsample ≤ 30 topics/domain, seed 20260921), input the
bge-base L512 hybrid, condition 2a_current only (the only condition where rule 3 helped on train). Fix of the rule-3
flaw: the cross-encoder is adopted only if its train macro at the chosen N exceeds the plain hybrid's (N = 0); dev once.

## 2026-10-13 23:06–23:14 — rule 5 result: cross-encoder over the bge-base Track-2 current-turn hybrid
command: `python3 rerank_ce.py --track 2 --conditions 2a_current --hybrid ../research/runs_v12/hybrid/bge-base_L512_t2.json
  --bm25 ../research/runs_v12/bm25/t2/runs --dense ../research/runs_v12/dense/bge-base_L512/t2/runs --data ../../reteco_data_v11
  --kit ../../RETECO/starter_kit --out ../research/runs_v12/ce_bge-base` (log `runs_v12/logs/ce_bge-base_t2.log`, ~8 min).
result: train N=0 0.2830, N=10 0.3039, N=20 0.3252, N=50 0.3435 → N=50, and 0.3435 > 0.2830 → adopted.
  dev 0.2540 → **0.3001**, CE − hybrid +0.0462 [+0.0311, +0.0614]; better in 10/11 domains.
conclusion: Final Track-2 current-turn system = BM25 ∪ bge-base hybrid, top 50 reordered by bge-reranker-v2-m3:
  dev 0.1758 (BM25) → 0.3001. Final systems overall (dev): 1a 0.2834, 1b 0.2865, 2a current 0.3001, 2a history 0.4342.
