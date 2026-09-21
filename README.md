# reteco-research

Directed Research (INFO 492, University of Arizona) on **SemEval-2027 Task 1 — RETECO**
(reasoning-oriented retrieval). Timur Kamarayev, mentor Prof. Steven Bethard. Started 2026-09-14.

Code, experiment log and generated results only. Notes and meeting briefs are kept outside the repo.

## Layout

```
semeval-reteco/                  (not a repo)
  RETECO/                        official task repo, pinned 23093c30, read-only
  reteco_data/                   official release, all 24 domains, read-only
  .venv/                         Windows venv, CPU only
  reteco-research/               <- this repo
    scripts/                     all code
    research/
      LOG.md                     lab notebook: one entry per run (append-only)
      RESULTS.md                 all week-1 tables (generated, see below)
      data_report.md             release inventory + integrity checks (generated)
      date_feasibility_train.json
      cases/                     fixed-seed failure-case sheets for hand labelling
        pilot_track{1,2}.md        must-label (iota; drones + biology)
        pilot_proposed_labels.md   assistant-proposed labels, unconfirmed
        wide_track{1,2}.md         optional (other domains)
      runs/
        pilot/                   first pass: iota, drones, biology
        track1/<domain>/         Track-1 dev runs (9 of 13 domains)
        track2/<domain>/         Track-2 dev runs (all 11 domains)
                                 each: results.json + runs/*.tsv (TREC run files)
```

## Scripts

| script | purpose |
| --- | --- |
| `week1_run.py` | Main runner. FastBM25 (rank-identical to starter-kit `bm25.py`, proven by `--selftest`); all 1a/1b/2a conditions; case sheets. |
| `aggregate_week1.py` | Per-domain + macro tables and paired bootstrap CIs, re-scored from run files and checked against `results.json`. |
| `run_remaining.py` | Runs `week1_run.py` per domain in subprocesses and appends LOG entries. |
| `date_quick.py` | Explicit-date feasibility on Track-1 **train** (regex; gold vs random corpus sample). ~2 min. |
| `date_feasibility.py` | Same with BM25 non-gold top-10 as contrast. Hours on `history`; not completed. |
| `get_data.py` · `check_open_questions.py` · `inspect_release.py` · `smoke_sample.py` | Download, schema checks, data report, pipeline smoke test. |

## Run (Windows PowerShell, from `D:\dev\semeval-reteco`)

```powershell
$py = ".\.venv\Scripts\python.exe"; $env:PYTHONUTF8 = "1"
& $py reteco-research\scripts\week1_run.py --kit RETECO\starter_kit --selftest

# one domain, dev
& $py reteco-research\scripts\week1_run.py --data reteco_data --kit RETECO\starter_kit `
    --split dev --track1 history --cases 5 --seed 20260921 `
    --out reteco-research\research\runs\track1\history

# summaries (paste into research/RESULTS.md)
cd reteco-research\scripts
& $py aggregate_week1.py --track 1 --runs ..\research\runs\track1 --initial ..\research\runs\pilot `
    --data ..\..\reteco_data --kit ..\..\RETECO\starter_kit --out ..\research\track1_summary.md
& $py aggregate_week1.py --track 2 --runs ..\research\runs\track2 --initial ..\research\runs\pilot `
    --data ..\..\reteco_data --kit ..\..\RETECO\starter_kit --out ..\research\track2_summary.md
& $py date_quick.py --data ..\..\reteco_data --out ..\research\date_feasibility_train.md
```

The same commands work from WSL with `python3` and forward slashes (no packages needed).

## Rules

1. Never modify `RETECO/` or `reteco_data/`.
2. Never report a number that did not come out of a run; log every run in `research/LOG.md`.
3. No tuning on dev. Fixed conditions only on dev; design analysis on train.
4. Case sheets are sampled with a fixed seed (20260921) before anyone reads them. Never resample.
   Proposed labels must be confirmed by a human before they are counted.
5. Negative and surprising results are reported as results.

## Gotchas

- Set `$env:PYTHONUTF8 = "1"` in every PowerShell window (starter kit opens files without `encoding=`).
- Track-2 qids are `<conv>_turn_<n>`; the curated sample uses `<conv>#turn<n>`. A mismatch scores silently as 0.
- The corpus is never split: always retrieve over the full domain corpus, for train and dev.
- Starter-kit `bm25.py` scores every document for every query (too slow); use `FastBM25`.
- Our BM25 ≠ official pyserini BM25 (no stemming or stopwords), so absolute scores are lower. Compare conditions within one retriever.
- Do not run the organisers' `build_release.py` / `download_raw.py`.
- 16 GB RAM: run large Track-1 domains (`history` 1.3 GB, `hsm`) one at a time.
