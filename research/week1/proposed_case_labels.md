# Proposed labels for the fixed-seed pilot cases

Seed: 20260921. These are provisional readings of the sampled case sheets, not
confirmed human labels. The sheets show excerpts of passages, so ambiguous cases
need review against the full document before ticking any category.

| track/domain | qid | proposed type | proposed failure mode | reason |
| --- | --- | --- | --- | --- |
| 1/iota | `2714_798` | time-period contextualization | lexical mismatch | The long migration query retrieves broad crypto text instead of the dated legacy-network passages. |
| 1/iota | `314_806` | event analysis/localization | lexical mismatch | Generic distributed-systems documents outrank the IOTA synchronization evidence. |
| 1/iota | `2194_800` | event analysis/localization | none; success contrast | The run finds two clock-related gold passages in its top five. |
| 2/drones | `ex_2271_turn_1` | self-contained | lexical mismatch | High-Kv motor explanations outrank the passages about ESC compatibility. |
| 2/drones | `ex_2240_turn_2` | continuation | lexical mismatch | Simulator/controller vocabulary attracts related negatives rather than the named compatible apps. |
| 2/drones | `ex_2324_turn_1` | self-contained | lexical mismatch | General buyer guides outrank the comparison of tracking and obstacle avoidance. |
| 2/drones | `ex_2424_turn_4` | continuation | implicit reasoning link | Range-focused text dominates although the turn asks about humidity and water effects on signal. |
| 2/drones | `ex_2424_turn_3` | continuation | history drowns the turn | Earlier fixed-wing range discussion appears prominent in retrieved text; the current turn asks about purchasable 4 km drones. |
| 2/drones | `ex_2324_turn_2` | continuation | history drowns the turn | The prior Mini 4 Pro comparison seems to dominate a new question about beginner value. |
| 2/drones | `ex_2424_turn_2` | coreference | lexical mismatch | The phrase "like that" depends on the prior range question, but results favor fixed-wing endurance. |
| 2/drones | `ex_2779_turn_1` | self-contained | gold looks wrong/debatable | A top-ranked non-gold passage directly explains voltage from cells in series; inspect the full passage and gold set. |
| 2/drones | `ex_2248_turn_2` | continuation | none; history helps | The earlier hazard discussion supplies context missing from the short current turn. |
| 2/drones | `ex_2693_turn_3` | coreference | none; history helps | Calibration context resolves "the drone" and retrieves the gyroscope passage at rank one. |
| 2/biology | `32_turn_3` | continuation | lexical mismatch | Results about salt and blood pressure miss the kidney response to seawater. |
| 2/biology | `6_turn_2` | continuation | history drowns the turn | Current-only finds some gold, but adding history removes it from the top ten. |
| 2/biology | `102_turn_3` | coreference | history drowns the turn | Current-only finds some gold; the longer yeast/sugar history displaces it. |
| 2/biology | `44_turn_2` | continuation | implicit reasoning link | Nighttime fear documents outrank the specific amygdala explanation. |
| 2/biology | `5_turn_1` | self-contained | lexical mismatch | General twin passages outrank the genetic and conception comparison. |
| 2/biology | `2_turn_3` | coreference | lexical mismatch | Receptor-count descriptions outrank the question about variation among people. |
| 2/biology | `102_turn_1` | self-contained | lexical mismatch | Related yeast questions outrank the osmosis mechanism. |
| 2/biology | `56_turn_1` | self-contained | lexical mismatch | Broad cell-membrane descriptions outrank the bilayer-stability mechanism. |
| 2/biology | `99_turn_7` | coreference | none; history helps | The previous sensor discussion supplies the referent for "those sensors". |
| 2/biology | `3_turn_4` | continuation | none; history helps | Earlier animal-laterality turns provide the topic; the gold laterality passage is rank one. |

No tally is asserted as a human annotation. Confirm or revise each row in the
original case sheets before reporting taxonomy counts.
