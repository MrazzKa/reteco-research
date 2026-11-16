# Error types of the main runs on dev (S4)

**Labels are preliminary, to be confirmed by a human.**

Selection (LOG 2026-11-16 14:29): per sub-task, 15 dev topics on which the main run scored nDCG@10 <= 0.1 (1a: run `1a`, pool 50; 1b: `1b`; 2a: `2a_history_rr`). The eligible keys (domain, topic id) were sorted and sampled with `random.Random(20260921).sample` per sub-task. All 45 sampled topics have nDCG@10 = 0. Material: `research/cases/error_material_dev.json`; labels: `research/cases/error_types_dev.json`.

Categories (one primary label per topic):

- **(a) recall miss**: no gold in the first-stage (BM25+dense hybrid) top 100 (mechanical);
- **(b) not lifted**: gold in the first-stage top 100 but not brought into the top 10 by the ReasonEmbed / reranker stages (mechanical; "demoted" if the final rank is worse than the hybrid rank);
- **(c) top-1 looks relevant**: our top-1 document visibly answers or clearly helps with the query / step (possible incomplete judgments);
- **(d) temporal mismatch** (Track 1 only): top documents on the right topic but the wrong period / version / date;
- **(e) expansion drift**: the LLM reason / HyDE clearly drifted from the question (wrong entity, wrong sense, invented specifics);
- **(f) other**.

Precedence (fixed in advance): a reading label (c) > (d) > (e) is used only when clearly visible from the shown texts; otherwise the mechanical label (a) or (b); (f) only when none fits. (c) is applied conservatively: "same topic" is not enough.

## Counts

| sub-task | a | b | c | d | e | f | eligible / topics |
|---|---|---|---|---|---|---|---|
| 1a | 2 | 7 | 3 | 0 | 3 | 0 | 151 / 519 |
| 1b | 4 | 3 | 6 | 0 | 2 | 0 | 395 / 1214 |
| 2a | 1 | 6 | 6 | 0 | 2 | 0 | 136 / 858 |
| all | 7 | 16 | 15 | 0 | 7 | 0 | 682 / 2591 |

Mechanical labels for comparison: 1a: a=4, b=11; 1b: a=9, b=6; 2a: a=2, b=13.

## 1a

### 1a.1 — history `67963_434` (nDCG@10 0.000)

> What does this source "IAA iii" mean? Which book? I've been reading a book about Genghis Khan by Frank McLynn and, going through its notes, I saw sources where I couldn't find anything about it, i.e. what publication was referred to. I want to find this source designated as "IAA iii".

- Gold (2 judged; best-placed shown): hybrid rank 267, final rank 267 — "## Description The Chronicle of Ibn al-Athir (1160-1233AD), entitled "al-Kamil fi'l-Ta'rikh", is one of the outstanding sources for the history of the mediaeval world. It covers the whole sweep of Isl ..."
- Mechanical label: (a)
- Our top 3:
  1. "About the pagination of this eBook This eBook contains a multi-volume set. To navigate this eBook by page number, you will need to use the volume numb ..."
  2. "i The Oxford History of the Ancient Near East ii The Oxford History of the Ancient Near East Editors: Karen Radner, Nadine Moeller, and D. T. Potts Th ..."
  3. "1. The Secret History of the Mongols , ch.V 2. Buell 1992 , pp. 3-7. 3. a b c Kradin, Nikolay N. (2016-01-11). Kyrgyz Khaganate . In Dalziel, Nigel; M ..."
- LLM reason: "Knowledge needed: Understanding academic source abbreviations, especially in historical or scholarly contexts. Relevant document topic: A scholarly wo ..."

**Preliminary label: (e)** — The expansion invents a referent for 'IAA iii' ('International Archives of Asia', a 1985 volume) while the gold is Ibn al-Athir's chronicle, so retrieval chases generic multi-volume series.

### 1a.2 — bitcoin `123461_13` (nDCG@10 0.000)

> Implementing Conditional Fund Locking in Bitcoin Similar to Ethereum's Smart Contracts I'm familiar with how Ethereum allows users to lock funds in smart contracts, which can then be released under specific conditions using mechanisms like the Hashed TimeLock Contract (HTLC) protocol. I'm interested ...

- Gold (4 judged; best-placed shown): hybrid rank 70, final rank 70 — "A Hash Time Locked Contract or HTLC is a class of payments that use hashlocks and timelocks to require that the receiver of a payment either acknowledge receiving the payment prior to a deadline by ge ..."
- Mechanical label: (b)
- Our top 3:
  1. "Una of the most interesting properties it has Bitcoin are time locks or timelock such as nLockTime. These types of functionalities allow users to defi ..."
  2. "CheckSequenceVerify (CSV) use cases Now let's examine some use cases that CSV allows us within Bitcoin thanks to its creation: Creation of contracts w ..."
  3. "When Bob wants to spend his new Bitcoin, he must first unlock the script. Alice would have locked the script when she sent her transaction to Bob’s ad ..."
- LLM reason: "Knowledge needed: Bitcoin's scripting limitations, transaction mechanics, and existing tools for conditional logic (e.g., time-locked transactions, mu ..."

**Preliminary label: (b)** — Best gold (HTLC definition) sits at hybrid rank 70, outside the 50-document rerank pool, so it was never reranked; the top-1 on nLockTime is on topic but only covers part of the question.

### 1a.3 — history `56929_710` (nDCG@10 0.000)

> What evidence is there of tank-vs-tank combat in Asia during the second world war? It has been known that the Japanese army during the Second World War did not value tanks highly and as such they were not always used effectively and had significantly worse characteristics than Allied armoured vehicl ...

- Gold (2 judged; best-placed shown): hybrid rank 3, final rank 11 — "Due to the war with China, Japan produced a large number of tanks. Although initially the Japanese used tanks to good effect in their campaigns, full-scale armored warfare did not occur in the Pacific ..."
- Mechanical label: (b)
- Our top 3:
  1. "While combat in the European Theater of Operations (ETO) consisted of high-profile armored warfare, the mainly naval nature of the Pacific Theater of ..."
  2. "Japanese Offensive With the last straw pulled by the Army and support shift towards the Navy, the logistical strain that was the Sino-Japanese War req ..."
  3. "Fonthill Media- Japanese Tanks and Armoured Warfare: 1932-45 A Military and Political History Author: David McCormack ISBN: 978-1-78155-810-2 Hardcove ..."
- LLM reason: "Knowledge needed: Historical accounts of armored battles in Asia during WWII, specifically between Allied and Japanese forces. Relevant document topic ..."

**Preliminary label: (c)** — Top-1 explains why armoured warfare was secondary in the Pacific theatre, close in content to the judged gold passage (hybrid 3, demoted to 11), so it looks like a judgment gap.

### 1a.4 — economics `45680_223` (nDCG@10 0.000)

> What should we do if the subsample have the opposite results to the general results? In my replication study, I examine whether a law (a law implemented staggered by different countries) has an impact on firms' cash equivalents. The result turning out for the whole sample is that the firms' cash equ ...

- Gold (3 judged; best-placed shown): hybrid rank not in pool, final rank not in top 1000 — "Why is applying the standard DiD setup in staggered treatment scenarios problematic? The traditional DiD framework functions adequately when dealing with scenarios featuring only two periods and a con ..."
- Mechanical label: (a)
- Our top 3:
  1. "30.3 Simple Difference-in-Differences DID first emerged as an econometric workhorse for natural experiments, settings where policy shocks or geographi ..."
  2. "Including unit-specific time trends (see above) is not the only solution to parallel-trends violations; indeed, scholars may desire more flexible solu ..."
  3. [gold of other topic] "Common Errors: How to (and Not to) Control for Unobserved Heterogeneity Review of Financial Studies Author(s) David A. Matsa Todd Gormley Controlling ..."
- LLM reason: "Knowledge needed: Understanding replication issues, subsample anomalies, and robustness checks in empirical economics. Relevant document topic: Replic ..."

**Preliminary label: (a)** — No gold (staggered DiD problems, Simpson's paradox) in the first-stage top 100; top-1 is a generic difference-in-differences text that does not address the reversed subsample result.

### 1a.5 — bitcoin `124603_8` (nDCG@10 0.000)

> Question about bitcoin mining difficulty adjustment formula in book mastering bitcoin 3rd edtion In book "Mastering bitcoin" 3rd, page 278, There is a formula about bitcoin mining difficulty adjustment formula as below: New Target = Old Target * (20,160 minutes / Actual Time of Last 2015 Blocks) I t ...

- Gold (3 judged; best-placed shown): hybrid rank 6, final rank 18 — "Target Block Time Difficulty is tweaked to ensure blocks are mined every 10 minutes, regardless of miner activity. Adjustment Formula The difficulty is recalculated using a formula that compares the a ..."
- Mechanical label: (b)
- Our top 3:
  1. [gold of other topic] "In Bitcoin, a difficulty adjustment period consists of 2016 blocks and with a 10 minute block target this is a period of approximately two weeks. To c ..."
  2. "In Bitcoin, a difficulty adjustment period consists of 2016 blocks, which is about two weeks with a 10-minute block target. To calculate the mining di ..."
  3. "Retargeting to Adjust Difficulty As we saw, the target determines the difficulty and therefore affects how long it takes to find a solution to the Pro ..."
- LLM reason: "Knowledge needed: Understanding Bitcoin's difficulty adjustment mechanism, specifically the formula used to adjust mining difficulty based on time pas ..."

**Preliminary label: (c)** — Top-1 (gold for another topic) and top-3 (the Mastering Bitcoin retargeting section itself) explain the 2016-block difficulty formula the question asks about; the gold was demoted from hybrid 6 to 18.

### 1a.6 — history `56068_771` (nDCG@10 0.000)

> Why did the Nazis collaborate with the Ustaše? The Croats are linguistically, ethnically and culturally a Slavic people. While the Ustaše did not see themselves as such, why did the Nazis choose to collaborate with what was essentially a nationalist organisation for a Slavic ethnic group?

- Gold (4 judged; best-placed shown): hybrid rank 4, final rank 13 — "It was founded as a nationalist organization that sought to create an independent Croatian state. It functioned as a terrorist organization before World War II.[51][44] After the invasion of Yugoslavi ..."
- Mechanical label: (b)
- Our top 3:
  1. "The Independent State of Croatia (Nezavisna Država Hrvatska, NDH) emerged as one of the most controversial and significant entities in the European th ..."
  2. "Nazi Germany initially did not support an independent Croatia, nor did it support the Ustaše, with Hitler stressing the importance of a strong and uni ..."
  3. "The ideology of the movement was a blend of fascism, Roman Catholicism and Croatian ultranationalism. The Ustaše supported the creation of a Greater C ..."
- LLM reason: "Knowledge needed: Understanding Nazi racial policies, the Ustaše's ideology, and the geopolitical context of WWII in the Balkans. Relevant document to ..."

**Preliminary label: (b)** — Golds at hybrid 4 and 44 were demoted to 13 and only lifted to 35; top-1 is a general overview of the NDH, while the more direct answer (Nazi stance on the Ustase) is at rank 2.

### 1a.7 — history `79533_1` (nDCG@10 0.000)

> What kind of knife did people use to cut open cows? I'm writing a fantastical story and one of the characters needs to cut open a cow equivalent. What kind of knife (shape, size, handle kind) was used to butcher cows? I looked online and only found references to brands of knives that work well. I do ...

- Gold (17 judged; best-placed shown): hybrid rank 68, final rank 68 — "In contrast to an Oldowan tool, which is the result of a fortuitous and probably unplanned operation to obtain one sharp edge on a stone, an Acheulean tool is a planned result of a manufacturing proce ..."
- Mechanical label: (b)
- Our top 3:
  1. "For the better understanding of various weapons, parts of dress, and army-implements, we have brought together a great number of such objects on pl. 2 ..."
  2. "More Viking men carried axes or spears. Battle axes had long handles, were light, well balanced and deadly. Battle axes had a variety of head shapes w ..."
  3. "This post once again comes to us from Cameron Laird: The solution to this one is the ever-helpful Ox (OE Oxa), who not only pulled the plough for plan ..."
- LLM reason: "Knowledge needed: Historical butchering tools from a medieval period, specifically knives used for slaughtering livestock. Relevant document topic: Me ..."

**Preliminary label: (b)** — All 17 golds are about prehistoric stone butchery tools (best at hybrid 68, outside the rerank pool); the expansion assumed a medieval cleaver and the top-3 are weapon texts.

### 1a.8 — history `76410_105` (nDCG@10 0.000)

> Was there an economic reason for Protestants' iconoclasm? Europe underwent major economic upheavals during the creation of Protestantism (cf. E. Michael Jones, Barren Metal or Goy Guide to World History ). Is this one reason why Protestants upheld iconoclasm ? Was it a sense of necessity or utilitar ...

- Gold (3 judged; best-placed shown): hybrid rank 18, final rank 19 — "The research demonstrates that iconoclastic revolutions involved complex discussions between religious convictions and practical concerns such as economic stability, governmental authority, and social ..."
- Mechanical label: (b)
- Our top 3:
  1. "The Protestant critique of religious iconography had significant economic repercussions that extended beyond theological debates. The systematic oblit ..."
  2. "Particular iconoclastic events that occurred in European towns throughout the first half of the 16th century illustrate the Reformation’s transformati ..."
  3. "The Protestant Reformation’s treatment of religious iconography was intricately linked to prevailing social structures, sometimes reflecting and occas ..."
- LLM reason: "Knowledge needed: Historical context of Protestant iconoclasm, especially during the 16th century, and links between economic conditions and religious ..."

**Preliminary label: (b)** — Top-1 discusses economic repercussions of Protestant iconoclasm rather than economic reasons for it; the best gold stayed at 18 -> 19 (never lifted).

### 1a.9 — history `72564_153` (nDCG@10 0.000)

> Has a region/territory/country using the Western 7-day week ever got 'out-of-sync' for the day of the week? In a previous question on History Stack Exchange, it was reported that the cycle of days-of-the-week have continued uninterrupted since at least 60 AD. Do we know of any groups of people who, ...

- Gold (1 judged; best-placed shown): hybrid rank 397, final rank 397 — "Didn't it get lost somewhere along the line? This question comes frequently to the per­sonal worker, and although it may present no problem to the majority of us, it might help some if we discussed it ..."
- Mechanical label: (a)
- Our top 3:
  1. [gold of other topic] "Cultures vary in which days of the week are designated the first and the last, though virtually all have Saturday, Sunday or Monday as the first day. ..."
  2. "The seven-day weekly cycle has remained unbroken in Christendom, and hence in Western history, for almost two millennia, despite changes to the Coptic ..."
  3. "Today I found out why we have a seven day week and the origins of each day’s name. Two of the earliest known civilizations to use a seven day week wer ..."
- LLM reason: "Knowledge needed: Historical use of the seven-day week across cultures, especially in Europe, and whether any region used a different starting day (e. ..."

**Preliminary label: (e)** — The expansion recasts 'out of sync' as different first days of the week and invents a 1243-1267 England/France discrepancy; top-1 is about which day starts the week.

### 1a.10 — history `72370_163` (nDCG@10 0.000)

> At the beginning of the 20th century, how did Austria-Hungary and Russia's foreign policies conflict in the Balkans? I'm reading The Sleepwalkers: How Europe Went to War in 1914 by Christopher Clark. Either I missed something or it was omitted, but I don't understand how Russia and Austria-Hungary's ...

- Gold (2 judged; best-placed shown): hybrid rank 34, final rank 32 — "In 1908, the Austro-Hungarian Empire formally annexed Bosnia and Herzegovina, a move that significantly escalated tensions in the Balkans and among the Great Powers of Europe. This region had been und ..."
- Mechanical label: (b)
- Our top 3:
  1. "The original Franco-Russian alliance was formed to protect both France and Russia from a German attack. In the event of such an attack, both states wo ..."
  2. "The Austro-Hungarian Empire, headquartered at Vienna, was a largely rural, poor, multicultural state. It was operated by and for the Habsburg family, ..."
  3. "The Balkan Wars were two conflicts that took place in the Balkan Peninsula in southeastern Europe in 1912 and 1913. Four Balkan states defeated the Ot ..."
- LLM reason: "Knowledge needed: Understanding early 20th-century Balkan geopolitics, the Austro-Hungarian and Russian imperial ambitions, and the role of alliances ..."

**Preliminary label: (b)** — Best gold (1908 Bosnia annexation) moved only from hybrid 34 to 32; top-1 is about the Franco-Russian alliance and does not address the Austro-Russian Balkan conflict.

### 1a.11 — economics `43853_228` (nDCG@10 0.000)

> What are the justification of using 1990 or 2010 as benchmark in studies? Normally, many international studies and documents using multiple-of-10 years (for example 1990, 2010) as the benchmark year. For example: Dong,2019, p.899 used 1990 as the benchmark to calculate the Export Market Leniency Law ...

- Gold (3 judged; best-placed shown): hybrid rank 8, final rank 30 — "Researchers in NOAA’s Global Monitoring Division calculate the AGGI using air samples collected every week at about 40 remote sites around the world. Technicians use state-of-the-art instruments to me ..."
- Mechanical label: (b)
- Our top 3:
  1. [gold of other topic] "A base year refers to the base point in time of a time series. The most frequent use of a base year in economic data is in compiling price indices suc ..."
  2. "The failure to update base years is a serious problem which affects the perceived quality of GDP data. Data on a country's GDP are used continually to ..."
  3. [gold of other topic] "Data reported in current (or “nominal”) prices for each year are measured in the prices for that particular year. For example, current price estimates ..."
- LLM reason: "Knowledge needed: Historical data standardization, international development benchmarks, census cycles, and data reliability in global studies. Releva ..."

**Preliminary label: (b)** — Gold demoted from hybrid 8 to 30; top-1 (gold for another topic) defines base years for price indices but does not explain why round years such as 1990/2010 are chosen.

### 1a.12 — history `76694_86` (nDCG@10 0.000)

> How did the Catholic Church grow in power between Rome and the Middle Ages? I am not a historian, but I love learning history, and have loved it since middle school. One thing that was odd to me even back then, though, is that there seemed to be a "gap" in European history. What I mean by this is th ...

- Gold (16 judged; best-placed shown): hybrid rank 35, final rank 13 — "## Belief and Institutions We should start by charting the broad outlines of the place of the medieval church in Western Europe. I should start off by noting that this is a huge topic – as will swiftl ..."
- Mechanical label: (b)
- Our top 3:
  1. "With the decline and fall of the Roman Empire in the west, the papacy became a political player, first visible in Pope Leo's diplomatic dealings with ..."
  2. "After the Fall of Rome , the papacy served as a source of authority and continuity. In the absence of a magister militum living in Rome, even the cont ..."
  3. "After the Fall of Rome, the papacy served as a source of authority and continuity. In the absence of a magister militum living in Rome, even the contr ..."
- LLM reason: "Knowledge needed: Understanding the transition of political and religious authority in post-Roman Europe, focusing on the Church’s rise from late anti ..."

**Preliminary label: (c)** — Top-1 describes how the papacy became a political power after the fall of the western Roman Empire, which directly answers the question; golds at hybrid 9 and 12 were demoted to 40 and 18.

### 1a.13 — history `70583_271` (nDCG@10 0.000)

> How do we know when Nero was born? If I go onto Wikipedia , I can see an answer of when he was born. But I can't really follow the sources. How do historians know when Nero was born?

- Gold (1 judged; best-placed shown): hybrid rank 524, final rank 524 — "Suetonius was also a close friend and secretary of Emperor Hadrian, who granted him privileged access to the imperial archives and libraries. Suetonius was particularly interested in the lives and cha ..."
- Mechanical label: (a)
- Our top 3:
  1. "All three principal sources for Emperor Nero's reign, including Tacitus, were senators. However, unlike other historians, Tacitus was more lenient, tr ..."
  2. "All three principal sources for Emperor Nero s reign, including Tacitus, were senators. However, unlike other historians, Tacitus was more lenient, tr ..."
  3. "Nero was born Lucius Domitius Ahenobarbus in 37 CE, but he was renamed Nero Claudius Caesar Augustus when his mother, Agrippina, married Emperor Claud ..."
- LLM reason: "To know when Nero was born, historians rely on ancient Roman records, such as inscriptions, official documents, and contemporary accounts. The key con ..."

**Preliminary label: (a)** — Only gold (Suetonius' access to imperial archives) is at rank 524; the expansion cites the Historia Augusta and contradictory birth dates, but the top-3 (Tacitus, a Nero biography) do not visibly follow that error.

### 1a.14 — cardano `9250_104` (nDCG@10 0.000)

> Why does staking happen with a delay? In Cardano, AFAICU, at the beginning of an epoch a snapshot is taken of the end state of previous epoch to see who staked, how much and where. But it seems that that state is not used as for that current epoch but for the next one instead. Is there a particular ...

- Gold (2 judged; best-placed shown): hybrid rank 22, final rank 12 — "A snapshot Mark at epoch transition from EpochN to EpochN+1 will be used for the slot leader election process during EpochN+2, when it becomes Set. Finally, it is employed for rewards calculation duri ..."
- Mechanical label: (b)
- Our top 3:
  1. [gold of other topic] "Time periods in Cardano: Epochs, slots, and nominations The Cardano network has time periods called Epochs that last 432000 slots, and each slot lasts ..."
  2. [gold of other topic] "For example, if you delegate ADA coins to a pool, it will only show up after a new snapshot. Epochs are used as a specific accounting period for which ..."
  3. "Chains are divided into blocks of time called epoch’s and individual units of time within an epoch are slots. For each slot, a stake pool is assigned ..."
- LLM reason: "Knowledge needed: Understanding Cardano’s epoch-based staking, block production, and state transition timing. Relevant document topic: Cardano’s staki ..."

**Preliminary label: (b)** — Gold (snapshot used two epochs later) was lifted from hybrid 22 to 12 but not into the top 10; top-1 is a general epochs/slots description, not the reason for the delay.

### 1a.15 — hsm `18796_657` (nDCG@10 0.000)

> What was this mathematical colloquium event at Tulane and what year did it take place? Steven Krantz in his book Mathematical Apocrypha on page 14 writes: A famous mathematician was once invited to give a colloquium at Tulane University in New Orleans. During the ceremonial dinner, the great man let ...

- Gold (1 judged; best-placed shown): hybrid rank 52, final rank 52 — "The Tulane Conference Following the panel discussion, Douglas sought funding from the Sloan Foundation for a conference on calculus reform (Douglas, 1985b). The result was the "Conference/Workshop To ..."
- Mechanical label: (b)
- Our top 3:
  1. "Friday, May 24, 2024 The organizing commitee is pleased to invite you to the XXVIth ISM Graduate Student Conference! The colloquium will be held at th ..."
  2. "@Book{Lehto:1998:MBH, author = "Olli Lehto", title = "Mathematics Without Borders: a History of the {International Mathematical Union}", publisher = p ..."
  3. "Description: The aim of this symposium on the history of mathematics is to take the theme of ideas in social context and focus it on how status is acq ..."
- LLM reason: "The question refers to a fictional anecdote from Steven Krantz's book *Mathematical Apocrypha*, not a real historical event. No actual mathematical co ..."

**Preliminary label: (e)** — The expansion declares the Tulane anecdote fictional ('no real year or event exists'), denying the premise; top-1 is an unrelated 2024 graduate conference.

## 1b

### 1b.1 — history `62574_607_step3` (nDCG@10 0.000)

> Question: Is there any example of a monarch being presumed dead but returning after the heir ascended to the throne? Has there ever been a monarch is incorrectly believed to be dead—perhaps disappeared for many months, incorrectly ...
>
> Step: Cross-reference coronation dates and timelines from authoritative historical sources.

- Gold (1 judged; best-placed shown): hybrid rank not in pool, final rank not in top 1000 — "Despite it traditionally being the duty of a king to bear children, Richard I never had children. King Richard I did marry Berengaria, the daughter of the king of Navarre on May 12, 1191, but they nev ..."
- Mechanical label: (a)
- Our top 3:
  1. "B July 22, 2016 at 1:51 pmA great video Claire, exploring this concept. I’m in the camp of Queen Jane. The current monarch chose her as his heir and s ..."
  2. "The timing of the coronation has varied throughout British history. King Edgar's coronation was some 15 years after his accession in 959 and may have ..."
  3. "How can we know that legitimacy matters to English monarchs? The general principle of managing shared beliefs is well known. Public events—such as cor ..."
- LLM reason: "Time period: 16th–18th century Europe. Topic: Monarchs presumed dead, heir ascending, return of the true monarch. Key concept: Two monarchs simultaneo ..."

**Preliminary label: (e)** — The expansion fabricates presumed-dead monarchs (Charles II after Edgehill, Mary I in 1553) while the gold is about Richard I; top-1 follows the Tudor framing (Queen Jane).

### 1b.2 — bitcoin `123461_13_step2` (nDCG@10 0.000)

> Question: Implementing Conditional Fund Locking in Bitcoin Similar to Ethereum's Smart Contracts I'm familiar with how Ethereum allows users to lock funds in smart contracts, which can then be released under specific conditions us ...
>
> Step: Compare Bitcoin's time-locking features with Ethereum's Hashed TimeLock Contract (HTLC) pr

- Gold (2 judged; best-placed shown): hybrid rank 26, final rank 23 — "A Hash Time Locked Contract or HTLC is a class of payments that use hashlocks and timelocks to require that the receiver of a payment either acknowledge receiving the payment prior to a deadline by ge ..."
- Mechanical label: (b)
- Our top 3:
  1. "Una of the most interesting properties it has Bitcoin are time locks or timelock such as nLockTime. These types of functionalities allow users to defi ..."
  2. "Hash Timelock Contracts operate based on two fundamental cryptographic principles: hashlocks and timelocks. Together, these mechanisms form a secure a ..."
  3. "Una of the innovative functions it has Bitcoin known as Timelock. This is a tool that it serves to establish and specify certain conditions under whic ..."
- LLM reason: "Knowledge needed: Bitcoin’s time-locking mechanisms and comparison with Ethereum’s HTLC protocol. Relevant document topic: Bitcoin time-locking featur ..."

**Preliminary label: (c)** — Top-1 describes Bitcoin's time-lock features (nLockTime) and top-2 explains HTLC hashlocks/timelocks, i.e. the two sides of the comparison the step asks for.

### 1b.3 — history `56978_708_step1` (nDCG@10 0.000)

> Question: Were Soviets invited to the Marshall Islands to observe the first hydrogen bomb detonations? In 1952, did the US invite, or consider inviting, Russian scientist to observe the detonation of the first hydrogen bomb? These ...
>
> Step: Search declassified US government documents from 1952 related to the hydrogen bomb tests i

- Gold (2 judged; best-placed shown): hybrid rank 344, final rank 344 — "The first Ivy shot, codenamed Mike, was the first successful full-scale test of a multi-megaton thermonuclear weapon ("hydrogen bomb") using the Teller-Ulam design. Unlike later thermonuclear weapons, ..."
- Mechanical label: (a)
- Our top 3:
  1. "The USA could be confident that the USSR would learn about the hydrogen bomb test from atmospheric sampling. It's possible to detect extremely low lev ..."
  2. "The world was never the same after the United States leveled Hiroshima and Nagasaki in August 1945 with atomic bombs. Not only had perhaps 180,000 civ ..."
  3. "On August 30, 1961, the Soviet Union issued a statement that it was abandoning the test moratorium. It, of course, blamed the United States, claiming ..."
- LLM reason: "Knowledge needed: U.S. nuclear policy, Cold War diplomacy, declassified records on 1952 hydrogen bomb tests, and whether the USSR was informed of U.S. ..."

**Preliminary label: (c)** — Top-1 argues the USA knew the USSR would detect the H-bomb test by atmospheric sampling, which directly addresses whether Soviets needed to be invited.

### 1b.4 — cardano `840_139_step1` (nDCG@10 0.000)

> Question: When will all 45 billion coins be in circulation? I cannot find any accurate information with what speed and based on what formula the coins which are not in circulation will be in circulation and when (approximately) al ...
>
> Step: Identify official sources or governing bodies responsible for coin circulation schedules.

- Gold (1 judged; best-placed shown): hybrid rank not in pool, final rank not in top 1000 — "Emission schedule: The token release rate is set at 0.22% of the remaining reserve per epoch (approximately every 5 days), ensuring a gradual distribution of ADA until the cap is reached. Distribution ..."
- Mechanical label: (a)
- Our top 3:
  1. "When it comes to Bitcoin (BTC), its max supply is 21 million coins and since none of them have been burnt, Bitcoins circulating and total supply are t ..."
  2. "Cardano, being a popular blockchain platform, has a number of coins and tokens in circulation. To explore the current state of these coins and tokens, ..."
  3. "| Feature | Max Supply | Total Supply | Circulating Supply | | --- | --- | --- | --- | | Simple Definition | The absolute maximum number of coins that ..."
- LLM reason: "No coins are being tracked for a "45 billion coin" universal circulation timeline. Coins are not issued in such a fixed, global quantity with a set da ..."

**Preliminary label: (e)** — The expansion reads '45 billion coins' as physical coins (U.S. Mint, ECB) instead of Cardano's ADA supply; the gold is the ADA emission schedule.

### 1b.5 — bitcoin `124510_9_step4` (nDCG@10 0.000)

> Question: Can I use Relative Locktime (BIP 68) to send funds to myself that can only be spent after a specific time in Bitcoin? Context: I want to send funds to myself in Bitcoin but prevent them from being spent until a specified ...
>
> Step: Verify the state and restrictions of UTXOs before the locktime expires using blockchain an

- Gold (1 judged; best-placed shown): hybrid rank 76, final rank 76 — "Also part of the BIP68/112/113 soft fork was the CheckSequenceVerify opcode[8], which provides for relative locktime the same feature CLTV provides for absolute locktime. When the CSV opcode is called ..."
- Mechanical label: (b)
- Our top 3:
  1. "Transaction Locktime (nLocktime) From the beginning, bitcoin has had a transaction-level timelock feature. Transaction locktime is a transaction-level ..."
  2. "Since the activation of BIP-68, new consensus rules apply for any transaction containing an input whose nSequence value is less than 231 (bit 1 = 231) ..."
  3. "nSequence as a consensus-enforced relative timelock Since the activation of BIP-68, new consensus rules apply for any transaction containing an input ..."
- LLM reason: "Yes, Relative Locktime (BIP 68) allows a transaction to be spendable only after a certain number of blocks or time passes. A relevant document would d ..."

**Preliminary label: (b)** — Only gold (CSV / BIP68 opcode) sits at hybrid 76, outside the rerank pool; top-1 covers absolute nLocktime, while top-2/3 on BIP-68 look relevant.

### 1b.6 — quant `70819_1086_step2` (nDCG@10 0.000)

> Question: What are common ways to realistically simulate the stock market using historical market data? I am currently using the FinRL library to try to automate Trading using Reinforcement Learning. However, I wanted to understan ...
>
> Step: Search for examples of historical data usage in stock market simulations, including method

- Gold (1 judged; best-placed shown): hybrid rank 940, final rank 940 — "ARIMA excels in the stock market by analyzing historical data to predict future stock prices, thereby aiding in short-term investment decisions. It integrates three essential components: Autoregressio ..."
- Mechanical label: (a)
- Our top 3:
  1. "Unrelated to FinRL I read here that you could do it with geometric Brownian motion like this: Assume you have historical stock data $S\_0, \dots, S\_N ..."
  2. "The simulation of financial time series is crucial for designing investment strategies and financial products. Two approaches are commonly used in pra ..."
  3. "The simulation of financial time series is crucial for designing investment strategies and financial products. Two approaches are commonly used in pra ..."
- LLM reason: "A relevant document would discuss stock market simulation methods using historical data, focusing on time-driven simulation and statistical models. Ke ..."

**Preliminary label: (a)** — Only gold (ARIMA) is at rank 940; top-1 appears to be the question post's own GBM recipe and top-2 a survey of simulation approaches, so the miss is mostly about the narrow gold.

### 1b.7 — genealogy `2975_328_step3` (nDCG@10 0.000)

> Question: Where do I find information about arranged employment in Australia in the 1850s? Many immigrants from England worked for the Hon. Edward Flood M.P. in the 1850s. They were employed mainly as sheep overseers, station hand ...
>
> Step: Review secondary sources analyzing labor practices and immigrant experiences in 1850s Aust

- Gold (1 judged; best-placed shown): hybrid rank 322, final rank 322 — "In 1839 Henry Parkes and his wife, Clarinda, were two of the thousands of assisted migrants. Parkes would later be Premier of New South Wales and one of the fathers of Federation. In England he had tr ..."
- Mechanical label: (a)
- Our top 3:
  1. "[*Among Australia's Pioneers Chinese Indentured Pastoral Workers on the Northern Frontier 1848 to c.1880*](http://www.amazon.com/gp/product/1452524807 ..."
  2. "Work such as hers could not be undone. The Land and Emigration Commissioners renewed in 1844 their sending of selected migrants—agricultural labourers ..."
  3. "AS there were wicket-keepers before Blackham, so there were labour unions before the gold discoveries. Convict artisans and labourers had, without uni ..."
- LLM reason: "Knowledge needed: Labor practices, immigrant employment patterns, and migration history in 19th-century Australia, specifically the 1850s. Relevant do ..."

**Preliminary label: (a)** — Only gold (assisted migrants, Henry Parkes) is at rank 322; top-3 are topically close (indentured pastoral workers, 1844-5 assisted emigration) but not about arranged employment of English migrants.

### 1b.8 — history `70583_271_step1` (nDCG@10 0.000)

> Question: How do we know when Nero was born? If I go onto Wikipedia , I can see an answer of when he was born. But I can't really follow the sources. How do historians know when Nero was born?
>
> Step: Identify primary sources or ancient texts that reference Nero's birth, such as Roman records or writings by contemporary historians.

- Gold (1 judged; best-placed shown): hybrid rank 105, final rank 105 — "Suetonius was also a close friend and secretary of Emperor Hadrian, who granted him privileged access to the imperial archives and libraries. Suetonius was particularly interested in the lives and cha ..."
- Mechanical label: (a)
- Our top 3:
  1. "All three principal sources for Emperor Nero s reign, including Tacitus, were senators. However, unlike other historians, Tacitus was more lenient, tr ..."
  2. "All three principal sources for Emperor Nero's reign, including Tacitus, were senators. However, unlike other historians, Tacitus was more lenient, tr ..."
  3. "Nero was born Lucius Domitius Ahenobarbus in 37 CE, but he was renamed Nero Claudius Caesar Augustus when his mother, Agrippina, married Emperor Claud ..."
- LLM reason: "To know when Nero was born, historians rely on primary sources like Roman records, inscriptions, or writings by contemporary historians (e.g., Suetoni ..."

**Preliminary label: (c)** — Top-1 names the principal ancient sources for Nero's reign (Tacitus and two others), which is what the step asks for, although it does not mention his birth.

### 1b.9 — history `69940_313_step3` (nDCG@10 0.000)

> Question: Is there any evidence that the US strategy at Midway was deliberate? The Battle of Midway was a crushing US victory over the Empire of Japan that, at face value, appears to be due to good SIGINT and a huge amount of luck ...
>
> Step: Cross-reference Japanese accounts or intelligence to understand their perspective on US ac

- Gold (1 judged; best-placed shown): hybrid rank 87, final rank 87 — "The operational effect on the Battle of Midway from their disjointed Marine Corps and Army aircraft, and later those of U.S. carrier torpedo squadrons, however, was significant. Japanese Striking Forc ..."
- Mechanical label: (b)
- Our top 3:
  1. "So, first off, I would recommend Shattered Sword: The untold Story of the Battle of Midway by John Lundstrom. While it focuses on the misconceptions a ..."
  2. "Admiral Yamamoto viewed the operation against Midway as the potentially decisive battle of the war, which could lead to the destruction of American st ..."
  3. "Having learned important lessons at Coral Sea, the United States Navy was prepared when the Japanese navy under Admiral Isoroku Yamamoto launched an o ..."
- LLM reason: "Knowledge needed: Understanding US strategic intent at Midway, especially regarding air raid tactics, and Japanese operational responses. Relevant doc ..."

**Preliminary label: (c)** — Top-1 recommends 'Shattered Sword', the standard account of Midway from the Japanese side, which fits the step's request for Japanese perspectives.

### 1b.10 — history `56929_710_step1` (nDCG@10 0.000)

> Question: What evidence is there of tank-vs-tank combat in Asia during the second world war? It has been known that the Japanese army during the Second World War did not value tanks highly and as such they were not always used eff ...
>
> Step: Identify key battles in Asia during the Second World War where Japanese and Allied forces

- Gold (1 judged; best-placed shown): hybrid rank 201, final rank 201 — "The Battles of Khalkhin Gol (Russian: Бои на Халхин-Голе; Mongolian: Халхын голын байлдаан) were the decisive engagements of the undeclared Soviet–Japanese border conflicts involving the Soviet Union, ..."
- Mechanical label: (a)
- Our top 3:
  1. "Type 95 Ha-Go tanks served during the Battle of Khalkhin Gol (Nomonhan) against the Soviet Red Army in 1939, against the British Army in Burma and Ind ..."
  2. "While combat in the European Theater of Operations (ETO) consisted of high-profile armored warfare, the mainly naval nature of the Pacific Theater of ..."
  3. "Type 95 Ha-Go tanks served during the Battle of Khalkhin Gol ( Nomonhan ) against the Soviet Red Army in 1939, 33 against the British Army in Burma an ..."
- LLM reason: "Knowledge needed: Key battles in Asia where Japanese and Allied forces clashed in tank engagements during WWII. Relevant document topic: WWII battles ..."

**Preliminary label: (c)** — Top-1 lists Type 95 Ha-Go engagements at Khalkhin Gol and in Burma, i.e. the key battles the step asks for (the gold is the Khalkhin Gol article at rank 201).

### 1b.11 — quant `74929_1079_step2` (nDCG@10 0.000)

> Question: Daily quotes TIPS (treasury inflation protected securities) data I am looking for historical quotes for US TIPS (treasury inflation protection security). What is a reliable source of data to get this information? Here's ...
>
> Step: Search for datasets or reports that include daily quotes for both active and matured TIPS.

- Gold (1 judged; best-placed shown): hybrid rank 359, final rank 359 — "Featuring 1.7 million end-of-day observations on nearly 7,000 Treasury instruments (bills, notes, bonds) Daily data since 1961 and month-end data since 1925 (monthly) Includes many supplemental files, ..."
- Mechanical label: (a)
- Our top 3:
  1. "Keywords: Yield curve, treasury market, inflation compensation, risk premia For over ten years, the U.S. Treasury has issued index-linked debt. Federa ..."
  2. "TIPS were first auctioned by the U.S. Treasury in January 1997. As of June 30, 2021, the market value of Treasury Inflation Protected Securities outst ..."
  3. "For over ten years, the U.S. Treasury has issued index-linked debt. Federal Reserve Board staff have fitted a yield curve to these indexed securities ..."
- LLM reason: "Knowledge needed: Reliable, daily historical data for US TIPS, including matured securities, from a trusted source. Relevant document topic: US Treasu ..."

**Preliminary label: (a)** — Only gold (CRSP Treasury database) is at rank 359; top-1 is the Fed's fitted TIPS yield curve, a daily dataset but not quotes for individual and matured TIPS.

### 1b.12 — history `68862_380_step3` (nDCG@10 0.000)

> Question: Could the "Taffy" Groups have been reinforced by air during the battle of Leyte Gulf? During the Battle for Leyte Gulf , most elements of the American fleet fought two "side" groups of the Japanese fleet to the south and ...
>
> Step: Cross-reference historical accounts of Taffy groups' engagement and resource depletion dur

- Gold (1 judged; best-placed shown): hybrid rank 47, final rank 15 — "situation looks almost hopeless and the group has requested air and surface aid from Admiral Stump. There is nothing more he can do. All of his available aircraft, 24 Avenger torpedo planes with Wildc ..."
- Mechanical label: (b)
- Our top 3:
  1. "Author’s Dedication To my mother, Betty Lardas, who went to join my late father on March 28, 2021. Ave atque vale. AIR CAMPAIGN CONTENTS INTRODUCTION ..."
  2. "tl;dr Halsey receives news of the danger at 0800. By 0930 Kurita is already withdrawing. At best a one-way strike could be organized to attack Kurita ..."
  3. "Taffy 3 consisted of six 18-knot escort carriers, known as baby flattops, accompanied by three destroyers and four destroyer escorts. Since no doctrin ..."
- LLM reason: "Knowledge needed: Logistics of aircraft refueling, range limitations, and historical engagement details of Taffy groups during the Battle of Leyte Gul ..."

**Preliminary label: (b)** — Gold lifted from hybrid 47 to 15 but not into the top 10; top-1 is book front matter (dedication and contents), not content about the Taffy groups.

### 1b.13 — history `68862_380_step1` (nDCG@10 0.000)

> Question: Could the "Taffy" Groups have been reinforced by air during the battle of Leyte Gulf? During the Battle for Leyte Gulf , most elements of the American fleet fought two "side" groups of the Japanese fleet to the south and ...
>
> Step: Locate primary sources detailing fleet positions and air operations during the Battle of L

- Gold (1 judged; best-placed shown): hybrid rank 7, final rank 15 — "The Composition of Taffy 3 Taffy 3 was comprised of six escort carriers, three destroyers, and four destroyer escorts, all tasked with providing air support for the amphibious landings at Leyte Gulf, ..."
- Mechanical label: (b)
- Our top 3:
  1. "Author’s Dedication To my mother, Betty Lardas, who went to join my late father on March 28, 2021. Ave atque vale. AIR CAMPAIGN CONTENTS INTRODUCTION ..."
  2. "Taffy 3 consisted of six 18-knot escort carriers, known as baby flattops, accompanied by three destroyers and four destroyer escorts. Since no doctrin ..."
  3. "By contrast, Admiral Kurita’s more powerful force debouched from San Bernardino Strait at 0035, expecting a fight but finding no ships guarding the st ..."
- LLM reason: "Knowledge needed: Fleet movements, air range, refueling capabilities, and operational logistics of U.S. and Japanese forces during the Battle of Leyte ..."

**Preliminary label: (b)** — Gold demoted from hybrid 7 to 15; top-1 is the same book front matter as in the step-3 topic.

### 1b.14 — cardano `4225_128_step2` (nDCG@10 0.000)

> Question: Is there a way for a validator to get the current time? Is it possible for a validator to get the current time without it being passed in via the redeemer? My validator is heavily dependent on the time being correct so i ...
>
> Step: Identify authoritative sources or standards that describe time synchronization and validat

- Gold (1 judged; best-placed shown): hybrid rank 31, final rank 12 — "How do Plutus scripts handle time? Plutus scripts get access to the transaction validity range, defined by its creator. When defining the validity range, a creator can decide that a transaction is val ..."
- Mechanical label: (b)
- Our top 3:
  1. [gold of other topic] "The limits of the validity interval are expressed in real time (POSIXTime), rather than slots, and the conversion from slots to real time is done by c ..."
  2. [gold of other topic] "The limits of the validity interval are expressed in real time (POSIXTime), rather than slots, and the conversion from slots to real time is done by c ..."
  3. [gold of other topic] "The limits of the validity interval are expressed in real time (POSIXTime), rather than slots, and the conversion from slots to real time is done by c ..."
- LLM reason: "Knowledge needed: Time synchronization standards in blockchain systems, especially how validators obtain accurate time without relying on external inp ..."

**Preliminary label: (c)** — Top-1 (gold for another topic) explains that validity intervals are in POSIXTime converted by consensus, which is how a Plutus validator gets the time; the gold was lifted from 31 to 12.

### 1b.15 — history `70284_294_step1` (nDCG@10 0.000)

> Question: Are there historical examples of civilization reaction to learning about impending doom? By impending doom, I mean events that are deadly, imminent, inexorable and unfightable (i.e. a volcano eruption, a deadly disease, ...
>
> Step: Identify historical events that qualify as 'impending doom' (e.g., volcanic eruptions, pan

- Gold (3 judged; best-placed shown): hybrid rank not in pool, final rank not in top 1000 — "### Legends There are many legends in Greece surrounding the Fall of Constantinople. It was said that the partial lunar eclipse that occurred on 22 May 1453 represented a fulfilment of a prophecy of t ..."
- Mechanical label: (a)
- Our top 3:
  1. "This is a pretty good place to apply Hanlon's Razor: Never attribute to malice that which is adequately explained by stupidity. While this probably ha ..."
  2. "My choice of reading over the last few weeks has narrowed to three books in my own library on the subject of the Black Death, the mysterious high mort ..."
  3. "Plague outbreaks would continue long after the Black Death pandemic of the 14th century but none would have the same psychological impact resulting in ..."
- LLM reason: "Knowledge needed: Historical events where a civilization received advance warning of an inevitable, deadly disaster (e.g., volcanic eruption, pandemic ..."

**Preliminary label: (a)** — No gold (fall of Constantinople, Titanic) in the first-stage pool; the top-3 are about pandemics, which the step itself suggests, so the expansion is not clearly at fault.

## 2a

### 2a.1 — hardware `ex_15430_turn_4` (nDCG@10 0.000)

> CURRENT: Can you actually run extra monitors off the 5600G’s graphics once you add a GPU, or does it switch over completely?
>
> History: Q: In building a PC with a Ryzen 5600G or 5600X, does Crossfire or SLI matter anymore when thinking about future GPU upgrades? A: SLI and Crossfire really don't ...

- Gold (1 judged; best-placed shown): hybrid rank 52, final rank 52 — "Short answer is no. There are things called hybrid crossfire as mentioned by others in above post but AMD have long stop doing it. And even that is very limited since it can only be done with low end ..."
- Mechanical label: (b)
- Our top 3:
  1. "However, it's essential to ensure that your motherboard has the necessary PCIe slots and power supply capacity to accommodate the graphics card you pl ..."
  2. [gold of other topic] "The Ryzen 5 5600G is compatible with a wide range of graphics cards. It supports PCIe 4.0, which is the latest version of the PCIe interface, offering ..."
  3. "The Ryzen 5 5600G comes with integrated graphics, but if you want to enhance your gaming or graphics-intensive tasks, you can use a dedicated graphics ..."
- LLM reason: "Knowledge needed: Understanding of Ryzen 5600G’s integrated graphics, PCIe support, and how discrete GPU integration works. Relevant document topic: R ..."

**Preliminary label: (b)** — Only gold (hybrid CrossFire no longer supported) sits at hybrid 52, outside the rerank pool; top-1 is generic PCIe and driver advice, not about using iGPU outputs alongside a GPU.

### 2a.2 — biology `6_turn_5` (nDCG@10 0.000)

> CURRENT: What happens if a species puts more energy into staying healthy instead of having kids?
>
> History: Q: In evolution, why doesn’t natural selection care much about traits that show up after we have kids? A: Natural selection mainly acts on traits that affect us ...

- Gold (5 judged; best-placed shown): hybrid rank 26, final rank 16 — "Evidence[edit] Growth and aging[edit] There is a large body of evidence indicating the negative effects of growth on longevity across many species. As a general rule, individuals of a smaller size gen ..."
- Mechanical label: (b)
- Our top 3:
  1. [gold of other topic] "Adaptivity and senescence[edit] An antagonistically pleiotropic gene can be selected for if it has beneficial effects in early life while having its n ..."
  2. [gold of other topic] "The antagonistic pleiotropy hypothesis was first proposed by George C. Williams in 1957 as an evolutionary explanation for senescence. Pleiotropy is t ..."
  3. [gold of other topic] "Role in disease[edit] The survival of many serious genetic disorders in our long evolutionary history has led researchers to reassess the role of anta ..."
- LLM reason: "Knowledge needed: Understanding evolutionary biology, particularly antagonistic pleiotropy and natural selection pressures on genes with early benefit ..."

**Preliminary label: (e)** — The expansion anchors on the earlier turn's antagonistic pleiotropy instead of the maintenance-versus-reproduction trade-off (disposable soma, the gold); the top-3 are all antagonistic pleiotropy passages.

### 2a.3 — economics `47_turn_2` (nDCG@10 0.000)

> CURRENT: What happens if banks start earning less from loans—do they just cut back on lending?
>
> History: Q: In banking, how do low interest rates affect how much banks want to lend? A: From what’s explained, low interest rates are connected to higher profits and ma ...

- Gold (1 judged; best-placed shown): hybrid rank 153, final rank 153 — "yi s.t. p1y1 + p2y2 = 1 and y1/y2 = (p1/p2)−σ  (5) The solution to this problem can be written in terms of state variable s = |z1 − z2| ∈ Z≥0 that captures the productivity gap between the two firms. ..."
- Mechanical label: (a)
- Our top 3:
  1. "Econometrica, Vol. 90, No. 1 (January, 2022), 193–221 LOW INTEREST RATES, MARKET POWER, AND PRODUCTIVITY GROWTH ERNEST LIU Department of Economics, Pr ..."
  2. "consumers’ assets from government bonds to deposits and an increase in both deposits and government bonds on the commercial banks’ balance sheet. (3) ..."
  3. "Currency Deposits So the buyer’s bank will in practice seek to attract or retain new deposits (and reserves) — in the example shown here, from the sel ..."
- LLM reason: "Knowledge needed: Understanding bank incentives, loan profitability, and how earnings affect lending behavior. Relevant document topic: Bank lending b ..."

**Preliminary label: (a)** — Only gold (a model passage on a productivity gap between firms) is at rank 153; top-1 is the title page of a paper on low interest rates and market power, not about bank lending.

### 2a.4 — earth_science `20_turn_1` (nDCG@10 0.000)

> CURRENT: In planetary geology, how do divergent boundaries actually create new oceanic plates?
>
> History: No previous conversation.

- Gold (1 judged; best-placed shown): hybrid rank 134, final rank 134 — "part4 ------------------- Stability[edit] Triple junctions may be described and their stability assessed without use of the geological details but simply by defining the properties of the ridges, tren ..."
- Mechanical label: (a)
- Our top 3:
  1. "strong>divergent boundary occurs when two tectonic plates move away from each other. Along these boundaries, earthquakes are common and magma (molten ..."
  2. "part1 ------------------- A mid-ocean ridge (MOR) is a seafloor mountain system formed by plate tectonics. It typically has a depth of about 2,600 met ..."
  3. "part3 ------------------- Types of plate boundaries Main article: List of tectonic plate interactions Three types of plate boundaries exist, character ..."
- LLM reason: "To answer this, one needs knowledge of plate tectonics, specifically how magma rises at divergent boundaries and solidifies to form new oceanic crust. ..."

**Preliminary label: (c)** — Top-1 explains that magma rises at divergent boundaries and solidifies into new oceanic crust, a direct answer, while the only gold is about triple-junction stability.

### 2a.5 — drones `ex_2271_turn_1` (nDCG@10 0.000)

> CURRENT: In drone building, can the same ESC handle both high Kv and low Kv brushless motors without any issues?
>
> History: No previous conversation.

- Gold (2 judged; best-placed shown): hybrid rank 14, final rank 22 — "To select the appropriate ESC for your FPV drone, ensure you understand the requirements: the ESC should be compatible with your battery's voltage and should handle the current draw of your chosen mot ..."
- Mechanical label: (b)
- Our top 3:
  1. "Will different brushless motor sizes work with the same flight controller and esc - Drones and Model Aircraft Stack Exchange Stack Internal Knowledge ..."
  2. "Choosing ESCs requires understanding several specifications. Current rating indicates how many amps the ESC can handle continuously. A 30A ESC handles ..."
  3. "If they stutter or otherwise don't spin up reliably, you may need to adjust the timing settings in the ESC firmware. This controls when the motor wind ..."
- LLM reason: "Knowledge needed: Understanding how Electronic Speed Controllers (ESCs) interact with motor Kv ratings, particularly regarding current handling, therm ..."

**Preliminary label: (c)** — Top-1 is a Stack Exchange thread on using different brushless motors with the same ESC and top-3 discusses ESC timing for low-Kv motors; the gold was demoted from 14 to 22.

### 2a.6 — earth_science `9_turn_8` (nDCG@10 0.000)

> CURRENT: How did it end up that the U.S. started calling the solstice the first day instead of the middle?
>
> History: Earlier discussion covered: Turn 1: In seasonal calendars, how do earlier summer starts in Celtic and Chinese traditions shape their Midsummer festivals?; Turn ...

- Gold (1 judged; best-placed shown): hybrid rank 5, final rank 16 — "part3 ------------------- Four-season reckoning Four Seasons by Alphonse Mucha (1897) Most calendar-based partitions use a four-season model to demarcate the warmest and coldest seasons, which are fur ..."
- Mechanical label: (b)
- Our top 3:
  1. "used in a wider sense, as the date (day) that such a passage happens. The solstices, together with the equinoxes, are connected with the seasons. In s ..."
  2. "is still ceremonially observed in Ireland and some East Asian countries. Summer is defined as the quarter of the year with the greatest insolation and ..."
  3. "part1 ------------------- A solstice is an event that occurs when the Sun reaches its most northerly or southerly excursion relative to the celestial ..."
- LLM reason: "Knowledge needed: Understanding historical and cultural views of solstices, seasonal definitions, and how calendars evolved. Relevant document topic: ..."

**Preliminary label: (b)** — Gold demoted from hybrid 5 to 16; top-1 notes that solstices are season starts in some languages and midpoints in others, but not how the U.S. convention arose.

### 2a.7 — politics `ex_93094_turn_1` (nDCG@10 0.000)

> CURRENT: In wartime reporting, why do governments often limit foreign press access, and how much is that about security concerns?
>
> History: No previous conversation.

- Gold (5 judged; best-placed shown): hybrid rank 31, final rank 29 — "The First World War presents an example of governmental censoring on a national scale. The government restricted publishing within the United States in addition to censoring reports from the war. The ..."
- Mechanical label: (b)
- Our top 3:
  1. "Countries may have specific national security laws that allow for censorship and restrictions on press freedom during wartime These laws often aim to ..."
  2. "There is an ongoing tension between journalists' desires to report on conflicts and military actions, and military concerns about security. Generally ..."
  3. "But, according to Shaw, the Secretary of Defense has said, �these principles may have to be �tweaked� given the unusual nature of this war�. And gover ..."
- LLM reason: "To answer this, one needs knowledge of media policy, wartime communication strategies, and national security practices. A relevant document would disc ..."

**Preliminary label: (c)** — Top-1 explains wartime national-security laws that restrict press freedom to protect operations and classified information, which answers the question.

### 2a.8 — medicalsciences `ex_34769_turn_3` (nDCG@10 0.000)

> CURRENT: I wonder if losing sleep makes it easier to put the weight back on, even after dieting?
>
> History: Q: In dieting, does not getting enough sleep change whether you lose more fat or more muscle? A: Yes, not getting enough sleep while dieting can really change w ...

- Gold (5 judged; best-placed shown): hybrid rank 21, final rank 17 — "This study examined whether experimental sleep restriction, designed to approximate the short sleep times of a growing number of people in modern society, may compromise the effect of reduced-calorie ..."
- Mechanical label: (b)
- Our top 3:
  1. "Lack of sleep can have a serious impact on your ability to lose weight. As a matter of fact, you may even pack on a few extra pounds as a direct resul ..."
  2. "One of the most direct links between sleep and weight loss lies in the hormonal shifts that occur when sleep is compromised. Two hormones – ghrelin an ..."
  3. "Even with calorie control and regular physical activity, sleep debt can create a physiological environment that resists fat loss. One key issue is the ..."
- LLM reason: "Knowledge needed: Understanding the link between sleep, appetite hormones, metabolism, and weight regain after dieting. Relevant document topic: Sleep ..."

**Preliminary label: (c)** — Top-1 says sleep loss hampers weight loss and can add pounds, and top-2 covers ghrelin/leptin, both addressing weight regain after dieting.

### 2a.9 — medicalsciences `ex_34029_turn_2` (nDCG@10 0.000)

> CURRENT: Is that why taking enzymes by mouth only works when the enzyme acts outside cells?
>
> History: Q: In erythropoietic protoporphyria, why is it so hard to treat the disease by just giving the missing ferrochelatase enzyme? A: It's tough to treat erythropoie ...

- Gold (2 judged; best-placed shown): hybrid rank 7, final rank 16 — "Among other approaches, enzyme replacement therapy (ERT) has advanced to the clinic and represents a beneficial strategy for 8 out of the 50–60 known LDs. However, despite its value, current ERT suffe ..."
- Mechanical label: (b)
- Our top 3:
  1. "Ferrochelatases either utilize protoporphyrin IX or coproporphyrin III as one substrate and ferrous iron as the other substrate ( Figure 1 ). FIGURE 1 ..."
  2. "Section 1 reviews the biology of lysosomes as important cellular organelles, offering information about the composition, structural and functional cha ..."
  3. "Furthermore, heme B is found in cytochrome b , a key component in Q-cytochrome c oxidoreductase (complex III) in oxidative phosphorylation . [ 4 ] Str ..."
- LLM reason: "Knowledge needed: Understanding enzyme function, cellular localization, and enzyme delivery limitations. Relevant document topic: Enzyme therapy and c ..."

**Preliminary label: (b)** — Gold demoted from hybrid 7 to 16; top-1 is about ferrochelatase substrates in mitochondria (the previous turn's topic), not about oral enzyme therapy.

### 2a.10 — medicalsciences `ex_34029_turn_1` (nDCG@10 0.000)

> CURRENT: In erythropoietic protoporphyria, why is it so hard to treat the disease by just giving the missing ferrochelatase enzyme?
>
> History: No previous conversation.

- Gold (2 judged; best-placed shown): hybrid rank 28, final rank 42 — "Ferrochelatase catalyses the eighth and terminal step in the biosynthesis of heme, converting protoporphyrin IX into heme B. It catalyses the reaction: Summary of heme B biosynthesis—note that some re ..."
- Mechanical label: (b)
- Our top 3:
  1. "Two inborn errors of heme biosynthesis, erythropoietic protoporphyria (EPP, OMIM #177000) and X-linked erythropoietic protoporphyria (XLEPP, OMIM #300 ..."
  2. "In summary, inhibition of ferrochelatase has been used to improve ALA-based PDT against prostate cancer ( Fukuhara et al., 2013 ) and reduce choroidal ..."
  3. "Erythropoietic protoporphyria (EPP) is an inherited cutaneous porphyria caused by reduced expression of ferrochelatase, the enzyme that catalyzes the ..."
- LLM reason: "To answer this, one must understand the biochemical basis of erythropoietic protoporphyria (EPP), specifically that the missing ferrochelatase enzyme ..."

**Preliminary label: (b)** — Gold demoted from hybrid 28 to 42; top-1 describes the genetics of EPP but not why giving the missing enzyme fails.

### 2a.11 — earth_science `106_turn_3` (nDCG@10 0.000)

> CURRENT: Is that why deserts really started spreading during the Cenozoic, when things cooled down?
>
> History: Q: In ancient deserts, how did Pangaea's interior help create the first really dry, non-icy deserts? A: Pangaea's interior became really dry because it was so f ...

- Gold (1 judged; best-placed shown): hybrid rank 2, final rank 20 — "desert - Children's Encyclopedia (Ages 8-11) desert - Student Encyclopedia (Ages 11 and up) Written by Jeremy M.B. Smith Associate Professor of Geography and Planning, University of New England, Armid ..."
- Mechanical label: (b)
- Our top 3:
  1. [gold of other topic] "The global geography of the Permian included massive areas of land and water. By the beginning of the Permian, the motion of the Earth's crustal plate ..."
  2. "open between the continental fragments. This process of continental rifting has taken place about 250 million years ago between South America and Afri ..."
  3. "part5 ------------------- History of the theory Summary Detailed map showing the tectonic plates with their movement vectors. The development of the t ..."
- LLM reason: "Knowledge needed: Understanding climate evolution, continental drift, and the Cenozoic cooling trend. Relevant document topic: Climate change during t ..."

**Preliminary label: (b)** — Gold demoted from hybrid 2 to 20; the top-3 are about Pangaea and the Permian (the previous turn's topic) rather than Cenozoic cooling and desert spread.

### 2a.12 — politics `ex_89563_turn_4` (nDCG@10 0.000)

> CURRENT: Is UNRWA even going to be able to send staff or supplies into Gaza once these new rules kick in?
>
> History: Q: In Gaza's education system, what is Israel planning to do about schools and teachers now that UNRWA is being banned? A: Israel is planning to make big change ...

- Gold (2 judged; best-placed shown): hybrid rank 20, final rank 20 — "In a seeming response to the international criticism, Prime Minister Benjamin Netanyahu's office said Israel was prepared to work with international partners, both in the 90 days before the legislatio ..."
- Mechanical label: (b)
- Our top 3:
  1. "If the legislation is implemented, aid to Gaza could be strangled and all UNRWA operations in the occupied territories paralyzed. Israel will reject a ..."
  2. "The ban on UNRWA does not only create a gap in its core role of providing protection and care for Palestinian refugees, but it also leads to direct an ..."
  3. "Israeli Prime Minister Benjamin Netanyahu instructed authorities to begin the immediate enforcement of a law banning the UN’s agency for Palestinian r ..."
- LLM reason: "Knowledge needed: Understanding current travel restrictions, Israeli-Gaza policies, and UNRWA’s operational capacity under new rules. Relevant documen ..."

**Preliminary label: (c)** — Top-1 states that under the legislation Israel will refuse coordination, UNRWA staff lose immunity and access may be denied, which directly answers the turn.

### 2a.13 — law `ex_106319_turn_4` (nDCG@10 0.000)

> CURRENT: What happens if Spirit’s already done everything on their end—can they still sell off the right to future payments?
>
> History: Q: In airline bankruptcies, is it possible for lease contracts to be transferred to another airline even if the original contract doesn’t allow it? A: Yes, in a ...

- Gold (1 judged; best-placed shown): hybrid rank 66, final rank 66 — "By an assignment, an obligee (one who has the right to receive a contract benefit) transfers a right to receive a contract benefit owed by the obligor (the one who has a duty to perform) to a third pe ..."
- Mechanical label: (b)
- Our top 3:
  1. "If a lienholder agrees to such treatment, it usually does so on the condition that its lien attaches to the proceeds of the sale. The other conditions ..."
  2. [gold of other topic] "Section 365 of the Bankruptcy Code — "Rejection" vs. "Assumption" vs. "Assumption and Assignment." A buyer in a Section 363 Sale has wide latitude to ..."
  3. "A Section 363 Sale process provides a bidder with the ability to select favorable contracts, licenses, leases, or other agreements that will be “assum ..."
- LLM reason: "Knowledge needed: Understanding how airline lease assignments work in bankruptcy, especially regarding assignment restrictions and court approval. Rel ..."

**Preliminary label: (e)** — The expansion stays on airline lease assignment in bankruptcy (the earlier turn) while the turn asks about assigning a right to future payment after full performance, which is the subject of the gold (hybrid 66).

### 2a.14 — drones `ex_2424_turn_4` (nDCG@10 0.000)

> CURRENT: I’m curious—do things like humidity or open water actually mess with the signal that much at that distance?
>
> History: Q: In drone flight range, do fixed wing drones usually go farther than multirotor drones if they use the same radio and battery setup? A: Fixed-wing drones usua ...

- Gold (4 judged; best-placed shown): hybrid rank 70, final rank 70 — "Commercial drones, often used for industrial applications like mapping, inspections, or filmmaking, generally have longer ranges. For example, the DJI Inspire 2 can fly up to 7 kilometers (4.3 miles), ..."
- Mechanical label: (b)
- Our top 3:
  1. "Cellular and Satellite Communication: Advanced drones, like the JOUAV CW-15 and CW-80E, can leverage cellular networks or satellite communications for ..."
  2. "All aircraft of any type use communications systems between the aircraft and the ground using radio frequency (RF). Some use cell phone connections, s ..."
  3. "Optimize Antenna Placement and Selection One of the most straightforward ways to boost your drone’s range is by optimizing the antennas: Antenna Posit ..."
- LLM reason: "Knowledge needed: Understanding how environmental factors like humidity and open water affect radio signal propagation over distance. Relevant documen ..."

**Preliminary label: (b)** — Golds (general drone range articles) start at hybrid 70, outside the rerank pool; top-1 is about cellular/satellite links, not humidity or water effects.

### 2a.15 — psychology `36_turn_1` (nDCG@10 0.000)

> CURRENT: In sexual orientation, is there real evidence that genetics, like the Xq28 region, play a role in being gay?
>
> History: No previous conversation.

- Gold (1 judged; best-placed shown): hybrid rank 74, final rank 74 — "SCIENCE sciencemag.org There are still many questions to be addressed. Plants have a remarkable ability to distinguish between friends and foes, allowing Rhizobia to enter the root while keeping other ..."
- Mechanical label: (b)
- Our top 3:
  1. "immunization to sex-specific proteins (4). Work in the 1990s isolated a relationship with the Xq28 region on the X chromosome (5, 6). Subsequent studi ..."
  2. "to genetic determinism or to resent this reduction. Attributing same-sex orientation to genetics could enhance civil rights or reduce stigma. Converse ..."
  3. "et al. found that genetics could eventually account for an upper limit of 8 to 25% of same-sex sexual behavior of the population. However, when all of ..."
- LLM reason: "Knowledge needed: Scientific evidence on genetic influences in sexual orientation, especially specific chromosomal regions like Xq28. Relevant documen ..."

**Preliminary label: (c)** — Top-1 summarises the 1990s Xq28 linkage findings and twin heritability estimates, a direct answer; the only gold (hybrid 74) starts with a Science passage on plant-Rhizobia signalling.

## Observations (preliminary)

- **Late-stage losses are at least as common as recall misses.** Mechanically, 30 of 45 topics are (b) and only 15 are (a). Of the 16 topics that keep a final (b) label, 8 look demoted (best gold ranked worse after ReasonEmbed / reranking), 5 have the best gold at hybrid rank 51-100 and apparently outside the rerank pool (final rank = hybrid rank), and 3 were lifted but not into the top 10. In 9 of the 45 topics a gold was already in the hybrid top 10 (1a: 5, 1b: 1, 2a: 3) and was pushed out, so the hybrid alone would have scored above 0 on these topics.
- **Many (c) cases look like real judgment gaps, but this needs a human check.** 15 of 45 topics have a top-1 that visibly answers the query or step (1a: 3, 1b: 6, 2a: 6). Several 2a topics have a single gold whose shown start reads off-topic (triple-junction stability for a divergent-boundary question; a plant-Rhizobia passage for Xq28), which suggests sparse judgments rather than a retrieval error. In 2 (c) cases the top-1 is gold for another topic of the same domain.
- **Expansion drift (e) has different forms in the two tracks.** In Track 1 (5 topics) the LLM invents facts or denies the premise: a made-up referent for "IAA iii", invented presumed-dead monarchs, a "fictional anecdote" verdict for the Tulane question, physical coins instead of ADA, and "first day of the week" instead of "out of sync". In 2a (2 topics) the expansion anchors on the earlier turn's concept instead of the current question.
- **History anchoring also shows up after expansion in 2a.** In 2a.9 and 2a.11 the expansion is on target, but the top-3 are about the previous turn's topic (ferrochelatase in mitochondria; Pangaea/Permian) and the gold was demoted (7 -> 16, 2 -> 20). This may point to the history-aware reranking rather than the LLM.
- **No clear temporal mismatches (d).** None of the 30 Track 1 topics showed top documents on the right topic but the wrong period. The Track 1 failures look topical or evidential, not temporal, although some of the topically close (a) cases (e.g. 1b.7, 1844-5 emigration versus the 1850s) might be read as (d) by a stricter annotator.
