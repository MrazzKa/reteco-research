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
    r14b = jload(os.path.join(R, "select", "rule14b_train.json"))
    if r14b:
        L += _breakdown(r14b, "Rule 14b (phase B): the main pipeline on answer-free histories vs the rule-14 run, train subsample")
    ens = sorted(glob.glob(os.path.join(R, "ensemble", "rule18_*.json")))
    if ens:
        L += ["## AG. Second reasoning embedder: Qwen3-Embedding-4B, alone and averaged with ReasonEmbed (rule 18, phase B)", "",
              "Same top-50 pool as the current system; E = mean of z(ReasonEmbed) and z(Qwen3-Embedding) per topic; way "
              "(top-N or interpolation weight) chosen on the train subsample. ReasonIR-8B was excluded (training positives "
              "drawn from the BRIGHT datastore; LOG 2026-11-10 09:58).", "",
              "| condition | current (ReasonEmbed) train / dev | Qwen3-Emb alone: way, train / dev | ensemble: way, train / dev | "
              "ensemble − current, train | dev | adopted |", "| --- | --- | --- | --- | --- | --- | --- |"]
        for p_ in ens:
            x = jload(p_)
            so, eb = x["second_only_best"], x["ensemble_best"]
            L.append(f"| {x['cond']} | {f4(x['current']['train'])} / {f4(x['current']['dev'])} | {so['how']}: {f4(so['train'])} / "
                     f"{f4(so['dev'])} | {eb['how']}: {f4(eb['train'])} / {f4(eb['dev'])} | {ci(eb['train_minus_current'])} | "
                     f"{ci(eb['dev_minus_current'])} | {x['adopted']} |")
        L += [""]
    cold = jload(os.path.join(R, "cold", "cold_report.json"))
    if cold:
        L += ["## AH. Cold run on a slice of a synthetic test release (B3, phase B)", "",
              cold.get("about", ""), "", "| part | topics | wall time | per topic | notes |", "| --- | ---: | ---: | ---: | --- |"]
        for r in cold["rows"]:
            L.append(f"| {r['part']} | {r['topics']} | {r['wall_s']:.0f} s | {r['per_topic_s']:.2f} s | {r.get('notes', '')} |")
        L += ["", cold.get("estimate", ""), ""]
    c1 = jload(os.path.join(R, "cold_full", "c1_report.json"))
    if c1:
        tm = c1["timing"]
        L += ["## AK. Full cold dress rehearsal of the submission (C1, 2026-11-10/11)", "",
              "All dev topics as a synthetic test release (gold fields removed, earlier answers kept), every cache empty, "
              "`submit.py` with exactly the submission runs; official format_checker + scorer on dev qrels. Pass "
              "criteria written before the run (LOG 2026-11-10 21:45): no crash, checker exit 0 everywhere, 2a_auto picks "
              "the main run in 11/11 domains, every run within ±0.005 of its research dev number. Paused by the user "
              "after the 1a runs and resumed (1b then ran with the Track-1 LLM texts already generated).", "",
              "| run | official (cold) | research (warm) | cold − warm [95% CI] | within ±0.005 | checker / sanity |",
              "| --- | ---: | ---: | --- | --- | --- |"]
        for v, x in c1["runs"].items():
            L.append(f"| {v} | {f4(x['official'])} | {f4(x['research'])} | {ci(x['cold_minus_warm'])} | "
                     f"{'yes' if x['within_tol'] else '**no**'} | {'ok' if x['checker_ok'] else 'FAIL'} / "
                     f"{'ok' if x['sanity_ok'] else 'FAIL'} |")
        g = c1["generations"]
        L += ["", f"2a_auto: {c1['auto_2a']}. LLM generations of the cold run: identical to the B3b fresh draw "
              + ", ".join(f"{k} {x['identical_to_b3b_fresh']}/{x['cold']}" for k, x in g.items())
              + "; identical to the research cache " + ", ".join(f"{k} {x['identical_to_research_cache']}/{x['cold']}"
                                                              for k, x in g.items())
              + ". So vLLM output is reproducible for the same set of inputs in one call; it changes with batch "
              "composition. The only run outside the tolerance is the 1a hybrid without ReasonEmbed (+0.015): its only "
              "difference from the warm run is the LLM texts, and ReasonEmbed (w 0.8) damps the same change to −0.001 "
              "in `1a`. `2a_history_q` uses no LLM; its −0.0002 comes from ReasonEmbed vectors computed in other batches.", "",
              "| run | topics | wall time | BM25 index | ReasonEmbed (new docs) | reranker (new pairs) |",
              "| --- | ---: | ---: | ---: | --- | --- |"]
        for r in tm["rows"]:
            L.append(f"| {r['variant']} | {r['topics']} | {r['wall_s'] / 60:.1f} min | {r['bm25_index_s']:.0f} s | "
                     f"{r['reasonembed_s']:.0f} s ({r['reasonembed_new_docs']}) | {r['llm_rerank_s']:.0f} s "
                     f"({r['llm_rerank_new_pairs']}) |")
        L += ["", f"Pre-generation of all LLM texts: Track 1 {tm['pregenerate_s']['1']:.0f} s, Track 2 "
              f"{tm['pregenerate_s']['2']:.0f} s. Wall time: Track 1 {tm['wall_s_track']['1'] / 3600:.2f} h, Track 2 "
              f"{tm['wall_s_track']['2'] / 3600:.2f} h, total {tm['wall_s_total'] / 3600:.2f} h for 519 1a queries, 1,214 "
              f"1b steps and 858 2a turns. Scaled to the test (350 / 820 / 200; BM25 indexing per domain kept fixed): "
              f"≈ {tm['test_estimate_s'] / 3600:.1f} h ("
              + ", ".join(f"{k} {v / 60:.0f} min" for k, v in tm["test_estimate_by_sub_s"].items())
              + ", plus pre-generation).", ""]
    nd = jload(os.path.join(R, "nondet", "report.json"))
    if nd:
        L += ["## AI. Run-to-run noise from LLM nondeterminism on dev (B3b, analysis)", "",
              "vLLM at temperature 0 is not batch-invariant: a fresh generation of the same inputs differs. Dev runs rebuilt "
              "with an empty LLM cache (ReasonEmbed and reranker caches shared) against the cached runs.", "",
              "| variant | cached (reported) | fresh draw | fresh − cached [95% CI] |", "| --- | ---: | ---: | --- |"]
        for v, x in nd["variants"].items():
            L.append(f"| {v} | {f4(x['cached'])} | {f4(x['fresh'])} | {ci(x['fresh_minus_cached'])} |")
        L += ["", "Identical generations (fresh vs cached): " + ", ".join(
            f"{k} {x['identical']}/{x['fresh']}" for k, x in nd["generations"].items()) + ".", ""]
    r13 = [(c, jload(os.path.join(R, "select", f"rule13_{c}_hybrid.json"))) for c in ("1b", "1a")]
    r13 = [(c, x) for c, x in r13 if x]
    if r13:
        L += ["## AJ. Several sampled HyDE passages on Track 1 (rule 13, phase B)", "",
              "n HyDE passages at temperature 0.7 (BM25: concatenated; dense: mean vector) against one at temperature 0; "
              "hybrid fused on full train. For 1b the hybrid stage adopted n = 5, but with ReasonEmbed on top the gain "
              "is +0.0023 [−0.0048, +0.0094] on train (dev +0.0031) — not adopted (LOG 18:41).", "",
              "| sub-task | candidate | hybrid train | hybrid dev |", "| --- | --- | ---: | ---: |"]
        for c, x in r13:
            for k, v in x["candidates"].items():
                L.append(f"| {c} | {k} | {f4(v['train'])} | {f4(v['dev'])} |")
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
