"""Week-5 tables for research/RESULTS.md (called by make_results.py).

Every number is read from a run output under research/runs_v13/; nothing is typed by hand.
Sections are skipped when their inputs do not exist yet.
"""
import json
import os

from results_week4 import ci, f4, jload

CONDS = ["1a", "1b_query+step", "2a_current", "2a_history"]
EXP_CONDS = ["1a", "1b_query+step", "2a_current"]
VARIANTS = ["q", "q+r", "r", "q+h", "h", "q+r+h"]
VAR_TEXT = {"q": "query", "q+r": "query + reasoning", "r": "reasoning only", "q+h": "query + HyDE passage",
            "h": "HyDE passage only", "q+r+h": "query + reasoning + HyDE"}


def week5(root):
    R = os.path.join(root, "research", "runs_v13")
    L = ["# Week 5: neutral tie-break, LLM query reasoning, passage-level scoring, reasoning embedder", "",
         "Same machine and data as week 4. Exact score ties are now broken by sha1(doc id) "
         "(`scripts/tiebreak.py`) instead of the doc id. Choices are made on **train** under rules 6–8 "
         "written in `research/LOG.md` before the runs (minimum margin +0.005 macro nDCG@10 and a train "
         "bootstrap lower bound > 0; \"no change\" always allowed); dev is one measurement per configuration.", ""]
    final = jload(os.path.join(R, "final.json"))
    if final:
        L += ["## M. Final systems (week 5) vs week 4", "",
              "| sub-track | system (chosen on train) | train | dev | week-4 dev (doc-id ties) | week-4 system, sha1 ties | dev − week-4 system [95% CI] |",
              "| --- | --- | ---: | ---: | ---: | ---: | --- |"]
        for cond in CONDS:
            r = final.get(cond)
            if r:
                L.append(f"| `{cond}` | {r['system']} | {f4(r['train'])} | **{f4(r['dev'])}** | {f4(r['week4_dev'])} | "
                         f"{f4(r['week4_dev_sha1'])} | {ci(r['dev_boot']) if r.get('dev_boot') else 'same system'} |")
        L += ["", "Train numbers of a cross-encoder or embedder stage are on its train subsample (≤ 30 topics per "
              "domain), as the depth/weight was chosen there.", ""]
    cmp_ = jload(os.path.join(R, "tiebreak/compare.json"))
    if cmp_:
        L += ["## N. Tie key: doc id (week 4) vs sha1(doc id) (week 5)", "",
              "| sub-track | system | train id | train sha1 | dev id | dev sha1 |", "| --- | --- | ---: | ---: | ---: | ---: |"]
        for cond in CONDS:
            for s, r in cmp_[cond].items():
                L.append(f"| `{cond}` | {s} | {f4(r['train_old'])} | {f4(r['train_new'])} | {f4(r['dev_old'])} | {f4(r['dev_new'])} |")
        ties = jload(os.path.join(R, "tiebreak/ties.json"))
        if ties:
            agg = {}
            for k, systems in ties.items():
                key, cond, split, _ = k.split("|")
                for s, c in systems.items():
                    a = agg.setdefault((key, cond, split, s), [0, 0, 0])
                    a[0] += c.get("gold_top10", 0)
                    a[1] += c.get("gold_tied", 0)
                    a[2] += c.get("gold_tied_first", 0)
            L += ["", "Gold documents in the top 10 that share their exact score with a non-gold document of the same "
                  "list (dev; `tied first` = ranked above all of its tied non-gold twins):", "",
                  "| sub-track | system | gold in top 10 | tied (id key) | tied first (id) | tied (sha1) | tied first (sha1) |",
                  "| --- | --- | ---: | ---: | ---: | ---: | ---: |"]
            for cond in CONDS:
                for s in ("bm25", "dense", "hybrid", "ce"):
                    o, n = agg.get(("id", cond, "dev", s)), agg.get(("sha1", cond, "dev", s))
                    if o and o[0]:
                        L.append(f"| `{cond}` | {s} | {n[0]} | {o[1]} | {o[2]} | {n[1]} | {n[2]} |")
        L.append("")

    # ------------------------------------------------------------- O. rule 6
    sel6 = {c: jload(os.path.join(R, f"select/rule6_{c}.json")) for c in EXP_CONDS}
    if any(sel6.values()):
        meta = jload(os.path.join(R, "llm/t2/meta.json")) or {}
        L += ["## O. LLM query reasoning (rule 6): query variants, train choice, dev", "",
              f"LLM `{meta.get('model', '')}` (rev {meta.get('revision', '')[:10]}, {meta.get('quant', '')}, vLLM, "
              "temperature 0, ≤ 256 new tokens). `r` = \"reason\" prompt (what is needed + what a relevant document "
              "looks like), `h` = HyDE passage. BM25 on the concatenated text; dense on the normalised mean of the "
              "vectors (r encoded as a query, h as a document). Encoders: Track 1 bge-small L256, Track 2 bge-base "
              "L512. Hybrid = BM25 ∪ dense, fusion tuned on train per variant.", ""]
        for c, s in sel6.items():
            if not s:
                continue
            L += [f"**`{c}`** — best on train `{s['best_on_train']}`; adopted: **{'yes' if s['adopted'] else 'no'}** "
                  f"→ `{s['chosen']}`" + (f"; train bootstrap best − q {ci(s['train_bootstrap_best_minus_baseline'])}"
                                          if s.get("train_bootstrap_best_minus_baseline") else "")
                  + (f"; dev chosen − q {ci(s['dev_bootstrap_chosen_minus_baseline'])}"
                     if s.get("dev_bootstrap_chosen_minus_baseline") else ""), "",
                  "| variant | BM25 train | BM25 dev | dense train | dense dev | hybrid train | hybrid dev | dev hybrid − q [95% CI] |",
                  "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |"]
            for v in VARIANTS:
                x = s["candidates"].get(v)
                if not x:
                    continue
                b = s["dev_bootstrap_each_minus_baseline"].get(v)
                L.append(f"| `{v}` {VAR_TEXT[v]} | {f4(x['bm25_train'])} | {f4(x['bm25_dev'])} | {f4(x['dense_train'])} | "
                         f"{f4(x['dense_dev'])} | {f4(x['train'])} | {f4(x['dev'])} | {ci(b) if b else ''} |")
            L.append("")
    rec = jload(os.path.join(R, "recovery/pairs.json"))
    if rec:
        L += ["### Week-4 dev gold categories under the new systems (top 100)", "",
              "Pairs (topic, gold document) from `runs_v12/categories/pairs.jsonl` (week-4 analysis system: bge-small "
              "L512 + BM25, depth 100). Count of pairs whose gold is now in the top 100 of each system's hybrid "
              "(and of its BM25 / dense lists).", "",
              "| system | condition | week-4 category | pairs | hybrid@100 | hybrid@10 | BM25@100 | dense@100 |",
              "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |"]
        for lab, r in rec.items():
            for cat in ("neither", "dense_only", "bm25_only", "bm25_only|beyond_window", "bm25_only|within", "both"):
                v = r["by_category"].get(cat)
                if v:
                    L.append(f"| {lab} | `{r['cond']}` | {cat} | {v['n']} | {v['hybrid@100']} | {v['hybrid@10']} | "
                             f"{v['bm25@100']} | {v['dense@100']} |")
        L.append("")

    # ------------------------------------------------------------- P. rule 7
    sel7 = {c: jload(os.path.join(R, f"select/rule7_{c}.json")) for c in EXP_CONDS}
    if any(sel7.values()):
        L += ["## P. Passage-level dense scoring, MaxP (rule 7)", "",
              "Document score = max over 510-token windows with 128 overlap (first window = the L512 cache; windows "
              "2+ only for documents > 510 tokens, ≤ 200 per document). Track 1 bge-small, Track 2 bge-base.", ""]
        for c, s in sel7.items():
            if not s:
                continue
            L += [f"**`{c}`** — baseline `{s['baseline']}`; best on train `{s['best_on_train']}`; adopted: "
                  f"**{'yes' if s['adopted'] else 'no'}** → `{s['chosen']}`"
                  + (f"; train bootstrap {ci(s['train_bootstrap_best_minus_baseline'])}"
                     if s.get("train_bootstrap_best_minus_baseline") else ""), "",
                  "| candidate | dense train | dense dev | hybrid train | hybrid dev |", "| --- | ---: | ---: | ---: | ---: |"]
            for k, x in s["candidates"].items():
                L.append(f"| {k} | {f4(x['dense_train'])} | {f4(x['dense_dev'])} | {f4(x['train'])} | {f4(x['dev'])} |")
            L.append("")
        man = jload(os.path.join(R, "maxp/index_summary.json"))
        if man:
            L += ["| track | docs | docs with extra passages | extra passages | encode (s) |", "| --- | ---: | ---: | ---: | ---: |"]
            for t, m in man.items():
                L.append(f"| {t} | {m['n_docs']:,} | {m['docs_with_extra_passages']:,} | {m['extra_passages']:,} | {m['encode_s']:.0f} |")
            L.append("")

    # ------------------------------------------------------------- Q. cross-encoder and reasoning embedder
    ce = jload(os.path.join(R, "ce_final/t2.json"))
    if ce:
        L += ["## Q. Cross-encoder over the week-5 Track-2 current-turn hybrid", "",
              "| input hybrid | N=0 train | N=10 | N=20 | N=50 | chosen N | dev N=0 | dev chosen | dev CE − hybrid [95% CI] |",
              "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |"]
        for cond, r in ce.items():
            b = r["by_depth"]
            L.append(f"| `{cond}` | {f4(b['0']['train_macro'])} | {f4(b['10']['train_macro'])} | {f4(b['20']['train_macro'])} | "
                     f"{f4(b['50']['train_macro'])} | {r['chosen_depth_on_train']} | {f4(b['0']['dev_macro'])} | "
                     f"{f4(b[str(r['chosen_depth_on_train'])]['dev_macro'])} | {ci(r['dev_bootstrap_ce_minus_hybrid'])} |")
        L.append("")
    re_ = {t: jload(os.path.join(R, f"reason/t{t}_reasonembed-4b.json")) for t in (1, 2)}
    if any(re_.values()):
        L += ["## R. Reasoning embedder (ReasonEmbed-Qwen3-4B, NF4) over the hybrid pool (rule 8)", "",
              "| condition | none train | none dev | best on train | its train | its dev | train boot best − none | docs encoded | encode (s) |",
              "| --- | ---: | ---: | --- | ---: | ---: | --- | ---: | ---: |"]
        for t, rep in re_.items():
            for cond, r in (rep or {}).items():
                if "best_on_train" not in r:
                    continue
                bh = r["by_how"]
                L.append(f"| `{cond}` | {f4(bh['none=0']['train'])} | {f4(bh['none=0']['dev'])} | `{r['best_on_train']}` | "
                         f"{f4(bh[r['best_on_train']]['train'])} | {f4(bh[r['best_on_train']]['dev'])} | "
                         f"{ci(r['train_bootstrap_best_minus_none']) if r.get('train_bootstrap_best_minus_none') else ''} | "
                         f"{r['docs_encoded']:,} | {r['encode_s']:.0f} |")
        L.append("")
    return L
