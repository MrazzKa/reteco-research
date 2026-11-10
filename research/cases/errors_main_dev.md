# Error examples of the main runs (dev)

Selection rule (LOG 2026-11-10 10:12, written before viewing): dev topics with nDCG@10 < 0.2 under the main run, sorted by (domain, topic id), 3 per sub-task drawn with `random.Random(20260921)`; no resampling. Ranks are in the main run's reranked top 50 ("> 50" = not there). Foreign = gold for another train/dev topic of the domain.

## 1a: 1a final (hybrid q+r+h + ReasonEmbed w 0.8)

Eligible dev topics (nDCG@10 < 0.2): 189 of 519.

### 1a.1 — history `57032_706` (nDCG@10 0.167)

Query:

> Why was there so little information about sex in Eastern Block countries? By "Taboo" I meant the lack of widespread access to the information (very few sources, sparse information in biology books etc). I've edited the title for clarification. As you all probably know, " there was no sex in Soviet Union " - at least according to famous TV shows that allowed people from Boston and Leningrad to talk

- gold (rank 32): This article examines how this campaign played out in the Latvian Soviet Socialist Republic (SSR) during the premiership of Leonid Brezhnev (1964–1982), focusing on two key tools that the Soviet leadership used to prevent VD transmission: criminal la
- gold (rank 6): Mass media had been an important technology of sexual enlightenment long before the Brezhnev era. In the 1920s, the Department of Sanitary Enlightenment produced and disseminated a large variety of sex education materials in an attempt to reach broad
- gold (rank > 50): In the early 1930s, suspected prostitutes were subjected to forced return to their home regions.[7] With the deployment of the Great Terror they were sentenced to imprisonment or re-education on the basis that prostitution constituted a remain of the
- rank 1 (not gold): The death of Stalin in 1953 brought important shifts in the messages of sexual enlightenment as the Soviet regime shifted towards more subtle, but more pervasive, methods for discipling and regulating the private lives of their citizens. Under the le

Reading (written after viewing): the rank-1 passage is on topic (Soviet sexual enlightenment under Brezhnev) and looks like a sibling chunk of the same source as two gold chunks; one gold chunk is at rank 6. A near-miss between chunks of one article rather than a topical error.

### 1a.2 — bitcoin `122022_24` (nDCG@10 0.141)

Query:

> Is there any way for a script to depend on blockchain info? The locktime opcodes OP_CHECKLOCKTIMEVERIFY and OP_CHECKSEQUENCEVERIFY indirectly allow for an approximate block number check, is there any way to obtain other information such as the previously mined block hash or current difficulty without having to rely on oracles?

- gold (rank 9): If you want to create secure, custom transaction conditions, focus on mastering the low-level command language that governs the validation of funds on the blockchain network. This stack-based language operates without loops, relying on a set of opcod
- gold (rank > 50): It is not advised to lock up bitcoins into the far future because it takes on risk of the bitcoin network changing. For example, if there were an ECDSA or RIPEMD160 algorithm break that made any coins spendable with a few months of CPU time, the netw
- gold (rank > 50): Bitcoin’s distributed and timestamped ledger, the blockchain, has potential uses far beyond payments. Many developers have tried to use the transaction scripting language to take advantage of the security and resilience of the system for applications
- rank 1 (not gold): Check Lock Time Verify (CLTV) In December 2015, a new form of timelock was introduced to bitcoin as a soft fork upgrade. Based on a specification in BIP-65, a new script operator called CHECKLOCKTIMEVERIFY (CLTV) was added to the scripting language. 

Reading (written after viewing): the question names CHECKLOCKTIMEVERIFY, and the rank-1 passage is about exactly that opcode — a match on the question's own terms. The gold passages explain what Script can and cannot see (the answer is "no access to chain state"); only one is in the top 10 (rank 9).

### 1a.3 — history `55806_789` (nDCG@10 0.000)

Query:

> Why do historians distinguish two Industrial revolutions, instead of just one? There was a 40 year gap between the two revolutions. Ending in 1830 and starting in 1870. However, why did historians distinguish two revolutions, instead of merging them together? First Industrial Revolution - 1760 - 1830 Started in Europe The start of new technology Steam engines Textile production Mass iron productio

- gold (rank > 50): Forms of industries that developed; the first British industrial revolution was based on textile industries which were characterized by small, owned by families, simple, cheap and easy to finance because it was not application of scientific theory, r
- gold (rank 21): Overall, there were two industrial revolutions. The First Industrial Revolution primarily took place in Great Britain and largely involved the steam engine. The Second Industrial Revolution took place in most of western and central Europe, the USA, a
- gold (rank > 50): The Industrial Revolution created so much growth that countries were willing to spy and steal to get their hands on the latest technology. The British government—determined to protect its economic advantage—even passed laws prohibiting the emigration
- gold (rank > 50): ​The major differences between the two revolutions occur in the sociocultural, and political responses of two different continents at two different times.
- rank 1 (not gold): Question: Why do historians distinguish two Industrial revolutions, instead of just one? We are actually entering into the 4th Industrial revolution. The first industrial revolution was defined by new ideas on how to organize labor which had a profou

Reading (written after viewing): the rank-1 document restates the question verbatim (a Q&A page whose answer was not judged gold); one gold passage is at rank 21. Query-copy documents compete with explanatory ones.

## 1b: 1b final (hybrid q+r+h + ReasonEmbed w 0.7)

Eligible dev topics (nDCG@10 < 0.2): 432 of 1214.

### 1b.1 — history `59267_627_step3` (nDCG@10 0.000)

Query:

> Was the danger of Germany bombing the US East Coast taken seriously and were measures taken to address it? In this CNN article an old lady from Dillon, South Carolina, recalls her memories from World War II and mentions not just fearing bombs from airplanes, but actual measures being taken against a || STEP: Analyze historical assessments of German air attack capabilities and their perceived threa

- gold (rank > 50): Called the Amerikabomber, the translation of which is extremely literal, the project was drafted up in a 33-page Luftwaffe document in 1942. Major German aircraft designers Messerschmitt, Focke-Wulf, Junkers and Heinkel submitted concepts for the pro
- rank 1 (not gold): The theory and practice of strategic bombing began in World War I but did not advance beyond the rudimentary stage. Between the wars, when some strategists were giving great emphasis to the defense, airmen believed that the airplane could not only gi

Reading (written after viewing): the step asks how German air-attack capability was assessed; the gold document is about one specific project (the "Amerikabomber") that neither the query nor the step names. The system returns general strategic-bombing history. Missing entity knowledge.

### 1b.2 — bitcoin `122143_23_step4` (nDCG@10 0.000)

Query:

> What was Bitcoin's Supply in the Pre-Alpha Release? (posted by Cryddit on Bitcointalk in 2013) So I'm doing some research into this Bitcoin code that apparently pre-dates the first release of Bitcoin v0.01 https://bitcointalk.org/index.php?topic=382374.0 There's a lot of differences in this code whe || STEP: Identify authoritative sources or archives documenting early Bitcoin development and codin

- gold (rank > 50): Sirius was one of the first volunteers to work with Satoshi in the early days of Bitcoin. These 260 emails span from May of 2009 (just 5 months after the launch of Bitcoin) to February of 2011. They’re a digital-gold mine of early Bitcoin history. I 
- rank 1 (not gold here; gold of another step of the same query (122143_23_step1, 122143_23_step2)): But wait, you ask, how can there be more bitcoin in this first draft, but less satoshis too? Answer: notice the decimal place difference here. In this pre-alpha of Bitcoin (2008), only four decimal places for satoshis are proposed, instead of the eig

Reading (written after viewing): the rank-1 passage is gold for steps 1 and 2 of the same query but not for this step (archives of early Bitcoin development). The ranking follows the shared query text more than the step; the step-4 gold (early e-mails) is not in the top 50.

### 1b.3 — history `56254_754_step2` (nDCG@10 0.000)

Query:

> Was Yahweh a god in a possible Edomite Pantheon? I understand from the Bible, from the Wikipedia articles Yahweh and Yahwism and from lectures of various scholars that polytheism was practiced by at least some religious leaders, priests, kings and laymen of the allegedly-Canaanite kingdom of Israel  || STEP: Analyze ancient texts (e.g., Bible, inscriptions) for references to Yahweh in Edomite cont

- gold (rank 42): Some scholars have pointed to biblical references about Yahweh coming from regions associated with Seir, Teman (in Edom), or even Midian. In Judges 5:4 and Deuteronomy 33:2, for instance, Yahweh appears in language that ties Him to locations southeas
- rank 1 (not gold): Short answer: yes. The earliest evidence for Yahweh worship is sparse, especially regarding its precise 'nature'. For the very early Edomite religious concepts it is even scarcer. For Yahweh it is also – sometimes fiercely – contested in many details

Reading (written after viewing): the rank-1 document is a direct answer to the question ("Short answer: yes …") but not judged gold for this step; the gold passage (biblical references to Seir/Teman) is at rank 42. Possibly a relevant but unjudged document.

## 2a: 2a main (history, Hb + ReasonEmbed w 0.9 + reranker w 0.4)

Eligible dev topics (nDCG@10 < 0.2): 155 of 858.

### 2a.1 — hardware `ex_10266_turn_5` (nDCG@10 0.000)

Query:

> CURRENT: Would having just an old HDD for extra storage slow things down a lot when you’re working with big files?
> 
> HISTORY: Q: In laptop upgrades, does adding a SATA SSD make more sense than replacing my NVMe SSD for balancing cost and storage? A: If you're looking to balance cost and storage for your laptop upgrade, adding a SATA SSD can make a lot of sense, especially since SATA SSDs are usually much cheaper than NVMe 

- gold (rank 22): So here we see a measurable performance difference between the two drives, and a significant one at that. I also suspect that Resharper should be somewhat more responsive, particularly when it loads the cache at solution start up. Why didn't I test c
- gold (rank > 50): NVMe delivers read/write speeds that reach and often exceed 7000 MB per second in newer generations. These drives are designed to support applications and environments that demand peak performance, reliability, and endurance. SATA offers read/write s
- rank 1 (not gold): Storage is sometimes overlooked when building a new PC, but is incredibly important. Hard disk drives are the oldest and the cheapest type of storage still used in modern PCs, and offer a great balance between price and capacity. These hard drives fe

Reading (written after viewing): the current question is about an old HDD for big files; rank 1 is a general overview of storage types. The gold documents are a specific benchmark write-up (rank 22) and an NVMe/SATA comparison (not in the top 50). Generic over specific.

### 2a.2 — biology `6_turn_5` (nDCG@10 0.000)

Query:

> CURRENT: What happens if a species puts more energy into staying healthy instead of having kids?
> 
> HISTORY: Q: In evolution, why doesn’t natural selection care much about traits that show up after we have kids? A: Natural selection mainly acts on traits that affect us before or during our reproductive years because that's when we're passing on our genes. Traits or mutations that show up after we've alread

- gold (rank > 50): The disposable soma theory of aging states that organisms age due to an evolutionary trade-off between growth, reproduction, and DNA repair maintenance. Formulated by Thomas Kirkwood, the disposable soma theory explains that an organism only has a li
- gold (rank > 50): Principles[edit] The disposable soma theory of aging posits that there is a trade-off in resource allocation between somatic maintenance and reproductive investment. Too low an investment in self-repair would be evolutionarily unsound, as the organis
- gold (rank > 50): Mechanisms[edit] The IGF-1 pathway, which represses FOXO, thus preventing gene expression of longevity-inducing proteins Growth and somatic maintenance[edit] Main article: Mechanistic target of rapamycin § Aging Much research has been done on the ant
- gold (rank 16): Evidence[edit] Growth and aging[edit] There is a large body of evidence indicating the negative effects of growth on longevity across many species. As a general rule, individuals of a smaller size generally live longer than larger individuals of the 
- gold (rank > 50): Criticism[edit] One of the main weaknesses of the disposable soma theory is that it does not postulate any specific cellular mechanisms to which an organism shifts energy to somatic repair over reproduction. Instead, it only offers an evolutionary pe
- rank 1 (not gold here; gold of another turn of the same conversation (6_turn_1, 6_turn_2)): Adaptivity and senescence[edit] An antagonistically pleiotropic gene can be selected for if it has beneficial effects in early life while having its negative effects in later life because genes tend to have larger impacts on fitness in an organism's 

Reading (written after viewing): the current turn asks about the maintenance-vs-reproduction trade-off (disposable soma theory, not named). Rank 1 is gold of turns 1 and 2 of the same conversation (antagonistic pleiotropy): the history pulls the ranking back to the earlier turns' gold. Only one of five gold chunks is in the top 50 (rank 16).

### 2a.3 — economics `28_turn_3` (nDCG@10 0.168)

Query:

> CURRENT: Is there a way to show a curved PPF with an equation, or is it always just a straight line?
> 
> HISTORY: Q: In production possibility frontiers, what does it mean if a point lies right on the curve? A: If a point lies right on the production possibility frontier curve, it means the economy is being perfectly efficient with its resources. At that point, you can't produce more of one good without having 

- gold (rank 23): Marginal rate of transformation [ [ edit ](/w/index.php?title=Production%E2%80%93possibility_frontier&action=edit§ion=4 "Edit section: Marginal rate of transformation") ] [ ![](//upload.wikimedia.org/wikipedia/commons/thumb/c/c2/PPF_marginal_rate_of_
- gold (rank 4): Shape [ [ edit ](/w/index.php?title=Production%E2%80%93possibility_frontier&action=edit§ion=5 "Edit section: Shape") ] The production-possibility frontier can be constructed from the contract curve in an [ Edgeworth production box ](/wiki/Edgeworth_b
- gold (rank > 50): [ ![](//upload.wikimedia.org/wikipedia/commons/thumb/4/4c/PPF_opportunity_cost.svg/250px- PPF_opportunity_cost.svg.png) ](/wiki/File:PPF_opportunity_cost.svg) Figure 6a: Standard PPF: increasing opportunity cost [ ![](//upload.wikimedia.org/wikipedia
- gold (rank 17): Opportunity cost [ [ edit ](/w/index.php?title=Production%E2%80%93possibility_frontier&action=edit§ion=6 "Edit section: Opportunity cost") ] [ ![](//upload.wikimedia.org/wikipedia/commons/thumb/4/4c/PPF_opportunity_cost.svg/220px- PPF_opportunity_cos
- rank 1 (not gold here; gold of another turn of the same conversation (28_turn_1)): * [ Printable version ](/w/index.php?title=Production%E2%80%93possibility_frontier&printable=yes "Printable version of this page \[p\]") In other projects * [ Wikimedia Commons ](https://commons.wikimedia.org/wiki/Category:Production_possibility_fron

Reading (written after viewing): rank 1 is a navigation/boilerplate chunk of the same Wikipedia page (gold for turn 1); a gold section ("Shape") is at rank 4. Boilerplate chunks of the right page score high on history terms.

