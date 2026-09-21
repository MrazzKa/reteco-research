# RETECO — Directed Research workspace

Timur Kamarayev · INFO 492, University of Arizona · mentor Prof. Steven Bethard
Task: SemEval-2027 Task 1 — RETECO (reasoning-oriented retrieval). Started 2026-09-14.

```
semeval-reteco/
  RETECO/            official repo, pinned 23093c30, read-only
  reteco_data/       official 4.7 GB release (all 24 domains), read-only
  .venv/             Windows venv (CPU only)
  reteco-research/   <- this folder
```

## Where things are

| file | what |
| --- | --- |
| **`MEETING.md`** | Week-1 brief for the meeting with Prof. Bethard. Start here. |
| `research/results/RESULTS.md` | All week-1 numbers in one file: Track 2 (11 domains), Track 1, date feasibility, failure-case tallies. |
| `research/LOG.md` | Append-only experiment log. Every run has an entry. |
| `research/data_report.md` | Per-domain inventory and integrity checks of the full release. |
| `research/week1/` | First pilot (iota, drones, biology): results, fixed-seed case sheets, proposed labels. |
| `research/week1_t1/<domain>/`, `research/week1_t2/<domain>/` | Wide dev runs: `results.json`, TREC run files, case sheets. |
| `docs/background.md` | Task, TEMPO/RECOR papers, proposal findings, upstream-code findings. |
| `docs/runbook.md` | Original setup instructions and handoff (historical). |
| `scripts/` | All code (see below). |

## Scripts

| script | purpose |
| --- | --- |
| `week1_run.py` | Main runner: FastBM25 (== starter-kit BM25, `--selftest`), all 1a/1b/2a conditions, case sheets. |
| `aggregate_week1.py` | Per-domain + macro tables, paired bootstrap CIs, re-scored from run files. |
| `run_remaining.py` | Runs `week1_run.py` per domain in subprocesses and appends to LOG. |
| `date_quick.py` | Explicit-date feasibility on Track-1 **train** (regex; gold vs random corpus sample). |
| `date_feasibility.py` | Same, with BM25 non-gold top-10 as contrast (slow: hours on `history`). |
| `get_data.py`, `check_open_questions.py`, `inspect_release.py`, `smoke_sample.py` | Data download, schema checks, data report, pipeline smoke test. |

## Reproduce (Windows PowerShell, from `D:\dev\semeval-reteco`)

```powershell
$py = ".\.venv\Scripts\python.exe"; $env:PYTHONUTF8 = "1"
& $py reteco-research\scripts\week1_run.py --kit RETECO\starter_kit --selftest
& $py reteco-research\scripts\week1_run.py --data reteco_data --kit RETECO\starter_kit `
    --split dev --track2 drones --cases 5 --seed 20260921 --out reteco-research\research\week1_t2\drones
cd reteco-research\scripts
& $py aggregate_week1.py --track 2 --runs ..\research\week1_t2 --initial ..\research\week1 `
    --data ..\..\reteco_data --kit ..\..\RETECO\starter_kit --out ..\research\results\track2_summary.md
```

## Ground rules

1. Never modify `RETECO/` or `reteco_data/`.
2. Never write a number that did not come out of a run; log every run in `research/LOG.md`.
3. No tuning on dev. Fixed conditions only; design analysis on train.
4. Failure cases are sampled with a fixed seed (20260921) before reading; labels proposed by an assistant must be confirmed by Timur.
