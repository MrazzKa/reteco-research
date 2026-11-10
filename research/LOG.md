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

---

# Week 5 (2026-10-26 →)

Context: meeting with Steve 2026-10-19 (answers to the 17.10 email): report the Track-2 id pattern to the organisers
(they published News on 17.10: ids are not a signal; test queries are built from documents not positive for any
train/dev query); Track-2 headline metric = current turn (+ the turns with new gold), +history reported separately;
order of work: LLM query reasoning → passage-level MaxP → reasoning embedders → temporal Track 1; register for 1a,
1b, 2a. Test evaluation 10–31 January 2027. Upstream RETECO pulled to `49f96ab` (News "Document IDs are not a
signal"; evaluation page: official 1a/1b/2a scores are averaged per domain, then over domains — what we do).
Week-5 outputs go to `research/runs_v13/`.

## 2026-10-26 13:24 — the doc-id tie-break is a hidden use of the id; corpus file order too
finding: every ranking script broke exact score ties by doc id ascending (bm25s_run.search, dense_search lexsort,
  hybrid.rank_by `(-key(d), d)`, rerank_ce). In the Track-2 StackExchange corpora gold ids are
  `<q>_doc_<n>` and negatives `<q>_google_neg_<n>`; "doc" < "google", so among exact duplicates gold came first.
  The neutral alternative suggested first, the corpus file position, leaks as well: gold documents sit at the start
  of the file (mean relative position of train+dev gold: drones 0.0067, biology 0.0020; LOG 13:24). Any order-dependent step
  (bm25s's native tie order, ANN insertion order) inherits this.
change: new `scripts/tiebreak.py`: tie key = sha1(doc id) (a fixed pseudo-random order), used by bm25s_run.py,
  dense_search.py, hybrid.py, rerank_ce.py, dense_run.py; `--tiebreak id` restores the old order. bm25s_run.search
  now retrieves k+32 and cuts after sorting, so ties at the depth cut are also ordered by the key (dense_search
  already did this). rerank_ce.py caches cross-encoder scores per (topic, document) and scores only missing pairs.
plan (no selection involved; the hybrid grid is re-tuned on train as before, dev once): re-run the final systems
  with the sha1 key into runs_v13 — BM25 depth 1000 (both tracks), dense bge-small L256 (Track 1) and bge-base L512
  (Track 2) from the week-4 embedding caches, hybrid, cross-encoder top 50 on 2a current (N chosen on train, N=0
  allowed). Old = runs_v12 (doc-id key). The new numbers are the baseline for every later comparison.

## 2026-10-26 13:33 — LLM for query-side reasoning: install and speed test
setup: vLLM 0.32.0 in a separate venv `~/semeval-reteco/.venv-llm` (Python 3.14, torch 2.13.0+cu130). WSL has no
  gcc and no sudo: triton's launcher is compiled with `zig cc` (pip `ziglang`) through a wrapper
  `~/semeval-reteco/tools/bin/cc` (CC=…), with Python 3.14 headers unpacked from the Ubuntu .debs (`apt-get download`
  + `dpkg -x`, no root). Eager mode (no CUDA graphs).
model: `cyankiwi/Qwen3-4B-Instruct-2507-AWQ-4bit` rev `b37d1ccb77e27a70fe4222d995fda27940eead5a` (AWQ W4A16,
  compressed-tensors; quantisation of Qwen/Qwen3-4B-Instruct-2507; 3.29 GiB on the GPU). The official FP8 build
  does not fit: Windows holds 1.7–4.3 GB of the 8 GB, varying over the session.
speed test: 50 Track-2 current-turn questions, prompt "reason", temperature 0, ≤ 256 new tokens, KV cache of only
  2,016 tokens (gpu-util 0.485): 15 s, 3.4 questions/s, 459 generated tokens/s, mean 136 tokens, none cut at 256.
estimate: 2 prompts × (2,971 Track-2 turns + 1,730 Track-1 queries + 3,976 Track-1 steps) = 17,354 generations
  ≈ 1.4 h at that rate (< 8 h), so everything is generated, Track 2 current first, then 1a, then 1b.
script: `scripts/llm_expand.py`, queue `research/runs_v13/logs/llm_gen.sh`, cache `research/runs_v13/llm/` (ignored).
  Prompts and model are in `llm/t*/meta.json`. The model sees only the query text (HTML stripped, ≤ 3,000 chars),
  never a qid or doc id.

## 2026-10-26 13:37 — rule 6 (before any expansion result): LLM query expansion per condition
conditions: 1a, 1b_query+step, 2a_current (Track-2 history is not expanded; it is secondary per the 19.10 meeting).
candidates: query variants v ∈ {q, q+r, r, q+h, h, q+r+h} (q original, r "reason" text, h "hyde" passage;
  `scripts/qexp_search.py`: BM25 on the concatenated text; dense on the normalised mean of the query vectors, r
  encoded as a query, h as a document), dense = the final encoder of the track (Track 1 bge-small L256, Track 2
  bge-base L512). For every v: hybrid(BM25_v, dense_v) tuned on train with the hybrid.py grid (as in week 4).
choice: v* = argmax train macro nDCG@10 of the tuned hybrid. Adopt v* only if train macro(v*) − train macro(q)
  ≥ +0.005 AND the paired bootstrap (topics resampled within domain, 10,000 draws, seed 20260921) of
  v* − q over train topics has a 95% lower bound > 0. Otherwise keep q ("do not expand" is always allowed).
  Dev: one measurement per configuration (all six are reported; only the train choice is the system).
  2a_current then: cross-encoder (bge-reranker-v2-m3, top 50, N ∈ {0, 10, 20, 50} on the train subsample as in
  rule 5) over the chosen hybrid; the cross-encoder always sees the original current question.

## 2026-10-26 13:37 — rule 7 (before any MaxP result): passage-level scoring (MaxP)
system: dense score of a document = max over passages of 510 tokens with 128 overlap (first window = the existing
  L512 cache; windows 2+ only exist for documents > 510 tokens; ≤ 200 passages per document). Encoder: bge-small
  for Track 1, bge-base for Track 2 (the final families). `scripts/passage_index.py` + `qexp_search.py --passages`.
candidates per condition (1a, 1b_query+step, 2a_current): hybrid(BM25_v, MaxP_v) for v ∈ {q, rule-6 choice}.
choice: compared against the system adopted under rule 6 for that condition; MaxP adopted under the same margin
  (train ≥ +0.005 and train bootstrap lower bound > 0). Dev once.

## 2026-10-26 13:24–13:42 — step 1 result: final systems with the sha1 tie key (runs_v13) vs doc id (runs_v12)
command: `research/runs_v13/logs/tiebreak.sh` (log `tiebreak.log`), then `scripts/tiebreak_compare.py --out
  research/runs_v13/tiebreak/compare.json` and `scripts/tie_study.py --out research/runs_v13/tiebreak/ties.json`.
cost: BM25 depth 1000 both tracks 7.5 min; dense 1.5 min; hybrid grids 8 min; cross-encoder 15 new pairs (cache
  copied from runs_v12/ce_bge-base and now kept per (topic, document)).
result (macro nDCG@10, train old → new / dev old → new):
  1a          BM25 0.1005 → 0.1005 / 0.1127 → 0.1127 · dense 0.2271 → 0.2251 / 0.2429 → 0.2430 · hybrid 0.2479 → 0.2462 / 0.2834 → **0.2834**
  1b          BM25 0.1101 → 0.1101 / 0.1181 → 0.1181 · dense 0.2407 → 0.2372 / 0.2417 → 0.2418 · hybrid 0.2694 → 0.2665 / 0.2865 → **0.2865**
  2a current  BM25 0.1667 → 0.1665 / 0.1758 → 0.1759 · dense 0.2573 → 0.2574 / 0.2350 → 0.2353 · hybrid 0.2803 → 0.2805 / 0.2540 → 0.2543
              + CE (N=50 again; train N=0 0.2828 → N=50 0.3430) 0.3435 → 0.3430 / 0.3001 → **0.3003**
  2a history  BM25 0.4082 → 0.4081 / 0.4034 → 0.4037 · dense 0.4387 → 0.4388 / 0.3839 → 0.3843 · hybrid 0.4806 → 0.4806 / 0.4342 → **0.4352**
  Hybrid configurations unchanged (min-max α 0.7 for 1a/1b/2a current; z-score α 0.6 for history, 100+100).
  Dev domains that change: hybrid 2a current only earth_science (+0.0038); history earth_science +0.0116,
  biology −0.0007 (dev new − old +0.0010 [+0.0002, +0.0021]); Track-1 hybrids identical on dev; Track-1 dense
  bitcoin +0.0002, cardano +0.0010. The five StackExchange domains (the ones with `_doc_` / `_google_neg_` ids) do
  not change at all: they hold no exact duplicates (order study, 2026-10-13), so the id order never decided a tie.
  The Track-1 train change (dense 1b −0.0035) is in iota (7/16 topics) and cardano: at 256 tokens documents
  sharing their first 256 tokens get identical vectors; `--tiebreak id` reproduces the old numbers exactly.
gold in the top 10 tied with a non-gold document (all judged topics; id key → sha1 key): dev 2a current hybrid
  2 of 548 (ranked first among its twins 0 → 2), CE 9 of 636 → 8 of 635; dev history hybrid 13 of 942 (8 → 10);
  dev 1a/1b hybrid 0; train at most 34 of 2,560 (history hybrid). Under the id key the tied gold was ranked first
  in 0–64% of the cases depending on the list, i.e. not systematically.
conclusion: The id tie-break was a hidden use of the id in principle, but it did not inflate any result: final
  dev systems move by ≤ 0.001 (history +0.001). The sha1 key is now the default everywhere; the runs_v13 numbers
  (1a 0.2834, 1b 0.2865, 2a current 0.3003, history 0.4352) are the baseline from here on. The corpus file
  order would have been a worse "neutral" key (gold sits at the start of the files).

## 2026-10-26 13:45 — side finding: Track-2 corpus file order reveals gold
check: relative position of train+dev gold documents in `documents.jsonl`: Track 2 drones 0.007, politics 0.008,
  economics 0.003, biology 0.002, earth_science 0.001, robotics 0.002 — in all six domains checked 100% of gold
  sits in the first 5% of the file. Track 1 (v1.1, deduplicated): iota 0.477, law 0.468, history 0.494, politics
  0.511 (5% in the first 5%, i.e. shuffled). Not used by any system; worth telling the organisers together with
  the id pattern (anything order-dependent — bm25s's native tie order, ANN insertion order — inherits it).

## 2026-10-26 13:46 — rule for the step-2 examples (written before any expansion result is seen)
file: `research/cases/query_reasoning_dev.md`. Conditions 2a_current and 1a, dev. System "after" = the rule-6 choice
  for the condition, or, if rule 6 keeps q, its best-on-train variant (labelled as such); "before" = q (the
  runs_v13 hybrid). Per condition, topics are split into improved (hybrid nDCG@10 after > before) and worsened
  (after < before); from each, 2 topics drawn with random.Random(20260921) over sorted qids → 8 examples. Shown:
  query, the generated text(s) the variant uses, each gold document (first 300 chars) with its hybrid rank before
  and after. No resampling.

## 2026-10-26 13:48 — rule 8 (before any reasoning-embedder result): reasoning embedder over the hybrid pool
model: ReasonEmbed `hanhainebula/reason-embed-qwen3-4b-0928` (BRIGHT 37.1 with original queries per its card),
  NF4 4-bit via bitsandbytes 0.50.2 (fp16 does not fit next to Windows' share of the GPU), last-token pooling,
  query instruction "Given a <domain> question, retrieve documents that help answer the question." (1b: "… and one
  research step, retrieve documents that help with that step."), documents ≤ 4,000 chars / 512 tokens.
  Caveat to report: ReasonEmbed's synthetic training data is built from BRIGHT-style corpora; six Track-2 domains
  are BRIGHT-derived, so a gain there may partly be domain exposure.
use: `scripts/reason_rerank.py`, over the pool (top 100) of the system adopted for the condition after rules 6–7;
  candidates: none, top-N reorder (N ∈ 10, 20, 50, 100), interpolation w ∈ 0.1…0.9 of min-max hybrid and embedder
  scores. Train subsample ≤ 30 topics per domain (seed 20260921), dev all topics.
choice: best on train; adopted only if train − none ≥ +0.005 and the train bootstrap lower bound > 0.
  2a current: the baseline is the cross-encoder system (hybrid + CE top 50); the embedder is adopted there only if
  its best train configuration beats the CE system's train macro on the same subsample by the same margin.
  Speed is measured first; full-corpus encoding with a 4B model is out of scope (Track 1: 1.17M documents).

## 2026-10-26 14:32 — LLM generation done; a key bug caught before any choice
generation: `llm_gen.sh` 13:40–14:32 (52 min) for 17,354 inputs (Track 2 2,971 × 2 prompts; Track 1 1a 1,730 × 2,
  1b 3,976 × 2): 4.2–10 inputs/s, 640–650 generated tokens/s with gpu-util 0.75 (KV cache ~ 2 GB). Mean output
  123–164 tokens; cut at 256 tokens: 0.03–0.4%; empty outputs 0.
bug: the first Track-2 `qexp_search.py` run (14:32–14:34) looked generations up by (split, qid). Track-2 qids such as
  `2_turn_1` repeat across the BRIGHT domains (524 train/dev collisions), so e.g. economics topics received
  earth_science expansions (train BM25 q+r economics 0.145 → 0.026, earth_science 0.244 → 0.463). Track 1 has no
  collisions. Fixed (key = (domain, split, qid)), `qexp/t2` deleted and re-run in `logs/step2b.sh`; the generations
  themselves were keyed by input text and are unaffected. No hybrid or rule-6 choice was computed on the broken runs.

## 2026-10-26 14:34–15:13 — rule 6 result: LLM query expansion
command: `research/runs_v13/logs/step2b.sh` (`qexp_search.py` per condition; `hybrid.py` with the six variants as
  conditions, logs `hyb_{2a,1a,1b}.log`), then `research/runs_v13/logs/select6.sh` → `runs_v13/select/rule6_*.json`.
cost: retrieval with all six variants 2 min (Track 2), 9 min (1a), 7 min (1b); hybrid grids 14–23 min (CPU, parallel).
result (macro nDCG@10; train / dev):
  2a current  q: BM25 0.1665/0.1759 · dense 0.2574/0.2353 · hybrid 0.2805/0.2543
              q+r+h: BM25 0.2959/0.2869 · dense 0.2943/0.2652 · hybrid **0.3367/0.3100**
              (q+r 0.3301/0.3040, q+h 0.3272/0.3114, h 0.3092/0.2918, r 0.3001/0.2725)
  1a          q: BM25 0.1005/0.1127 · dense 0.2251/0.2430 · hybrid 0.2462/0.2834
              q+r+h: BM25 0.1323/0.1620 · dense 0.2583/0.2899 · hybrid **0.2949/0.3258**
              (q+h 0.2879/0.3212, q+r 0.2837/0.3245, r 0.2781/0.3003, h 0.2773/0.2953)
  1b          q: BM25 0.1101/0.1181 · dense 0.2372/0.2418 · hybrid 0.2665/0.2865
              q+r+h: BM25 0.1470/0.1620 · dense 0.2779/0.3097 · hybrid **0.3226/0.3505**
              (q+h 0.3150/0.3377, h 0.3104/0.3341, q+r 0.3032/0.3386, r 0.2969/0.3284)
rule 6: best on train = q+r+h in all three conditions; train bootstrap q+r+h − q: 2a +0.0562 [+0.0460, +0.0661],
  1a +0.0486 [+0.0348, +0.0627], 1b +0.0560 [+0.0440, +0.0688] → **adopted** everywhere.
  dev q+r+h − q: 2a +0.0557 [+0.0406, +0.0705], 1a +0.0425 [+0.0214, +0.0630], 1b +0.0640 [+0.0467, +0.0817].
  Fusion configs (train, all 100+100): 2a z-score α 0.6; 1a min-max α 0.6; 1b z-score α 0.7.
conclusion: Query-side reasoning with a 4B local LLM is the largest single gain since the hybrid: +0.04 to +0.06
  nDCG@10 on every sub-track, train and dev agree, every expansion variant beats the plain query, and using both
  generated texts with the query is best. BM25 gains most on Track 2 (0.176 → 0.287 dev: the LLM supplies the
  vocabulary of the answer); text-only expansions (r, h without q) are weaker than adding them to the query.

## 2026-10-26 15:45–15:51 — rule 6, 2a current: cross-encoder over the q+r+h hybrid — not adopted
command: `research/runs_v13/logs/step4.sh` (rerank_ce.py --conditions 2a_current__q+r+h --query-cond 2a_current, cache
  from runs_v13/ce reused per (topic, document); out `runs_v13/ce_final/t2.json`).
result (train subsample ≤ 30 topics/domain): N=0 0.3671, N=10 0.3604, N=20 0.3578, N=50 0.3456 → the best N (10) is
  below N=0, so under rule 6 (N ∈ {0, 10, 20, 50}) the cross-encoder is **not applied**. (The script prints its
  best non-zero N; the rule's choice is N=0.) Dev, reported once: N=0 0.3100, N=10 0.3208, N=20 0.3176, N=50 0.3138.
conclusion: Once the query carries the LLM's reasoning and HyDE text, the general cross-encoder (which sees only the
  short original question) no longer helps on train; on dev it would still add ~+0.01 (CI includes 0). We keep the
  train decision.

## 2026-10-26 14:53–16:06 — passage index and rule 7 (MaxP)
index: `passage_index.py` (log `step2b.log`): Track 1 bge-small 878,611 extra passages for 167,074 documents (14% of
  1,167,159; 331 documents hit the 200-passage cap), encode 28 min + tokenise 4 min; Track 2 bge-base 31,575 extra
  passages for 15,734 documents (3%), 2.5 min. First-window re-encoding check cos ≥ 0.9993 in every domain.
  Summary `runs_v13/maxp/index_summary.json`. Search with MaxP: `step3.sh` (qexp_search.py --passages, all six
  variants), hybrids `maxp_hyb_*.log`; choice `logs/select7.sh` → `runs_v13/select/rule7_*.json`.
result (train / dev; baseline = rule-6 system):
  2a current  rule-6 q+r+h hybrid 0.3367/0.3100 · MaxP q 0.2989/0.2738 · MaxP q+r+h **0.3507/0.3319**
              train MaxP − rule 6 +0.0140 [+0.0103, +0.0177] → **adopted**; dev +0.0219 [+0.0149, +0.0295].
              dense alone (q): 0.2574 → 0.2783 train, 0.2353 → 0.2581 dev.
  1a          rule-6 0.2949/0.3258 · MaxP q 0.2257/0.2666 · MaxP q+r+h 0.2714/0.3174 → not adopted.
  1b          rule-6 0.3226/0.3505 · MaxP q 0.2461/0.2560 · MaxP q+r+h 0.2878/0.3221 → not adopted.
  On Track 1 MaxP dense alone is about level with the L256 first window (1a q+r+h 0.2606 vs 0.2583 train), but the
  hybrid loses 2–4 points: the max over many passages shifts the score distribution of long documents and the
  fusion (tuned per variant) does not recover. (MaxP here also means a 512-token first window, while the Track-1
  system uses 256: two changes at once.)
caveat (checked after the result, before adopting it anywhere): the Track-2 gain sits in BRIGHT domains with few
  long documents — biology +0.075 train / +0.081 dev with only 141 documents > 510 tokens, earth_science +0.117 /
  +0.078 with 410. In those corpora long documents are mostly gold: biology 100 of 141 long documents are train/dev
  gold (71%), earth_science 166 of 410 (40%), psychology 7%, economics 5%; StackExchange domains ≈ 0%. MaxP gives a
  long document several chances, so part of the gain is a length effect that matches how the BRIGHT corpora were
  built, not better matching. It reads only text, so it is within the rules, but whether it survives on test
  (gold = documents not positive for any train/dev query) is unknown. Both 2a systems (with and without MaxP) are
  reported; this goes to Steve as a question.

## 2026-10-26 16:07 — rule 8 amended before any train result (cost): pool 50, FP8 through vLLM
speed: ReasonEmbed-4B is compute-bound on this GPU: 7.2 docs/s with bitsandbytes NF4 (batch 8, 512 tokens) and
  8.7 docs/s with vLLM FP8 (`scripts/embed_vllm.py`, pooling runner; vectors agree with NF4 at cos 0.98–0.99, so
  the pooling is the card's last-token pooling). Pool 100 for 1a + 1b + 2a ≈ 150k documents ≈ 5 h; therefore:
  pool = top 50 (N ∈ 10, 20, 50; interpolation over the top 50), backend vLLM FP8, order 2a current → 1a → 1b.
  Baselines (the systems adopted after rules 6–7): 2a = MaxP q+r+h hybrid, 1a/1b = q+r+h hybrid. Choice as written
  at 13:48 (train margin +0.005 and bootstrap lower bound > 0; "none" allowed).
disclosure: the speed test (15:51) ran on the 38 dev topics of drones and printed their dev nDCG for every way of
  using the score (none 0.2568, best 0.3182). It was not intended as a measurement; the choice below uses train only.

## 2026-10-26 16:08 — rule 9 (before running): temporal signal inside the Track-1 ranking (step 5)
system: over the top 100 of the adopted Track-1 system (q+r+h hybrid), score = (1 − w)·minmax(hybrid fused score)
  + w·T(d), T(d) = share of the query's years y for which the document mentions a year in [y − 1, y + 1]
  (years 1500–2099 and decades "1990s" expanded; documents fully scanned). Topics without a year keep the hybrid
  order. Year source ∈ {query text, query + the LLM "reason" text (asked to state the time explicitly)};
  w ∈ {0.05, 0.1, 0.2, 0.3, 0.5}; "none" allowed. 1a and 1b separately; all train topics.
choice: best on train, adopted only with train − none ≥ +0.005 and train bootstrap lower bound > 0. Dev once.
  (The week-3 version — a post-hoc reorder of BM25's top 100 — lost on train; this one is a weighted feature
  inside the fusion, over a much better pool.)

## 2026-10-26 16:09–16:10 — rule 9 result: temporal signal inside the Track-1 ranking — negative
command: `python3 temporal_rerank.py --conditions 1a__q+r+h 1b_query+step__q+r+h --query-cond 1a 1b_query+step
  --hybrid runs_v13/qexp/t1/hybrid_{1a,1b}.json … --llm runs_v13/llm/t1 --out runs_v13/temporal/t1.json`
  (log `logs/temporal.log`; document-year caches in `temporal/cache/`, git-ignored).
coverage: topics with at least one year — from the query 47% (train 1a) / 48% (1b); query + LLM reason 73% / 78%.
result (train / dev): 1a none 0.2949/0.3258; best year feature q|0.05 0.2934/0.3253, q+r|0.05 0.2943/0.3247; every
  weight lowers train, monotonically in w (w = 0.5: 0.2536 / 0.2248). 1b none 0.3226/0.3505; q+r|0.05
  0.3212/0.3480 … w = 0.5: 0.2527. Best on train = none → **not adopted** (both conditions).
conclusion: Second negative result for explicit years on Track 1 (after the week-3 post-hoc reorder). Inside a strong
  pool, year agreement does not separate gold from the other on-topic documents; the LLM's stated time raises
  coverage to ~75% of topics but not usefulness. Temporal relevance in TEMPO seems to be carried by content
  (events, versions, periods described in words), which the expanded query already captures better than years.

## 2026-10-26 16:13 — analysis (no choice made): where the week-5 gains come from
Track 1: q+r+h hybrid beats the plain-query hybrid in 12 of 13 domains on train and on dev (1a and 1b); the
  exception is iota (dev 1a −0.102, 1b −0.016; 10 dev queries). Largest dev gains: workplace +0.13, politics +0.09,
  economics +0.08/+0.11.
Track 2 current turn, dev macro by source (BRIGHT 6 domains / StackExchange 5 domains):
  week-4 hybrid 0.2610 / 0.2463 · week-4 hybrid + CE 0.3189 / 0.2780 · q+r+h hybrid 0.3727 / 0.2348 ·
  MaxP q+r+h 0.4099 / 0.2384. Train: week-4 hybrid 0.2842 / 0.2760 · q+r+h 0.3917 / 0.2707 · MaxP q+r+h 0.4181 / 0.2698.
reading: the LLM expansion helps the BRIGHT-derived domains a lot (+0.11 dev, +0.11 train) and does nothing or
  slightly hurts on StackExchange (−0.01 dev, −0.005 train); on StackExchange the week-4 cross-encoder system is
  the best we have (0.278 dev). Possible reasons, untested: BRIGHT gold are encyclopaedic/web pages whose wording an
  LLM reproduces well, StackExchange gold are other posts; and the BRIGHT data are public since 2024 and may be in
  the LLM's training data. A per-source system (e.g. CE for StackExchange domains) is NOT selected here, because the
  idea came from this dev breakdown; it is a question for Steve and would need a new train-only rule.

## 2026-10-26 16:21 — rule 8 run: FP8 attempt crashed; switched to NF4, chunked and restartable
16:07–16:19: the vLLM FP8 job (all 2a documents in one call) died after 11 min with `CUDA error: unknown error`
  while Windows' share of the GPU rose to 5.3 GB / 38% utilisation; nothing was saved. No result was produced.
change (before any rule-8 train result): backend bitsandbytes NF4 in-process (2.7 GB, 7.2 docs/s), batch 4,
  documents embedded in chunks of 2,000 with the cache saved after each, and the job restarted automatically up to
  20 times (`runs_v13/logs/step5b.sh`). Pool 50, conditions and choice rule as amended at 16:07.

## 2026-10-26 16:21–17:34 — rule 8 result, 2a current: ReasonEmbed over the top 50 — adopted
command: `research/runs_v13/logs/step5b.sh` (reason_rerank.py --backend bnb --bits 4 --pool 50, input = MaxP q+r+h
  hybrid; query = the original current question with the instruction; out `runs_v13/reason/t2_reasonembed-4b.json`).
cost: 33,937 documents + 1,188 queries, 73 min (≈ 7.7 texts/s), one attempt, no GPU failure.
result (train = subsample ≤ 30 topics/domain; dev all): none 0.3828 / 0.3319 · top-N reorder N=10 0.3871/0.3565,
  N=20 0.4010/0.3752, N=50 0.4106/0.3811 · interpolation w=0.5 0.4167/0.3775, 0.7 0.4310/0.3880,
  **w=0.8 0.4359/0.3901**, 0.9 0.4250/0.3888. Best on train w=0.8; train − none +0.0531 [+0.0312, +0.0749] →
  **adopted**. Dev − none +0.0582 [+0.0450, +0.0714]; better in 11/11 domains; BRIGHT 0.4099 → 0.4686,
  StackExchange 0.2384 → 0.2960 (largest: medicalsciences +0.106, robotics +0.083, economics +0.076).
conclusion: Unlike the LLM expansion, the reasoning embedder helps the StackExchange domains as much as the BRIGHT
  ones, so its gain is not only BRIGHT exposure (caveat stays: its training data are BRIGHT-style). It also
  replaces the cross-encoder's role on StackExchange (0.278 with the week-4 CE system → 0.296).
  Track-2 current-turn system: query reasoning + MaxP hybrid + ReasonEmbed (w 0.8 over the top 50): dev 0.3901.

## 2026-10-26 17:34–19:01 — rule 8 result, 1a: ReasonEmbed over the top 50 — adopted
input: q+r+h hybrid (`qexp/t1/hybrid_1a.json`); query = original 1a query (HTML stripped) with the instruction.
cost: 34,417 documents + 909 queries, 86 min (Track-1 documents fill the 512-token window more often).
result (train subsample / dev): none 0.2823 / 0.3258 · top-N N=10 0.2737/0.3275, N=20 0.2888/0.3431,
  N=50 0.2893/0.3538 · interpolation w=0.5 0.3024/0.3553, 0.7 0.3072/0.3647, **w=0.8 0.3078/0.3667**, 0.9
  0.3034/0.3631. Best on train w=0.8; train − none +0.0254 [+0.0073, +0.0448] → **adopted**. Dev − none +0.0409
  [+0.0190, +0.0639]; better in 12/13 domains (hsm −0.025; largest history +0.098, monero +0.097, economics +0.083).
conclusion: The reasoning embedder also helps Track 1, where last week's cross-encoder hurt at every depth.
  Pure reordering of the top 10 is slightly harmful on train; mixing its score with the hybrid's (w 0.8) is best on
  both tracks.

## 2026-10-26 19:01–19:35 — rule 8 result, 1b: ReasonEmbed over the top 50 — adopted
input: q+r+h hybrid (`qexp/t1/hybrid_1b.json`); query = query + step (as in 1b_query+step) with the 1b instruction.
cost: 13,608 new documents (the rest cached from 1a) + 1,590 queries, 34 min.
result (train subsample / dev): none 0.3442 / 0.3505 · top-N N=10 0.3398/0.3513, N=20 0.3496/0.3800, N=50
  0.3490/0.3927 · interpolation w=0.5 0.3740/0.3947, 0.6 0.3743/0.4045, **w=0.7 0.3754/0.4053**, 0.8 0.3748/0.4083,
  0.9 0.3641/0.4014. Best on train w=0.7; train − none +0.0312 [+0.0120, +0.0507] → **adopted**. Dev − none
  +0.0548 [+0.0364, +0.0730]; better in 13/13 domains (largest genealogy +0.113, quant +0.100, workplace +0.083).
conclusion: Rule 8 adopted the reasoning embedder on all three conditions (interpolation weight 0.7–0.8 over the top
  50). Final systems: LLM query expansion → BM25 + dense hybrid (+ MaxP on Track 2) → ReasonEmbed-4B mixed into the
  top 50. Total GPU time for rule 8: 3 h 14 min (82k documents at 5–8 per second).

## 2026-11-02 13:05 — step 0: sync and checks
repo: local main = origin/main = `0f3e6ad` (week 5 pushed); working tree clean.
RETECO kit: `git pull --ff-only` 49f96ab → 7ee8acf: only `docs/index.html` (News 26.10 "RETECO is now in Pyserini":
  prebuilt Lucene indexes and BM25/BM25QS baselines for the 13 Track-1 domains of data v1.1; the starter kit stays
  the reference baseline). scorer.py, format_checker.py and the data format are unchanged. No other News since 17.10.
plan for today (estimates written before starting; session ends 17:00): step 1 foreign-gold diagnostics + rule 10
  ~1 h CPU (+ ~15 min GPU for ReasonEmbed over the no-MaxP pool); step 3 history pipeline: LLM generations ~35 min
  GPU, retrieval + hybrid grids ~30 min CPU, ReasonEmbed ~45 min GPU; step 4 contamination ablation: download
  ~10 min, generations ~25 min GPU, retrieval + grids ~30 min CPU; step 2 submission pipeline ~2 h (coding while
  the GPU runs, then an end-to-end dev check). GPU jobs run one at a time (queue: history generations → Llama
  generations → ReasonEmbed no-MaxP → ReasonEmbed history). Step 5 (several HyDE samples) only if time is left.

## 2026-11-02 13:07 — rules 10–13 (written before any of the runs they govern)
definitions (step 1, `scripts/foreign_gold.py`): for a topic q of domain D, a *foreign gold* document is a train or
  dev gold document of another topic of D that is not gold for q (on test all train/dev gold are negatives: News
  17.10). A *test-like* topic is one none of whose gold documents is gold for any topic of the other split.
  Long document = more than one 510-token passage in the MaxP index (bge tokenizer), i.e. > 510 tokens.
rule 10 (2a current, MaxP): A = current main run (ReasonEmbed w 0.8 over the top 50 of the MaxP q+r+h hybrid);
  B = the same without MaxP (ReasonEmbed over the top 50 of the rule-6 q+r+h hybrid, weight chosen on train from the
  rule-8 grid {none, top-N, interp 0.1…0.9}). Train = the rule-8 subsample (≤ 30 topics per domain, seed 20260921).
  MaxP stays in the main run only if on train BOTH (a) the foreign-gold share of the top-10 slots of A minus that of
  B is < 1 percentage point, and (b) on the test-like train topics A − B ≥ +0.005 macro nDCG@10 with paired-bootstrap
  95% lower bound > 0 (topics resampled within domain, 10,000 draws, seed 20260921). Otherwise the main run is B and
  A is the fallback run. For the LLM expansion and ReasonEmbed stages: report only, no choice.
rule 11 (2a with history, week-5 pipeline): LLM inputs (same model, prompts reason + hyde, temperature 0):
  (a) `2a_hist3q` = current question first, then the last ≤ 3 earlier user questions; (b) `2a_hist3qa` = (a) with the
  earlier answers from `conversation_history` (part of the released input). Retrieval: q = the week-4 history text
  with the current question first (`2a_history_qfirst`), BM25 and bge-base L512 dense (no MaxP), variants q and
  q+r+h, hybrid grid tuned on train as in week 4. Candidates: H0 = week-4 history hybrid (train 0.4806), Ha, Hb
  (q+r+h with the generations of (a) / (b)). Best on train adopted over H0 only with train ≥ +0.005 and bootstrap
  lower bound > 0; between Ha and Hb the more complex (b) needs the same margin over (a). Then ReasonEmbed over the top
  50 of the adopted hybrid: query = current question first, then the earlier turns in the form of the adopted input
  (questions only for H0 / (a), Q/A for (b)), instruction "Given a <domain> conversation, retrieve documents that help
  answer the current question.", ≤ 512 tokens; weight from the rule-8 grid on the train subsample, adopted with the
  same margin over "none".
rule 12 (main 2a run): main = the system with the best train macro nDCG@10 (rule-8 subsample) among {best current-turn
  system after rule 10, best history system after rule 11}; the more complex one (history) needs ≥ +0.005 and
  bootstrap lower bound > 0 over the other. Both are reported on dev, plus the 79 dev turns with new gold and the
  T1…T5+ depth breakdown, plus the foreign-gold share.
rule 13 (several HyDE samples, only if time): n ∈ {1, 3, 5} HyDE generations at temperature 0.7, seed 0, plus
  reason at temperature 0; dense = mean of the vectors, BM25 = concatenation; n chosen on train with the usual margin
  (n = 1 always allowed), then ReasonEmbed on top with its weight re-chosen on train. Order 2a (rule-12 main), 1a, 1b.
step 4 setup (ablation, no choice): LLM without BRIGHT exposure = Llama-3.2-3B-Instruct (knowledge cutoff December
  2023 per Meta's model card; BRIGHT was released July 2024). meta-llama repo is gated and no HF token is configured
  here, so the ungated mirror `unsloth/Llama-3.2-3B-Instruct` rev `006f5dcd1393c3add266de40994ba96225e9689d` (same
  weights, bf16) is used with vLLM online FP8 quantisation. Same prompts, temperature 0, conditions 2a current and
  1a (1b if time). Report q+r+h − q of the train-tuned hybrid for both LLMs, BRIGHT vs StackExchange.

## 2026-11-02 13:10 — step 1, part 1: foreign gold for the hybrid stages (no ReasonEmbed yet)
command: `python3 foreign_gold.py --data ../../reteco_data_v11 --kit ../../RETECO/starter_kit --runs ../research/runs_v13
  --out ../research/runs_v13/foreign/report_hybrid.json` (46 s, CPU). Definition detail fixed before the run: gold of
  the same group (other steps of the same 1b query, other turns of the same conversation) is NOT foreign, because on
  test those are test gold too; groups are keyed by (split, group).
result (macro; foreign share of top-10 slots, corpus share in brackets; train all topics / dev):
  1a  week-4 hybrid 5.6% / 4.8% (0.4%) · q+r+h 5.5% / 6.3%.  1b week-4 5.9% / 4.9% · q+r+h 5.8% / 5.3%.
  2a current  week-4 hybrid 1.5% / 1.3% (0.64%) · q+r+h 2.5% / 2.0% · + MaxP 3.2% / 2.4%.
  2a history  week-4 hybrid 1.7% / 1.6%.
  Long documents (> 510 tokens) in the 2a-current top 10: 9.8% (week 4) → 14.1% (q+r+h) → 18.6% (MaxP) on train;
  foreign gold among them 6.1% → 10.1% → 12.5% (all Track-2 long documents: 4.1% are train/dev gold).
  Removing all foreign gold from the ranking raises nDCG@10 by 0.002–0.010 (2a current MaxP train 0.3507 → 0.3544).
  Test-like topics: almost all (2a train 2110 of 2113, dev 854 of 858; 1a 1202/1211, 511/519): train and dev share
  very few gold documents, so the test-like subset barely differs from the full set (noted for rule 10 (b)).
reading so far: every stage that helps also pulls slightly more foreign gold into the top 10 (Track 2: 1.5% → 3.2%
  of the slots, i.e. 2.4× → 5× the corpus share), MaxP most of all and mostly through long documents; in absolute
  terms the effect is small (≤ 0.01 nDCG@10 if all foreign gold vanished). Track 1 is flat (~5–6%, 12–15× the corpus
  share, the same for every stage: TEMPO queries of a domain share topics). ReasonEmbed stages follow (GPU queue).

## 2026-11-02 13:07–13:41 — rule 11 inputs: history generations (Qwen3-4B, reason + hyde)
command: `research/runs_v13/logs/gen_1102.sh` (first call), finished and re-checked by `queue_1102.sh` (log
  `gen_1102.log`, `queue_1102.log`): `llm_expand.py --track 2 --conditions 2a_hist3q 2a_hist3qa --prompts reason hyde`.
cost: 11,884 generations (2,971 turns × 2 inputs × 2 prompts) in 33 min, ~5.0 inputs/s, 634 generated tokens/s
  (longer inputs than the current-turn run). Mean output 124–139 tokens; cut at 256: 0.03–0.07%; empty 0.
  Same model, revision, prompts, temperature 0 as week 5; the model sees the current question and ≤ 3 earlier turns
  (questions, or questions + released answers), never an id. Turn-1 bodies differ from the current-turn ones only
  by the label "Current question:" and were regenerated.
note: estimate was 35 min (written 13:05); actual 33 min. The queue was reordered at 13:10 (before any result):
  ReasonEmbed jobs for step 1 / rule 10 now run before the Llama generations (step 1 has priority over step 4).

## 2026-11-02 13:41–13:47 — rule 10 runs and result: MaxP leaves the main 2a current-turn run
runs (queue `queue_1102.sh`, log `queue_1102.log`; `reason_rerank.py --save-runs runs_v13/foreign/runs`, query vectors
  now cached by sha1(text)): (A) re-run of the rule-8 system on the MaxP pool (`--name 2a_maxp`): 0 new documents +
  1,188 queries, 80 s; reproduces rule 8 (none 0.3828/0.3319, best interp 0.8 0.4359/0.3901; interp 0.9 train 0.4251
  vs 0.4250 before — query vectors re-encoded in a different batch). (B) ReasonEmbed over the rule-6 q+r+h hybrid
  without MaxP (`--name 2a_nomaxp`): 1,324 new documents, 210 s; train subsample / dev: none 0.3671/0.3100, top-50
  0.4069/0.3760, interp 0.7 0.4226/0.3731, **0.8 0.4317/0.3779** (best on train), 0.9 0.4213/0.3789; train − none
  +0.0645 [+0.0430, +0.0857].
foreign gold: `foreign_gold.py --conditions 2a_current --out runs_v13/foreign/report.json` (train = rule-8 subsample,
  330 topics, all of them test-like):
  share of top-10 slots taken by foreign gold, train / dev: A 2.55% / 2.59%, B 2.30% / 2.45% (corpus 0.64%);
  long documents in the top 10: A 18.4% / 17.5%, B 16.0% / 15.4%.
rule 10: (a) foreign share A − B on train = +0.25 pp < 1 pp → satisfied; (b) test-like train topics A − B = +0.0042
  [−0.0007, +0.0092] → below the +0.005 margin and the interval includes 0 → **not satisfied**.
  **Decision: main 2a current-turn run = B (no MaxP, ReasonEmbed w 0.8); A (with MaxP) = fallback run.**
  Dev, reported once: A − B = +0.0123 [+0.0073, +0.0174] (A 0.3901, B 0.3779): on dev MaxP still helps. The rule
  was written to be conservative about a component whose gain is partly a corpus-construction effect, and the train
  evidence for it (once ReasonEmbed is on top) is weak; we keep the train decision and report both.
note: the test-like criterion barely bites (train and dev share almost no gold), so (b) amounts to "MaxP must
  still help clearly on train once ReasonEmbed rescoring is on top"; this is stated in RESULTS.

## 2026-11-02 13:50–14:22 — step 2: end-to-end submission pipeline, dev check
code: `configs/submission.json` (everything frozen: LLM checkpoint + revision + quantisation + prompts + temperature +
  seed, BM25 parameters, encoder + window + MaxP flag, fusion config from the train-chosen hybrid reports, ReasonEmbed
  checkpoint, NF4, pool 50, weight, instructions, tie key sha1, seeds); `scripts/submit.py` (reads only that file,
  the release topic files and the corpora — no qrels; LLM cache keyed by sha1(prompt + model + text); missing
  generations through `llm_expand.py --bodies` in the LLM venv; BM25 → dense (+MaxP) → fusion → ReasonEmbed top 50 →
  then rest of the fused pool, the dense list and the BM25 list, cut at 1000; one file per (variant, domain) because
  Track-2 topic ids repeat across domains; run ids `UA_<sub>_<variant>`); `scripts/score_submission.py` (official
  format_checker with qrels + corpus, own sanity checks, official scorer.py per domain, macro over domains).
pre-check (CPU): topic texts, LLM inputs and history texts built by submit.py equal the research ones for every dev
  topic of 1a, 1b, 2a current, 2a_hist3q, 2a_hist3qa (0 mismatches).
commands: `submit.py --variants 2a_nomaxp 2a_maxp 1a` and `--variants 1b --data ../../reteco_data_v11 --split dev
  --out runs_v13/submit/dev` (logs `submit_dev.log`, `submit_dev_1b.log`; generations and ReasonEmbed vectors from cache:
  0 new generations, 0 new documents), then `score_submission.py --variants 1a 1b 2a_nomaxp 2a_maxp --out
  runs_v13/submit_check.json`.
result (official macro nDCG@10 vs research): 1a 0.3667 = 0.3667 · 1b 0.4053 = 0.4053 · 2a no-MaxP 0.3779 = 0.3779 ·
  2a MaxP 0.3901 = 0.3901 (all differences 0.0000; per domain identical, e.g. drones 0.3049). format_checker exit 0 for
  every file; judged topics missing 0, duplicate doc ids 0, unknown doc ids 0, score order violations 0, depth 1000.
timing on dev (cached LLM/ReasonEmbed, so these are retrieval costs only): Track-1 BM25 indexing dominates (288–309 s
  for 13 domains, rebuilt per variant), Track 2 25–28 s; BM25 search 0.01–0.02 s/topic; dense 0.01–0.02 s/topic
  (1b 0.22 s/topic while the Llama job shared the GPU); fusion 1 ms/topic.
test-time estimate (~350 1a queries, ~820 1b steps at the dev ratio 2.34 steps/query, ~200 2a turns, 2–3 2a variants):
  LLM 2 prompts × ~1,600–1,800 inputs at 5–8 inputs/s ≈ 6–10 min (+ ~2 min model load per call); BM25 indexes ≈ 11 min;
  dense < 2 min; ReasonEmbed is the cost: pool documents per topic on dev 43.8 (1a), 22.6 (1b, steps share pools),
  28.3 (2a); only 9–15% of dev pool documents were already in the train-subsample pools, so expect ≈ 15k (1a) + ~9k
  (1b beyond 1a) + ~6k per 2a variant ≈ 35–40k new documents at 7–8 docs/s ≈ 75–90 min. Total ≈ 1.75–2 h on this
  laptop, restartable (vectors saved every 2,000 documents).

## 2026-11-02 13:53–14:19 — step 4 generations: Llama-3.2-3B-Instruct (FP8), reason + hyde
command: `queue_1102.sh` → `llm_expand.py --llm llama3.2-3b --track 2 --conditions 2a_current` and `--track 1
  --conditions 1a` (out `runs_v13/llm_llama/t{1,2}`, git-ignored; meta.json records model, revision 006f5dc…, fp8).
cost: 2a 5,942 generations at ~13 inputs/s (1,619 tokens/s); 1a 3,460 at ~3.4 inputs/s (longer Track-1 inputs);
  26 min in total, gpu-util 0.75. Mean reason output ~170 tokens (longer than Qwen's ~136).

## 2026-11-02 13:41–13:58 — rule 11, hybrid stage: history with the LLM (Hb adopted)
commands: `research/runs_v13/logs/step3_hist.sh` (log `step3_hist.log`): `qexp_search.py --track 2 --cond 2a_hist3q
  --query-cond 2a_history_qfirst --variants q q+r+h` and `--cond 2a_hist3qa --variants q+r+h` (out `runs_v13/hist/t2`,
  0 missing generations), `hybrid.py` over the three conditions (out `hist/t2/hybrid.json`, 7 min).
incident: the scripted choice (`select_rule.py`, then `rule11_choice.py`) failed because the week-4 history report
  (`runs_v13/hybrid/bge-base_L512_t2.json`) has no train per-topic values; the waiting ReasonEmbed job was stopped
  before it ran. Fix: `hybrid.py --conditions 2a_history --dense-cond 2a_history_qfirst` re-run on the same runs_v13
  BM25/dense files (out `hist/t2/hybrid_h0.json`, 3 min): same configuration (z-score α 0.6) and the same numbers
  (train 0.4806, dev 0.4352); `rule11_choice.py` now reads H0 from there (`select/rule11.json`).
result (train / dev, fusion chosen on train): H0 (week 4, no LLM) 0.4806 / 0.4352 · Ha (LLM input = current + ≤ 3
  earlier questions) 0.4800 / 0.4452 · Hb (+ earlier answers) **0.5112 / 0.4601**.
  train Ha − H0 −0.0006 [−0.0113, +0.0099]; Hb − H0 +0.0306 [+0.0202, +0.0407]; Hb − Ha +0.0312 [+0.0248, +0.0378]
  → **Hb adopted** (margin over H0 and over Ha). Dev Hb − H0 +0.0250 [+0.0099, +0.0399]; Ha − H0 +0.0101 [−0.0056, +0.0257].
reading: the LLM needs the earlier answers to help; with questions only it adds nothing over the plain history text
  on train. Next: ReasonEmbed over the Hb top 50 (`step3b_hist_reason.sh`, after the GPU queue).

## 2026-11-02 14:25 — rule for the history examples (written before any example is seen)
file: `research/cases/history_llm_dev.md`. Systems: before = H0 (week-4 history hybrid), after = Hb (rule-11 hybrid,
  LLM input with earlier answers). Dev turns with turn number ≥ 2, split into improved (nDCG@10 after > before) and
  worsened; 2 from each drawn with random.Random(20260921) over sorted (domain, qid) → 4 examples. Shown: current
  question, the history the LLM saw (first 400 chars), the LLM reason text (first 400 chars), each gold document's
  first 250 chars with its rank before and after. No resampling.

## 2026-11-02 14:24 — rule 13 clarified (before any sampled generation exists)
"n = 1 always allowed" means: the baseline is the current system (one HyDE passage at temperature 0). Candidates:
  n = 3 and n = 5 HyDE passages sampled at temperature 0.7 (vLLM, seed 0, one request with n = 5; n = 3 = the first
  three samples), reason text unchanged (temperature 0). BM25 query = q + r + all n passages; dense = normalised sum of
  e(q), e_query(r) and the mean of the n e_doc(h_i). n = 1 at temperature 0.7 is reported, not a candidate. Hybrid grid
  tuned on train per candidate; n* = best train macro, adopted over the baseline with +0.005 and bootstrap lower
  bound > 0; then ReasonEmbed over the top 50 with its weight re-chosen on the rule-8 train subsample, and the
  final comparison against the current final system of the condition on that subsample with the same margin.
  Order: 2a main (rule 12), then 1a, then 1b — as time allows before 17:00.

## 2026-11-02 14:20–14:31 — step 4 result: contamination ablation with an LLM that predates BRIGHT (no choice)
commands: `research/runs_v13/logs/step4_llama.sh` (log `step4_llama.log`): `qexp_search.py --variants q+r+h --llm
  runs_v13/llm_llama/t{2,1} --llm-model unsloth/Llama-3.2-3B-Instruct` for 2a current and 1a (0 missing generations),
  `hybrid.py` per condition (fusion tuned on train: 2a z-score α 0.6, 1a z-score α 0.7; logs `llama_hyb_*.log`);
  bootstraps (train topics / dev topics, within domain) in `runs_v13/llama/bootstrap_full.json`.
result (q+r+h hybrid − plain-query hybrid q; train / dev):
  2a current, all 11 domains: Qwen3-4B +0.0562 [+0.046, +0.066] / +0.0557 [+0.041, +0.071];
                              Llama-3.2-3B +0.0235 [+0.013, +0.033] / +0.0282 [+0.014, +0.043]
    BRIGHT (6):         Qwen +0.1075 [+0.095, +0.121] / +0.1117 [+0.091, +0.133]; Llama +0.0665 [+0.054, +0.080] / +0.0747 [+0.056, +0.094]
    StackExchange (5):  Qwen −0.0053 [−0.022, +0.011] / −0.0115 [−0.032, +0.009]; Llama −0.0280 [−0.044, −0.012] / −0.0276 [−0.051, −0.005]
  1a (TEMPO, not BRIGHT): Qwen +0.0486 [+0.035, +0.063] / +0.0425 [+0.021, +0.063]; Llama +0.0274 [+0.013, +0.042] / +0.0231 [+0.001, +0.046]
  macro train/dev: 2a q 0.2805/0.2543, Qwen 0.3367/0.3100, Llama 0.3040/0.2825; 1a q 0.2462/0.2834, Qwen 0.2949/0.3258,
  Llama 0.2737/0.3064.
reading: an LLM whose documented knowledge cutoff (December 2023) predates BRIGHT (July 2024) reproduces the same
  pattern — a large gain in the BRIGHT-derived domains, none (here even a loss) in the StackExchange ones. Qwen is
  stronger everywhere, and by a similar factor in BRIGHT domains (Llama reaches 62% of Qwen's train gain) and on Track 1
  where BRIGHT plays no role (56%). So the BRIGHT gain is not mainly benchmark contamination; it is consistent with
  BRIGHT gold being encyclopaedic text whose vocabulary any instruction LLM reproduces. Limits: the BRIGHT source
  documents (Wikipedia pages, StackExchange posts) predate both models, so exposure to the documents themselves cannot
  be excluded; one alternative model, one size (3B vs 4B), Llama via an ungated mirror with FP8 quantisation.

## 2026-11-02 14:20–14:33 — rule 11, second stage: ReasonEmbed over the history hybrid (adopted)
command: `research/runs_v13/logs/step3b_hist_reason.sh` (log `step3b_hist_reason.log`): `reason_rerank.py --track 2
  --conditions 2a_hist3qa__q+r+h --query-cond 2a_hist3qa --name 2ah_hybrid --pool 50 --save-runs runs_v13/foreign/runs`
  (query = current question first, then ≤ 3 earlier Q/A turns, instruction "Given a <domain> conversation, retrieve
  documents that help answer the current question."; ≤ 512 tokens).
cost: 4,506 new documents + 1,188 queries, 751 s.
result (train subsample / dev): none 0.5170 / 0.4601 · top-N N=10 0.5419/0.4980, N=20 0.5658/0.5296, N=50 0.5812/0.5438 ·
  interp 0.5 0.5585/0.5154, 0.7 0.5750/0.5343, 0.8 0.5818/0.5386, **0.9 0.5830/0.5475** (best on train).
  train − none +0.0660 [+0.0406, +0.0911] → **adopted** (w 0.9). Dev − none +0.0874 [+0.0723, +0.1019].

## 2026-11-02 14:33 — rule 12 result: the main 2a run is the history system
command: `foreign_gold.py --conditions 2a_history` then `final_1102.py --runs runs_v13` (inside `step5_hyde.sh`, log
  `step5_hyde.log`; out `select/rule12.json`, `final_1102.json`).
result (train subsample, same 330 topics): current-turn best after rule 10 (B, no MaxP) 0.4317 vs history (Hb +
  ReasonEmbed w 0.9) 0.5830; history − current +0.1513 [+0.1172, +0.1871] → **main 2a = with history**; fallbacks:
  current turn without MaxP (B) and with MaxP (A). Dev: history 0.5475, B 0.3779, A 0.3901.
foreign gold, 2a history (dev top 10): week-4 hybrid 1.59%, Hb hybrid 1.74%, + ReasonEmbed 2.16% (corpus 0.64%);
  removing all foreign gold: 0.5475 → 0.5503.
dev breakdown (`t2_breakdown.py`, out `foreign/t2_breakdown_dev.json`; mean over turns):
  | system | macro | first turn (211) | recycled gold (568) | new gold (79) | T1 | T2 | T3 | T4 | T5+ |
  | history main | 0.5475 | 0.5213 | 0.6371 | 0.3759 | 0.5213 | 0.5963 | 0.6021 | 0.6417 | 0.5870 |
  | history hybrid (no ReasonEmbed) | 0.4601 | 0.4195 | 0.5556 | 0.3149 | 0.4195 | 0.4870 | 0.5199 | 0.5914 | 0.5430 |
  | current, no MaxP (B) | 0.3779 | 0.5019 | 0.3805 | 0.3580 | 0.5019 | 0.3838 | 0.3629 | 0.3685 | 0.4062 |
  | current, MaxP (A) | 0.3901 | 0.5188 | 0.3989 | 0.3677 | 0.5188 | 0.4017 | 0.3824 | 0.3815 | 0.4235 |
reading: as in week 4, most of the history gain is on turns whose gold was already gold for an earlier turn (the
  earlier answers are in the input) — 0.38 → 0.64. But unlike week 4 (history hybrid 0.208 vs current 0.245 on the 79
  new-gold turns), the week-5 history system no longer loses on new-gold turns (0.376 vs 0.358 / 0.368). First turns
  have no history; their difference (0.521 vs 0.502) comes from the different fusion weight, ReasonEmbed weight and
  instruction. Caveat for test: how often test target turns reuse earlier gold is unknown; the current-turn runs stay
  as fallbacks and as the analysis numbers (Steve, 19.10).

## 2026-11-02 14:33–14:53 — incident: GPU overcommit stalled two jobs (no result affected)
what: the dev check of the new variants (`submit.py --variants 2a_history 1a_noRE 1b_noRE`, log `submit_dev2.log`) ran
  next to the rule-13 vLLM job (gpu-util 0.75, n = 5 sampling). GPU memory reached 7.7 of 8 GB; both processes sat at
  100% with almost no progress (submit.py stuck in the dense stage of the 9th Track-2 domain for ~15 min; the first
  generation chunk took ~20 min instead of ~3). Killed submit.py at 14:53; generation then ran at ~3 min per 256 inputs.
  Fix (before re-running): `submit.py` skips the ReasonEmbed stage entirely when a variant has `use: false`; the dev
  check of the new variants is re-run once the GPU is free. README now warns not to run submit.py next to vLLM.

## 2026-11-02 14:33–15:37 — rule 13 result for 2a (history, the rule-12 main condition): several HyDE samples — negative
commands: `research/runs_v13/logs/step5_hyde.sh` (log `step5_hyde.log`): `llm_expand.py --track 2 --conditions
  2a_hist3qa --prompts hyde --samples 5 --temperature 0.7` (14,855 passages for 2,971 inputs; 14:33–15:27, ~20 min of
  it stalled by the GPU overcommit above, then ~3 min per 256 inputs, 0.9 inputs/s, ~580 tokens/s); `qexp_search.py
  --variants q+r+h1s q+r+h3 q+r+h5` (0 missing; out `runs_v13/hyde5/t2`); `hybrid.py` (6 min); `select_rule.py --rule 13`
  (out `select/rule13_hybrid.json`).
result (hybrid, fusion tuned on train: z-score α 0.6 for all; train / dev): baseline one HyDE at temperature 0
  **0.5112 / 0.4601** · one sample at 0.7 (reported only) 0.5094 / 0.4603 · n = 3 0.5074 / 0.4588 · n = 5 0.5030 / 0.4569.
  Best on train = the baseline → **not adopted**; the ReasonEmbed stage of rule 13 is therefore not run.
reading: averaging several sampled passages makes the history query slightly worse, monotonically in n, on train and
  dev. With the history and the earlier answers in the prompt, one deterministic passage already carries the useful
  vocabulary; extra samples add drift.
not done (time): rule 13 for 1a and 1b. 1a would need ~55 min of n = 5 generation (Track-1 inputs are long, ~0.5–0.9
  inputs/s) and would have blocked the GPU for the dev check of the main 2a run; the queued job (`step5_hyde_1a.sh`)
  was cancelled at 15:29 before generating anything.

## 2026-11-02 15:31–15:41 — step 2, dev check of the main 2a run and the fallbacks (after the GPU was free)
command: `submit.py --variants 2a_history 1a_noRE 1b_noRE --split dev` (log `submit_dev2.log`; 0 new generations,
  0 new ReasonEmbed documents; the noRE variants skip ReasonEmbed), then `score_submission.py` over all seven variants
  (out `runs_v13/submit_check.json`).
result (official macro nDCG@10 = research number, all differences 0.0000): main runs 1a 0.3667, 1b 0.4053,
  2a history 0.5475; fallbacks 1a no-ReasonEmbed 0.3258, 1b no-ReasonEmbed 0.3505, 2a current no-MaxP 0.3779,
  2a current MaxP 0.3901. format_checker exit 0 everywhere; missing 0, duplicates 0, unknown ids 0, depth 1000.

## 2026-11-02 15:44–16:13 — step 4 extension: Llama-3.2-3B on 1b (ablation, no choice)
command: `research/runs_v13/logs/step4_llama_1b.sh` (log `step4_llama_1b.log`): generations 7,952 (3,976 steps × 2
  prompts) 15:44–16:05; `qexp_search.py --cond 1b_query+step --variants q+r+h` (0 missing; out `runs_v13/llama/t1b`);
  `hybrid.py` (fusion tuned on train: z-score α 0.7). (A first launch at 15:39 waited on a `pgrep -f` pattern that
  matched a stale waiting shell; relaunched without the wait at 15:44.)
result (q+r+h hybrid − plain-query hybrid; train / dev): Qwen +0.0560 [+0.044, +0.069] / +0.0640 [+0.047, +0.082];
  Llama +0.0417 [+0.029, +0.054] / +0.0486 [+0.028, +0.070]; macro Llama 0.3083 / 0.3352 (q 0.2665 / 0.2865,
  Qwen 0.3226 / 0.3505). Llama reaches 74% of Qwen's train gain on 1b (56% on 1a, 62% on the BRIGHT domains of 2a).

## 2026-11-02 16:15 — session summary and what is left
submission systems (train-chosen; dev nDCG@10; `configs/submission.json`, RESULTS section X):
  1a main 0.3667 (fallback without ReasonEmbed 0.3258) · 1b main 0.4053 (fallback 0.3505) · 2a main = history 0.5475
  (rule 12; fallbacks current turn without MaxP 0.3779 — rule 10 — and with MaxP 0.3901). All seven variants are
  reproduced exactly by `submit.py` from the topic files with the official checker and scorer.
done today: step 0, step 1 (foreign gold + rule 10), step 2 (submission pipeline + dev check + test-time estimate),
  step 3 (rules 11, 12), step 4 (2a, 1a and 1b), step 5 for 2a (negative).
not done: rule 13 for 1a and 1b (time; cancelled before generating). Open: Steve's answers to the 26.10 questions
  were never recorded; the format of the official run upload (one file per domain?) is not announced yet.

## 2026-11-10 08:09 — A0: sync and checks
repo: local main = origin/main = `1261932`, working tree clean. RETECO kit: `git fetch` → nothing new (HEAD 7ee8acf);
  scorer / format_checker / data unchanged. Website News checked 08:12: last item 26.10 (Pyserini); nothing on the test
  format, the Track-2 test fields (`conversation_history`, earlier answers), the run upload format or a run limit
  ("submission limits will be announced"); evaluation opens 10 Jan 2027, closes ≤ 31 Jan 2027. Disk 849 GB free.
context (from the user, 09.11): Steve cancelled the 9.11 meeting and asked for a written update; on 02.11 he agreed to
  all proposed next steps, so a per-source choice (BRIGHT / StackExchange) is now allowed under a written rule. Open
  risk: whether test `conversation_history` contains the earlier answers is not stated anywhere (question sent to the
  organisers' list on 09.11, no answer yet); the main 2a run depends on them.
history format audit (all train+dev turns, CPU): turn 1 always "No previous conversation."; 2,264 turns ≥ 2, 0 empty
  answers. 2,149 turns have one Q/A pair per earlier turn; 115 long conversations (turn ≥ 6) use another layout:
  "Earlier discussion covered: Turn 1: <question>; Turn 2: …" (questions only) + "Recent conversation:" with the last
  two Q/A pairs. The frozen parser (`llm_expand.history_pairs`) ignores the summary line, so those turns give the LLM
  2 earlier turns instead of 3 — this is what produced the dev 0.5475 and stays frozen for the main run.
  237 continuation lines (answers over several lines) are appended to the answer, as before.
plan for phase A (10 h from 08:09; A6 starts by 17:30 at the latest). Estimates: A1 ~2 h (code 40 min, retrieval
  + hybrid 15 min CPU/GPU, ReasonEmbed 2 × ~13 min GPU, submit/synthetic checks 30 min); A2 ~1.5 h (answer generation
  ~15 min GPU, reason+hyde ~10 min, submit.py over train-sub + dev ~20 min); A3 ~1 h (2 × ReasonEmbed ~13 min GPU);
  A4 ~3–4 h (download ~10 min, speed test, then scoring as time allows); A5 CPU check 15 min; A6 40 min.
  GPU queue strictly one job at a time: A1 ReasonEmbed → A3 ReasonEmbed → A2 vLLM → A2 submit → A4 reranker.

## 2026-11-10 08:13 — rules 14–17 and the A2 design (written before any of the runs they govern)
rule 14 (2a fallback without earlier answers). "Without answers" = no text of any earlier answer reaches any input:
  BM25 text, dense query, LLM input, ReasonEmbed query. Text without answers: q = current question + newline +
  the released history with every answer removed (`history.strip_answers`; summary questions and Q lines kept) —
  new condition `2a_history_qonly_qfirst`; the week-4 `2a_history_qfirst` text DOES contain the answers (it is the
  whole history string), so H0 and Ha of rule 11 are not answer-free. LLM input = `2a_hist3q` (current + ≤ 3 earlier
  questions; existing generations). ReasonEmbed query = the `2a_hist3q` body, instruction "Given a <domain>
  conversation, retrieve documents that help answer the current question.", ≤ 512 tokens, pool 50, weight = best on
  the train subsample in the rule-8 grid {none, top-N, interp 0.1…0.9}. Code asserts, per topic, that no earlier
  answer (any 40-char prefix of a parsed answer of ≥ 20 chars) occurs in any of the four inputs.
  Candidates, in order of complexity: (iii) B = current turn, no MaxP (rule 10; train-sub 0.4317);
  (ii) H0q + ReasonEmbed (plain answer-free history text, BM25 + bge-base hybrid tuned on full train, no LLM);
  (i) Haq + ReasonEmbed (q+r+h with the 2a_hist3q generations over the answer-free text, hybrid tuned on full train).
  Choice on the rule-8 train subsample (330 topics): take the best by train macro; it is adopted only if it beats
  every simpler candidate by ≥ +0.005 with paired-bootstrap 95% lower bound > 0 (10,000, seed 20260921, within
  domain); otherwise drop it and repeat among the rest; B is the default. Dev once per candidate (+ the T1…T5+,
  recycled / new gold breakdown).
  submit.py: per Track-2 domain file, if at least one turn with turn ≥ 2 has a non-empty parsed answer → main
  `2a_history`, else → the rule-14 fallback (new variant `2a_history_q`). Decision + counters in stdout and in
  `<out>/2a_auto/decision.json`; the fallback variant is always built as its own run too.
A2 (analysis, no choice): LLM-written earlier answers instead of the reference ones. Qwen3-4B (same checkpoint, vLLM,
  temperature 0, max 256 new tokens), prompt: answer the question in ≤ 150 words, given the earlier turns of the same
  conversation (≤ 3 earlier turns, with OUR generated answers — generated turn by turn, so no reference answer is
  ever seen), no documents. The released history strings are rebuilt with each reference answer replaced by the
  generated answer of that turn (same layout, same truncation of nothing else). Then the frozen main 2a pipeline
  (Hb + ReasonEmbed w 0.9, fusion z-score α 0.6, no re-tuning) via submit.py on the rule-8 train subsample and on
  dev. Report macro, recycled-gold (568 dev) / new-gold (79) turns, T1…T5+, against reference answers and rule 14.
rule 15 (per-source query variant, Track 2). Groups by domain name: BRIGHT = biology, earth_science, economics,
  psychology, robotics, sustainable_living; StackExchange = drones, hardware, law, medicalsciences, politics.
  For 2a current (B) and 2a history (main), the q-system = plain-query hybrid (2a current: `2a_current__q`, rule-6
  report; history: H0 = week-4 history hybrid, text with answers) + ReasonEmbed over its top 50 with the same query
  and instruction as the current system of that condition and its weight chosen on the whole train subsample
  (rule-8 grid). The q+r+h system is the current one. For each group G: the grouped system uses the q-system on G
  only if, on the train-subsample topics of G, q-system − q+r+h system ≥ +0.005 with bootstrap lower bound > 0
  (within domain, as above); otherwise unchanged. Dev reported once per group and for the combined system.
rule 16 (LLM reranker). Qwen/Qwen3-Reranker-4B (pointwise yes/no, prompt exactly as in the model card), transformers
  + bitsandbytes NF4 (fp16 compute); fallback Qwen3-Reranker-0.6B fp16 if 4B does not fit or runs < 5 pairs/s
  (reason logged). Pool = top 20 of the final system of the condition (train subsample + dev, the saved rule-8/11
  runs): 1a, 1b, 2a history (main), 2a current B. Instruction per domain in the ReasonEmbed style; query: 1a query;
  1b query + step; 2a history = the ReasonEmbed query of Hb (current first, ≤ 3 earlier Q/A); 2a current = current
  question. Document cut to 512 tokens; scores cached by sha1(instruction + query + document text).
  Grid on the train subsample: none; reranker order over the top N; interpolation (1 − w)·z(final) + w·z(reranker)
  over the top N, w ∈ {0.1 … 0.9}; N ∈ {10, 20}; z over the N pool documents of the topic; ties sha1. Best on train
  adopted over none with +0.005 and bootstrap lower bound > 0; dev once. If adopted: new submission.json entry +
  submit.py stage + dev check with score_submission.py. Order 2a history → 1a → 2a current → 1b.
rule 17 (ReasonEmbed pool 50 → 100), conditional. CPU first: on train (all topics) the share of gold documents in
  the top 100 but not the top 50 of the hybrid of each final system. ReasonEmbed at 100 is run for a condition only if
  that share is ≥ 3% of its gold; then 50 vs 100 chosen on the train subsample (weight re-chosen in the rule-8 grid)
  with the usual margin. If rule 16 adopts a reranker, rule 17 is evaluated without it (stated in RESULTS).

## 2026-11-10 08:14–08:20 — A1 / rule 14, retrieval + hybrid stage on the answer-free history text
code: `scripts/history.py` (new: label normalisation, `parse`, `has_answers`, `strip_answers`, `qonly_qfirst`,
  `assert_answer_free`; audit `python3 history.py --data ../../reteco_data_v11`: normalisation changes 0 of 2,971
  released strings, the frozen parser output changes for 0 turns, 2,264/2,264 turns ≥ 2 have answers, 0 after
  `strip_answers`; all earlier turns are found (Q/A pairs + summary questions) for every turn; 0 unparsed lines).
  `dense_search.plan` gains `2a_history_qonly_qfirst` (asserts answer-free per topic: 40-char windows from the start,
  middle and end of each earlier answer, windows that also occur in a question excluded — answers often echo the
  question). LLM input `2a_hist3q` = current + ≤ 3 earlier questions (frozen generations of 02.11, 0 missing).
command: `research/runs_v13/logs/queue_1110a.sh` (log `queue_1110a.log`): `qexp_search.py --cond 2a_hist3q --query-cond
  2a_history_qonly_qfirst --variants q q+r+h` (out `runs_v13/histq/t2`, 1.5 min) and `hybrid.py` (4.5 min).
result (hybrid, fusion tuned on full train; train / dev macro nDCG@10):
  H0q (plain answer-free history) z-score α 0.7: 0.3877 / 0.3545 (BM25 0.2678/0.2812, dense 0.3631/0.3245)
  Haq (q+r+h, LLM sees questions only) z-score α 0.6: 0.4311 / 0.3917 (BM25 0.3762/0.3663, dense 0.3932/0.3446)
  for reference: current-turn q+r+h hybrid 0.3367 / 0.3100; with answers H0 0.4806 / 0.4352, Hb 0.5112 / 0.4601.
reading: without any answer the earlier questions still carry a lot (+0.09 train over the current-turn hybrid); the
  answers add another +0.08 (Hb − Haq). ReasonEmbed stage running (then rule-14 choice).

## 2026-11-10 08:19 — rule 17, CPU part: gold between ranks 51 and 100 of the frozen hybrids
command: `python3 pool_depth.py --runs ../research/runs_v13 --data ../../reteco_data_v11 --out
  ../research/runs_v13/select/rule17_ceiling.json` (23 s). Share of all gold documents (micro) that the hybrid puts in
  its top 100 but not its top 50, train (all topics) / dev; recall@50 train in brackets:
  1a 8.9% / 7.4% (0.538) · 1b 6.9% / 6.7% (0.717) · 2a current B 8.4% / 10.3% (0.681) · 2a history 5.3% / 7.1% (0.866).
  All four ≥ 3% → ReasonEmbed over the top 100 is to be run for every condition (GPU; scheduled after A4 — phase B1
  if it does not fit; note: a pool of 100 roughly doubles the documents to encode, ~40 min per condition).

## 2026-11-10 08:20–08:36 — A1 / rule 14 result: the answer-free fallback is H0q + ReasonEmbed (no LLM)
commands: `queue_1110a.sh` → `reason_rerank.py --backend bnb --bits 4 --pool 50 --query-cond 2a_hist3q` over the
  `histq` hybrids (`--name 2ahq_haq`: 1,555 new documents + 898 queries, 260 s; `--name 2ahq_h0q`: 5,046 new
  documents, 495 s; runs saved in `runs_v13/foreign/runs`, score dumps in `runs_v13/scores/`); then
  `rule14_choice.py` (out `select/rule14.json`) and `t2_breakdown.py` (out `select/rule14_breakdown_dev.json`).
  Answer-free check before scoring (CPU, all 2,971 train/dev turns): LLM input `2a_hist3q`, ReasonEmbed query and
  BM25/dense text pass `assert_answer_free`; positive control: the check fires on 2,264/2,264 with-answer bodies.
result (train subsample 330 topics / dev 858; ReasonEmbed weight chosen on train):
  B (current turn, rule 10)           0.4317 / 0.3779 (w 0.8)
  H0q + ReasonEmbed                   0.5168 / 0.4802 (w 0.9; hybrid alone 0.3970 / 0.3545)
  Haq + ReasonEmbed                   0.5264 / 0.4852 (w 0.8; hybrid alone 0.4536 / 0.3917)
  train tests: Haq − H0q +0.0096 [−0.0069, +0.0267] → fails; H0q − B +0.0851 [+0.0542, +0.1169] → passes.
  **Decision: answer-free fallback = H0q + ReasonEmbed w 0.9** (no LLM at all). Dev − B: H0q +0.1023 [+0.0828, +0.1220];
  Haq +0.1074 [+0.0899, +0.1250].
dev breakdown (mean over turns): first turn (211) / recycled gold (568) / new gold (79):
  main with answers 0.5213 / 0.6371 / 0.3759 · H0q+RE 0.4797 / 0.5390 / 0.3766 · Haq+RE 0.5014 / 0.5439 / 0.4022 ·
  B 0.5019 / 0.3805 / 0.3580. T2…T5+: H0q+RE 0.511 / 0.504 / 0.545 / 0.537 (main 0.596 / 0.602 / 0.642 / 0.587).
reading: the earlier QUESTIONS alone recover most of the history gain on recycled-gold turns (0.38 → 0.54; the
  answers take it to 0.64). On first turns H0q+RE is below B (0.480 vs 0.502) because it has no LLM: a "B on turn 1,
  H0q+RE later" combination looks better but was not a pre-registered candidate — noted, not adopted.
submission: `configs/submission.json` gains `2a_history_q` (variant "q": no LLM; BM25 on the answer-free text; dense
  e_query(q); z-score α 0.7; ReasonEmbed w 0.9 with the conversation instruction over current + ≤ 3 earlier
  questions) and `_auto_2a` (with answers → `2a_history`, without → `2a_history_q`). `submit.py`: new query type
  `2a_hist3q_qonly` (asserts answer-free inputs per topic), plain variant without LLM, `--variants 2a_auto` (decision +
  parser counters per domain in stdout and `2a_auto/decision.json`; both variants always built), history label
  normalisation before parsing (identity on train/dev).
dev check: `submit.py --variants 2a_history_q --split dev` (45 s; 0 new ReasonEmbed documents) + `score_submission.py`
  → official macro **0.4802 = research 0.4802**; format_checker exit 0 for all 11 files, missing 0, dup 0, unknown 0.

## 2026-11-10 08:36–08:51 — A3 / rule 15 result: per-source query variant — no change
commands: `queue_1110a.sh` → `reason_rerank.py` over the plain-query pools: `--conditions 2a_current__q --query-cond
  2a_current --name 2a_cur_q` (rule-6 q hybrid) and `--conditions 2a_history --query-cond 2a_hist3qa --name 2ah_h0`
  (week-4 history hybrid H0, ReasonEmbed query = the main run's: current + ≤ 3 earlier Q/A); ~7 min each. Then
  `rule15_choice.py` (out `select/rule15.json`). Score dumps of the four final systems re-made from cached vectors
  (0 new documents; they reproduce 0.4317/0.3779 and 0.5830/0.5475 exactly) for rule 16.
q-systems over all 11 domains (train sub / dev): current q 0.3967 / 0.3591 (w 0.9) vs q+r+h 0.4317 / 0.3779;
  history H0 0.5804 / 0.5377 (w 0.9) vs Hb 0.5830 / 0.5475.
result by group (train q − q+r+h [95%] → choice; dev q − q+r+h for reference):
  2a current  BRIGHT        −0.0623 [−0.0944, −0.0328] → q+r+h   (dev −0.0533)
  2a current  StackExchange −0.0022 [−0.0218, +0.0173] → q+r+h   (dev +0.0226 [+0.0053, +0.0407])
  2a history  BRIGHT        −0.0047 [−0.0250, +0.0148] → q+r+h   (dev −0.0150)
  2a history  StackExchange −0.0000 [−0.0175, +0.0168] → q+r+h   (dev −0.0036)
  **Decision: no per-source split** (no group passes the margin on train); combined = current systems.
reading: once ReasonEmbed is on top, the LLM's loss on StackExchange (−0.005 / −0.012 at the hybrid stage on 02.11)
  disappears on train (−0.002) — the reasoning embedder absorbs it — while the BRIGHT gain stays (+0.06). On dev the
  StackExchange current-turn q-system would have been better (+0.023); that is a dev observation only, the train
  rule says no. With history, the LLM adds nothing measurable on top of H0 + ReasonEmbed in either group (train
  +0.000 / +0.005): almost all of the history system's strength comes from the history text + ReasonEmbed.

## 2026-11-10 08:52–09:17 — A2: the main 2a run with LLM-written earlier answers (analysis, no choice)
code: `scripts/gen_answers.py` (generate: LLM venv; build: synthetic releases), `scripts/a2_report.py`.
command: `research/runs_v13/logs/queue_1110b.sh` (log `queue_1110b.log`):
  `gen_answers.py --phase generate` — targets = rule-8 train subsample (330 turns) + all dev turns (858); 407
  conversations need earlier answers; 1,168 answers generated turn by turn in 10 rounds (5.3 min; mean 103 words, 2
  cut at 256 tokens, 0 empty). Prompt (system "You are a helpful assistant in a conversation. Answer in plain English
  text only."; user "Answer the current question below as a knowledgeable assistant would, in at most 150 words. Do
  not ask questions back." + ≤ 3 earlier turns with OUR earlier answers + current question); Qwen3-4B AWQ, temperature 0.
  `--phase build`: data_gen / data_ref releases (`benchmark_trainsub.json` = the 330 subsample turns, `benchmark_dev.json`
  = all dev turns); 1,961 Q/A pairs replaced, question order matched 1,961/1,961, layout unchanged (summary lines kept).
  Then the frozen main run `submit.py --variants 2a_history` on data_gen (trainsub: 502 new LLM generations + 319 new
  ReasonEmbed documents, 6.8 min; dev: 12.5 min) and on data_ref trainsub (control, all cached).
control: data_ref trainsub = 0.5830 = research train-subsample number (exact).
result (macro nDCG@10; mean over turns for groups; bootstrap vs the reference-answer run):
  | system | train sub | dev | dev first (211) | dev recycled (568) | dev new gold (79) |
  | main, reference answers   | 0.5830 | 0.5475 | 0.5213 | 0.6371 | 0.3759 |
  | main, LLM-written answers | 0.5205 | 0.4823 | 0.5213 | 0.5396 | 0.3663 |
  | no answers (rule 14)      | 0.5168 | 0.4802 | 0.4797 | 0.5390 | 0.3766 |
  | current turn B            | 0.4317 | 0.3779 | 0.5019 | 0.3805 | 0.3580 |
  LLM-written − reference: train −0.0626 [−0.0808, −0.0452], dev −0.0652 [−0.0771, −0.0535].
  dev by depth T2 / T3 / T4 / T5+: reference 0.596 / 0.602 / 0.642 / 0.587; LLM-written 0.503 / 0.509 / 0.534 / 0.551;
  no answers 0.511 / 0.504 / 0.545 / 0.537.
reading (paper: "what access to the reference answers is worth"): the whole advantage of the main run over the
  answer-free run (+0.067 dev) comes from the reference answers being written from the gold documents. Answers our
  own LLM writes without documents are worth nothing measurable over the questions alone (dev +0.002, train +0.004;
  on recycled-gold turns 0.540 vs 0.539). The loss is entirely on later turns (T2+) and mostly on recycled-gold turns
  (0.637 → 0.540); new-gold turns barely move (0.376 → 0.366). If test histories carry reference answers built like
  train/dev, the main run should keep its dev level; if a deployed system had to use its own answers, expect ≈ 0.48.

## 2026-11-10 09:17–09:27 — A1 check: synthetic test releases and the 2a automation
code: `scripts/make_test_release.py` (dev topic files → split "test": Track-2 turn fields `gold_doc_ids`, `answer`,
  `subquestion_reasoning(_metadata)`, conversation `original_answer` and the gold count in `metadata` removed; no
  qrels; documents symlinked). Release 1 = released histories (647 turns ≥ 2 with answers); release 2 = the same
  with every earlier answer removed (`--strip-answers`; 0 turns with answers after). Both outside the repo (scratchpad).
commands (`queue_1110b.sh`): `submit.py --variants 2a_auto --split test` on each release; then format_checker (with the
  dev qrels and the corpus) and nDCG@10 with the dev qrels (the topic ids are the dev ids).
result:
  release with answers: decision `2a_history` for 11/11 domains (counters per domain in stdout and decision.json:
    turns ≥ 2 with answer = all, 0 unparsed lines, normalisation changed 0 strings); `2a_auto` = 0.5475 (= dev main).
  release without answers: decision `2a_history_q` for 11/11 domains (turns ≥ 2 with answer 0; the stripped strings
    keep their Q lines, so every pair parses with an empty answer); `2a_auto` = 0.4802 (= dev of the rule-14 run).
  format_checker exit 0 for all 66 files (3 variants × 2 releases × 11 domains); run ids UA_2a_auto / UA_2a_history /
  UA_2a_history_q. Both variants are built in both cases (the main run on the stripped release generated 1,294 new
  LLM texts, 4.7 min).
observation (dev only, not a rule-14 candidate): the main pipeline fed the answer-free histories (its LLM input then
  has the earlier questions with empty "A:" lines; fusion α 0.6 and ReasonEmbed w 0.9 of the main run) scores 0.4908
  on dev, above the rule-14 run (0.4802). Rule 14b is pre-registered below for phase B; until then the automation
  follows rule 14.

## 2026-11-10 09:28 — rule 14b (pre-registered, phase B; before any train run of it)
candidate M0 = the frozen main 2a pipeline run on answer-free histories (`history.without_answers`), no re-tuning,
  on the rule-8 train subsample via submit.py (as in A2). It replaces H0q + ReasonEmbed as the answer-free fallback only
  if on train M0 − H0q+RE ≥ +0.005 with bootstrap lower bound > 0 (M0 is the more complex: it needs the LLM).
  Dev is already known for M0 (0.4908, seen above) — it is reported, not used.
