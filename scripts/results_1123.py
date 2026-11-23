#!/usr/bin/env python3
"""RESULTS sections of the 2026-11-23 session (called by make_results.py): AQ query variants (N1), AR Track-1
guidance (N2a / rule 20), AS one answer-free system (N3), AT several LLM draws (N4), AU test readiness (N6),
AV paper tables (N5). Every number is read from a report under research/runs_v13."""
import json
import os

from results_week4 import f4, jload

CONDS = (("1a", "1a"), ("1b", "1b"), ("2a_current", "2a current (B)"), ("2a_history", "2a history (Hb, no reranker)"))
VARS = ("q", "q+r", "q+h", "q+r+h")


def _ci(x):
    return f"[{f4(x[0])}, {f4(x[1])}]" if x else ""


def _b(b):
    if not b:
        return "–"
    return f"{b['diff']:+.4f} [{b['ci95'][0]:+.4f}, {b['ci95'][1]:+.4f}]"


def week9(root):
    R = os.path.join(root, "research", "runs_v13")
    L = ["# 2026-11-23: query variants, Track-1 guidance (rule 20), M0 as a run, LLM draws, test readiness", "",
         "Organisers' mail of 18.11 / 21.11 (Track-1 query-side guidance is a test input; BRIGHT-trained retrievers "
         "allowed on Track 1) and the supervisor's decisions of 19.11 are recorded in `research/LOG.md` (entry "
         "2026-11-23 12:55). Rules N1–N4 and rule 20 were written before the runs they govern.", ""]
    n1 = jload(os.path.join(R, "n1", "report.json"))
    if n1:
        V = n1["variants"]
        L += ["## AQ. Query variants through the whole final system (N1, analysis, no choice)", "",
              "Final system = the variant's train-chosen hybrid + ReasonEmbed over the top 50 with the way chosen on the "
              "rule-8 train subsample (every variant met the rule-8 margin unless marked). q = the question with no "
              "LLM (2a history: the released history text = H0); r = LLM reasoning; h = HyDE passage. Train = rule-8 "
              "subsample; dev = all topics, 95% bootstrap interval of the macro; Δ = paired difference to q+r+h "
              "(topics resampled within domain, 10,000, seed 20260921).", "",
              "| task | system | ReasonEmbed | train | dev [95% CI] | Δ dev vs q+r+h [95% CI] | Δ train vs q+r+h |",
              "| --- | --- | --- | ---: | --- | --- | --- |"]
        for c, lab in CONDS:
            for k, nm in (("_bm25_q", "BM25 only (q)"), ("_hybrid_q", "hybrid (q)")):
                x = V[c][k]
                L.append(f"| {lab} | {nm} | – | {f4(x['train'])} | {f4(x['dev'])} {_ci(x['dev_ci'])} | "
                         f"{_b(x['delta_vs_qrh']['dev'])} | – |")
            for v in VARS:
                x = V[c][v]
                way = x["reasonembed_way"] + ("" if x["rule8_margin_met"] else " (margin not met)")
                d = x.get("delta_vs_qrh", {})
                L.append(f"| {lab} | + ReasonEmbed, {'**' + v + '**' if v == 'q+r+h' else v} | {way} | {f4(x['train'])} | "
                         f"{f4(x['dev'])} {_ci(x['dev_ci'])} | {_b(d.get('dev'))} | {_b(d.get('train'))} |")
        L += ["", "Recall@k of the submitted q+r+h hybrid (submission order: fused pool, then dense, then BM25, depth "
              "1,000; train = full split):", "",
              "| task | split | R@10 | R@20 | R@50 | R@100 | R@200 | R@1000 |", "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
        for c, lab in CONDS:
            for sp in ("train", "dev"):
                m = n1["recall"][c][sp]["macro_recall"]
                L.append(f"| {lab} | {sp} | " + " | ".join(f4(m[k]) for k in ("10", "20", "50", "100", "200", "1000")) + " |")
        L += ["", "Where the dev gold documents sit in the q+r+h hybrid list (counts of (topic, gold) pairs):", "",
              "| task | 1–10 | 11–50 | 51–100 | 101–200 | 201–1000 | not retrieved |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
        for c, lab in CONDS:
            g = n1["recall"][c]["dev"]["gold_rank_buckets"]
            L.append(f"| {lab} | " + " | ".join(str(g.get(k, 0)) for k in ("1-10", "11-50", "51-100", "101-200",
                                                                           "201-1000", "not retrieved")) + " |")
        L += ["", "ReasonEmbed cost of a deeper pool (dev; distinct documents per domain, i.e. with a cold cache as on a "
              "test day, divided by the topics; time at 7 and 10 documents/s, RESULTS AF; pool 100 gave nothing "
              "measurable on dev, RESULTS AD):", "",
              "| task | dev topics | corpus docs | pool 50 | pool 100 | pool 200 | pool 1000 |", "| --- | ---: | ---: | --- | --- | --- | --- |"]
        for c, lab in CONDS:
            co = n1["cost"][c]
            cells = [f"{co[f'pool{p}']['docs_per_topic']:.0f}/topic, {co[f'pool{p}']['distinct_docs']:,} docs, "
                     f"{co[f'pool{p}']['minutes_at_10_per_s']:.0f}–{co[f'pool{p}']['minutes_at_7_per_s']:.0f} min"
                     for p in (50, 100, 200, 1000)]
            L.append(f"| {lab} | {co['topics_dev']} | {co['corpus_docs']:,} | " + " | ".join(cells) + " |")
        L.append("")
    rec = jload(os.path.join(R, "guidance", "recon.json"))
    g = jload(os.path.join(R, "guid", "report.json"))
    if rec or g:
        L += ["## AR. Track-1 query-side guidance: reconnaissance (N2a) and rule 20 (separate runs)", ""]
    if rec:
        d8, d5 = rec["ngram"]["dev"]["8"], rec["ngram"]["dev"]["5"]
        nv = rec["novel_terms"]["dev"]
        L += ["g = `guidance.guidance_text`: key_time_anchors + temporal_intent + retrieval_reasoning + the plan actions "
              "(plan gold_ids dropped, `gold_passage_annotations` never read, every g asserted free of corpus ids). "
              f"g has median {rec['g']['dev']['words']['median']} words (dev; {rec['g']['dev']['tokens_reasonembed']['median']} "
              f"ReasonEmbed tokens, max {rec['g']['dev']['tokens_reasonembed']['max']}); gold ids in g: "
              f"{rec['ids']['dev']['g_with_gold_id']} (dev) / {rec['ids']['train']['g_with_gold_id']} (train).", "",
              "| dev (519 queries) | 8-grams in gold | 8-grams in top-10 non-gold | 8-grams in 10 random | 5-grams in gold | 5-grams in top-10 non-gold |",
              "| --- | ---: | ---: | ---: | ---: | ---: |"]
        for s in ("guidance", "llm_reason", "query"):
            L.append(f"| {s} | {d8[s]['gold']['mean_share']:.4f} | {d8[s]['top10_nongold']['mean_share']:.4f} | "
                     f"{d8[s]['random10']['mean_share']:.4f} | {d5[s]['gold']['mean_share']:.4f} | "
                     f"{d5[s]['top10_nongold']['mean_share']:.4f} |")
        L += ["", "| dev | novel words per query | share in gold | in top-10 non-gold | in 10 random |", "| --- | ---: | ---: | ---: | ---: |"]
        for s in ("guidance", "llm_reason"):
            x = nv[s]
            L.append(f"| {s} | {x['n_novel']:.1f} | {x['gold']:.3f} | {x['top10_nongold']:.3f} | {x['random10']:.3f} |")
        sv = rec["steps_vs_plan"]["dev"]
        L += ["", f"1b: every dev step instruction is one of its query's plan actions ({sv['step_is_a_plan_action']} / "
              f"{sv['steps']}; the plans have {sv['plan_actions_of_these_queries']} actions). Examples: "
              "`research/cases/track1_guidance_dev.md`.", ""]
    if g:
        L += ["Rule 20: G1 = g added to BM25, dense and the ReasonEmbed query (LLM texts unchanged); G2 = the LLM also "
              "sees g. Each candidate: fusion on full train, ReasonEmbed way on the train subsample with the rule-8 "
              "margin. Δ = paired bootstrap vs the main run.", "",
              "| task | system | ReasonEmbed | train | dev [95% CI] | Δ train [95% CI] | Δ dev [95% CI] |",
              "| --- | --- | --- | ---: | --- | --- | --- |"]
        for sub, x in g["subtasks"].items():
            L.append(f"| {sub} | main | – | {f4(x['main']['train'])} | {f4(x['main']['dev'])} {_ci(x['main']['dev_ci'])} | – | – |")
            for c in ("G1", "G2"):
                y = x[c]
                star = " ← chosen" if c == x["chosen"] else ""
                L.append(f"| {sub} | {c}{star} | {y['reasonembed_used']} | {f4(y['train'])} | {f4(y['dev'])} {_ci(y['dev_ci'])} | "
                         f"{_b(y['minus_main']['train'])} | {_b(y['minus_main']['dev'])} |")
            L.append(f"| {sub} | G2 − G1 | | | | {_b(x['G2_minus_G1']['train'])} | {_b(x['G2_minus_G1']['dev'])} |")
        L += ["", "Usual adoption margin (≥ +0.005, lower bound > 0) on train for the chosen candidate: " +
              "; ".join(f"{sub} {'met' if x['margin_would_be_met_on_train'] else 'not met'}" for sub, x in g["subtasks"].items()) +
              ". Separate runs `1a_guid` / `1b_guid` (configs/submission.json `_separate_runs`); the main runs are unchanged.", ""]
        for sub, x in g["subtasks"].items():
            dd = x[x["chosen"]]["dev_per_domain_minus_main"]
            L.append(f"Dev per domain, {sub} chosen − main: " + ", ".join(f"{k} {v:+.3f}" for k, v in sorted(dd.items(), key=lambda t: -t[1])) + ".")
        L.append("")
    chk = jload(os.path.join(R, "n3", "check_dev.json"))
    m0 = jload(os.path.join(R, "n3", "m0_vs_h0q_dev.json"))
    if chk or m0:
        L += ["## AS. One answer-free system for the paper: `2a_history_noans` = M0 (N3)", ""]
        if chk:
            c = chk["2a_history_noans"]
            ident = jload(os.path.join(R, "n3", "identical.json")) or {}
            rel = jload(os.path.join(R, "n3", "check_rel_noans.json")) or {}
            fc_ok = all(v.get("format_checker_exit") == 0 for v in rel.get("2a_history_noans", {}).get("checks", {}).values())
            L += [f"`submit.py --variants 2a_history_noans --split dev`: official macro {f4(c['official_macro_ndcg10'])} "
                  f"(research M0 {f4(c['research_dev'])}); ranking identical to the 16.11 M0 dev files in "
                  f"{ident.get('domains_identical_to_m0_1116', ['?', '?'])[0]} / {ident.get('domains_identical_to_m0_1116', ['?', '?'])[1]} "
                  f"domains; synthetic test release without answers: format_checker exit 0 on every file: {fc_ok}.", ""]
        if m0:
            r14b = jload(os.path.join(R, "select", "rule14b_train.json")) or {}
            L += ["| system | train sub | dev | dev first turn | dev recycled | dev new | dev vs M0 [95% CI] |",
                  "| --- | ---: | ---: | ---: | ---: | ---: | --- |"]
            trk = {"M0 (2a_history_noans)": "M0 main pipeline, no answers", "H0q+RE (2a_history_q)": "H0q+RE (rule 14)"}
            for k, x in m0.items():
                gr = x["groups"]
                t = r14b.get(trk.get(k, ""), {}).get("macro")
                L.append(f"| {k} | {f4(t) if t else '–'} | {f4(x['macro'])} | {f4(gr['first_turn']['ndcg10'])} | "
                         f"{f4(gr['recycled_gold']['ndcg10'])} | {f4(gr['new_gold']['ndcg10'])} | {_b(next((v for kk, v in x.items() if kk.startswith('vs_')), None))} |")
            tb = r14b.get("M0 main pipeline, no answers", {}).get("vs_H0q+RE (rule 14)")
            L += ["", f"Last column: system − M0 on dev (paired bootstrap within domain). Train subsample M0 − H0q+RE: "
                  f"{_b(tb)} (rule 14b).", ""]
    n4 = jload(os.path.join(R, "n4", "report.json"))
    if n4:
        L += ["## AT. Several LLM draws (N4, analysis, no choice)", "",
              f"Realisations {n4['realisations']}: 0 = the research generation cache; 1–3 = fresh generations of every "
              "LLM input with the input order shuffled (random.Random(s)), temperature 0, one vLLM call per track. "
              "Everything after the LLM is the frozen submission pipeline (`submit.py --stages`). Mean, SD (n − 1) and "
              "range of the domain-macro nDCG@10; differences are taken within each draw.", "",
              "| system | train mean ± SD | train range | dev mean ± SD | dev range | dev per draw |",
              "| --- | --- | ---: | --- | ---: | --- |"]
        for s, x in n4["systems"]["dev"].items():
            if "mean" not in x:
                continue
            t = n4["systems"]["trainsub"].get(s, {})
            L.append(f"| {s} | {f4(t.get('mean'))} ± {f4(t.get('sd'))} | {f4(t.get('range'))} | {f4(x['mean'])} ± {f4(x['sd'])} | "
                     f"{f4(x['range'])} | {', '.join(f4(v) for v in x['values'])} |")
        L += ["", "| difference | train mean ± SD | train min…max | dev mean ± SD | dev min…max |", "| --- | --- | --- | --- | --- |"]
        for s, x in n4["diffs"]["dev"].items():
            t = n4["diffs"]["trainsub"].get(s, {})
            L.append(f"| {s} | {t.get('mean', 0):+.4f} ± {t.get('sd', 0):.4f} | {t.get('min', 0):+.4f} … {t.get('max', 0):+.4f} | "
                     f"{x['mean']:+.4f} ± {x['sd']:.4f} | {x['min']:+.4f} … {x['max']:+.4f} |")
        ch = n4.get("r0_check", {})
        ok = all(v["equal"] for sp in ch.values() for v in sp.values())
        idg = n4.get("identical_generations", {})
        L += ["", f"r0 reproduces every research number: {ok}. Generations identical to the research cache: " +
              ", ".join(f"{k} {v['identical_to_research']}/{v['n']}" for k, v in idg.items()) + ".", ""]
    ts = jload(os.path.join(R, "testday", "out", "test_summary.json"))
    if ts:
        L += ["## AU. Test readiness: `scripts/run_test.sh` on a synthetic test release from dev (N6)", ""]
        L += ["| run | files | format_checker failures | topics | stage time (s) |", "| --- | ---: | ---: | ---: | ---: |"]
        for v, r in ts["variants"].items():
            tot = sum(x for k, x in (r.get("timing_s") or {}).items() if k.endswith("_s"))
            L.append(f"| `{v}` | {r['files']} | {r['format_checker_fail']} | {r.get('n_topics', '–')} | {tot:.0f} |")
        a2 = ts["variants"].get("2a_auto", {})
        L += ["", f"2a_auto: {a2.get('auto_2a')}; history counters {a2.get('history_counters')}. Problems: "
              f"{ts['problems'] or 'none'}."]
        sc = jload(os.path.join(R, "testday", "score_vs_dev.json"))
        if sc:
            L += ["", "The rehearsal files scored with the dev qrels (official scorer) vs the research numbers: " +
                  ", ".join(f"`{v}` {f4(x['official_macro_ndcg10'])} ({f4(x['research_dev'])})" for v, x in sc.items()) + "."]
        L.append("")
    return L
