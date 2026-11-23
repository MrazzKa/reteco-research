# Track-1 query-side guidance: 4 dev examples (N2a, LOG 2026-11-23 12:58)

Rule (fixed before viewing): keys (domain, id) sorted; `random.Random(20260921).sample(keys, 4)`. g = `guidance.guidance_text` (plan gold ids removed; `gold_passage_annotations` never read). Shown: query (first 400 chars), g, the other query-side fields (short), the first 300 chars of the first gold document (qrels order). Not resampled.

## history / 70471_283

**Query:** Was it illegal in 18th century France or Spain to use false titles of nobility? The friend of popes and kings and noblemen, and of all the male and female ruffians and vagabonds of Europe, abbé, soldier, charlatan, gamester, financier, diplomatist, viveur, philosopher, virtuoso, “chemist, fiddler, and buffoon,” each of these, and all of these was Giacomo Casanova, Chevalier de Seingalt , Knight of

**g:** Time anchors: 18th century; 1760; 1767. Temporal intent: period definition. Reasoning: To answer, retrieve legal codes, decrees, or historical records from 18th century France and Spain addressing noble titles and their misuse. Plan: 1. Identify and locate 18th century legal codes or decrees from France and Spain related to nobility and title usage. 2. Search for historical analyses or secondary sources discussing the enforcement of laws on false noble titles in the 18th century. 3. Cross-reference Casanova's documented activities with legal contexts in France and Spain during the specified period.

**Other query-side fields:**

- query_summary: The query asks if using false noble titles was illegal in 18th century France or Spain, focusing on Casanova's era.
- expected_granularity: decade
- is_temporal_query: True
- query_temporal_events: Giacomo Casanova using the title 'Chevalier de Seingalt' in 1760 Casanova detained in Spain in 1767
- query_temporal_signals: 18th century 1760 1767 Casanova's time
- quality_checks: cross-check dates from multiple sources prefer primary/authoritative sources verify historical accuracy of Casanova's documented activities
- temporal_reasoning_class_primary: time_period_contextualization
- temporal_reasoning_class_secondary: historical_attribution_and_context

**First gold document (start, 3 gold in all):** In some countries, the local lord could impose restrictions on such a commoner's movements, religion or legal undertakings. Nobles exclusively enjoyed the privilege of hunting. In France, nobles were exempt from paying the taille, the major direct tax. Peasants were not only bound to the nobility by

## cardano / 6888_120

**Query:** How do validators know a policy script is expired based only on slot number? A policy script can be set to expire. For example: { &quot;before&quot;: 51000000 } The number corresponds to a slot number within the epoch the script is being created. However, the current slot number will be below that number again in subsequent epochs (since slot number starts at 0 each epoch and counts up). How does 

**g:** Time anchors: slot number; epoch transitions. Temporal intent: before after. Reasoning: To retrieve temporal evidence, focus on documentation explaining slot number mechanics, epoch transitions, and validator logic for policy expiration. Plan: 1. Locate technical documentation on slot numbering and epoch transitions in blockchain systems. 2. Identify validator rules or algorithms for interpreting slot-based expiration conditions. 3. Cross-reference examples of policy scripts with expiration logic tied to slot numbers.

**Other query-side fields:**

- query_summary: The query asks how validators determine policy script expiration based on slot numbers across epochs.
- expected_granularity: epoch-level
- is_temporal_query: True
- query_temporal_events: policy script expiration
- query_temporal_signals: before current slot number epoch subsequent epochs
- quality_checks: verify slot-to-epoch mapping logic ensure validator rules align with authoritative blockchain documentation
- temporal_reasoning_class_primary: event_analysis_and_localization
- temporal_reasoning_class_secondary: sources_methods_and_documentation

**First gold document (start, 2 gold in all):**  In many ways, epochs are the calendar of the Cardano community. These epochs are broken into slots, and each slot is one second. Thus, a Cardano epoch is 432,000 slots, which adds up to 5 days. Many Cardano community events are organized around epochs. Compensations for participating in running the

## history / 66498_462

**Query:** How to understand the geography of Napoleon&#39;s military campaigns? I am currently reading Napoleon The Great by Andrew Roberts and I am facing a few issues. While I can understand when Roberts describes Napoleon's life, I am having a hard time understanding the military campaigns of the book. He mentions places like Lodi &amp; Toulon but it is hard to even visualize and understand what is happe

**g:** Time anchors: Napoleon's era; Battle of Lodi; Siege of Toulon. Temporal intent: timeline. Reasoning: To retrieve temporal evidence, focus on historical maps, campaign timelines, and descriptions of battles and locations during Napoleon's era. Plan: 1. Locate historical maps and atlases detailing Napoleon's military campaigns, focusing on Lodi and Toulon. 2. Retrieve detailed timelines and descriptions of Napoleon's campaigns from authoritative historical sources. 3. Cross-reference artillery and geographic details with military history texts and visual aids.

**Other query-side fields:**

- query_summary: The query seeks to understand the geography and timeline of Napoleon's military campaigns as described in Andrew Roberts' book.
- expected_granularity: period
- is_temporal_query: True
- query_temporal_events: Napoleon's military campaigns Battle of Lodi Siege of Toulon
- query_temporal_signals: Napoleon's military campaigns mentions places like Lodi & Toulon map
- quality_checks: cross-check dates and locations from multiple sources use authoritative historical maps and campaign records
- temporal_reasoning_class_primary: event_analysis_and_localization
- temporal_reasoning_class_secondary: time_period_contextualization

**First gold document (start, 1 gold in all):** Roberts has been indefatigable in tracking down memorabilia and visiting the sites of battles, palaces and places of exile. This is all richly depicted and woven into a narrative that is told with the aplomb of an accomplished historical storyteller. But underlying structures and more long-term shif

## genealogy / 12774_283

**Query:** How were absentees recorded on the Protestation Returns? The Protestation Returns of 1641/2 are currently being digitised and made freely accessible on the UK Parliament website . My understanding is that for each parish the oath was performed by everybody on a single day in February or March of 1641/2. Were only inhabitants of the parish recorded on the return for that parish? How were visitors o

**g:** Time anchors: 1641/2; February; March. Temporal intent: period definition. Reasoning: Temporal evidence should focus on the procedural context of the Protestation Returns, including documentation of absentees and qualifications for oath-taking during the specified period. Plan: 1. Locate digitised records of the Protestation Returns from 1641/2 on the UK Parliament website or archival sources. 2. Examine historical guidelines or instructions for recording absentees and non-residents in the Protestation Returns. 3. Identify any annotations or supplementary records indicating later additions or handling of absentees. 4. Cross-reference parish-specific records to verify consistency in recording practices.

**Other query-side fields:**

- query_summary: The query seeks to understand how absentees and non-residents were recorded in the Protestation Returns of 1641/2.
- expected_granularity: month
- is_temporal_query: True
- query_temporal_events: Protestation Returns of 1641/2
- query_temporal_signals: 1641/2 February March single day at a later date
- quality_checks: cross-check dates and practices across multiple parishes verify against authoritative archival sources ensure digitised records match original documentation
- temporal_reasoning_class_primary: time_period_contextualization
- temporal_reasoning_class_secondary: sources_methods_and_documentation

**First gold document (start, 6 gold in all):** The Protestation Returns of 1641–1642 are lists of English males over the age of 18 who took, or did not take, an oath of allegiance "to live and die for the true Protestant religion, the liberties and rights of subjects and the privilege of Parliaments." These lists were usually compiled by parish,

