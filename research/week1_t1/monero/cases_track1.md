# Track 1 failure cases (1a)

_seed 20260921; cases were sampled at random from nDCG@10 = 0 before reading them. Label each one; do not re-sample._

### monero · `3554_903` · 1a nDCG@10 = 0.000

**Query:** Energy consumed to protect the Monero network <p>Based on typical Monero mining equipment used today, approximately how many Kilowatt-hours (kWh) of electricity are consumed each day in by computers running the Monero cryptonight PoW mining algorithm?</p> <p>Based on global average energy costs and the above daily Kilowatt-hour (kWh) usage estimate how much money is spent on network energy consumption based on the Monero network hash rate today?</p>

**Steps:**
- Identify specifications of typical Monero mining equipment, including energy consumption per hash.  _(nDCG@10: query+step 0.00, step_only 0.00, query+all 0.00)_

**Gold passages:**
- `monero/85afb984_13411.txt` — The problem is that these devices are very expensive and can be afforded by few. This leads to few entities owning a big amount of the hashrate of the network, which is a serious threat to the security of the network itself. For example, if big ASIC operators  …
- `monero/f1626b50_13410.txt` — RandomX is a Proof of Work (PoW) algorithm finely optimized for the Central Processing Unit (CPU). The motive behind the algorithm is to prevent ASIC mining while improving the network’s security. That, in turn, facilitates miners to mine Monero with CPUs and  …

**BM25 top 5:**
1. `monero/01d18df3_3282.txt`  — Mining profitability models depend on multiple factors: coin price, block rewards, network difficulty (hashrate), electricity costs, hardware investment, etc. For any PoW coin, the basic condition for miner profitability is: Mining revenue ≥ Electricity cost + …
2. `monero/7e1a7d57_13579.txt`  — Monero uses Proof-of-Work, which means miners use their CPU to solve cryptographic puzzles that secure the network, verify transactions, and create new blocks roughly every two minutes. When your machine contributes valid work, you earn a share of the block re …
3. `monero/9cbd1dfd_5034.txt`  — How To Build A Crypto Mining Rig In 2020 To Earn Bitcoin And Ether. The Ultimate Resource For The Bitcoin Miner And The Mining Industry (#GotBitcoin) Mining with home rigs is back, so here’s what those interested need to know to put together their own rig at h …
4. `monero/3554_64cd4492b59e2bad_3.txt`  — * Cryptocurrency is a decentralized digital cash system. * Cryptocurrency is a digital asset designed to work as a medium of exchange wherein individual coin ownership records are stored in a ledger existing in a form of a computerized database using strong cr …
5. `monero/42a5a591_2317.txt`  — Estimates of climate damages from Bitcoin mining follow methods described in the existing literature in this space5,29. The primary estimate of interest is electricity consumption per BTC coin mined (in kWh per coin), as derived from the daily network hash rat …

- [ ] TEMPO class: event analysis/localization · time-period contextualization · other TEMPO class (write it in) · not temporal at all
- [ ] Failure mode: right topic, wrong period · period partly covered · lexical mismatch · gold looks wrong/debatable · other
- Note: 

---

### monero · `10071_871` · 1a nDCG@10 = 0.000

**Query:** Why does sending Monero coins out once prevent me from sending more of my remaining XMR coins immediately? <p>I wanted to pay 2 people. I sent some Monero to the first person and then I couldn't send any xmr coins to the second one. Why do I have to wait for the first to confirm first? Is there a work around to this? And doesn't this prevent adoption? How does the exchanges handle this problem? And are there proposals to fix this?</p>

**Gold passages:**
- `monero/11e8fe77_5638.txt` — In Monero, the set of unspent outputs (UTXOs) effectively includes all transaction outputs. Because of ring signatures, it's impossible to definitively mark a specific output as spent — any given output can appear multiple times in other users' transaction rin …
- `monero/6ebeaf9f_5639.txt` — You might have multiple inputs in your account, in many different denominations (For example: you deposited 0.5 XMR on Friday, and 0.75 XMR on Saturday). So, when have a transaction with an input of 0.5 XMR, but you only want to send 0.1 XMR, your transaction  …
- `monero/b5271b05_5640.txt` — In short, when a user sends Monero, the transaction is signed using a ring signature, which obscures the true spender. The sender’s input is mixed with a group of past transaction outputs, randomly selected from the blockchain as decoys. These decoys, along wi …

**BM25 top 5:**
1. `monero/1e51e3ef_5909.txt`  — Would like to hear anyone’s guess on future price. End of 2017, 2018 and beyond. been accurate so far, but my numbers have changed a bit short term - $300 mid term - $500 end-of-year - $835 Love it @kek. Top 3 I’m guessing Bitcoin, Ethereum, Zcash. I predict z …
2. `monero/bdad97fe_1903.txt`  — Users have mixed experiences with FixedFloat. Positive feedback highlights fast exchanges and low fees, with no issues for some long-term users swapping to XMR. However, many report funds locked randomly, intrusive KYC demands like video recordings, and false  …
3. `monero/11931_8428dc6178b274a4_0.txt`  — | | | | | | --- | --- | --- | --- | | | | | | | --- | --- | --- | | | **Hacker News**new | past | comments | | | | | login | | | | | | | | | --- | --- | --- | | | | Coin Carbon Cap – PoW cryptocurrencies ranked by energy efficiency (coincarboncap.com) | | | |  …
4. `monero/13570_629effce9a0f4c0b_0.txt`  — | | | | | | --- | --- | --- | --- | | | | | | | --- | --- | --- | | | **Hacker News**new | past | comments | | | | | login | | | | | | | | | --- | --- | --- | | | | Things we learned about LLMs in 2024 (simonwillison.net) | | | | 984 points by simonw 11 months …
5. `monero/13e12797_8543.txt`  — Now that we've had a chance to talk about local storage, I hope you understand why you (probably) shouldn't be using it. Unless you need to store publicly available information that: Is not at all sensitive Doesn't need to be used in an ultra high performance  …

- [ ] TEMPO class: event analysis/localization · time-period contextualization · other TEMPO class (write it in) · not temporal at all
- [ ] Failure mode: right topic, wrong period · period partly covered · lexical mismatch · gold looks wrong/debatable · other
- Note: 

---

### monero · `3515_904` · 1a nDCG@10 = 0.000

**Query:** Has the testnet been reset with a new genesis block? <p>I mined some testnet monero using version 0.10.0.0 a few months ago. Now, when I restore from my testnet wallet seed with version 0.10.1.0, it says 0 balance.</p>

**Steps:**
- Cross-check community discussions or FAQs for confirmation of the reset and its impact on wallet balances.  _(nDCG@10: query+step 0.00, step_only 0.00, query+all 0.00)_

**Gold passages:**
- `monero/55ffaf7d_13701.txt` — A lot has changed since the Tari testnet launched in April and Tari contributors agreed that it would be wise to take everything they’ve learned and reset the testnet. This reset comes after 6 months of squashing bugs, implementing many new features, uncoverin …
- `monero/617a678f_13702.txt` — A faulty or outdated node can make your wallet seem “stuck.” If you’re using a remote node, switch to another one in the connection settings. If you’re running a local node, ensure it’s updated to the latest version of Monero and fully synced with the network. …

**BM25 top 5:**
1. `monero/10054_dc80b6b403f6ad85_0.txt`  — | | | | | | | | | | | | | | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | | | | | | | | | | | | | | | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | | | | | | | | | --- | --- | --- | --- | --- | | **takuma sato** (O …
2. `monero/6622_fd4fc1bf5512fa61_0.txt`  — | | | | | | | | | | | | | | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | | | | | | | | | | | | | | | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | | | | | | | | | --- | --- | --- | --- | --- | | **Braden\_Hearn**  …
3. `monero/357d748e_0946.txt`  — The Blockchain Developer A Practical Guide for Designing, Implementing, Publishing, Testing, and Securing Distributed Blockchain-based Projects — Elad Elrom The Blockchain Developer A Practical Guide for Designing, Implementing, Publishing, Testing, and Securi …
4. `monero/357d748e_1150.txt`  — The Blockchain Developer A Practical Guide for Designing, Implementing, Publishing, Testing, and Securing Distributed Blockchain-based Projects — Elad Elrom The Blockchain Developer A Practical Guide for Designing, Implementing, Publishing, Testing, and Securi …
5. `monero/17d7a642_9150.txt`  — This release fixes an issue that could cause Feather to be unable to access hardware wallets on Windows 11. 2.1.2 changelog (2022-12-20) (This release is only available for AppImage builds) Fix issue with embedded version number in previous release. 2.1.1 chan …

- [ ] TEMPO class: event analysis/localization · time-period contextualization · other TEMPO class (write it in) · not temporal at all
- [ ] Failure mode: right topic, wrong period · period partly covered · lexical mismatch · gold looks wrong/debatable · other
- Note: 

---

### monero · `7922_877` · 1a nDCG@10 = 0.000

**Query:** Is the high transaction fees problem addressed in the upcoming monero v7 upgrade? <p>I've read the official release notes for Lithium Luna but there is no mention of any solution for the problem. At the same time I saw on twitter/forums some devs comment that it is addressed.</p> <p>Does someone have more information on this topic? </p> <p>Are there changes in the XMR constants per kb?</p> <p>Are the bulletproofs comming in the September's upgrade?</p>

**Steps:**
- Locate official Monero v7 upgrade release notes and announcements for September.  _(nDCG@10: query+step 0.00, step_only 0.00, query+all 0.00)_
- Search developer forums, GitHub repositories, and social media for discussions on transaction fees and bulletproofs in the context of the upgrade.  _(nDCG@10: query+step 0.00, step_only 0.00, query+all 0.00)_
- Cross-reference findings with authoritative cryptocurrency news sources for confirmation.  _(nDCG@10: query+step 0.00, step_only 0.00, query+all 0.00)_

**Gold passages:**
- `monero/1208f88b_7136.txt` — Since the bulletproofs deployment, the size of an average transaction has dropped by at least 80%, as well as the transaction fees. More explanations on Monero's implementation of bulletproofs could be found on youtube fondajo channel in a conversation with Sa …
- `monero/8d025375_7137.txt` — Monero developers have released a new version of the protocol, which will go into effect between October 18th and 19th. In addition to changing the proof-of-work algorithm to deter ASIC mining, the new upgrade includes improvements to Monero’s privacy function …

**BM25 top 5:**
1. `monero/11152_ad9f99a1f96d4840_205.txt`  — 1. To be fair, Burniske is not the only analyst-turned-VC who has not publicly disd his trading positions of coins, but that’s a separate topic. [↩] 2. One reviewer mentioned: “Likely it was partially intentional to release in late 2008 / early 2009, but did i …
2. `monero/12479_8c83e2113ae7536d_227.txt`  — 1. To be fair, Burniske is not the only analyst-turned-VC who has not publicly disd his trading positions of coins, but that’s a separate topic. [↩] 2. One reviewer mentioned: “Likely it was partially intentional to release in late 2008 / early 2009, but did i …
3. `monero/12780_853deebbc44dac09_179.txt`  — 1. To be fair, Burniske is not the only analyst-turned-VC who has not publicly disd his trading positions of coins, but that’s a separate topic. [↩] 2. One reviewer mentioned: “Likely it was partially intentional to release in late 2008 / early 2009, but did i …
4. `monero/13570_853deebbc44dac09_179.txt`  — 1. To be fair, Burniske is not the only analyst-turned-VC who has not publicly disd his trading positions of coins, but that’s a separate topic. [↩] 2. One reviewer mentioned: “Likely it was partially intentional to release in late 2008 / early 2009, but did i …
5. `monero/3718_ebb4b9e2cf2833f3_156.txt`  — 1. To be fair, Burniske is not the only analyst-turned-VC who has not publicly disd his trading positions of coins, but that’s a separate topic. [↩] 2. One reviewer mentioned: “Likely it was partially intentional to release in late 2008 / early 2009, but did i …

- [ ] TEMPO class: event analysis/localization · time-period contextualization · other TEMPO class (write it in) · not temporal at all
- [ ] Failure mode: right topic, wrong period · period partly covered · lexical mismatch · gold looks wrong/debatable · other
- Note: 

---

### monero · `7072_882` · 1a nDCG@10 = 0.000

**Query:** Block height and notification procedure for v7+ forks <p>Has the block height for the v7 fork been decided upon yet? What procedure will be used to provide notice exchanges, mining pools and merchants about the upcoming fork. </p> <p>Starting with v7 will their be any wallet based notification systems for upcoming forks?</p>

**Steps:**
- Search official blockchain development repositories or forums for v7 fork announcements and block height details.  _(nDCG@10: query+step 0.00, step_only 0.00, query+all 0.00)_
- Locate procedural documentation or communication protocols for notifying stakeholders about forks.  _(nDCG@10: query+step 0.00, step_only 0.00, query+all 0.00)_

**Gold passages:**
- `monero/0190d8ed_7647.txt` — Dear ViaBTC users: Monero (XMR) will undergo a hard fork at block height 1,788,000 at around March 09, 2019 (UTC). The hard fork upgrade will NOT generate new blockchain assets. To avoid unexpected problems, we suggest miners to update the mining software and  …
- `monero/c7e2be81_7646.txt` — On IRC and Matrix, the most used chat platforms in the Monero community (which are bridged together). These platforms allow for large group chats and are where all scheduled Monero community meetings, dev meetings, and research lab meetings are held. These mee …
- `monero/f2f22560_7645.txt` — The latest hard fork also introduced a tweak to Monero's CryptoNight proof-of-work hashing algorithm. This backwards-incompatible change makes all existing ASIC (application-specific integrated circuit) mining hardware useless. Such specialized hardware is a b …

**BM25 top 5:**
1. `monero/85025fec_5630.txt`  — 51% attacks are real and relevant today. Bitcoin Gold (rank #28 @ 2018‑05‑29) and Verge (rank #33 @ 2018‑05‑29) suffered recent attacks with double spend transactions following ([], []). In a conservative analysis, successful attacks on PoW cryptocurrencies ar …
2. `monero/f9226c3b_10203.txt`  — IET COMPUTING SERIES 29 Blockchains for Network Security Series Page for front matter IET Book Series on Big Data – Call for Authors Editor-in-Chief: Professor Albert Y. Zomaya, University of Sydney, Australia The topic of big data has emerged as a revolutiona …
3. `monero/f9226c3b_13806.txt`  — IET COMPUTING SERIES 29 Blockchains for Network Security Series Page for front matter IET Book Series on Big Data – Call for Authors Editor-in-Chief: Professor Albert Y. Zomaya, University of Sydney, Australia The topic of big data has emerged as a revolutiona …
4. `monero/f9226c3b_6839.txt`  — IET COMPUTING SERIES 29 Blockchains for Network Security Series Page for front matter IET Book Series on Big Data – Call for Authors Editor-in-Chief: Professor Albert Y. Zomaya, University of Sydney, Australia The topic of big data has emerged as a revolutiona …
5. `monero/f9226c3b_7989.txt`  — IET COMPUTING SERIES 29 Blockchains for Network Security Series Page for front matter IET Book Series on Big Data – Call for Authors Editor-in-Chief: Professor Albert Y. Zomaya, University of Sydney, Australia The topic of big data has emerged as a revolutiona …

- [ ] TEMPO class: event analysis/localization · time-period contextualization · other TEMPO class (write it in) · not temporal at all
- [ ] Failure mode: right topic, wrong period · period partly covered · lexical mismatch · gold looks wrong/debatable · other
- Note: 

---
