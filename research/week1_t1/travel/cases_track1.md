# Track 1 failure cases (1a)

_seed 20260921; cases were sampled at random from nDCG@10 = 0 before reading them. Label each one; do not re-sample._

### travel · `186482_1157` · 1a nDCG@10 = 0.000

**Query:** What happens if I miss my French night train (intercit&#233;s de nuit) if my connecting Eurostar is delayed or cancelled? <p>I may want to travel from the Netherlands to Latour-de-Carol, in southern France, by taking the Eurostar from Amsterdam to Paris, then the Intercités de Nuit to Latour-de-Carol. This is offered as an option on SNCF Connect, and can be booked in one go.</p> <p>The connection time in Paris is about 1-2 hours, which makes it easy to miss the connection if the Eurostar train has a significant delay. What rights do I have as a passenger? Especially considering that, while these tickets are booked together, they have different operators.</p> <p>I recall that, in the opposite direction, a delay can entitle you to board any later Eurostar train on the same day. That is of course not possible with a night train that departs once a day.</p>

**Steps:**
- Search for official Eurostar and SNCF policies on missed connections and passenger rights.  _(nDCG@10: query+step 0.00, step_only 0.43, query+all 0.00)_
- Retrieve documentation on EU rail passenger rights regulations, especially regarding multi-operator bookings.  _(nDCG@10: query+step 0.00, step_only 0.00, query+all 0.00)_

**Gold passages:**
- `travel/05c5f169_16005.txt` — Any other journeys connecting a Eurostar Service and a service provided by another carrier(s) e.g. SNCF, SNCB, DB,… even purchased in a single commercial transaction, represent separate contracts of carriage.In case ofissues relating to delays, missed connecti …
- `travel/44781a26_16004.txt` — TheAgreement on Journey Continuation ( AJC for short) is an agreement between several European rail operators, enabling passengers on international trains to catch the next available train at no extra cost if they miss their connection.

**BM25 top 5:**
1. `travel/bddf1dad_20676.txt`  — Enter a keyword to start your query or check our frequently asked questions below. You can buy your international train tickets (with or without seat reservation, depending on train type): online on www.sncb-international.com via the SNCB International app (iP …
2. `travel/5579e4a5_14858.txt`  — Europe by Rail 2nd Edition Here’s what the critics say about Frommer’s: “Amazingly easy to use. Very portable, very complete.” —Booklist “Detailed, accurate, and easy-to-read information for all price ranges.” —Glamour Magazine “Hotel information is close to e …
3. `travel/dd19140e_16264.txt`  — Across the continent, flights are priced at a fraction of the cost of train tickets, hampering the growing number of people who want to travel sustainably. The big question is: why? When Tess Longfield booked her family holiday this year, sustainable travel wa …
4. `travel/47345a58_20628.txt`  — I've already checked the FAQ in NS website: "Can I travel at a time that is different from what I have planned?". It covers the following situations: Train travel within the Netherlands to or from the boarding station of an international train For a train jour …
5. `travel/444625f7_16049.txt`  — When buying tickets for journeys that involve changes of train, you have a choice between: booking an end-to-end journey in one transaction, OR making separate bookings (on different websites) for each train you will be travelling by. Making separate bookings  …

- [ ] TEMPO class: event analysis/localization · time-period contextualization · other TEMPO class (write it in) · not temporal at all
- [ ] Failure mode: right topic, wrong period · period partly covered · lexical mismatch · gold looks wrong/debatable · other
- Note: 

---

### travel · `183966_1189` · 1a nDCG@10 = 0.000

**Query:** What is the situation with land border crossings on the Georgia-Azerbaijan border? <p>Azerbaijan has extended its Special Quarantine Regime until January 2. I have been led to believe that the land border restrictions of the Special Quarantine Regime prevent any travel to Azerbaijan from neighboring countries via land borders. Is this true? Is it possible to enter Azerbaijan via land borders such as the Georgian-Azerbaijani border before January 2 2024, or only by air?</p> <p><a href="https://www.turan.az/ext/news/2023/9/free/Social/en/9045.htm" rel="noreferrer">https://www.turan.az/ext/news/2023/9/free/Social/en/9045.htm</a></p>

**Steps:**
- Search for official government statements or updates from Azerbaijan regarding the Special Quarantine Regime and border policies.  _(nDCG@10: query+step 0.00, step_only 0.00, query+all 0.00)_
- Retrieve recent news articles or reports discussing the status of land border crossings between Georgia and Azerbaijan.  _(nDCG@10: query+step 0.00, step_only 0.00, query+all 0.00)_
- Verify the timeline and restrictions by cross-referencing multiple authoritative sources, including international travel advisories.  _(nDCG@10: query+step 0.00, step_only 0.00, query+all 0.00)_

**Gold passages:**
- `travel/1cd7d0ce_24380.txt` — The Azerbaijani government, through a decree signed by Prime Minister Ali Asadov, has decided to maintain the special quarantine regime related to the COVID-19 pandemic until January 1, 2026. This measure effectively extends the closure of the country’s land b …
- `travel/e1e47919_24379.txt` — According to the Azerbaijani Ministry of Foreign Affairs, under current COVID-19 regulations, foreign nationals and stateless persons are permitted to enter and leave the country only by air. Overland borders remain closed to passenger traffic and may only be  …
- `travel/f7a64fd9_24378.txt` — Authorities justify the border policy as necessary to “prevent the spread of the coronavirus and its potential negative consequences,” according to VisaNews. Yet in a global context where nearly all nations have abandoned pandemic restrictions, the decision on …

**BM25 top 5:**
1. `travel/183966_4555261b6c251b55_7.txt`  — * 1Ron Synovitz, “Analysis: Nagorno-Karabakh War Transforms the Legacy of Azerbaijani President Aliyev”, Radio Free Europe/Radio Liberty, 17 December 2020, https://www.rferl.org/a/nagorno-karabakh-legacy-azerbaijani-president-a… * 2Bahruz Samadov, “Azerbaijan  …
2. `travel/d1859cb7_24419.txt`  — We call it Regime, without "Special Quarantine" crap. So, indeed the regime has been extended until October 1st 2025, which means our land borders (including Georgia-Azerbaijan border) will be closed at least until then. I've read that foreigners can leave the …
3. `travel/183966_4555261b6c251b55_11.txt`  — * 1“A week has passed since the incident with Bakhtiyar Hajiyev. There is no result”, Turan Agency, 28 April 2022, https://www.turan.az/cache/2022/Chetin\_sual/free/news-2022---free-Cheti… * 2Ibid * 3“Social activist Bakhtiyar Hajiyev was arrested”, MeydanTV,  …
4. `travel/183966_4555261b6c251b55_4.txt`  — * 1“Azerbaijan Country Report 2022”, BTI Transformation Index, 2022, * 2Bahruz Samadov, “Azerbaijan’s new reality”, OC Media, 24 December 2020, * 3Heydar Isayev, “Two years on, Azerbaijan’s land borders remain d”, Eurasianet, 29 Aprel 2022, https://eurasianet. …
5. `travel/183966_4555261b6c251b55_6.txt`  — * Azerbaijan’s system of governance is consolidated authoritarianism. The constitution and other national legislation are repeatedly violated, and citizens are effectively barred from participating in political processes and decision-making. There is no sign o …

- [ ] TEMPO class: event analysis/localization · time-period contextualization · other TEMPO class (write it in) · not temporal at all
- [ ] Failure mode: right topic, wrong period · period partly covered · lexical mismatch · gold looks wrong/debatable · other
- Note: 

---

### travel · `186393_1158` · 1a nDCG@10 = 0.000

**Query:** Is 55 minutes connection in WAW possible? <p>I have a flight booked from Rzeszow to London with a connection in Warsaw, it's one booking booked on LOT directly and it's not a self-transfer. The connection in WAW is for 55 minutes. It's from domestic to international so will need to go through passport control but no security.</p> <p>Is 55 minutes possible? I'm not too worried as the flight from WAW to LHR was delayed every day in the last few days by 15 minutes+ and the flight from RZE to WAW arrived earlier than schedule every day in the last few days. But in general is this connection in WAW tight? Looking on WAW maps it seems to be relatively a small airport.</p>

**Steps:**
- Retrieve information about WAW airport layout, passport control times, and average connection times for domestic to international flights.  _(nDCG@10: query+step 0.00, step_only 0.00, query+all 0.00)_

**Gold passages:**
- `travel/53e12923_16423.txt` — If you are unfortunate enough to arrive or depart from Warsaw Chopin during peak immigration hours - generally 7 AM to 9 AM and again from 2 PM to 4 PM - be prepared for lines. While airports often claim smooth processes, the reality is that higher passenger v …
- `travel/c5e46151_16421.txt` — On arrival, get off the air bridge or bus and proceed to the terminal. Then check the flight schedule and go to the gate displayed at your flight number. Transfers from a Schengen country to a non-Schengen country On arrival, get off the air bridge or bus and  …
- `travel/cafe2884_16422.txt` — Chopin is one of the smaller international hubs in Europe. When flying between two Schengen countries, connections can be made in 35 minutes. (LOT, Poland’s flag carrying airline, is notorious for holding flights for late arrivals.) Just keep in mind that the  …

**BM25 top 5:**
1. `travel/629dc38f_16694.txt`  — When you book an itinerary with a connection (as a single ticket, not a self-transfer, of course), the booking system will check that it matches the published minimum connection time (MCT) for that combination. While airports usually have general rules for eac …
2. `travel/eba243f8_24377.txt`  — In theory, it’s possible to get between all terminals at LAX but T1 without leaving the secured area. In practice, this is most useful for getting between TBIT and T4 through T8 and makes enjoying the superior lounges and retail in TBIT a reasonable option. An …
3. `travel/201618_b49915dd47743045_1.txt`  — That reminds me of a fun story about our last trip from Ukraine to Poland before the war. I used the free connection between open-jaws on an award ticket and flew ODS->WAW->KRK. It seemed ok, about 70 minute connection in Warsaw and I pushed as always though t …
4. `travel/e56ff9fe_0003.txt`  — Last week, I shared about my booking home from Istanbul, which included a 60-minute connection in London (and also a tight connection in Chicago). Even transferring within Heathrow Terminal 2 is complicated and I knew that I had virtually no room for error. My …
5. `travel/8363d63e_0957.txt`  — Like other US airports, SFO doesn't have a sterile transit area but it does have a kind of organised international-to-international transit procedure. There are many flights from Europe to Polynesia using this route. In this case, there is staff to guide you a …

- [ ] TEMPO class: event analysis/localization · time-period contextualization · other TEMPO class (write it in) · not temporal at all
- [ ] Failure mode: right topic, wrong period · period partly covered · lexical mismatch · gold looks wrong/debatable · other
- Note: 

---

### travel · `184237_1186` · 1a nDCG@10 = 0.000

**Query:** Is the Paris USA embassy open for h1b appointment and processing in case of shutdown? <p>I live and work in the USA. While here, I transitioned to a different visa while in the USA and as such, I do not have a stamp for my new passport. I intend to visit my family and secure this stamp in December. However, I'm aware there's a looming threat of a shutdown. In the event of such a shutdown, would the Paris embassy still handle H1-B appointments and process passports?</p>

**Steps:**
- Search for official statements or policies from the Paris USA embassy regarding operations during government shutdowns.  _(nDCG@10: query+step 0.00, step_only 0.00, query+all 0.00)_
- Retrieve historical data on embassy operations during past U.S. government shutdowns, focusing on visa processing.  _(nDCG@10: query+step 0.00, step_only 0.00, query+all 0.00)_

**Gold passages:**
- `travel/1b08c375_23754.txt` — At this time, scheduled passport and visa services in the United States and at U.S. Embassies and Consulates overseas will continue during the lapse in appropriations as the situation permits. We will not update this account until full operations resume, with  …
- `travel/2d9e92dc_23756.txt` — The notable impact may be for USCIS petitions that require pre-filing actions by the Department of Labor (DOL), such as H-1B Labor Condition Applications (LCAs). DOL is not a fee-funded government agency, so their immigration-related functions will be suspende …
- `travel/7055c1a0_23753.txt` — The Department of State generally continues to offer consular services during a shutdown, as many visa operations are funded by application fees. This means that visa interviews and adjudications usually remain available. That said, if the shutdown is prolonge …
- `travel/a5cf39f2_23755.txt` — Even in a shutdown, some services persist if they are funded by user fees rather than relying on annual appropriations. The US Embassy in India noted that “consular services will continue to function during the lapse in Congressional appropriations.” But not a …

**BM25 top 5:**
1. `travel/192450_40f68c0c691d619a_3.txt`  — * December 18th - Q&A’s published on the World Journal Weekly on December 18, 2022 1. Can Shoplifting Affects a Citizenship? 2. What Will Happen to a Child’s (18 years old) Derivative Immigration Visa Status If His Principal Immigration (Parents) Do not Mainta …
2. `travel/e4316a6a_7468.txt`  — It's unlikely that the Trump presidency will have any immediate consequences for H1B holder and even less likely for H1B holders from Germany. This being said, getting H1B stamped in your passport is a tedious and time consuming process that requires careful p …
3. `travel/187688_63ff06c9ab013ca4_272.txt`  — Planning a trip from Malaysia to the USA can be an exciting experience, but before you can explore the United States, you’ll need to secure a visa. This guide will help you understand the process, requirements, and steps for applying for a US visa as a Malaysi …
4. `travel/b83b8823_6438.txt`  — Dear Greg, I read with care your post and many Q&A. I am still skeptical about what is _legal_ and best to do in my case because USCIS is a bit vague. I have been married for more than 5 years to a Japanese national and we have a son that is both Japanese and  …
5. `travel/192188_4a5f41be3389f928_0.txt`  — | | | | | | --- | --- | --- | --- | | Effective Nov 1 2025: Apply for Immigrant Visa IV in Your Country of Residence 11/11/2025 0 Comments * The Department of State is now requiring immigrant visa applicants to interview in the consular district designated for …

- [ ] TEMPO class: event analysis/localization · time-period contextualization · other TEMPO class (write it in) · not temporal at all
- [ ] Failure mode: right topic, wrong period · period partly covered · lexical mismatch · gold looks wrong/debatable · other
- Note: 

---

### travel · `201562_1094` · 1a nDCG@10 = 0.000

**Query:** What&#39;s the limit, if any, on the number of stops or duration that a single PNR may contain? <p>I wonder the following: What is the limit, if any, on the number of stops or duration that a single PNR may contain?</p>

**Steps:**
- Search airline or travel industry guidelines for PNR rules, focusing on duration and stop limits.  _(nDCG@10: query+step 0.00, step_only 0.00, query+all 0.00)_

**Gold passages:**
- `travel/1c1b55d8_0599.txt` — Electronic Ticket Definition and Eligibility · American electronic tickets must be validated and plated on AA/001. · The itinerary may contain no more than 16 segments of airspace for each ticket, this includes ARNK segments. · Open segments are allowed when t …
- `travel/1c1b55d8_0600.txt` — Electronic Ticket Definition and Eligibility · American electronic tickets must be validated and plated on AA/001. · The itinerary may contain no more than 16 segments of airspace for each ticket, this includes ARNK segments. · Open segments are allowed when t …
- `travel/d27fe46e_0601.txt` — It happens every time travelers book a flight. No matter whether they eventually buy tickets and board a plane or cancel the reservation and stay home, the deed is done. Data on them has been collected and saved in the form of a passenger name record or PNR.

**BM25 top 5:**
1. `travel/686f3c49_0693.txt`  — What's the limit, if any, on the number of stops or duration that a single PNR may contain?
2. `travel/6fb8a7cb_2997.txt`  — For a Schengen visa, for any day of your visit, you need to respect all of: The valid from ... until dates The max duration Valid from: 01 June 2025 Valid until: 30 June 2025 Max Duration: 10 days You cannot enter before 01 June 2025 You cannot stay beyond 30  …
3. `travel/9e1e1b7d_24953.txt`  — 6.1 Forms of Payment Currently, Star Air accepts the following payment methods: a) Cash, b) Credit Cards (Visa, MasterCard), c) Debit Cards, and Cash Wallet* and Internet banking* *For tickets bought directly from Star Air or Trade Partners that offer such a s …
4. `travel/37bb953d_0741.txt`  — From a technical point of view, there are five parts of a PNR required before the booking can be completed. They are: The name of the passenger Contact details for the travel agent or airline office. Ticketing details, either a ticket number or a ticketing tim …
5. `travel/e1b2ff90_24919.txt`  — At SpiceJet, we recognise that travel plans may require adjustments. Our policies for cancellations, changes, and delays are designed to provide the necessary support and flexibility. Below are the key details regarding each aspect of our policies. Cancellatio …

- [ ] TEMPO class: event analysis/localization · time-period contextualization · other TEMPO class (write it in) · not temporal at all
- [ ] Failure mode: right topic, wrong period · period partly covered · lexical mismatch · gold looks wrong/debatable · other
- Note: 

---
