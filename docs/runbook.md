# Runbook and handoff (historical)

Merged from the former root files `00_START_HERE.md`, `TONIGHT.md`, `HANDOFF.md` (2026-09-21). These were the setup instructions for week 1; all phases are done or recorded in `research/LOG.md`. Headings demoted one level.

---

<!-- source: HANDOFF.md -->
## Handoff for Claude Code — RETECO week-1 runs (Timur Kamarayev)

You are helping Timur, an undergraduate doing Directed Research (INFO 492, University
of Arizona) with Prof. Steven Bethard on **SemEval-2027 Task 1 — RETECO:
Reasoning-Oriented Retrieval**. Everything below has been prepared in an earlier
chat; your job is to **run it on his machine, verify it, extend it where cheap,
and fill in the meeting brief with real numbers**. Work in phases, report after
each phase, and stop to ask when a step would take more than ~45 minutes.

Talk to Timur in Russian; write all files in English.

---

### 0. Ground rules (non-negotiable)

1. **Never modify** `RETECO/` (official repo) or `reteco_data/` (official data).
   All new code goes in `reteco-research/scripts/`, all outputs under
   `reteco-research/research/`.
2. **Never write a number that did not come out of a run.** No estimates in
   tables. If something did not run, say so.
3. **Log every run** in `reteco-research/research/LOG.md` using the template at
   the top of that file (date, command, split, domains, result, runtime, notes).
4. **Dev-set discipline.** No hyperparameter is tuned in this work. All runs here
   are fixed conditions, so running them on dev is fine — but do not iterate on
   dev (no "try variant, look at dev, try another"). If you are about to, stop
   and tell Timur.
5. Failure cases are sampled with a **fixed seed before anyone reads them**. Do
   not resample, do not cherry-pick.
6. Report negative and surprising results plainly. A discrepancy vs. the official
   numbers is a finding to explain, not something to patch away.
7. Machine: **Windows 11, ~16 GB RAM, no CUDA GPU.** Do not install torch, do not
   download models. Everything here is CPU-only.

---

### 1. Layout on disk

```
D:\dev\semeval-reteco\
  reteco-research\        <- already unzipped (this file lives here)
    00_START_HERE.md      overview, verified facts, gotchas
    TONIGHT.md            human runbook (you are the automated version of it)
    notes\                task/paper summaries, upstream-code and proposal findings
    research\LOG.md       experiment log — append to it
    research\weekly\2026-09-21_meeting.md   meeting brief with [ ] to fill
    scripts\
      smoke_sample.py           pipeline test on the repo's curated sample
      get_data.py               download chosen domains (or --all) from HF
      check_open_questions.py   excluded_ids / step nesting / reasoning field
      inspect_release.py        per-domain data report
      week1_run.py              all runs + failure-case sheets (see §4)
  RETECO\                 <- to clone (pinned commit below)
  reteco_data\            <- to download
  .venv\                  <- to create
```

Upstream pins: RETECO `23093c30e568a337c6293de4c58ffcccddbded5b`;
TEMPO `tempo-bench/Tempo` `8731487`; RECOR `RECOR-Benchmark/RECOR` `ba05460`.

---

### 2. Task facts you need

- Two tracks. **Track 1** (TEMPO, temporal): 1a whole-query retrieval, 1b
  step-wise retrieval. 13 domains, 1,654,055 docs. **Track 2** (RECOR,
  conversational): 2a turn retrieval (2b/2c are generation, out of scope). 11
  domains, 507,141 docs.
- Metric: binary **nDCG@10**, pytrec_eval, **macro-averaged over domains**.
- Split 70/30 per domain, seed 20270101. **The corpus is never split** — always
  retrieve over the full domain corpus.
- Dev sizes: Track 1 519 queries / 1,214 steps; Track 2 211 conversations / 858 turns.
- Hidden test: ~350 Track-1 queries, ~200 Track-2 turns (small → noisy).
- Six Track-2 domains are BRIGHT-derived (biology, earth_science, economics,
  psychology, robotics, sustainable_living); five are StackExchange (drones,
  hardware, law, medicalsciences, politics).

Official BM25 dev reference (pyserini) — macro: 1a 0.0967 · 1b 0.1063 ·
2a current 0.1827 · 2a +history 0.4379. Per-domain values are hard-coded in
`week1_run.py` (`REF`) and in `RETECO/starter_kit/BASELINE_RESULTS.md`.
Our BM25 is the **pure-Python starter-kit BM25** (different tokeniser from
Lucene), so expect small gaps; large gaps must be investigated.

#### Hypotheses this week's runs are testing

- **H1** (from the official table, already true there): the +history gain is
  larger on BRIGHT-derived domains than on StackExchange ones (dev +0.341 vs
  +0.152, complete separation). Check it holds with our runs.
- **H2**: `conversation_history` contains the previous turns' **reference answers**
  (`Q: … / A: …` blocks), and later turns reuse earlier gold passages. So part of
  the +history gain may come from answer text derived from the gold passages.
  Tested by the ablation: current / +questions only / +answers only / +full
  history, plus `DIAG_gold_recycling` and `2a_ORACLE_prev_turn_gold`.
- **H3** (Track 1b): the three query strategies the task proposal permits —
  Query+Step (official), Step-Only, Query+All — differ; only Query+Step has
  published numbers.
- **E2 feasibility** (Track 1a): how often do queries and gold passages state
  explicit dates? Decides whether a date-overlap reranker is worth building.

---

### 3. Phase 1 — environment and self-tests (≈10 min)

```powershell
cd D:\dev\semeval-reteco
git clone https://github.com/DataScienceUIBK/RETECO.git
git -C RETECO checkout 23093c30e568a337c6293de4c58ffcccddbded5b
python --version                 # need >= 3.10
python -m venv .venv
$py = ".\.venv\Scripts\python.exe"
& $py -m pip install -U pip huggingface_hub
& $py -m pip freeze > reteco-research\research\env_freeze.txt
$env:PYTHONUTF8 = "1"            # starter-kit scripts open files without encoding=
                                 # -> cp1252 UnicodeDecodeError on Windows otherwise

& $py reteco-research\scripts\week1_run.py --kit RETECO\starter_kit --selftest
& $py reteco-research\scripts\smoke_sample.py RETECO
```

Pass criteria: `selftest OK: FastBM25 == starter_kit BM25 ...`; smoke test prints
three scored runs (1a ≈ 0.7821, 2a current ≈ 0.7331, 2a history ≈ 0.7824 — these
are on a gold-only sample corpus and mean nothing as scores).

Also record: `java -version` (needed only for the optional official baseline in
Phase 7), CPU core count, free RAM, free disk on D:.

Initialise version control for the research folder (not for RETECO or data):
```powershell
git -C reteco-research init; git -C reteco-research add -A
git -C reteco-research commit -m "Week-1 workspace as handed off"
```

### 4. Phase 2 — data (≈15–40 min, mostly download)

Download the **full release** (4.73 GB) — we want all 24 domains available:

```powershell
& $py reteco-research\scripts\get_data.py --list
& $py reteco-research\scripts\get_data.py --all --out reteco_data
```

`get_data.py` prints the folder to use as `--data` (normally `reteco_data`). It has
never been run against the real HF repo (the chat sandbox could not reach HF). If the
layout differs from `track1_tempo/<domain>/…`, `track2_recor/<domain>/…`, stop and
show Timur the `--list` output; adapt `get_data.py`, not the data.

Then:
```powershell
& $py reteco-research\scripts\check_open_questions.py --data reteco_data `
    *> reteco-research\research\open_questions.txt
& $py reteco-research\scripts\inspect_release.py --data reteco_data `
    --out reteco-research\research\data_report.md
```

Report to Timur: (1) do Track-1 records carry non-empty `excluded_ids`? Upstream
TEMPO zeroes those documents before ranking; the RETECO starter kit never mentions
the field — if present, that is a real deviation worth noting. (2) are 1b steps
nested under `steps` with `step_id` / `step_instruction` / `gold_ids`? (3) what
share of Track-2 turns carry `subquestion_reasoning`? (4) the integrity line
"gold ids present in corpus" should be ~100% everywhere; anything less is a finding.

### 5. Phase 3 — quick pass on three domains (≈10–20 min)

This is the must-have for the meeting. Do it before anything wide.

```powershell
& $py reteco-research\scripts\week1_run.py --data reteco_data `
    --kit RETECO\starter_kit --split dev `
    --track1 iota --track2 drones biology --cases 8 `
    --out reteco-research\research\week1
```

Check: pure-Python results vs `official ref` column. Expect the same order of
magnitude; flag any |Δ| > 0.05 and look at why (tokenisation? missing topics? qid
mismatch — Track-2 qids must be `<conv>_turn_<n>`). Note the runtime per domain
and use it to estimate Phases 4–5 before starting them.

**Show Timur `research\week1\results.md` now.**

### 6. Phase 4 — all 11 Track-2 domains, dev (≈30–70 min)

Measured cost of `week1_run.py`: ~0.14 s/query for short queries, ~0.9 s/query for
history-length queries on a 50k-doc corpus; index build ~1 min per 50k docs. Track 2
dev is 858 turns × 5 conditions. Run domains **in parallel processes** (3–4 at a
time, watch RAM), one output folder per domain:

```powershell
$t2 = "biology","drones","earth_science","economics","hardware","law",
      "medicalsciences","politics","psychology","robotics","sustainable_living"
foreach ($d in $t2) {
  Start-Process -NoNewWindow -FilePath $py -ArgumentList @(
    "reteco-research\scripts\week1_run.py","--data","reteco_data",
    "--kit","RETECO\starter_kit","--split","dev","--track2",$d,"--cases","5",
    "--out","reteco-research\research\week1_t2\$d") `
    -RedirectStandardOutput "reteco-research\research\week1_t2\$d.log"
}
```
(Create `research\week1_t2\` first; throttle to 3–4 concurrent if RAM is tight —
simplest is to run them in batches.)

Then **write `scripts/aggregate_t2.py`** that reads every `results.json` and
`runs/*.tsv` and produces `research/week1_t2/summary.md` with:

1. Per-domain table: current, +questions only, +answers only, +full history,
   ORACLE hist+reasoning, ORACLE prev-turn gold, recycling share, n — with the
   official current/history refs next to ours.
2. Macro averages for all 11, for BRIGHT (6) and for StackExchange (5), per
   condition. Does H1 still show complete separation in our runs?
3. **Paired bootstrap** (10,000 resamples of turns, seed 0, within each domain,
   then macro) 95% CIs for these differences: history − current,
   answers-only − questions-only, full history − answers-only. Per-turn nDCG@10
   comes from re-scoring the run files against `qrels_dev.txt` with
   `RETECO/starter_kit/ir_metrics.ndcg_at_k`.
4. Turn-depth table (T1…T5+) macro over domains for each condition.
5. A 3–5 sentence plain reading of H2: does the gain travel with the answers or
   with the questions? Be careful with causal language.

### 7. Phase 5 — Track 1 (time-boxed)

First time one medium domain for 1a+1b (e.g. `history` or `politics`), then
extrapolate to all 13. **If the extrapolated total is under ~90 min, run all 13
in parallel batches like Phase 4; otherwise run the fastest subset that fits and
list the skipped domains.** Tell Timur the estimate before launching.

```powershell
& $py reteco-research\scripts\week1_run.py --data reteco_data `
    --kit RETECO\starter_kit --split dev --track1 <domain> --cases 5 `
    --out reteco-research\research\week1_t1\<domain>
```

Then `scripts/aggregate_t1.py` → `research/week1_t1/summary.md`: per-domain and
macro nDCG@10 for 1a and the three 1b strategies, official refs alongside,
paired bootstrap CIs for Step-Only − Query+Step and Query+All − Query+Step
(resampling steps within domain). Note: Query+All gives all steps of a query the
same ranking — say so in the summary.

### 8. Phase 6 — E2 feasibility: explicit dates (≈10 min, cheap and important)

Write `scripts/date_feasibility.py`. For every Track-1 domain on **train** (this
is design analysis — keep it off dev):

- Regex for explicit temporal expressions, start simple and state it exactly:
  4-digit years `\b(1[5-9]\d\d|20\d\d)\b`, decades `\b(1[5-9]\d0s|20\d0s)\b`,
  and month-year (`January 2017`, `Jan 2017`).
- Report the share of **queries**, **gold passages**, and **non-gold BM25 top-10
  passages** containing at least one match, and the median number of distinct
  years per query.
- For queries with years: share whose gold passages contain at least one year
  within the query's year span (min–max ±1), vs. the same for BM25's non-gold
  top-10. If gold passages overlap the query's span much more often than
  non-gold top-10, a date-overlap reranker (experiment E2) is promising; if not,
  temporal alignment here is mostly implicit — also a finding.

Output `research/week1_t1/date_feasibility.md`. Keep it one table + 3 sentences.

### 9. Phase 7 — optional: exact official baseline, one domain

Only if Java 21 is installed (`java -version`). Otherwise skip and note "next week".
```powershell
& $py -m pip install pyserini gensim pytrec_eval
$env:JAVA_HOME = "<path to JDK 21>"
cd RETECO\starter_kit
& ..\..\.venv\Scripts\python.exe official_baseline.py --data ..\..\reteco_data `
    --out ..\..\baselines_official --splits dev --track1 iota --track2 drones
```
Must match `BASELINE_RESULTS.md` per-domain dev values (iota 1a 0.2083, 1b 0.3289;
drones 0.1695 / 0.2954) to ~3 decimals. Do not run it on all domains tonight
(gensim on the large Track-1 corpora may not fit in 16 GB).

### 10. Phase 8 — failure cases (Timur labels; you assist)

Case sheets: `research/week1/cases_track1.md`, `cases_track2.md` (and per-domain
ones from Phases 4–5). Each case has checkboxes for the organisers' taxonomy
(TEMPO temporal classes; RECOR discourse types: continuation · coreference ·
self-contained · topic-shift) and a failure mode.

You may **propose** a label for each case as a line `Proposed (Claude): …` with a
one-sentence reason. **Timur must confirm or change every one** — the ticked box is
his. Then tally per file. Label the three Phase-3 sheets first (8 per domain);
the wide-run sheets are optional.

### 11. Phase 9 — fill the brief, log, commit

1. Fill every `[ ]` in `research/weekly/2026-09-21_meeting.md` from the results
   files. Add rows for the 11-domain Track-2 summary, the Track-1 summary, and
   the date-feasibility table where they strengthen the story; keep the brief
   under ~2 pages. If H2 does **not** hold on real data, rewrite Finding 2 and the
   recommendation honestly — the brief says what would change the recommendation.
2. Rewrite the 2-minute opener at the bottom so every bracket is a real number.
3. Append LOG entries for every phase.
4. `git -C reteco-research add -A; git -C reteco-research commit -m "Week-1 runs"`.
5. Give Timur, in Russian: the 5 most important numbers, what surprised you, and
   anything that failed or was skipped.

---

### 12. Known gotchas

- `$env:PYTHONUTF8="1"` in every new PowerShell window.
- Track-2 qids: starter kit and release use `<conv>_turn_<n>`; the repo's curated
  sample uses `<conv>#turn<n>` (only `smoke_sample.py` touches that, and normalises it).
  A mismatch scores silently as 0.
- The starter kit's `bm25.py` scores every document for every query — far too slow
  on real corpora. `week1_run.py` uses `FastBM25`, which is proven identical by
  `--selftest`. Do not swap in `bm25_baseline.py` for wide runs.
- `build_release.py` / `download_raw.py` are the organisers' build scripts. Don't run them.
- Output filenames contain `+` (e.g. `1b_query+step`) — fine on Windows, quote in PowerShell.
- If a domain run dies from memory, rerun it alone rather than in a batch.

### 13. What NOT to do this session

No dense retrievers, no LLM calls, no model downloads, no tuning on dev, no edits
to official code or data, no emailing anyone.

---

<!-- source: 00_START_HERE.md -->
> **For the 21 Sep meeting: open `TONIGHT.md` and follow it top to bottom.**

## RETECO — Directed Research workspace (Timur Kamarayev, Fall 2026)

Mentor: Prof. Steven Bethard · weekly meeting **Mondays 08:30–09:00** · Task: SemEval-2027 Task 1 (RETECO) · Started 2026-09-14
Organisers: Abdallah, Ali, Abdul-Mageed, Duh, Jatowt · contact `abdelrahman.abdallah@uibk.ac.at`
Mailing list: <https://groups.google.com/g/semeval-2027-reteco> — **join before anything else**

This folder is the *working* half of the project. The official task repo and the
4.5 GB dataset live next to it and are **never modified**:

```
semeval-reteco/
  RETECO/            # official repo, pinned, read-only
  reteco_data/       # official 4.5 GB release, read-only
  reteco-research/   # <- this folder: my code, notes, logs, reports
```

---

### 1. What has already been verified (2026-09-14)

Everything below was checked against the upstream sources, not assumed.

| Claim | Status |
| --- | --- |
| Repo `DataScienceUIBK/RETECO` exists, starter kit + docs present | ✅ verified |
| Pinned commit at time of checkout | `23093c30e568a337c6293de4c58ffcccddbded5b` (2026-08-30) |
| Official metric = nDCG@10 via `pytrec_eval`, macro-averaged over domains | ✅ verified |
| BM25 dev baselines 1a `0.0967` · 1b `0.1063` · 2a `0.1827` · 2a+hist `0.4379` | ✅ verified in `starter_kit/BASELINE_RESULTS.md` |
| Release: 24 domains, 2,161,196 docs, 70/30 split, seed `20270101` | ✅ verified in `DATASET_CARD.md` |
| Evaluation window 10–31 Jan 2027; RETECO close date still TBA | ✅ verified on task site |
| TEMPO paper arXiv 2601.09523 · RECOR paper ACL 2026 Findings / arXiv 2601.05461 | ✅ verified |
| Full end-to-end pipeline (load → BM25 → TREC run → official scorer) | ✅ **executed successfully** on the curated sample data |

Papers and official docs are summarised in [`notes/task_and_papers.md`](notes/task_and_papers.md).

#### Gotchas already found (saves hours later)

1. **Track-2 query-id formats differ between sources.** The curated sample
   `qrels.txt` uses `ex_111149#turn1`; the starter kit and the full release use
   `ex_111149_turn_1`. Mismatched ids score as a silent **0.0**, not as an error.
   `scripts/smoke_sample.py` normalises this.
2. **`pyserini` needs a JDK** (21 works). Without `JAVA_HOME`/`JVM_PATH` the
   *official* baseline will not run. The **pure-Python starter** (`bm25_baseline.py`
   + `scorer.py`) has zero dependencies — start there.
3. **The corpus is never split.** Retrieval always runs against the full domain
   corpus for both train and dev. Do not "index the split".
4. **The curated sample corpus contains only gold passages.** Scores on it are
   meaningless (~0.73–0.78 nDCG). It validates plumbing only.
5. **`build_release.py` / `download_raw.py` are the organisers' own build path**
   and point at their cluster paths. Do not run them. Use `hf download`.
6. **`excluded_ids` is handled upstream but appears nowhere in RETECO's starter
   kit.** First thing to grep after download — see `notes/upstream_code_findings.md` §1.
7. **The HF dataset viewer does not work for these splits.** No online preview.

---

### 2. Local setup (Windows 11, no CUDA — matches my machine)

Disk: **4.73 GB** download + extraction + working space — keep ~11 GB free. RAM: the largest single domain corpus
is the binding constraint; stream JSONL, never `json.load` a corpus.

```powershell
mkdir C:\dev\semeval-reteco; cd C:\dev\semeval-reteco

git clone https://github.com/DataScienceUIBK/RETECO.git
cd RETECO; git checkout 23093c30e568a337c6293de4c58ffcccddbded5b; cd ..
## (detached HEAD is intentional — the upstream must not move under us)

py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install huggingface_hub pyarrow tqdm pytrec_eval gensim
pip freeze > reteco-research\research\env_freeze.txt
```

`pyserini` is deliberately **not** installed yet — it needs a JDK and is only
required to reproduce the *official* numbers exactly. Add it in step 5.

#### Step order

```powershell
## 1. Pipeline smoke test — no download needed, ~5 seconds
python reteco-research\scripts\smoke_sample.py .\RETECO

## 2. Get the data (~4.5 GB, one download)
hf download DataScience-UIBK/RETECO-SemEval2027 --repo-type dataset --local-dir reteco_data

## 3. Inspect what actually arrived  (PHASE C)
python reteco-research\scripts\inspect_release.py --data .\reteco_data `
    --out reteco-research\research\data_report.md

## 4. Pure-Python baseline on ONE small domain first  (PHASE D, cheap)
cd RETECO\starter_kit
python run_release.py --data ..\..\reteco_data --split dev --track1 iota --track2 drones

## 5. Official baseline — needs JDK 21 + pyserini; this is the number that counts
pip install pyserini
$env:JAVA_HOME="C:\Program Files\Java\jdk-21"
python official_baseline.py --data ..\..\reteco_data --out ..\..\baselines_official `
    --splits dev --track1 iota --track2 drones     # one domain, then scale up
```

Reference targets for step 5 (per-domain, dev): `iota` 1a `0.2083`, `drones` 2a
`0.1695` / +hist `0.2954`. Full per-domain table is in `BASELINE_RESULTS.md`.
If the numbers differ, **investigate the difference — do not patch the code
until it matches.**

---

### 3. Contents

| Path | What |
| --- | --- |
| `scripts/smoke_sample.py` | End-to-end pipeline check on the curated sample. **Tested, works.** |
| `scripts/inspect_release.py` | PHASE C data report generator. Tested against a release-shaped tree built from the sample; not yet against the real 4.5 GB release. |
| `notes/task_and_papers.md` | PHASE B: official docs + TEMPO + RECOR summaries, open questions. |
| `notes/proposal_findings.md` | The accepted task proposal: test-set size, permitted 1b query strategies, official error taxonomies, mentor alignment. |
| `notes/upstream_code_findings.md` | What the upstream TEMPO/RECOR code actually does — `excluded_ids` deviation, how "+Reasoning" is built, BRIGHT overlap. |
| `TONIGHT.md` | Step-by-step runbook (Windows) for the first meeting. |
| `research/weekly/2026-09-21_meeting.md` | Meeting brief: agenda, findings, recommendation, experiments, questions, opener. |
| `scripts/get_data.py` | Download only chosen domains from Hugging Face. |
| `scripts/week1_run.py` | One command: reproduction runs, 1b strategies, history ablations, oracles, failure-case sheets. `--selftest` proves its BM25 ranks identically to the starter kit's. |
| `scripts/check_open_questions.py` | `excluded_ids`, step nesting, reasoning-field presence. |
| `research/LOG.md` | Experiment log. One entry per run, no exceptions. |

### 4. Standing rules (from the ROCmPilot post-mortem)

Develop on `train`. Touch `dev` to measure, and record every time you do.
Never select examples after seeing results. Report negative results as results.
A formatting improvement is not a retrieval improvement. If a number looks good,
look for the leak first.

---

<!-- source: TONIGHT.md -->
## TONIGHT — runbook for the 21 Sep meeting

> **Short on time (it's morning, meeting at 8:30)?**
> - **≥ 2 h left:** do everything below, but `--cases 5` and label 5 per domain.
> - **~1 h left:** Steps 1–5 only; while Step 5 runs, read the brief. Walk in with
>   the numbers, say the cases aren't labelled yet, show one case unlabelled.
> - **< 45 min:** skip the computer. Go with the brief as is: Finding 1 is from the
>   official table and is real; Finding 2 is from the curated sample — say exactly
>   that, and make "run it on real dev data" next week's first item. That is still
>   a solid first update.

Total: ~2 h of your time, of which ~30–40 min is the computer running on its own.
Everything is PowerShell on Windows. If any step prints an error, copy the whole
error into the chat and stop — don't improvise fixes.

Folder you will end up with:

```
C:\dev\semeval-reteco\
  RETECO\            official repo (never edit)
  reteco-research\   this folder (unzipped)
  reteco_data\       downloaded data (never edit)
  .venv\             Python environment
```

---

### Step 0 — unzip (2 min)

Unzip `reteco-research.zip` into `C:\dev\semeval-reteco\` so that this file is at
`C:\dev\semeval-reteco\reteco-research\TONIGHT.md`.

### Step 1 — environment (5 min)

```powershell
cd C:\dev\semeval-reteco
git clone https://github.com/DataScienceUIBK/RETECO.git
git -C RETECO checkout 23093c30e568a337c6293de4c58ffcccddbded5b
python --version                       # needs 3.10 or newer
python -m venv .venv
$py = ".\.venv\Scripts\python.exe"
& $py -m pip install -U pip huggingface_hub
$env:PYTHONUTF8 = "1"                  # starter kit opens files without encoding=
```

`$py` and `PYTHONUTF8` only live in this PowerShell window. If you open a new
window, run the last two lines again. Using `$py` directly avoids the
"running scripts is disabled" error that `Activate.ps1` often hits.

### Step 2 — self-tests (1 min)

```powershell
& $py reteco-research\scripts\week1_run.py --kit RETECO\starter_kit --selftest
& $py reteco-research\scripts\smoke_sample.py RETECO
```

Expected: `selftest OK` and three scored runs ending with the
`NOTE: sample corpus = gold passages only` line.

### Step 3 — data, only three domains (5–15 min)

```powershell
& $py reteco-research\scripts\get_data.py --list
& $py reteco-research\scripts\get_data.py --track1 iota --track2 drones biology
```

The last line prints the folder to use as `--data`. Usually
`C:\dev\semeval-reteco\reteco_data`. If it prints something else, use that below.

Why these three: `iota` and `drones` are the organisers' own example domains;
`biology` is the BRIGHT-derived domain with the biggest history gain, so it pairs
with `drones` (StackExchange) for the comparison in the meeting brief.

### Step 4 — the open questions (1 min)

```powershell
& $py reteco-research\scripts\check_open_questions.py --data reteco_data
```

Save the output: `... > reteco-research\research\open_questions.txt`

### Step 5 — the week-1 run (20–40 min, runs by itself)

```powershell
& $py reteco-research\scripts\week1_run.py --data reteco_data `
    --kit RETECO\starter_kit --split dev `
    --track1 iota --track2 drones biology --cases 8 `
    --out reteco-research\research\week1
```

It prints progress. When done it prints the results table and writes:

- `research\week1\results.md` — the numbers for the meeting
- `research\week1\cases_track1.md`, `cases_track2.md` — failure cases to label
- `research\week1\runs\` — run files

Start Step 6 on the first domain's cases while the rest is still running only if
the case files already exist; otherwise wait.

### Step 6 — label the cases (30–40 min, the important human part)

Open `cases_track2.md` and `cases_track1.md` (VS Code or Notepad). For each case:

1. Read the history/query, the gold passages, and what BM25 returned.
2. Tick one **category** (the organisers' own taxonomy) and one **failure mode**:
   replace `[ ]` with `[x]` and delete the options that don't apply.
3. One line in `Note:` — what would a person have needed to find the gold?

Do not skip cases because they are hard or boring, and do not re-run to get
different ones. That is the whole point of the fixed seed. Aim for all 8 per
domain; if tired, stop at 5 each and say so honestly tomorrow.

Then tally at the top of each file, e.g. `coreference 4 · continuation 3 · ...`.

### Step 7 — fill the brief (10 min)

Open `research\weekly\2026-09-21_meeting.md` and replace every `[ ]` using
`results.md` and your tallies. Only numbers that are in `results.md`.

### Step 8 — sleep

In the morning: read the brief once, say the 2-minute opener out loud once,
bring the laptop with `results.md` and one case file open.

---

### If you have extra time (optional, in this order)

1. Add a domain each: `--track1 politics --track2 law` (download first with `get_data.py`).
2. Paste `results.md` into the chat — I'll sanity-check the numbers before you walk in.

Not tonight: the official pyserini baseline (needs Java 21 — next week's job).
