"""2026-11-10 tables for research/RESULTS.md (called by make_results.py): the submission table (section X,
superseding the 11-02 one), 2a without earlier answers (rule 14, section Z), the cost of reference answers
(A2, section AA), per-source query variant (rule 15, AB), the LLM reranker (rule 16, AC), the ReasonEmbed pool
depth (rule 17, AD) and later phase-B sections. Every number is read from a run output under
research/runs_v13/; sections are skipped when their inputs do not exist yet.
"""
import glob
import json
import os

from results_week4 import f4, jload


def ci(b):
    if not b:
        return ""
    return f"{b['diff']:+.4f} [{b['ci95'][0]:+.4f}, {b['ci95'][1]:+.4f}]"


def week7(root):
    R = os.path.join(root, "research", "runs_v13")
    L = ["# 2026-11-10: 2a without earlier answers, cost of reference answers, per-source variant, LLM reranker", "",
         "Rules 14–17 were written in `research/LOG.md` (entry 2026-11-10 08:13) before the runs they govern "
         "(train decides on the rule-8 subsample; margin +0.005 and train bootstrap lower bound > 0; dev once).", ""]
    fin = jload(os.path.join(R, "final_1110.json"))
    if fin:
        L += ["## X. Submission systems (2026-11-10; supersedes the 2026-11-02 table further down)", "",
              "Dev = official qrels over the `scripts/submit.py` files (identical to the research numbers); 95% interval "
              "= bootstrap of the domain macro (topics resampled within domain, 10,000 draws, seed 20260921). Train = "
              "rule-8 subsample (≤ 30 topics per domain), the number the run was chosen on.", "",
              "| sub-task | run | role | how it is built | train | dev [95% CI] |", "| --- | --- | --- | --- | ---: | --- |"]
        subl = lambda r: "1a" if r["query"] == "1a" else ("1b" if r["query"].startswith("1b") else "2a")
        rank_ = lambda r: (subl(r), 0 if str(r["role"]).startswith("main") else 1, -(r["dev"] or 0))
        for r in sorted(fin["rows"], key=rank_):
            L.append(f"| {subl(r)} | `{r['run_id']}` | {r['role']} | "
                     f"{r['source']} | {f4(r['train'])} | {f4(r['dev'])} [{f4(r['dev_ci95'][0])}, {f4(r['dev_ci95'][1])}] |")
        if fin.get("auto_2a"):
            au = fin["auto_2a"]
            L += ["", f"2a automation (`submit.py --variants 2a_auto`): per domain file, earlier answers present in "
                      f"`conversation_history` → `{au['with_answers']}`, otherwise → `{au['without_answers']}`."]
        L += [""]
    r14 = jload(os.path.join(R, "select", "rule14.json"))
    if r14:
        L += ["## Z. 2a without earlier answers (rule 14)", "",
              "Every earlier answer is removed from every input (BM25 text, dense query, LLM input, ReasonEmbed query; "
              "asserted per topic). H0q = answer-free history text (current question first), BM25 + bge-base hybrid; "
              "Haq = the same with the LLM (input: current + ≤ 3 earlier questions), q+r+h; both + ReasonEmbed over "
              "the top 50 (weight chosen on train). B = current turn only (rule 10).", "",
              "| system | ReasonEmbed weight (train) | train, hybrid only | train | dev |", "| --- | --- | ---: | ---: | ---: |"]
        for k in ("B", "H0q+RE", "Haq+RE"):
            L.append(f"| {k} | {r14['weights'].get(k)} | {f4(r14['re_none'][k]['train'])} | {f4(r14['train_sub'][k])} | "
                     f"{f4(r14['dev'][k])} |")
        L += ["", "Train tests (best minus simpler, bootstrap): " + "; ".join(f"{k} {ci(v)}" for k, v in r14["train_tests"].items()),
              "", f"**Chosen: {r14['chosen']}** (run `{r14['chosen_run']}`). Dev minus B: " +
              "; ".join(f"{k} {ci(v)}" for k, v in r14["dev_minus_B"].items()), ""]
    bd = jload(os.path.join(R, "select", "rule14_breakdown_dev.json"))
    if bd:
        L += _breakdown(bd, "Dev by turn group and depth (mean over turns; macro = official)")
    a2 = jload(os.path.join(R, "a2", "report.json"))
    if a2:
        L += ["## AA. How much does the main 2a run owe to the reference answers? (A2, analysis, no choice)", "",
              "The earlier answers in `conversation_history` were written from the gold documents. Here they are "
              "replaced by answers our LLM writes itself (Qwen3-4B, temperature 0, ≤ 150 words, given the earlier turns "
              "with its own earlier answers, no documents), and the frozen main pipeline is run unchanged (no "
              "re-tuning). Same layout of the history string; only the answer texts differ.", ""]
        for sp in ("trainsub", "dev"):
            if sp in a2:
                L += _breakdown(a2[sp], f"{'Train subsample' if sp == 'trainsub' else 'Dev'}")
        if a2.get("answers"):
            s = a2["answers"]
            L += [f"Generated answers: {s.get('n')} (mean {s.get('mean_words')} words; cut at 256 tokens: "
                  f"{s.get('cut')}).", ""]
    r15 = jload(os.path.join(R, "select", "rule15.json"))
    if r15:
        L += ["## AB. Per-source query variant on Track 2 (rule 15)", "",
              "q-system = plain-query hybrid + ReasonEmbed (weight chosen on the whole train subsample); q+r+h = the "
              "current system. Groups by domain name: BRIGHT = " + ", ".join(r15["groups"]["BRIGHT"]) +
              "; StackExchange = " + ", ".join(r15["groups"]["StackExchange"]) + ".", "",
              "| condition | group | q train | q+r+h train | q − q+r+h train | q dev | q+r+h dev | q − q+r+h dev | chosen |",
              "| --- | --- | ---: | ---: | --- | ---: | ---: | --- | --- |"]
        for cond, res in r15["conditions"].items():
            for g, x in res["groups"].items():
                m = x["macro"]
                L.append(f"| {cond} | {g} | {f4(m['q']['train'])} | {f4(m['q+r+h']['train'])} | {ci(x['train_q_minus_qrh'])} | "
                         f"{f4(m['q']['dev'])} | {f4(m['q+r+h']['dev'])} | {ci(x['dev_q_minus_qrh'])} | {x['chosen']} |")
        L += [""] + [f"- {cond}: q weight {res['q_weight']}, q+r+h weight {res['q+r+h_weight']}; combined system train "
                     f"{f4(res['combined']['train'])} / dev {f4(res['combined']['dev'])} (current {f4(res['all']['q+r+h']['train'])} / "
                     f"{f4(res['all']['q+r+h']['dev'])})" for cond, res in r15["conditions"].items()] + [""]
    rr = sorted(glob.glob(os.path.join(R, "rerank", "rule16_*.json")))
    if rr:
        L += ["## AC. LLM reranker over the final top N (rule 16)", "",
              "Qwen3-Reranker (pointwise yes/no, model-card prompt; NF4 for 4B), score = logit(yes) − logit(no); "
              "document cut to 512 tokens; z-normalised interpolation with the final score over the top N.", "",
              "| condition | model | pairs | none train / dev | reranker only @10 | @20 | best on train | its train / dev | "
              "train best − none | dev best − none | adopted |",
              "| --- | --- | ---: | --- | --- | --- | --- | --- | --- | --- | --- |"]
        for p in rr:
            x = jload(p)
            bh = x["by_how"]
            nk = [k for k in bh if k.startswith("none")][0]
            fmt = lambda k: f"{f4(bh[k]['train'])} / {f4(bh[k].get('dev'))}" if k in bh else ""
            L.append(f"| {x['cond']} | {x['model'][0].split('/')[-1]} | {x['pairs']} | {fmt(nk)} | {fmt('only@10')} | "
                     f"{fmt('only@20')} | {x['best_on_train']} | {fmt(x['best_on_train'])} | "
                     f"{ci(x['train_bootstrap_best_minus_none'])} | {ci(x['dev_bootstrap_best_minus_none'])} | {x['adopted']} |")
        L += [""]
    r17 = jload(os.path.join(R, "select", "rule17_ceiling.json"))
    if r17:
        L += ["## AD. ReasonEmbed pool depth 50 → 100 (rule 17)", "",
              "Share of all gold documents that the frozen hybrid ranks 51–100 (the most a pool of 100 can add).", "",
              "| system | train gold | train recall@50 | train share 51–100 | dev share 51–100 | run at 100? |",
              "| --- | ---: | ---: | ---: | ---: | --- |"]
        for k, v in r17.items():
            L.append(f"| {k} | {v['train']['gold']} | {f4(v['train']['recall50'])} | {100 * v['train']['share_51_100']:.1f}% | "
                     f"{100 * v['dev']['share_51_100']:.1f}% | {'yes' if v['train']['run_rule17'] else 'no (< 3%)'} |")
        L += [""]
        r17b = jload(os.path.join(R, "select", "rule17.json"))
        if r17b:
            L += ["| system | pool 50 train / dev | pool 100 train / dev | train 100 − 50 | chosen |", "| --- | --- | --- | --- | --- |"]
            for k, v in r17b.items():
                L.append(f"| {k} | {f4(v['p50']['train'])} / {f4(v['p50']['dev'])} | {f4(v['p100']['train'])} / "
                         f"{f4(v['p100']['dev'])} | {ci(v['train_boot'])} | {v['chosen']} |")
            L += [""]
    ab = jload(os.path.join(R, "ablation_1110.json"))
    if ab:
        L += ["## AE. Ablation by stage, per sub-task (B5; same topics for every stage)", "",
              "Train = rule-8 subsample, dev = all topics; every stage on exactly the same topics. 95% interval = "
              "bootstrap of the domain macro; Δ = paired difference to the previous stage (topics resampled within "
              "domain). Fusion, ReasonEmbed weight and reranker weight as chosen on train.", ""]
        for name, x in ab.items():
            L += [f"### {name} (train {x['topics']['train']} / dev {x['topics']['dev']} topics)", "",
                  "| stage | train [95% CI] | Δ train | dev [95% CI] | Δ dev | Δ against |", "| --- | --- | --- | --- | --- | --- |"]
            for r in x["rows"]:
                L.append(f"| {r['stage']} | {f4(r['train'])} [{f4(r['train_ci95'][0])}, {f4(r['train_ci95'][1])}] | "
                         f"{ci(r['train_minus_prev'])} | {f4(r['dev'])} [{f4(r['dev_ci95'][0])}, {f4(r['dev_ci95'][1])}] | "
                         f"{ci(r['dev_minus_prev'])} | {r.get('delta_vs') or ''} |")
            L += [""]
    cp = jload(os.path.join(R, "compute_1110.json"))
    if cp:
        L += ["## AF. Compute: models, revisions, throughput (B5)", "", cp["machine"] + ".", "",
              "| stage | model | revision | precision | measured throughput | LOG entry |", "| --- | --- | --- | --- | --- | --- |"]
        for x in cp["components"]:
            L.append(f"| {x['stage']} | {x['model']} | {x['revision']} | {x['precision']} | {x['throughput']} | {x['log']} |")
        L += ["", "End to end: " + cp["end_to_end"] + ".", ""]
    return L


def _breakdown(bd, title):
    L = [f"### {title}", "", "| system | macro | first turn | recycled gold | new gold | T1 | T2 | T3 | T4 | T5+ | vs first row |",
         "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |"]
    for lab, r in bd.items():
        g, dpt = r["groups"], r["depth"]
        cell = lambda d, k: f"{f4(d[k]['ndcg10'])} ({d[k]['n']})" if k in d else ""
        vs = next((v for k, v in r.items() if k.startswith("vs_")), None)
        L.append(f"| {lab} | {f4(r['macro'])} | {cell(g, 'first_turn')} | {cell(g, 'recycled_gold')} | {cell(g, 'new_gold')} | "
                 + " | ".join(cell(dpt, b) for b in ("T1", "T2", "T3", "T4", "T5+")) + f" | {ci(vs)} |")
    return L + [""]
