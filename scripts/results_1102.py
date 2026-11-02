"""2026-11-02 tables for research/RESULTS.md (called by make_results.py): foreign gold (rule 10), the
2a-with-history pipeline (rules 11-12), the contamination ablation (step 4), the end-to-end submission
check and the final table. Every number is read from a run output under research/runs_v13/; sections
are skipped when their inputs do not exist yet.
"""
import json
import os

from results_week4 import ci, f4, jload

BRIGHT = {"psychology", "biology", "sustainable_living", "robotics", "earth_science", "economics"}
CONDS = [("1a", "1a"), ("1b", "1b_query+step"), ("2a_current", "2a current turn"), ("2a_history", "2a with history")]


def pct(v):
    return "" if v is None else f"{100 * v:.2f}%"


def src_macro(per_dom, src):
    vals = [sum(v) / len(v) for d, v in per_dom.items() if v and ((d in BRIGHT) == (src == "bright"))]
    return sum(vals) / len(vals) if vals else None


def week6(root):
    R = os.path.join(root, "research", "runs_v13")
    L = ["# 2026-11-02: foreign gold, submission pipeline, 2a with history, contamination ablation", "",
         "Rules 10–13 were written in `research/LOG.md` before the runs they govern (train decides; margin +0.005 "
         "and train bootstrap lower bound > 0; dev measured once per configuration).", ""]
    fin = jload(os.path.join(R, "final_1102.json"))
    if fin:
        L += ["## X. Submission systems (2026-11-02)", "",
              "Train = rule-8 subsample (≤ 30 topics per domain, seed 20260921) for every row. Test-like = topics none "
              "of whose gold is gold for a topic of the other split. Foreign gold = train/dev gold of another query "
              "of the domain (on test all of them are negatives).", "",
              "| sub-task | run | what is in it | train | dev | dev, test-like topics (n) | foreign gold in dev top 10 |",
              "| --- | --- | --- | ---: | ---: | --- | ---: |"]
        for row in fin["rows"]:
            L.append(f"| {row['sub']} | {row['role']} `{row['run_id']}` | {row['what']} | {f4(row['train'])} | "
                     f"{f4(row['dev'])} | {f4(row['dev_testlike'])} ({row['n_testlike']}) | {pct(row['foreign_dev'])} |")
        L += [""] + [f"- {n}" for n in fin.get("notes", [])] + [""]
    F = jload(os.path.join(R, "foreign", "report.json"))
    if F:
        L += ["## T. Foreign gold: how much do the systems lean on train/dev gold? (step 1, rule 10)", "",
              "`scripts/foreign_gold.py`. Foreign-gold share = share of the top-10 slots taken by gold documents of "
              "*other* queries of the domain (other steps of the same 1b query and other turns of the same "
              "conversation are not foreign); corpus share = the same documents as a share of the corpus. Long = "
              "> 510 tokens. Removed = nDCG@10 after deleting all foreign gold from the ranking.", ""]
        for cond, label in CONDS:
            if cond not in F:
                continue
            L += [f"### {label}", "",
                  "| stage | split | n | nDCG@10 | foreign in top 10 | foreign in corpus | long in top 10 | "
                  "foreign share of long docs in top 10 (corpus) | test-like n | nDCG@10 test-like | nDCG@10, foreign removed |",
                  "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: |"]
            for stage, views in F[cond].items():
                for view in ("train", "train_sub", "dev"):
                    r = views.get(view)
                    if not r:
                        continue
                    L.append(f"| {stage} | {view} | {r['n_topics']} | {f4(r['ndcg10'])} | {pct(r['foreign_share_top10'])} | "
                             f"{pct(r['foreign_share_corpus'])} | {pct(r['long_share_top10'])} | "
                             f"{pct(r['foreign_share_of_long_in_top10'])} ({pct(r['gold_share_of_long_in_corpus'])}) | "
                             f"{r['n_testlike']} | {f4(r['ndcg10_testlike'])} | {f4(r['ndcg10_foreign_removed'])} |")
            L.append("")
        r10 = F.get("rule10")
        if r10:
            t, d = r10["train_sub"], r10["dev"]
            L += ["**Rule 10** (2a current; A = ReasonEmbed over the MaxP pool, B = over the no-MaxP pool):", "",
                  "| | foreign share A − B | A − B, all topics | A − B, test-like topics (n) |", "| --- | ---: | --- | --- |",
                  f"| train (subsample) | {t['foreign_share_diff_pp']:+.2f} pp | {ci(t['all_A_minus_B'])} | "
                  f"{ci(t['testlike_A_minus_B'])} ({t['n_testlike']}) |",
                  f"| dev | {d['foreign_share_diff_pp']:+.2f} pp | {ci(d['all_A_minus_B'])} | "
                  f"{ci(d['testlike_A_minus_B'])} ({d['n_testlike']}) |", "",
                  f"Decision: **{r10['decision']}**.", ""]
    r11 = jload(os.path.join(R, "select", "rule11.json"))
    if r11:
        L += ["## V. 2a with history: week-5 pipeline (rules 11, 12)", "",
              "H0 = week-4 history hybrid (no LLM). Ha / Hb = q+r+h hybrid, q = history text with the current question "
              "first; LLM input = current question + last ≤ 3 earlier questions (a) or questions and answers (b).", "",
              "| system | fusion (train) | train | dev | dev − H0 [95% CI] |", "| --- | --- | ---: | ---: | --- |"]
        for k in ("H0", "Ha", "Hb"):
            c = r11["cfg"][k]
            L.append(f"| {k} | {c['norm']} α {c['alpha']} | {f4(r11['train'][k])} | {f4(r11['dev'][k])} | "
                     f"{ci(r11['dev_minus_H0'][k]) if k in r11['dev_minus_H0'] else ''} |")
        L += ["", "Train tests: " + "; ".join(f"{k} {ci(v)}" for k, v in r11["train_tests"].items())
              + f". Hybrid-stage choice: **{r11['chosen']}**.", ""]
        rep = jload(os.path.join(R, "reason", "t2_reasonembed-4b.json")) or {}
        row = rep.get("2ah_hybrid")
        if row:
            bh = row["by_how"]
            L += ["ReasonEmbed over the top 50 of the chosen history hybrid (train subsample / dev):", "",
                  "| use | train | dev |", "| --- | ---: | ---: |"]
            for k in ("none=0", "top=10", "top=50", "interp=0.5", "interp=0.7", "interp=0.8", "interp=0.9"):
                if k in bh:
                    L.append(f"| {k} | {f4(bh[k]['train'])} | {f4(bh[k]['dev'])} |")
            tb = row.get("train_bootstrap_best_minus_none")
            L += ["", f"Best on train: {row['best_on_train']}; train − none {ci(tb) if tb else '—'}; "
                  f"dev − none {ci(row['dev_bootstrap_best_minus_none'])}.", ""]
    r12 = jload(os.path.join(R, "select", "rule12.json"))
    if r12:
        L += [f"**Rule 12** (main 2a run): train current {f4(r12['train']['current'])} vs history "
              f"{f4(r12['train']['history'])}, history − current {ci(r12['train_history_minus_current'])} → "
              f"**{r12['decision']}**.", ""]
    bd = jload(os.path.join(R, "foreign", "t2_breakdown_dev.json"))
    if bd:
        labs = list(bd)
        groups = ["first_turn", "recycled_gold", "new_gold"]
        depths = sorted({b for v in bd.values() for b in v["depth"]})
        L += ["### Track 2 dev by turn group and depth (nDCG@10, mean over turns; macro = official)", "",
              "| system | macro | " + " | ".join(f"{g} (n={bd[labs[0]]['groups'][g]['n']})" for g in groups) + " | "
              + " | ".join(f"{b} (n={bd[labs[0]]['depth'][b]['n']})" for b in depths) + " |",
              "| --- | ---: | " + " | ".join("---:" for _ in groups + depths) + " |"]
        for lab, v in bd.items():
            L.append(f"| {lab} | {f4(v['macro'])} | " + " | ".join(f4(v["groups"][g]["ndcg10"]) for g in groups) + " | "
                     + " | ".join(f4(v["depth"][b]["ndcg10"]) for b in depths) + " |")
        L.append("")
    llama = {t: jload(os.path.join(R, "llama", t, "hybrid.json")) for t in ("t1", "t1b", "t2")}
    if any(llama.values()):
        L += ["## W. Contamination ablation: an LLM that predates BRIGHT (step 4, no choice)", "",
              "Llama-3.2-3B-Instruct (knowledge cutoff December 2023, BRIGHT released July 2024; ungated mirror "
              "`unsloth/Llama-3.2-3B-Instruct`, FP8 in vLLM) vs Qwen3-4B-Instruct-2507 (released 2025), same prompts, "
              "temperature 0. q+r+h hybrid tuned on train per LLM; q = no expansion.", "",
              "| condition | split | q (no LLM) | Qwen3-4B q+r+h | Llama-3.2-3B q+r+h | Qwen gain | Llama gain | "
              "BRIGHT: Qwen / Llama gain | StackExchange: Qwen / Llama gain |",
              "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |"]
        spec = {"t2": ("2a current", f"{R}/qexp/t2/hybrid_2a_current.json", "2a_current"),
                "t1": ("1a", f"{R}/qexp/t1/hybrid_1a.json", "1a"),
                "t1b": ("1b", f"{R}/qexp/t1/hybrid_1b.json", "1b_query+step")}
        for t, (label, qpath, cond) in spec.items():
            if not llama[t]:
                continue
            qrep = json.load(open(qpath))["conditions"]
            q, qw, ll = qrep[f"{cond}__q"], qrep[f"{cond}__q+r+h"], llama[t]["conditions"][f"{cond}__q+r+h"]
            for sp in ("train", "dev"):
                key = f"{sp}_per_topic"
                pq, pw, pl = q[key]["linear*"], qw[key]["linear*"], ll[key]["linear*"]
                mq = q["systems"]["linear*"][f"{sp}_macro"]
                mw = qw["systems"]["linear*"][f"{sp}_macro"]
                ml = ll["systems"]["linear*"][f"{sp}_macro"]
                if t == "t2":
                    sb = (f"{src_macro(pw, 'bright') - src_macro(pq, 'bright'):+.4f} / "
                          f"{src_macro(pl, 'bright') - src_macro(pq, 'bright'):+.4f}")
                    ss = (f"{src_macro(pw, 'se') - src_macro(pq, 'se'):+.4f} / "
                          f"{src_macro(pl, 'se') - src_macro(pq, 'se'):+.4f}")
                else:
                    sb = ss = "n/a (TEMPO)"
                L.append(f"| {label} | {sp} | {f4(mq)} | {f4(mw)} | {f4(ml)} | {mw - mq:+.4f} | {ml - mq:+.4f} | {sb} | {ss} |")
        abl = jload(os.path.join(R, "llama", "bootstrap.json"))
        if abl:
            L += ["", "Paired bootstrap (dev): " + "; ".join(f"{k} {ci(v)}" for k, v in abl.items()) + "."]
        L.append("")
    r13 = jload(os.path.join(R, "select", "rule13_hybrid.json"))
    h5 = jload(os.path.join(R, "hyde5", "t2", "hybrid.json"))
    if r13 and h5:
        L += ["## Y. Several sampled HyDE passages (rule 13), 2a with history", "",
              "HyDE sampled at temperature 0.7 (vLLM, seed 0, n = 5 per input; n = 3 = first three), reason text unchanged; "
              "BM25 = q + r + all passages, dense = normalised sum of e(q), e(r) and the mean of the passage vectors. "
              "Baseline = the rule-11 Hb hybrid (one passage at temperature 0).", "",
              "| HyDE | train | dev |", "| --- | ---: | ---: |",
              f"| 1 passage, temperature 0 (baseline) | {f4(r13['candidates']['n1_t0']['train'])} | {f4(r13['candidates']['n1_t0']['dev'])} |"]
        for c, lab in (("2a_hist3qa__q+r+h1s", "1 sample, temperature 0.7 (reported only)"),
                       ("2a_hist3qa__q+r+h3", "3 samples"), ("2a_hist3qa__q+r+h5", "5 samples")):
            sy = h5["conditions"][c]["systems"]["linear*"]
            L.append(f"| {lab} | {f4(sy['train_macro'])} | {f4(sy['dev_macro'])} |")
        L += ["", f"Choice on train: **{r13['chosen']}** (adopted = {r13['adopted']}); not run for 1a / 1b (time).", ""]
    sc = jload(os.path.join(R, "submit_check.json"))
    if sc:
        L += ["## U. End-to-end submission check (dev, `scripts/submit.py` from the topic files, official tools)", "",
              "Runs written from `configs/submission.json` (generations and document vectors from cache), checked with "
              "`starter_kit/format_checker.py`, scored per domain with `starter_kit/scorer.py`, macro over domains.", "",
              "| variant | topics | official macro nDCG@10 | research dev | difference | checker errors | missing / dup / unknown | "
              "time per topic (s): BM25 index+search, dense, fusion, ReasonEmbed |",
              "| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |"]
        for v, r in sc.items():
            ch = r["checks"].values()
            pt = r["per_topic_s"]
            L.append(f"| {v} | {r['n_topics']} | {f4(r['official_macro_ndcg10'])} | {f4(r['research_dev'])} | "
                     f"{r['diff_vs_research']:+.4f} | {sum(c['format_checker_exit'] != 0 for c in ch)} | "
                     f"{sum(c['judged_missing'] for c in ch)} / {sum(c['duplicates'] for c in ch)} / "
                     f"{sum(c['unknown_docs'] for c in ch)} | "
                     f"{pt.get('bm25_index_s', 0) + pt.get('bm25_search_s', 0):.2f}, "
                     f"{pt.get('dense_index_load_s', 0) + pt.get('dense_search_s', 0):.2f}, {pt.get('fusion_s', 0):.3f}, "
                     f"{pt.get('reasonembed_s', 0):.2f} |")
        L += ["", "Dev timings exclude the LLM and ReasonEmbed (both cached). Test-time estimate (LOG 2026-11-02 13:50–14:22): "
              "LLM ≈ 6–10 min for ~350 1a queries, ~820 1b steps and ~200 2a turns; BM25 indexes ≈ 11 min; ReasonEmbed on "
              "≈ 35–40k new pool documents (only 9–15% of dev pool documents were already in the train pools) at 7–8 docs/s "
              "≈ 75–90 min; total ≈ 1.75–2 h on the RTX 4060 laptop, restartable.", ""]
    return L
