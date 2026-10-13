## 4. Rough frequency of error types (larger fixed-seed sample, preliminary labels)

Sheets: `research/runs_v12/categories/sheet_{neither,bm25_only,dense_only}.md`, made by
`scripts/label_sample.py` with the same rule as above (seed 20260921), skipping the
examples already shown. One primary label per pair, assigned by the assistant from the
query, the gold document's opening and both systems' top hit. **Not human-validated;
treat the counts as a first impression, n = 52.**

### Neither (20 pairs: 10 Track 1, 10 Track 2)

| label | meaning | Track 1 | Track 2 | sheet rows |
| --- | --- | ---: | ---: | --- |
| instance / world knowledge | gold is a specific instance the query never names (Blackletter for "writing styles of scribes", the Titanic for "reaction to impending doom", Venus figurines, an Iliad passage, Musschenbroek's pyrometer, Trinity House) | 6 | 0 | 1, 2, 5, 6, 9, 10 |
| abstract inferential link | gold explains a concept the question needs but does not name (price discrimination, national-origin law for "city or state", gene expression for "how does a neuron start making Sst") | 2 | 4 | 4, 8, 12, 13, 15, 17 |
| context-dependent turn | elliptical turn; the missing referent is in the history (current turn only here) | 0 | 2 | 11, 14 |
| near-copy outranks gold | the question's own text, or a sibling chunk of the gold's source, is retrieved instead | 1 | 1 | 7, 20 |
| fragment of a long source | gold is a mid-document chunk without the query's framing | 0 | 1 | 16 |
| weak / debatable judgement | the gold looks only loosely related to the question (possible labelling issue — not established) | 1 | 2 | 3, 18, 19 |

### BM25-only (16 pairs: 8 + 8)

| label | meaning | count | sheet rows |
| --- | --- | ---: | --- |
| exact rare term, name or identifier | proper names (Adolphus Dolo / "General Peanut Butter", Gazprom), code identifiers (`rosdep`, `TransformStamped`), acronyms (PPF), rare words ("galls") | 11 | 1, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14 |
| match beyond the encoder's window | long document or boilerplate opening; the matching passage comes later (Hansard speech, Wikipedia section, wikiHow page, model-kit page) | 5 | 2, 3, 6, 15, 16 |

### Dense-only (16 pairs: 8 + 8)

| label | meaning | count | sheet rows |
| --- | --- | ---: | --- |
| paraphrase / vocabulary mismatch | same meaning, different words ("blood tests" vs "blood typing", "write in a date after I signed" vs "blank fields completed after signature", "leftover oxygen" vs "inert gas asphyxiation") | 10 | 4, 6, 7, 9, 10, 11, 12, 14, 15, 16 |
| verbose query dilutes BM25 | long Track-1 post; BM25 is drawn to documents matching incidental terms, the encoder keeps the main question | 5 | 1, 2, 3, 5, 8 |
| inferential link | as above (state recording-consent law for "where the customer calls from") | 1 | 13 |

## 5. Hypotheses from the meeting brief — status

| hypothesis | evidence (all dev pairs unless stated) | status |
| --- | --- | --- |
| BM25-only = exact names, numbers, rare terms | BM25-only pairs have the highest share of queries with numbers whose numbers occur in the gold (Track 1 1a: 0.53 vs 0.24 for dense-only); 11/16 sampled are exact-term cases | supported |
| BM25-only = information lost by the embedding | BM25-only golds are long (Track 1 1a: 1,279 words on average vs 234 for dense-only); 68% exceed the window and in 44% the query terms occur only beyond it (2% for dense-only) | supported — truncation is a measurable cause |
| Dense-only = paraphrase / different wording | dense-only pairs have about half the lexical overlap of BM25-found pairs (0.18 vs 0.36–0.40 on Track 1, 0.21 vs 0.40–0.42 on Track 2); 10/16 sampled are paraphrases | supported |
| Neither = multi-hop / reasoning | neither-pairs have the lowest overlap (0.16 Track 1); in the sample, 12/20 need an inference step (instance or concept the query does not name) | supported, preliminary |
| Neither = temporal/numeric reasoning | no sampled Track-1 failure turns on a date computation; dates appear (1880 census, 18th century) but the failure is the missing instance, not the arithmetic | not observed in this sample |
| Neither = labelling issues | 3/20 judged "weak/debatable" by the assistant | open — needs a human check, gold labels untouched |

**New patterns** that recur and were not in the brief:

1. **Near-duplicates crowd the top ranks.** Two copies of the same passage under different
   ids (text differs slightly, so v1.1 deduplication kept both) and copies of the question
   text itself occupy dense and BM25 top ranks (examples BM25-only 2, Both 4, Neither 1).
2. **Boilerplate and link-only chunks.** Several gold documents are link lists or
   navigation templates (BEA data pages, Wikipedia infobox chunks); encoders represent
   them poorly and they attract other boilerplate (Neither 4).
3. **Multi-part questions.** Long Track-1 posts ask two things; a single query vector
   follows the main one (BM25-only 1 and 2).

## 6. Data notes found during this analysis (not used by any system)

- **Track-2 document ids encode the construction.** In the five StackExchange-derived
  domains, 100% of gold documents (train+dev) are named `<question>_doc_<n>`, while only
  1.1–1.5% of corpus documents have that form; 64–76% of `_doc_` documents are gold. Most
  negatives are `<question>_google_neg_<n>`. A system reading ids could exploit this; ours
  never read ids. Worth reporting to the organisers in case the hidden test set is built
  the same way. (`scripts/id_artifact.py`, `research/runs_v12/id_artifact.json`.)
- **Exact duplicates in Track 2.** BRIGHT-derived domains contain 5–42% documents that
  belong to an exact-duplicate group (robotics 42%); StackExchange domains none. See the
  indexing-order study in `research/RESULTS.md`.

## 7. Caveats

- Pooled counts are dominated by large domains: on Track 1 `1a`, `history` contributes
  1,010 of the 1,783 gold pairs (240 queries with ~4 gold documents each). The per-domain
  tables show the other domains separately; the direction (dense-only ≫ BM25-only) holds
  in every Track-1 domain at k=100 except where both are tiny.
- One dense model (bge-small, 512 tokens). A larger or longer-context encoder would move
  pairs out of "BM25-only" (the truncation cases) — model comparison is in RESULTS.md.
- k=100 categories describe candidate generation; k=10 categories describe what the
  metric sees. Both tables are in section 1.
- Track 2 `2a_current` deliberately ignores the conversation; elliptical turns therefore
  fail for both systems by construction.
- Labels in sections 3–4 are one annotator's (the assistant's) reading of the opening of
  each gold document; they are hypotheses for Steve and the team to check.
