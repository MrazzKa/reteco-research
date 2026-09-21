# Background: task, papers, proposal, upstream code

Merged from the former `notes/` folder (2026-09-21). Content unchanged; headings demoted one level.

---

<!-- source: notes/task_and_papers.md -->
## PHASE B — Official materials, TEMPO, RECOR

Compiled 2026-09-14 from the pinned repo (`23093c30`), the task website, and the
two source papers. Numbers below are quoted from those sources, not estimated.

---

### 1. The task in one paragraph

Standard retrieval rewards topical similarity. RETECO evaluates relevance
*conditioned on a missing dimension*: a passage can be on-topic but from the
wrong period (Track 1), or the current turn can be uninterpretable without what
the conversation already established (Track 2). Both tracks reduce to the same
interface — rank document ids per query/turn — scored with binary **nDCG@10**
via `pytrec_eval`, macro-averaged over domains. There is no composite
leaderboard number; generation quality (2b/2c) is reported separately.

#### Sub-tracks

| | Input | Output | Files |
| --- | --- | --- | --- |
| 1a | temporal query + domain corpus | ranked docs per query | `examples_*.jsonl`, `qrels_*.txt` |
| 1b | decomposed steps + corpus | ranked docs per step | `steps_*.jsonl`, `qrels_steps_*.txt` |
| 2a | conversation + target turn + corpus | ranked passages per turn | `benchmark_*.json`, `qrels_*.txt` |
| 2b | conversation + **gold** passages | grounded answer | `benchmark_*.json` |
| 2c | conversation + corpus | top-5 ids **and** answer | both |

Entering a single sub-track carries no penalty.

#### Data (verified counts)

24 self-contained domains, **2,161,196** documents total — Track 1: 13 domains,
1,654,055 docs, 1,730 queries, 3,976 steps; Track 2: 11 domains, 507,141 docs,
707 conversations, 2,971 turns. Split 70/30 per domain, seed `20270101`, exact
id lists published in `split_manifest.json`. Three split rules: the corpus is
never split; a query's steps stay inside its own record; a conversation's turns
never cross the boundary. Gold judgments released for both splits; the test set
is hidden with private judgments.

#### Diagnostics beyond nDCG@10

- Track 1: Temporal Precision@10, Temporal Relevance@10, **Temporal Coverage@10**
  (fraction of required periods hit by at least one top-10 doc), nDCG|FC@10
  (nDCG restricted to fully-covered queries). On the hidden test these labels
  come from a frozen, human-checked LLM judge.
- Track 2: per-domain results and **turn-depth groups T1/T2/T3/T4/T5+** — the
  cleanest way to separate "good single-turn retriever" from "actually uses history".

#### Calendar

Training data released 30 Aug 2026 · evaluation window opens 10 Jan 2027 ·
RETECO close date TBA, no later than 31 Jan 2027 · system papers Feb 2027
(tentative) · workshop summer 2027. Registration is not open yet; building does
not depend on it.

---

### 2. TEMPO (Track 1 source)

Abdallah, Ali, Abdul-Mageed, Jatowt — *TEMPO: A Realistic Multi-Domain Benchmark
for Temporal Reasoning-Intensive Retrieval*, arXiv 2601.09523 (Jan 2026).
University of Innsbruck + UBC.

**Question.** Temporal QA benchmarks ask for simple fact-seeking over news;
reasoning-intensive retrieval benchmarks (BRIGHT, RAR-b) ignore time. Neither
covers needs that require reasoning *about temporal evolution* and synthesising
evidence across periods.

**Data.** 1,730 complex queries over 13 StackExchange domains, plus 3,976
decomposed retrieval steps with gold documents mapped per step (this is what
makes 1b multi-hop-evaluable). Ten temporal reasoning classes, including event
localisation and time-period contextualisation.

**Metrics.** nDCG@10 plus the temporal family (Temporal Coverage@k, Temporal
Precision@k) — designed to catch "right topic, wrong period" and "covers one of
three required periods".

**Headline result.** Of 12 evaluated retrieval systems, the best (DiVeR) reaches
only **32.0 nDCG@10** and **71.4% Temporal Coverage@10**.

**What this means for us.** The gap between the RETECO BM25 baseline (~0.10 dev)
and the best published system (~0.32) is large but the ceiling is also low —
nobody has solved this. Coverage, not precision, is the named failure mode:
systems retrieve about the topic and miss required periods.

> Related work worth a look later: *Difficulty-Gated Fusion of Reasoning Views
> for Temporal Retrieval* (arXiv 2608.08940) reports improvements on Tempo for
> all six retrievers tested, with the strongest reaching ~0.297–0.303 nDCG@10 —
> i.e. query-side reasoning views are an active and reproducible direction.

---

### 3. RECOR (Track 2 source)

Ali, Abdallah, Agarwal, Patel, Jatowt — *RECOR: Reasoning-focused Multi-turn
Conversational Retrieval Benchmark*, Findings of ACL 2026 (arXiv 2601.05461).
Innsbruck + Oracle AI.

**Question.** Multi-turn conversation and reasoning-intensive retrieval are
benchmarked separately; real information seeking needs both.

**Construction.** A *Decomposition-and-Verification* framework turns complex
single queries into fact-grounded multi-turn dialogues: atomic facts verified
against sources, and an **explicit retrieval reasoning string generated per
turn**. Human validation: naturalness 4.2 (κ=0.79), turn coherence 4.6 (κ=0.77),
question quality 4.2 (κ=0.75), groundedness 4.4 (κ=0.73).

**Scale.** 707 conversations, 2,971 turns, 11 domains; 507,141 documents of
which 2,900 positive and 504,241 hard negatives — a **174:1** negative ratio.
Average 4.20 turns per conversation (3–12), ~5.87 semantic aspects, 2.01
supporting documents per turn. Queries ~18 words, answers ~70, accumulated
history ~155 words.

**Headline results.**
- Baseline (current turn) `.236` → History+Reasoning `.479` nDCG@10, averaged
  across retrievers — roughly a doubling, paired *t* = 119.67.
- Reasoning-specialised retrievers dominate dense encoders: DIVER `.584` with
  History+Reasoning (95% CI .520–.649), ReasonIR `.552`.
- History+Reasoning improves *with* turn depth, suggesting accumulated context
  helps retrievers more than generators.
- Implicit reasoning stays hard: when the logical link is not stated in the text,
  performance does not recover.
- Generation: coherence is highest (.895–.940), **completeness** lowest
  (.750–.846).

**Do not confuse two "doubling" numbers.** RECOR's `.236 → .479` is averaged
over many retrievers with the gold reasoning string. RETECO's starter kit
`.1827 → .4379` is **BM25 only, history only, no reasoning**. Both are in the
handoff notes; they are not the same experiment.

---

### 4. The sharpest open question found so far

The released Track-2 records carry, per turn, a gold field
`subquestion_reasoning` plus `subquestion_reasoning_metadata` with
`target_information`, `relevance_signals` and `irrelevance_signals`. In the
curated sample, **13 of 13 turns have it.**

That field is the "+Reasoning" half of RECOR's headline result. So:

- If the **hidden test set also ships it**, then the competitive move is to use
  it, and the research question becomes how to consume it well.
- If it **does not**, then `.479` is an oracle upper bound, and the real problem
  is *generating* that reasoning from conversation + turn at inference time —
  which is a much more interesting undergraduate contribution, and directly
  measurable against the oracle (gold reasoning) ceiling on dev.

Either way this determines what the whole semester is about, and it is answerable
by (a) checking whether the field is present in the released train/dev, and
(b) asking the organisers at `abdelrahman.abdallah@uibk.ac.at`. **Ask Bethard
first whether he wants me to email the organisers.**

Equivalent question for Track 1: are the decomposed steps of 1b supplied at test
time, or must they be generated? The task page words 1b as "the temporal query is
represented through reasoning steps", implying supplied — verify in the release.

---

### 5. Reading queue

1. TEMPO §3 (data construction) and §5 (results + failure analysis) — the
   temporal-coverage failure mode in detail.
2. RECOR §4.1 (retrieval results, Table 3) and the turn-depth analysis.
3. Bethard's own temporal work, once he names the paper he'd want me to read.
4. BRIGHT (arXiv 2407.12883) — the reasoning-retrieval benchmark both papers
   position against; explains why "59.0 → 18.3" is the framing of this whole area.

---

<!-- source: notes/proposal_findings.md -->
## The accepted task proposal — what it adds

Source: `docs/assets/papers/RETECO_SemEval_2027_Proposal.pdf` in the pinned repo
(6 pages, the proposal SemEval accepted on 11 Aug 2026). None of this is on the
task website.

### 1. The hidden test set is small, and already annotated

> "approximately **350 Track 1 test queries** and **200 Track 2 test turns**",
> stratified across all domains (13 and 11 respectively).

It was annotated during the original dataset construction from unseen source
material and has never been released — so contamination is genuinely controlled,
but the evaluation is **small**. 200 turns spread over 11 domains is ~18 turns
per domain. With macro-averaging over domains, a per-domain estimate rests on
about eighteen items.

**Consequence for us:** differences of a couple of nDCG points on Track 2 will
not be distinguishable from noise on the test set. Any claim we make should come
with a paired bootstrap or at minimum a per-domain breakdown. It also mildly
favours Track 1 (350 queries) if we care about our own results being measurable.

### 2. Sub-track 1b explicitly permits three query strategies

> "Three query strategies are permitted: **Step-Only** (each step as the sole
> query), **Query+Step** (the original query concatenated with each step), and
> **Query+All** (the original query with all steps combined)."

The official baseline implements **Query+Step** only (`f"{base_query}\n\nStep:
{step_instruction}"`, verbatim from TEMPO's `run_step.py`). Step-Only and
Query+All are sanctioned by the organisers and **have no published numbers**.

That is a free, legitimate, zero-risk first experiment: three query
constructions, one variable, official metric, no new model. Exactly the shape of
experiment to bring to a first meeting.

### 3. Rules on resources

Official-leaderboard retrieval must use the **provided corpus**. Open-source and
proprietary models — embedders, LLMs, judging APIs — are permitted but **must be
disclosed** for an open-vs-closed comparison. So using an LLM to generate query
reasoning is allowed, provided it is declared.

### 4. Ready-made error taxonomies — do not invent our own

The proposal reports the distribution of the categories the annotators already
used:

- **TEMPO — 10 temporal reasoning classes**, led by event analysis / localization
  **36%** and time-period contextualization **21%**.
- **RECOR — 6 discourse-dependency types**: continuation **35%**, coreference
  **29%**, self-contained **24%**, topic-shift **11%**.

PHASE E should classify failures into *these* categories and report nDCG@10 per
category. That is more defensible than a taxonomy we made up, comparable to the
organisers' own analysis, and immediately answers "where does BM25 actually break".

Note `self-contained 24%` in particular: a quarter of RECOR turns need no history
at all, which means the history effect is concentrated in the other 76% and the
per-category breakdown will be sharper than the aggregate.

### 5. Annotation definitions worth quoting in the report

- Track 1: a passage is gold only when it is **both topically relevant and
  temporally aligned** — its time scope matches a required anchor period. An
  unrelated date does not count.
- Track 2: a passage is gold only when it supports the answer **through
  multi-step inference**, not surface overlap, with anaphora and ellipsis
  resolved against prior turns.

Agreement on the pilots: TEMPO κ=0.82 (reasoning class), κ=0.85 (gold relevance);
RECOR κ≥0.73 across criteria.

### 6. Sub-track 2a is defined WITHOUT the reasoning field

> "Given **all prior turns plus the current question** and a domain corpus,
> systems retrieve passages for the current turn…"

No mention of a supplied reasoning annotation, either in the 2a definition or in
the description of how the test set was built ("supporting passages annotated for
each target turn" — passages, not reasoning). Combined with `ablation_eval.py`
showing that "+Reasoning" is literally the gold string pasted onto the query,
the working assumption is now:

**`subquestion_reasoning` is training-time supervision, not test-time input.**

Not proven. Still worth confirming — but we should plan as if we must generate it.

### 7. Mentor alignment — this changed my reading

Bethard's temporal work is not adjacent to Track 1, it is the **toolbox for the
named failure mode**:

- *Fusing Temporal Graphs into Transformers for Time-Sensitive Question Answering*
  (Su, Howard, Hakim, Bethard — EMNLP Findings 2023)
- *Transformer-Based Temporal Information Extraction and Application: A Review*
  (Su, Howard, Bethard — EMNLP 2025) — a survey of exactly the techniques a
  temporal retrieval system would need
- *A Semantic Parsing Framework for End-to-End Time Normalization* (2025), and the
  long SCATE / Clinical TempEval / narrative-timeline line before it

TEMPO's reported failure is **Temporal Coverage@10 = 71.4%** even for the best
system — i.e. right topic, missing required period. Time normalization turns a
temporal expression into a machine-readable interval. Normalising expressions on
both the query and the document side and filtering or reranking on interval
overlap is a direct attack on that failure mode, it is cheap (CPU, no GPU), and
it is the thing the mentor knows better than almost anyone.

That is a stronger argument for Track 1 than "he mentioned temporal overlap in an
email". It should be checked against data before committing — but it is the
hypothesis to check first.

### 8. Kevin Duh

Organiser, Johns Hopkins, not an author of either source paper. He and Bethard
co-edited the NAACL 2024 proceedings. If a question needs an organiser's answer,
Bethard likely has a direct line — which is another reason to ask him before
emailing `abdelrahman.abdallah@uibk.ac.at` cold.

---

<!-- source: notes/upstream_code_findings.md -->
## Upstream code findings — TEMPO and RECOR

Read 2026-09-14 from the two upstream repos that RETECO's official baseline
copies verbatim. Both are pinned below. These are things you cannot learn from
the task website.

| Repo | Commit | Date |
| --- | --- | --- |
| `tempo-bench/Tempo` | `8731487254e0988eaf2ca4ae3e93ff587fec64d0` | 2026-02-16 |
| `RECOR-Benchmark/RECOR` | `ba054605492da40139799300aa5dbed271e1d7e8` | 2026-01-14 |
| `DataScienceUIBK/RETECO` | `23093c30e568a337c6293de4c58ffcccddbded5b` | 2026-08-30 |

RETECO pin confirmed to contain `877522b` ("Sync dataset card copy…"), the last
commit touching `starter_kit/`. Our checkout is current for the starter kit.

---

### 1. `excluded_ids` — a real deviation from upstream, worth checking

TEMPO's `retrievers.py::retrieval_bm25` takes an `excluded_ids` argument and
**zeroes the score of those documents per query** before ranking (same in every
dense retriever it ships; `get_scores()` applies it centrally). `run_step.py`
carries `excluded_ids` through from the step records.

The string `excluded` appears **nowhere** in RETECO's `starter_kit/*.py` —
not in `official_baseline.py`, not in `bm25_baseline.py`, not in `build_release.py`.

So one of these is true, and it is cheap to find out after download:

- the released `examples_*.jsonl` no longer carry `excluded_ids` (organisers
  dropped the field when rebuilding), or
- the field is there and the official baseline silently ignores it.

Why it matters: in BRIGHT-style benchmarks the exclusion list typically removes
the query's own source post from the corpus. Ignoring it **inflates or deflates**
scores depending on whether the source post is also a gold document, and it is a
plausible second contributor to the 1a gap (RETECO dev `0.0967` vs TEMPO
published `0.108`) that `BASELINE_RESULTS.md` attributes only to the 70/30 split.

**Action:** after download, grep one `examples_*.jsonl` for `excluded_ids`.
Record the answer in the log either way. If present and unused → question for the
organisers, and a legitimate first finding to bring to Bethard.

### 2. RECOR "+Reasoning" is string concatenation onto the query

`experiments/retrieval/ablation_eval.py` builds the query as
`"\n\n".join(parts)` where parts are, in order:

1. `turn['query']`
2. `"Conversation History:\n" + turn['conversation_history']` — only if
   `--append-history`, and skipped when history is literally
   `"No previous conversation."`
3. `"Reasoning:\n" + turn['subquestion_reasoning']` — only if `--append-reasoning`
4. `"Reasoning Metadata:\n"` + `Target Information: …`, `Relevance Signals: …`
   (comma-joined), `Irrelevance Signals: …` — only if `--append-reasoning-metadata`

There is no model, no rewriting, no selection. The whole `.236 → .479` result is
**gold annotations pasted into the query string.** This settles the question from
week 1: the "+Reasoning" condition is an oracle, and the interesting research
problem is whether that text can be *produced* at inference time from the
conversation alone.

Note also that a fourth, stronger condition exists upstream and is not in RETECO's
baseline table: history + reasoning + reasoning metadata. Worth measuring as an
upper bound on our own dev split.

RETECO's `official_baseline.py::_recor_topics` implements exactly conditions
1 and 1+2 — same prefix string `"Conversation History:\n"`, same
`"No previous conversation."` skip. Our 2a numbers should therefore match
upstream's Base and +History byte for byte, and they do (within 0.003).

### 3. RECOR's plain `run_retrieval.py` uses current turn only

`load_queries()` takes `turn['query']` and nothing else, sets
`excluded_ids[qid] = []` unconditionally, and **skips turns with no gold docs**.
That last detail matters for denominators: turns without judgments are not scored,
so "2,971 turns" is not necessarily the number of scored topics.

### 4. Six of eleven RECOR domains come from BRIGHT

Per the RECOR README: BRIGHT → biology, earth_science, economics, psychology,
robotics, sustainable_living; StackExchange → Drones, hardware, law,
medicalsciences, politics. The sample records carry
`metadata.method = "unified_bright_workflow"`.

Consequence to keep in mind before claiming anything about "reasoning-specialised
retrievers win": ReasonIR and DIVER are built for BRIGHT-style reasoning
retrieval. A per-domain split of results (BRIGHT-derived vs StackExchange-derived)
is a cheap, honest diagnostic nobody in the baseline table has reported. It is
also a decent candidate for a small contribution.

### 5. TEMPO step records upstream

`run_step.py` loads config `steps` from `tempo26/Tempo`, groups flat step rows by
`q_id`, and uses fields `step_id`, `step_text`, `query`, `excluded_ids`. RETECO's
release nests steps inside the query record and renames the text field to
`step_instruction`. Query string is identical:
`f"{base_query}\n\nStep: {step_text}"`.

The steps are **supplied**, not generated — so 1b is not a decomposition task
unless we choose to make it one.

### 6. Organisers (from the task site, 5 people)

Abdelrahman Abdallah (Innsbruck), Mohammed Ali (Innsbruck), Muhammad Abdul-Mageed
(UBC), **Kevin Duh (Johns Hopkins)**, Adam Jatowt (Innsbruck).
Contact: `abdelrahman.abdallah@uibk.ac.at`.
Mailing list: `https://groups.google.com/g/semeval-2027-reteco` — **join it**;
registration and platform details will be announced there.

Kevin Duh is on the RETECO organiser list but is not an author of either source
paper — he is presumably the SemEval-side co-organiser.

### 7. Corrections to earlier notes

- Dataset total size is **4.73 GB** on Hugging Face, not 4.5 GB. Plan ~11 GB free
  (download + extraction + working space).
- The HF dataset viewer is not available for these splits — you cannot preview
  online, you must download.
- The evaluation set is described as "separate, **newly annotated**, and released
  without judgments during the evaluation window". Newly annotated, so its field
  inventory is not guaranteed to match train/dev. This makes question 1 in
  `task_and_papers.md` §4 (does `subquestion_reasoning` ship at test time?) both
  more urgent and genuinely unanswerable without asking.
