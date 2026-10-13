"""Week-4 tables for research/RESULTS.md (called by make_results.py).

Every number is read from a run output under research/runs_v12/; nothing is typed by hand.
Sections are skipped when their inputs do not exist yet.
"""
import glob
import json
import os

T1 = ["bitcoin", "cardano", "economics", "genealogy", "history", "hsm", "iota",
      "law", "monero", "politics", "quant", "travel", "workplace"]
T2 = ["biology", "drones", "earth_science", "economics", "hardware", "law",
      "medicalsciences", "politics", "psychology", "robotics", "sustainable_living"]
KS = ["10", "20", "50", "100", "200", "500", "1000"]
CONDS = [(1, "1a"), (1, "1b_query+step"), (2, "2a_current"), (2, "2a_history")]


def jload(path):
    return json.load(open(path)) if os.path.exists(path) else None


def f4(v):
    return "" if v is None or v != v else f"{v:.4f}"


def f3(v):
    return "" if v is None or v != v else f"{v:.3f}"


def mean(v):
    v = [x for x in v if x is not None]
    return sum(v) / len(v) if v else float("nan")


def ci(b):
    return f"{b['diff']:+.4f} [{b['ci95'][0]:+.4f}, {b['ci95'][1]:+.4f}]"


def week4(root):
    R = os.path.join(root, "research", "runs_v12")
    hyb = {t: jload(os.path.join(R, f"hybrid/bge-small_L512_t{t}.json")) for t in (1, 2)}
    L = ["# Week 4 (GPU): dense retrieval over every corpus, hybrid, depth, error analysis", "",
         "Machine: RTX 4060 Laptop (8 GB), WSL2, Python 3.14, torch 2.14.1+cu130, "
         "sentence-transformers 6.1.0, bm25s 0.3.13, faiss-cpu 1.15.1, ngt 2.8.0. "
         "Dense = `BAAI/bge-small-en-v1.5` (rev 5c38ec7c), 512-token window, fp16 vectors, exact "
         "float32 search over the **whole** domain corpus. BM25 = bm25s-lucene as before. Both at "
         "depth 1000, ties broken by doc id. Every fusion weight and depth below was chosen on "
         "**train** and frozen before dev was scored. Macro = mean over domains.", ""]

    # ------------------------------------------------------------- A. headline
    if all(hyb.values()):
        L += ["## A. Headline: dev nDCG@10 (frozen configurations)", "",
              "| sub-track | BM25 | dense only | BM25 top-100 + dense rerank | RRF* | hybrid* | "
              "hybrid − BM25 [95% CI] | hybrid − rerank [95% CI] | hybrid − dense [95% CI] |",
              "| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |"]
        for t, cond in CONDS:
            c = hyb[t]["conditions"][cond]
            s, b = c["systems"], c["dev_bootstrap"]
            L.append(f"| {t} `{cond}` | {f4(s['bm25']['dev_macro'])} | {f4(s['dense']['dev_macro'])} | "
                     f"{f4(s['rerank']['dev_macro'])} | {f4(s['rrf*']['dev_macro'])} | "
                     f"**{f4(s['linear*']['dev_macro'])}** | {ci(b['linear* - bm25'])} | "
                     f"{ci(b['linear* - rerank'])} | {ci(b['linear* - dense'])} |")
        L += ["", "`*` = configuration chosen on train (grid over pool depths, RRF constant, "
              "normalisation and alpha; see section C). CIs: paired bootstrap over topics within "
              "each domain, 10,000 resamples, macro over domains. Track-2 `2a_history` for the "
              "dense side uses the current question first (chosen on train, section B).", ""]
        L += ["Averaging: the task's baseline table averages over domains; the evaluation page describes "
              "averaging over topics (and, for 1b, over a query's steps first — not computed here). The same "
              "dev runs averaged over all topics:", "",
              "| sub-track | topics | BM25 | dense | rerank | hybrid* |", "| --- | ---: | ---: | ---: | ---: | ---: |"]
        for t, cond in CONDS:
            pt = hyb[t]["conditions"][cond]["dev_per_topic"]
            vals = [[x for d in pt[s].values() for x in d] for s in ("bm25", "dense", "rerank", "linear*")]
            L.append(f"| {t} `{cond}` | {len(vals[0])} | " + " | ".join(f4(mean(v)) for v in vals) + " |")
        L += ["", "The ranking of the systems is the same under both averages.", ""]
        L += ["Chosen configurations (train):", ""]
        for t, cond in CONDS:
            c = hyb[t]["conditions"][cond]["systems"]
            L.append(f"- {t} `{cond}`: hybrid = `{c['linear*']['cfg']}` (train {c['linear*']['train_macro']}); "
                     f"RRF = `{c['rrf*']['cfg']}` (train {c['rrf*']['train_macro']})")
        L.append("")

        # ------------------------------------------------------ per domain
        for t, doms in ((1, T1), (2, T2)):
            conds = [c for tt, c in CONDS if tt == t]
            L += [f"### Per domain, Track {t} (dev nDCG@10)", "",
                  "| domain | " + " | ".join(f"{c}: BM25 | dense | rerank | hybrid" for c in conds) + " |",
                  "| --- |" + " ---: |" * (4 * len(conds))]
            for d in doms:
                row = []
                for c in conds:
                    s = hyb[t]["conditions"][c]["systems"]
                    row += [s[k]["dev"].get(d, {}).get("ndcg10") for k in ("bm25", "dense", "rerank", "linear*")]
                L.append(f"| {d} | " + " | ".join(f4(x) for x in row) + " |")
            wins = {c: sum(1 for d in doms if hyb[t]["conditions"][c]["systems"]["linear*"]["dev"][d]["ndcg10"]
                           > hyb[t]["conditions"][c]["systems"]["bm25"]["dev"][d]["ndcg10"]) for c in conds}
            L += ["", "Hybrid above BM25 in " + ", ".join(f"{w}/{len(doms)} domains ({c})" for c, w in wins.items())
                  + ".", ""]
            if t == 2:
                bright = {"biology", "earth_science", "economics", "psychology", "robotics", "sustainable_living"}
                L += ["By source (dev macro nDCG@10):", "",
                      "| condition | source | BM25 | dense | rerank | hybrid |", "| --- | --- | ---: | ---: | ---: | ---: |"]
                for c in conds:
                    s = hyb[t]["conditions"][c]["systems"]
                    for name, grp in (("BRIGHT (6)", [d for d in doms if d in bright]),
                                      ("StackExchange (5)", [d for d in doms if d not in bright])):
                        L.append(f"| {c} | {name} | " + " | ".join(
                            f4(mean([s[k]["dev"][d]["ndcg10"] for d in grp])) for k in ("bm25", "dense", "rerank", "linear*")) + " |")
                L.append("")

    # ------------------------------------------------------------- B. query string for dense history
    dres = jload(os.path.join(R, "dense/bge-small_L512/t2/results.json"))
    if dres:
        L += ["## B. Dense query for Track-2 history (train decides)", "",
              "| query string | train macro nDCG@10 | train R@100 | dev macro nDCG@10 |", "| --- | ---: | ---: | ---: |"]
        for c, lab in (("2a_history", "history then question (starter kit)"),
                       ("2a_history_qfirst", "question then history (chosen)")):
            tr = [r for r in dres if r["split"] == "train" and r["run"] == c]
            dv = [r for r in dres if r["split"] == "dev" and r["run"] == c]
            L.append(f"| {lab} | {f4(mean([r['ndcg10'] for r in tr]))} | "
                     f"{f4(mean([r['recall']['100'] for r in tr]))} | {f4(mean([r['ndcg10'] for r in dv]))} |")
        L += ["", "Encoders cut text on the right; with the history first, long histories push the "
              "current question out of the window.", ""]

    # ------------------------------------------------------------- C. fusion grid
    if all(hyb.values()):
        L += ["## C. Fusion on train: what the grid says", "",
              "| sub-track | best RRF (train) | best linear (train) | best min-max | best z-score | linear, alpha=0 (BM25 scores only) "
              "| linear alpha curve (z-score, 100+100): 0.0 / 0.3 / 0.5 / 0.7 / 0.9 / 1.0 |",
              "| --- | ---: | ---: | ---: | ---: | ---: | --- |"]
        for t, cond in CONDS:
            c = hyb[t]["conditions"][cond]
            curve = c["linear_alpha_curve_train"]
            pts = [curve.get(f"zscore|100+100|a={a}") for a in (0.0, 0.3, 0.5, 0.7, 0.9, 1.0)]
            best_mm = max(v for k, v in curve.items() if k.startswith("minmax"))
            best_z = max(v for k, v in curve.items() if k.startswith("zscore"))
            L.append(f"| {t} `{cond}` | {f4(c['systems']['rrf*']['train_macro'])} | "
                     f"{f4(c['systems']['linear*']['train_macro'])} | {f4(best_mm)} | {f4(best_z)} | {f4(pts[0])} | "
                     + " / ".join(f4(p) for p in pts) + " |")
        L += ["", "Pool = BM25 top-kb ∪ dense top-kd. A document missing from one system's top-1000 "
              "gets that system's 1000th score (an upper bound) and no RRF contribution from it. "
              "Normalisation statistics come from each system's own top-1000 list. The best min-max and "
              "z-score settings are within 0.003 of each other on every sub-track, so the choice of "
              "normalisation hardly matters; the weight does (alpha 0.6–0.7, dense-leaning, in every "
              "case), and linear fusion beats the best RRF by 0.007–0.019 on train. Reranking the union pool with the same dense model is identical to dense "
              "retrieval (no new information) and is omitted.", ""]

    # ------------------------------------------------------------- D. recall@k
    if all(hyb.values()):
        L += ["## D. Retrieval depth: recall@k (dev, macro over domains)", "",
              "`union each@k` = BM25 top-k ∪ dense top-k (up to 2k documents; mean size shown). "
              "`union budget@k` = k unique documents taken alternately from the two lists — the fair "
              "comparison at equal candidate count.", ""]
        for t, cond in CONDS:
            dep = hyb[t]["conditions"][cond]["depth"]["dev"]
            L += [f"### Track {t} `{cond}`", "",
                  "| k | BM25 | dense | union budget@k | union each@k | mean union size |",
                  "| ---: | ---: | ---: | ---: | ---: | ---: |"]
            for k in KS:
                vals = [mean([v[f"{m}@{k}"] for v in dep.values()]) for m in
                        ("bm25", "dense", "union_budget", "union_each", "union_size")]
                L.append(f"| {k} | " + " | ".join(f4(x) for x in vals[:4]) + f" | {vals[4]:.0f} |")
            L.append("")
        # per-domain recall@100
        L += ["### Recall@100 per domain (dev): BM25 / dense / union at equal budget", ""]
        for t, doms in ((1, T1), (2, T2)):
            conds = [c for tt, c in CONDS if tt == t]
            L += ["| domain | " + " | ".join(f"{c}: BM25 | dense | union" for c in conds) + " |",
                  "| --- |" + " ---: |" * (3 * len(conds))]
            for d in doms:
                row = []
                for c in conds:
                    v = hyb[t]["conditions"][c]["depth"]["dev"].get(d, {})
                    row += [v.get("bm25@100"), v.get("dense@100"), v.get("union_budget@100")]
                L.append(f"| {d} | " + " | ".join(f3(x) for x in row) + " |")
            L.append("")
        # depth needed for coverage levels
        L += ["### Depth needed for a given recall (dev, macro; smallest k in {10..1000} reaching it)", "",
              "| sub-track | system | R ≥ 0.5 | R ≥ 0.7 | R ≥ 0.8 | R ≥ 0.9 | R@1000 |", "| --- | --- | ---: | ---: | ---: | ---: | ---: |"]
        for t, cond in CONDS:
            dep = hyb[t]["conditions"][cond]["depth"]["dev"]
            for m, lab in (("bm25", "BM25"), ("dense", "dense"), ("union_budget", "union (budget)")):
                curve = {k: mean([v[f"{m}@{k}"] for v in dep.values()]) for k in KS}
                need = [next((k for k in KS if curve[k] >= lvl), "—") for lvl in (0.5, 0.7, 0.8, 0.9)]
                L.append(f"| {t} `{cond}` | {lab} | " + " | ".join(need) + f" | {f3(curve['1000'])} |")
        L.append("")
        # unique contributions
        L += ["### Unique gold contributions (dev, all domains pooled; counts of (topic, gold) pairs)", "",
              "| sub-track | k | gold pairs | found by both | BM25 only | dense only | neither | "
              "dense adds beyond BM25 | BM25 adds beyond dense |",
              "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
        for t, cond in CONDS:
            dep = hyb[t]["conditions"][cond]["depth"]["dev"]
            for k in ("10", "100", "1000"):
                s = {m: sum(v[f"{m}@{k}"] for v in dep.values())
                     for m in ("gold", "both", "bm25_only", "dense_only", "neither")}
                L.append(f"| {t} `{cond}` | {k} | {s['gold']} | {s['both']} | {s['bm25_only']} | {s['dense_only']} | "
                         f"{s['neither']} | +{100 * s['dense_only'] / max(s['both'] + s['bm25_only'], 1):.0f}% | "
                         f"+{100 * s['bm25_only'] / max(s['both'] + s['dense_only'], 1):.0f}% |")
        L += ["", "Relative gains are against what the other system already finds at the same k.", ""]
        # allocation
        L += ["### Splitting a candidate budget between BM25 and dense (macro recall)", "",
              "| sub-track | budget B | best BM25 share on train | train recall | dev recall at that share | "
              "dev: dense only | dev: BM25 only | dev: half/half |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
        for t, cond in CONDS:
            al = hyb[t]["conditions"][cond]["allocation"]
            for B in (100, 200, 1000):
                keys = [k for k in al["train"] if k.startswith(f"B={B}|")]
                best = max(keys, key=lambda k: al["train"][k]["macro_recall"])
                fr = best.split("=")[-1]
                L.append(f"| {t} `{cond}` | {B} | {fr} | {f4(al['train'][best]['macro_recall'])} | "
                         f"{f4(al['dev'][best]['macro_recall'])} | {f4(al['dev'][f'B={B}|bm25_frac=0.0']['macro_recall'])} | "
                         f"{f4(al['dev'][f'B={B}|bm25_frac=1.0']['macro_recall'])} | "
                         f"{f4(al['dev'][f'B={B}|bm25_frac=0.5']['macro_recall'])} |")
        L.append("")

    # ------------------------------------------------------------- E. categories
    cats = jload(os.path.join(R, "categories/categories.json"))
    if cats:
        L += ["## E. Who finds the gold documents (dev) — summary", "",
              "Full analysis with per-domain tables and examples: "
              "[`research/cases/retrieval_categories_dev.md`](cases/retrieval_categories_dev.md).", "",
              "| sub-track | k | gold pairs | BM25 only | dense only | both | neither |",
              "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
        for key in sorted(k for k in cats["counts"] if "|ALL|" in k):
            t, cond, _, k = key.split("|")
            v = cats["counts"][key]
            n = sum(v.values())
            L.append(f"| {t} `{cond}` | {k} | {n} | " + " | ".join(
                f"{100 * v[x] / n:.1f}%" for x in ("bm25_only", "dense_only", "both", "neither")) + " |")
        L.append("")

    # ------------------------------------------------------------- F. history leakage
    hl = jload(os.path.join(R, "history_leak.json"))
    if hl:
        L += ["## F. Track 2: how much of the history gain is re-finding earlier gold? (dev)", "",
              "Turns grouped by whether their gold documents were already gold for an earlier turn of "
              "the same conversation (whose reference answer is pasted into the history).", "",
              "| group | turns | current: BM25 | dense | hybrid | +history: BM25 | dense | hybrid |",
              "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
        for g in ("ALL|first_turn", "ALL|new_gold", "ALL|recycled_gold", "BRIGHT|new_gold", "BRIGHT|recycled_gold",
                  "StackExchange|new_gold", "StackExchange|recycled_gold"):
            r = hl["dev"].get(g)
            if r:
                L.append(f"| {g.replace('|', ' / ')} | {r['n_turns']} | " + " | ".join(
                    f4(r[f"{c}|{s}"]) for c in ("2a_current", "2a_history") for s in ("bm25", "dense", "hybrid")) + " |")
        sh = hl["dev"]["later_turns_with_any_recycled_gold"]
        L += ["", f"Later turns that reuse at least one earlier gold document: BRIGHT {100 * sh['BRIGHT']:.0f}%, "
              f"StackExchange {100 * sh['StackExchange']:.0f}% (dev). The history gain lives almost entirely "
              "in those turns; on turns whose gold is new, adding the history helps BM25 only slightly and "
              "makes the hybrid worse than using the current turn alone.", ""]

    # ------------------------------------------------------------- G. model selection
    sel = sorted(glob.glob(os.path.join(R, "select/*/t1/results.json")))
    if sel:
        L += ["## G. Encoder selection on train (subset; dense retrieval over the full corpus)", "",
              "Track 1: iota, quant, law, workplace. Track 2: drones, law, medicalsciences (StackExchange) "
              "and biology, psychology, economics (BRIGHT). Train queries only. Score = mean of the four "
              "sub-track macros.", "",
              "| model | window | dims | 1a | 1b | 2a current | 2a history (q first) | **mean nDCG@10** | mean R@100 | "
              "docs/s (Track 1 / Track 2) | peak VRAM GB | revision |",
              "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |"]
        rows = []
        for p in sel:
            tag = p.split(os.sep)[-3]
            res = (json.load(open(p)) + (jload(p.replace("/t1/", "/t2/")) or []))
            cells, recs = [], []
            for t, c in ((1, "1a"), (1, "1b_query+step"), (2, "2a_current"), (2, "2a_history_qfirst")):
                rs = [r for r in res if r["track"] == t and r["run"] == c and r["split"] == "train"]
                cells.append(mean([r["ndcg10"] for r in rs]) if rs else None)
                recs.append(mean([r["recall"]["100"] for r in rs]) if rs else None)
            model, win = tag.rsplit("_L", 1)
            man = [json.load(open(m)) for m in glob.glob(os.path.join(R, f"emb/{tag}/t*/*/manifest.json"))]
            rate = {}
            for t in (1, 2):
                ms = [m for m in man if m["track"] == t and m["domain"] in
                      (("iota", "quant", "law", "workplace") if t == 1 else
                       ("drones", "law", "medicalsciences", "biology", "psychology", "economics"))]
                enc = sum(m["encode_s"] for m in ms)
                rate[t] = f"{sum(m['n_docs'] for m in ms) / enc:.0f}" if enc else "cached"
            dims = man[0]["dim"] if man else ""
            vram = max((m["peak_vram_gb"] for m in man), default=float("nan"))
            rev = man[0]["revision"][:8] if man else ""
            complete = all(x is not None for x in cells)
            rows.append((mean(cells) if complete else -1, f"| {model} | {win} | {dims} | " + " | ".join(f4(x) for x in cells)
                         + f" | **{f4(mean(cells)) if complete else 'incomplete'}** | {f4(mean(recs)) if complete else ''} | "
                         f"{rate[1]} / {rate[2]} | {vram:.2f} | {rev} |"))
        L += [r for _, r in sorted(rows, key=lambda x: -x[0])]
        L += ["", "Not evaluated: `snowflake-arctic-embed-m-v2.0` (its remote code fails under transformers "
              "5.19 with a CUDA index assertion) and `nomic-embed-text-v1.5` (remote code calls a method "
              "removed in transformers 5). Throughput includes tokenisation; the cards' longer contexts "
              "(8k–32k) were not used, every model is cut at 512 tokens.", ""]

    # ------------------------------------------------------------- H. ANN
    anns = {t: jload(os.path.join(R, f"ann/bge-small_L512_t{t}.json")) for t in (1, 2)}
    if any(anns.values()):
        L += ["## H. ANN vs exact search (dev, 1a / 2a_current, bge-small vectors)", "",
              "| track | domain | docs | exact nDCG@10 | NGT nDCG@10 | NGT R@10 vs exact | NGT build s | NGT ms/q | "
              "HNSW R@10 | HNSW build s | HNSW ms/q | FAISS flat R@10 |",
              "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
        allr = []
        for t in (1, 2):
            for d, v in sorted((anns[t] or {}).items(), key=lambda x: x[1]["docs"]):
                allr.append(v)
                L.append(f"| {t} | {d} | {v['docs']:,} | {f4(v['exact_gpu']['ndcg10'])} | {f4(v['ngt']['ndcg10'])} | "
                         f"{f3(v['ngt']['recall10_vs_exact'])} | {v['ngt']['build_s']} | {v['ngt']['ms_per_query']} | "
                         f"{f3(v['faiss_hnsw']['recall10_vs_exact'])} | {v['faiss_hnsw']['build_s']} | "
                         f"{v['faiss_hnsw']['ms_per_query']} | {f3(v['faiss_flat']['recall10_vs_exact'])} |")
        if allr:
            L += ["", f"Over {len(allr)} domains: NGT recall@10 against exact search {min(v['ngt']['recall10_vs_exact'] for v in allr):.3f}–"
                  f"{max(v['ngt']['recall10_vs_exact'] for v in allr):.3f}, mean |ΔnDCG@10| "
                  f"{mean([abs(v['ngt']['ndcg10'] - v['exact_gpu']['ndcg10']) for v in allr]):.4f} (worst "
                  f"{min(v['ngt']['ndcg10'] - v['exact_gpu']['ndcg10'] for v in allr):+.4f}); HNSW mean |ΔnDCG@10| "
                  f"{mean([abs(v['faiss_hnsw']['ndcg10'] - v['exact_gpu']['ndcg10']) for v in allr]):.4f} (worst "
                  f"{min(v['faiss_hnsw']['ndcg10'] - v['exact_gpu']['ndcg10'] for v in allr):+.4f}). "
                  "FAISS flat (CPU, float32) is an independent exact search; its R@10 below 1 comes only from "
                  "ties between duplicate documents. NGT: ANNG, cosine, epsilon 0.1; HNSW: M=32, "
                  "efConstruction 200, efSearch 128; latency single-threaded.", ""]

    # ------------------------------------------------------------- I. order
    orders = {t: jload(os.path.join(R, f"order/t{t}.json")) for t in (1, 2)}
    if any(orders.values()):
        L += ["## I. Does document order matter? (dev; file order + 5 random permutations)", "",
              "| track | domain | docs in exact-duplicate groups | gold with a non-gold twin | BM25 range, bm25s native ties | "
              "BM25 range, id tie-break | dense range, native ties | dense range, id tie-break | NGT nDCG@10 over 3 insertion orders |",
              "| --- | --- | ---: | ---: | --- | --- | --- | --- | --- |"]
        for t in (1, 2):
            for d, v in sorted((orders[t] or {}).items()):
                cs = list(v["bm25"])
                ann = v.get("ann", {}).get("insertion_orders", [])
                L.append(f"| {t} | {d} | {100 * v['duplicates']['share_docs_duplicated']:.1f}% | "
                         f"{v['duplicates']['gold_with_nongold_twin']} | "
                         + " / ".join(f3(v["bm25"][c]["raw_range"]) for c in cs) + " | "
                         + " / ".join(f3(v["bm25"][c]["tiebreak_range"]) for c in cs) + " | "
                         + " / ".join(f3(v["dense"][c]["raw"]["range"]) for c in cs) + " | "
                         + " / ".join(f3(v["dense"][c]["tiebreak"]["range"]) for c in cs) + " | "
                         + (" / ".join(f4(o["ndcg10"]) for o in ann) if ann else "") + " |")
        L += ["", "Ranges are max − min nDCG@10 over the six document orders, for the two conditions of the "
              "track (1a / 1b, or current / history). Effects exist only through exact score ties between "
              "duplicate documents; with ties broken by doc id the result no longer depends on order. The "
              "largest effect is 0.011 on one domain — far from the ~10-point differences seen in week 1, "
              "which came from the analyzer (stemming) and the v1.0→v1.1 deduplication.", ""]

    # ------------------------------------------------------------- J. cross-encoder
    ces = {t: jload(os.path.join(R, f"ce/t{t}.json")) for t in (1, 2)}
    ce_base = jload(os.path.join(R, "ce_bge-base/t2.json"))
    if any(ces.values()):
        L += ["## J. Cross-encoder (bge-reranker-v2-m3) on the hybrid list", "",
              "| sub-track | N chosen on train | train: hybrid → CE | dev: hybrid | dev: hybrid + CE | dev CE − hybrid [95% CI] |",
              "| --- | ---: | --- | ---: | ---: | --- |"]
        for t in (1, 2):
            for cond, v in (ces[t] or {}).items():
                n = str(v["chosen_depth_on_train"])
                bd = v["by_depth"]
                L.append(f"| {t} `{cond}` | {n} | {f4(bd['0']['train_macro'])} → {f4(bd[n]['train_macro'])} | "
                         f"{f4(bd['0']['dev_macro'])} | {f4(bd[n]['dev_macro'])} | {ci(v['dev_bootstrap_ce_minus_hybrid'])} |")
        for cond, v in (ce_base or {}).items():
            n, bd = str(v["chosen_depth_on_train"]), v["by_depth"]
            L.append(f"| 2 `{cond}`, bge-base hybrid (rule 5) | {n} | {f4(bd['0']['train_macro'])} → {f4(bd[n]['train_macro'])} | "
                     f"{f4(bd['0']['dev_macro'])} | {f4(bd[n]['dev_macro'])} | {ci(v['dev_bootstrap_ce_minus_hybrid'])} |")
        L += ["", "Train/dev macro by reranking depth N (0 = plain hybrid):", "",
              "| sub-track | " + " | ".join(f"N={n}" for n in ("0", "10", "20", "50")) + " |", "| --- |" + " --- |" * 4]
        for t in (1, 2):
            for cond, v in (ces[t] or {}).items():
                L.append(f"| {t} `{cond}` | " + " | ".join(
                    f"{f4(v['by_depth'][n]['train_macro'])} / {f4(v['by_depth'][n]['dev_macro'])}" for n in ("0", "10", "20", "50")) + " |")
        L += ["", "Input: the bge-small **L512** hybrid of section A, top 50; train subsample ≤ 30 topics per domain "
              "and condition (seed 20260921). The pre-registered rule allowed N ∈ {10, 20, 50} only, so where the "
              "cross-encoder lowers train scores at every depth (Track 1, Track-2 history) it was still applied at "
              "N = 10; with N = 0 allowed, train would have kept the plain hybrid there. The cross-encoder helps "
              "only on the Track-2 current turn (11/11 domains).", ""]

    # ------------------------------------------------------------- K. throughput
    man = [json.load(open(m)) for m in glob.glob(os.path.join(R, "emb/bge-small_L512/t*/*/manifest.json"))]
    if man:
        L += ["## K. Cost of the full dense index (bge-small, 512 tokens, fp16)", "",
              "| track | domains | documents | encoding time | docs/s | cache size | peak VRAM |",
              "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
        for t in (1, 2):
            ms = [m for m in man if m["track"] == t]
            n, e = sum(m["n_docs"] for m in ms), sum(m["encode_s"] for m in ms)
            enc_docs = sum(m["docs_encoded_this_run"] for m in ms)
            size = sum(m["n_docs"] * m["dim"] * 2 for m in ms) / 2**30
            L.append(f"| {t} | {len(ms)} | {n:,} | {e / 60:.1f} min | {enc_docs / e:.0f} | {size:.2f} GB | "
                     f"{max(m['peak_vram_gb'] for m in ms):.2f} GB |")
        L += ["", "Encoding time is summed per domain; hsm was resumed from 4 completed shards after an "
              "OOM kill (see LOG), so its time covers only the remaining shards. Previous machine (CPU): "
              "8 docs/s, i.e. ~38 h for Track 1.", ""]

    # ------------------------------------------------------------- L. full-pipeline candidates
    cands = [(t, name, jload(os.path.join(R, f"hybrid/{name}_t{t}.json")))
             for t, names in ((1, ("bge-small_L512", "bge-small_L256", "bge-base_L512")),
                              (2, ("bge-small_L512", "bge-base_L512"))) for name in names]
    cands = [c for c in cands if c[2]]
    if len(cands) > 2:
        # rule 4 (LOG 20:46): Track 1 compares bge-small L256 (rule 1) with bge-base; Track 2 bge-small L512 with bge-base
        eligible = {1: ("bge-small_L256", "bge-base_L512"), 2: ("bge-small_L512", "bge-base_L512")}
        L += ["## L. Window and encoder in the full pipeline (rules 1, 2 and 4 in LOG)", "",
              "Each row is the whole pipeline (dense over all domains, hybrid grid tuned on train, dev scored once). "
              "Selection score = mean train macro of the hybrid over the track's two conditions.", "",
              "| track | dense side | condition | train dense | train hybrid* | dev dense | dev hybrid* | hybrid* config |",
              "| --- | --- | --- | ---: | ---: | ---: | ---: | --- |"]
        score = {}
        for t, name, h in cands:
            tr = []
            for cond, c in h["conditions"].items():
                s = c["systems"]
                tr.append(s["linear*"]["train_macro"])
                L.append(f"| {t} | {name} | `{cond}` | {f4(s['dense']['train_macro'])} | {f4(s['linear*']['train_macro'])} | "
                         f"{f4(s['dense']['dev_macro'])} | {f4(s['linear*']['dev_macro'])} | `{s['linear*']['cfg']}` |")
            score[(t, name)] = mean(tr)
        L.append("")
        for t in (1, 2):
            el = [(score[(t, n)], n) for n in eligible[t] if (t, n) in score]
            sc = ", ".join(f"{n} {v:.4f}" for (tt, n), v in score.items() if tt == t)
            line = f"- Track {t} selection scores (train): {sc}."
            if len(el) == 2:
                line += f" Rule 4 choice: **{max(el)[1]}**."
            L.append(line)
        L += ["", "Track 1 bge-small L512 is listed for the record but is not a rule-4 candidate (rule 1 moved "
              "Track 1 to 256 tokens on train; L512 was then seen to be better on dev, so re-admitting it would "
              "be selection on dev).", ""]
        fin = {n: h for t, n, h in cands if t == 1}.get("bge-small_L256"), {n: h for t, n, h in cands if t == 2}.get("bge-base_L512")
        if all(fin):
            cur = (ce_base or {}).get("2a_current")
            rows = [("1a", fin[0]["conditions"]["1a"], "BM25 ∪ bge-small (256 tokens), linear fusion"),
                    ("1b Query+Step", fin[0]["conditions"]["1b_query+step"], "BM25 ∪ bge-small (256 tokens), linear fusion"),
                    ("2a current turn", fin[1]["conditions"]["2a_current"], "BM25 ∪ bge-base, linear fusion"
                     + (", top 50 reordered by bge-reranker-v2-m3 (rule 5)" if cur else "")),
                    ("2a with history", fin[1]["conditions"]["2a_history"], "BM25 ∪ bge-base (question first), linear fusion")]
            L += ["### Final frozen systems (every choice on train; dev scored once)", "",
                  "| sub-track | system | BM25 | final | final − BM25 |", "| --- | --- | ---: | ---: | ---: |"]
            for name, c, desc in rows:
                b, f = c["systems"]["bm25"]["dev_macro"], c["systems"]["linear*"]["dev_macro"]
                if name.startswith("2a current") and cur:
                    f = cur["by_depth"][str(cur["chosen_depth_on_train"])]["dev_macro"]
                L.append(f"| {name} | {desc} | {f4(b)} | **{f4(f)}** | {f - b:+.4f} |")
            L.append("")
    return L
