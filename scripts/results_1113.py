"""2026-11-16 tables for research/RESULTS.md (called by make_results.py): the submission without pool 100
(section X, superseding the 11-10 table), the `subquestion_reasoning` reconnaissance (AL), rule 19 — SR as a
separate 2a run (AM), the dev breakdown of the main pipeline on answer-free histories (M0, AN), preliminary error
types of the main runs (AO) and the paper tables (AP). Every number is read from a run output under
research/runs_v13/ (or research/cases/, research/paper_tables/); sections are skipped when their inputs do not
exist yet. (File name follows the task list of 13.11; the session ran on 16.11.)
"""
import json
import os

from results_1109 import _breakdown, ci
from results_week4 import f4, jload


def _pct(a, b):
    return f"{a} / {b} ({100.0 * a / b:.1f}%)" if b else f"{a} / {b}"


def week8(root):
    R = os.path.join(root, "research", "runs_v13")
    L = ["# 2026-11-16: submission without pool 100, subquestion_reasoning (rule 19), paper tables, error types", "",
         "Supervisor decisions of 11.11 and organisers' answers of 10.11 / 13.11 / 15.11 are recorded in `research/LOG.md` "
         "(entry 2026-11-16 14:21). Rule 19 was written before any run that uses `subquestion_reasoning`.", ""]
    fin = jload(os.path.join(R, "final_1116.json"))
    if fin:
        nums = jload(os.path.join(root, "research", "paper_tables", "numbers.json")) or {}
        L += ["## X. Submission systems (2026-11-16; pool 100 dropped; supersedes the 2026-11-10 table further down)", "",
              "Pool 100 (rule 17) is dropped for cost by the supervisor's decision of 2026-11-11 (not a train rule): 1a main = "
              "ReasonEmbed over the top 50; the 2a current-turn fallback likewise. Dev = official qrels over the "
              "`scripts/submit.py` files (dev split, warm caches; identical to the research numbers); 95% interval = bootstrap "
              "of the domain macro (topics within domain, 10,000 draws, seed 20260921). Train = rule-8 subsample.", "",
              "| sub-task | run | role | how it is built | train | dev [95% CI] |", "| --- | --- | --- | --- | ---: | --- |"]
        subl = lambda r: "1a" if r["query"] == "1a" else ("1b" if r["query"].startswith("1b") else "2a")
        rank_ = lambda r: (subl(r), 0 if str(r["role"]).startswith("main") else (2 if str(r["role"]).startswith("unused") else 1),
                           -(r["dev"] or 0))
        for r in sorted(fin["rows"], key=rank_):
            if str(r["role"]).startswith("unused"):
                continue
            L.append(f"| {subl(r)} | `{r['run_id']}` | {r['role']} | "
                     f"{r['source']} | {f4(r['train'])} | {f4(r['dev'])} [{f4(r['dev_ci95'][0])}, {f4(r['dev_ci95'][1])}] |")
        un = [r for r in fin["rows"] if str(r["role"]).startswith("unused")]
        if un:
            L += ["", "Unused since 11.11 (kept in the config to reproduce the tables): " +
                  "; ".join(f"`{r['run_id']}` dev {f4(r['dev'])}" for r in un) + "."]
        if fin.get("auto_2a"):
            au = fin["auto_2a"]
            L += ["", f"Main 2a = `2a_auto`: per domain file, earlier answers present → `{au['with_answers']}`, otherwise → "
                      f"`{au['without_answers']}` (organisers, 10.11: the test histories keep the answers)."]
        sc = jload(os.path.join(R, "submit_check_1116.json"))
        if sc:
            bad = [v for v, x in sc.items() if any(c.get("format_checker_exit") != 0 for c in x.get("checks", {}).values())]
            L += ["", f"Official format_checker: exit 0 on every file of {len(sc)} runs" if not bad else
                  f"format_checker failures: {bad}"]
        t = nums.get("compute.no_p100.test_estimate_h")
        if t is not None:
            L += ["", f"Estimated time for the full test without pool 100 (C1 timings, see `research/paper_tables/README.md`): "
                      f"≈ {t} h (with pool 100: {nums.get('compute.with_p100.test_estimate_h', '')} h)."]
        L += [""]
    rc = jload(os.path.join(R, "sr", "recon.json"))
    if rc:
        L += ["## AL. `subquestion_reasoning` (SR): what the field is and whether it leaks gold (S2a, analysis)", "",
              "SR = turn field `subquestion_reasoning`; SRM = `subquestion_reasoning_metadata`. Organisers (10.11): both are "
              "in the Track-2 test turns. `scripts/sr_recon.py`; examples in `research/cases/subquestion_reasoning_dev.md`.", "",
              "| | train | dev |", "| --- | ---: | ---: |"]
        s = rc["structure"]
        L.append(f"| turns with SR (string) | {_pct(s['train']['sr_present'], s['train']['turns'])} | {_pct(s['dev']['sr_present'], s['dev']['turns'])} |")
        L.append(f"| first turns with SR | {_pct(s['train']['sr_present_first'], s['train']['first_turns'])} | "
                 f"{_pct(s['dev']['sr_present_first'], s['dev']['first_turns'])} |")
        for k, lab in (("sr_words_first", "SR words, first turns (median [min, max])"), ("sr_words_later", "SR words, later turns")):
            L.append(f"| {lab} | {s['train'][k]['median']:g} [{s['train'][k]['min']}, {s['train'][k]['max']}] | "
                     f"{s['dev'][k]['median']:g} [{s['dev'][k]['min']}, {s['dev'][k]['max']}] |")
        L.append(f"| SRM keys | {', '.join(f'`{k}`' for k in s['train']['srm_keys'])} | same |")
        for k, v in s["dev"]["srm_words"].items():
            L.append(f"| SRM `{k}` words (median) | {s['train']['srm_words'][k]['median']:g} | {v['median']:g} |")
        ids = rc["ids"]
        for k, lab in (("sr_gold_id", "SR contains a gold doc id"), ("srm_gold_id", "SRM contains a gold doc id"),
                       ("sr_idlike", "SR contains a doc-id-like string"), ("srm_idlike", "SRM contains a doc-id-like string")):
            L.append(f"| {lab} | {ids['train'][k]} | {ids['dev'][k]} |")
        for k, lab in (("sr_gold_title", "BRIGHT turns: gold page title as a phrase in SR"),
                       ("sr_chance_title", "… chance (another conversation's gold titles)"),
                       ("sr_gold_slug", "BRIGHT turns: gold question slug in SR"),
                       ("query_gold_title", "… for comparison: title in the current question"),
                       ("history_gold_title", "… title in the released history"),
                       ("answer_gold_title", "… title in the reference answer")):
            L.append(f"| {lab} | {_pct(ids['train'][k], ids['train']['bright_turns'])} | {_pct(ids['dev'][k], ids['dev']['bright_turns'])} |")
        L += ["", "Share of word n-grams found verbatim (mean over turns; train = rule-8 subsample, dev = all turns):", "",
              "| text | n | split | in gold docs | in top-10 non-gold (main run) | in 10 random docs |", "| --- | ---: | --- | ---: | ---: | ---: |"]
        for src in ("sr", "srm", "answer", "query"):
            for n in ("8", "5"):
                for sp in ("train", "dev"):
                    x = rc["ngram"][sp]["all"][n][src]
                    L.append(f"| {src.upper() if src in ('sr', 'srm') else src} | {n} | {sp} | {f4(x['gold']['mean_share'])} | "
                             f"{f4(x['top10_nongold']['mean_share'])} | {f4(x['random10']['mean_share'])} |")
        nt = rc.get("novel_terms")
        if nt:
            L += ["", "Novel content words (≥ 4 letters, not in the current question or released history): where do they occur?", "",
                  "| text | split | novel words per turn | share in gold | share in top-10 non-gold | share in 10 random |",
                  "| --- | --- | ---: | ---: | ---: | ---: |"]
            for src, lab in (("sr", "SR"), ("llm_reason", "our LLM reason text")):
                for sp in ("train", "dev"):
                    x = nt[sp]["all"][src]
                    L.append(f"| {lab} | {sp} | {x['n_novel']:.1f} | {f4(x['gold'])} | {f4(x['top10_nongold'])} | {f4(x['random10'])} |")
        t1 = rc.get("track1", {})
        if t1:
            g = t1.get("dev_query_guidance_with_gold_id")
            L += ["", f"Track 1: test inputs are `examples` (query) and `steps` (`step_instruction`, already used by 1b). The "
                      f"`guidance_*.jsonl` files are gold-bearing (`query_guidance.retrieval_plan` names a gold id in "
                      f"{g[0]} of {g[1]} dev queries) and are not used."]
        L += ["", "Reading: SR has no id and copies no gold text (0 shared 8-grams), but it is written with knowledge of the "
              "target information (it names entities from the gold / original post that the turn does not mention). Its "
              "text may be used under the task's rules (it is a test input); SRM is not used (scope).", ""]
    sr = jload(os.path.join(R, "sr", "report.json"))
    if sr:
        L += ["## AM. Rule 19: `subquestion_reasoning` as a separate 2a run (no adoption; the main run is unchanged)", "",
              "S1 = BM25 q + r + h + s, dense + e_query(s); S2 = s replaces the LLM reason r. Both: ReasonEmbed / reranker "
              "query = Hb query + \"\\nReasoning: \" + s (history cut to the token limit, never SR); fusion tuned on full "
              "train, ReasonEmbed way and reranker way on the rule-8 train subsample. B + SR = current turn + SR (S1 form, "
              "no reranker); SR only = BM25 / dense / ReasonEmbed on s alone.", "",
              "| system | train | dev | dev BRIGHT | dev StackExchange |", "| --- | ---: | ---: | ---: | ---: |"]
        for r in sr["rows"]:
            L.append(f"| {r['system']} | {f4(r['train'])} | {f4(r['dev'])} | {f4(r['dev_bright'])} | {f4(r['dev_se'])} |")
        d = sr["diffs"]
        L += ["", f"**`2a_history_sr` = {sr['chosen_system']}** (better final train macro). Minus the main run "
                  f"`2a_history_rr`: train {ci(d['train']['all'])}, dev {ci(d['dev']['all'])}; BRIGHT dev {ci(d['dev']['bright'])}, "
                  f"StackExchange dev {ci(d['dev']['se'])}. The usual adoption margin (≥ +0.005, lower bound > 0) would "
                  f"{'be met' if sr['margin_would_be_met_on_train'] else 'not be met'} on train — no adoption either way "
                  f"(supervisor's decision).", "",
              f"Other differences (train / dev): S1 − S2 {ci(d['train']['S1_vs_S2'])} / {ci(d['dev']['S1_vs_S2'])}; "
              f"B + SR − B {ci(d['train']['B+SR_vs_B'])} / {ci(d['dev']['B+SR_vs_B'])}; SR only − B {ci(d['train']['SRonly_vs_B'])} / "
              f"{ci(d['dev']['SRonly_vs_B'])}; SR only − main {ci(d['train']['SRonly_vs_main'])} / {ci(d['dev']['SRonly_vs_main'])}.", "",
              "Stages (fusion on full train; ReasonEmbed and reranker ways on the train subsample):", "",
              "| system | fusion | hybrid train / dev | ReasonEmbed way | + ReasonEmbed train / dev | reranker way | + reranker train / dev |",
              "| --- | --- | --- | --- | --- | --- | --- |"]
        for k, st in sr["stages"].items():
            cfg = st.get("hybrid_cfg") or {}
            fz = f"{cfg.get('norm', '')} α {cfg.get('alpha', '')}" if cfg else ""
            rb = st.get("reasonembed_best") or {}
            rrb = st.get("reranker_by_how_best") or {}
            L.append(f"| {k} | {fz} | {f4(st.get('hybrid_train_full'))} / {f4(st.get('hybrid_dev'))} | {st.get('reasonembed_best_on_train')} | "
                     f"{f4(rb.get('train'))} / {f4(rb.get('dev'))} | {st.get('reranker_best_on_train', '–')} | "
                     f"{f4(rrb.get('train')) if rrb else '–'} / {f4(rrb.get('dev')) if rrb else '–'} |")
        L += [""]
        L += _breakdown(sr["breakdown"]["dev"], "Dev by turn group and depth (mean over turns; macro = official)")
        L += _breakdown(sr["breakdown"]["train"], "Train subsample by turn group and depth")
    m0 = jload(os.path.join(R, "a2", "m0_dev_breakdown.json"))
    if m0:
        L += ["## AN. Cost of the reference answers with M0 (dev breakdown of the frozen main pipeline on answer-free histories)", "",
              "M0 = the main 2a pipeline without reranker (`2a_history`), unchanged, fed histories with every earlier answer removed "
              "(rule 14b candidate; train 0.5220 in RESULTS rule 14b). Dev run: `submit.py --variants 2a_history` on the synthetic "
              "test release from dev with `--strip-answers` (LOG 2026-11-16).", ""]
        L += _breakdown(m0, "Dev by turn group and depth (vs first row: paired bootstrap)")
    er = jload(os.path.join(root, "research", "cases", "error_types_dev.json"))
    if er:
        cats = ["a", "b", "c", "d", "e", "f"]
        names = {"a": "recall miss (no gold in first-stage top 100)", "b": "gold in top 100, not lifted / pushed down",
                 "c": "top 1 looks relevant (judgment gap?)", "d": "temporal mismatch", "e": "LLM expansion drifted",
                 "f": "other"}
        L += ["## AO. Error types of the main runs on dev (S4; labels preliminary, to be confirmed by a human)", "",
              "15 dev topics per sub-task with nDCG@10 ≤ 0.1 (rule LOG 2026-11-16 14:29); topics and labels in "
              "`research/cases/error_types_dev.md`.", "",
              "| sub-task | eligible (≤ 0.1) | " + " | ".join(f"({c}) {names[c]}" for c in cats) + " |",
              "| --- | ---: | " + " | ".join("---:" for _ in cats) + " |"]
        for sub, x in er["subtasks"].items():
            cnt = {c: sum(1 for i in x["items"] if i["label"] == c) for c in cats}
            L.append(f"| {sub} | {x['eligible']} / {x['topics']} | " + " | ".join(str(cnt[c]) for c in cats) + " |")
        L += [""]
    pt = os.path.join(root, "research", "paper_tables")
    if os.path.isdir(pt):
        tex = sorted(f for f in os.listdir(pt) if f.endswith(".tex"))
        L += ["## AP. Paper tables", "", "`scripts/paper_tables.py` writes LaTeX tables (booktabs) and `numbers.json` (every number "
              "cited in the text) to `research/paper_tables/`; the source of each table is in its README: " +
              ", ".join(f"`{t}`" for t in tex) + ".", ""]
    return L
