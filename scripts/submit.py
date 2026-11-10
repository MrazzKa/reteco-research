#!/usr/bin/env python3
"""End-to-end submission runs from the frozen configuration (configs/submission.json).

Input: the topic files of a release split (Track 1 `examples_<split>.jsonl` / `steps_<split>.jsonl`,
Track 2 `benchmark_<split>.json`) and the corpora. qrels are never read. Output: one official run
file per (sub-task variant, domain), `qid Q0 docid rank score run_id`, depth 1000:

  <out>/<variant>/<domain>.txt          (Track-2 topic ids repeat across domains, so one file per domain)
  <out>/<variant>/manifest.json         topics per domain, timings per stage, sanity checks

Pipeline per topic (all frozen in the config):
  1. LLM query reasoning (reason + hyde prompts, temperature 0). Generations are cached by
     sha1(prompt + model + input text), never by topic id; missing ones are generated with vLLM in the
     LLM venv (llm_expand.py --bodies).
  2. BM25 (bm25s, Lucene k1 0.9 b 0.4) on q + r + h; dense (bge, mean of the q / r / h vectors; MaxP over
     510-token passages when the config says so); depth 1000 each, scores kept at 6 decimals as in the
     research runs.
  3. Linear fusion of the two lists (normalisation and alpha from the config) over the union of the
     top kb / kd.
  4. ReasonEmbed-4B (NF4) over the top 50: (1 - w) minmax(fused) + w minmax(embedder).
  Then: positions 1-50 = step 4, then the rest of the fused pool, then the remaining dense and BM25
  documents, cut at 1000. Ties anywhere: sha1(doc id) (scripts/tiebreak.py). No component reads a doc
  id or a document's position in the corpus file to rank.

    python3 submit.py --config ../configs/submission.json --variants 1a 1b 2a \
        --data ../../reteco_data_v11 --split dev --out ../research/runs_v13/submit/dev
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bm25s_run import build, search  # noqa: E402
from dense_index import domain_dir  # noqa: E402
from dense_search import GpuIndex  # noqa: E402
from embed_models import load_encoder  # noqa: E402
from gold_categories import fetch  # noqa: E402
import history as H  # noqa: E402
from hybrid import Query  # noqa: E402
from llm_expand import LLMS, MAX_INPUT_CHARS, clean as llm_clean, history_body, key_of  # noqa: E402
from passage_index import MaxPIndex, pdir  # noqa: E402
from reason_rerank import Embedder, clean as re_clean, instruction, load_cache, rank, save_cache, scored  # noqa: E402
from tie_study import fused, order  # noqa: E402
import tiebreak  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LLM_PY = os.path.expanduser("~/semeval-reteco/.venv-llm/bin/python")


def rp(p):
    return p if os.path.isabs(p) else os.path.join(ROOT, p)


def read_jsonl(p):
    with open(p, encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]


# ---------------------------------------------------------------- topics (no qrels)
def hist_text(t):
    h = t.get("conversation_history", "") or ""
    return "" if h.lower().startswith("no previous") else h


def topics(data, split, cfg, dom):
    """[(topic id, q text, LLM body, ReasonEmbed query text)] in release order."""
    out = []
    q = cfg["query"]
    if cfg["track"] == 1:
        d = os.path.join(data, "track1_tempo", dom)
        if q == "1a":
            for r in read_jsonl(os.path.join(d, f"examples_{split}.jsonl")):
                out.append((r["id"], r["query"], f"Question: {llm_clean(r['query'])}", r["query"]))
        else:  # 1b_query+step
            for r in read_jsonl(os.path.join(d, f"steps_{split}.jsonl")):
                for s in r.get("steps", []):
                    text = f"{r['query']}\n\nStep: {s.get('step_instruction', '')}"
                    body = (f"Question: {llm_clean(r['query'])}\n\nCurrent research step (the document should "
                            f"serve this step): {llm_clean(s.get('step_instruction', ''))}")
                    out.append((s["step_id"], text, body, text))
        return out
    d = os.path.join(data, "track2_recor", dom)
    bench = json.load(open(os.path.join(d, f"benchmark_{split}.json"), encoding="utf-8"))
    bench = [bench] if isinstance(bench, dict) else bench
    for c in bench:
        for t in c["turns"]:
            tid = f"{c['id']}_turn_{t['turn_id']}"
            # label variants of the history are mapped to the canonical "Q: "/"A: " lines (identity on train/dev)
            t = dict(t, conversation_history=H.normalize(t.get("conversation_history", "") or ""))
            if q == "2a_current":
                out.append((tid, t["query"], f"Question: {llm_clean(t['query'])}", t["query"]))
            elif q == "2a_hist3q_qonly":  # rule 14: no earlier answer in any input
                qtext = H.qonly_qfirst(t)
                body = history_body(t, False)
                ans, qs = H.answers(t), H.questions(t)
                for what, x in (("BM25/dense text", qtext), ("LLM input / ReasonEmbed query", body)):
                    H.assert_answer_free(x, ans, what, qs)
                out.append((tid, qtext, body, body))
            else:  # history: q = current question first, then the released history; LLM/embedder see <= 3 turns
                answers = q == "2a_hist3qa"
                qtext = (t["query"] + "\n" + hist_text(t).strip()).strip()
                body = history_body(t, answers)
                out.append((tid, qtext, body, body))
    return out


# ---------------------------------------------------------------- LLM generations
def load_gen(path):
    out = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    out[r["key"]] = r["output"]
    return out


def generations(cfg, bodies, timing):
    lc = cfg["llm"]
    model = LLMS[lc["name"]][0]
    cache = rp(lc["cache"])
    gen = {}
    for p in lc["prompts"]:
        g = load_gen(os.path.join(cache, f"{p}.jsonl"))
        todo = sorted({b for b in bodies if key_of(p, b, model) not in g})
        if todo:
            t0 = time.time()
            with tempfile.TemporaryDirectory() as tmp:
                bp = os.path.join(tmp, "bodies.json")
                json.dump(todo, open(bp, "w", encoding="utf-8"))
                env = dict(os.environ, CC=os.path.expanduser("~/semeval-reteco/tools/bin/cc"))
                subprocess.run([LLM_PY, os.path.join(HERE, "llm_expand.py"), "--track", str(cfg["track"]),
                                "--llm", lc["name"], "--bodies", bp, "--prompts", p, "--out", cache,
                                "--gpu-util", str(lc.get("gpu_util", 0.6)), "--max-seqs", "64",
                                "--max-batched", "2048"], check=True, env=env)
            timing[f"llm_{p}_generate_s"] = round(time.time() - t0, 1)
            timing[f"llm_{p}_generated"] = len(todo)
            g = load_gen(os.path.join(cache, f"{p}.jsonl"))
        gen[p] = {b: g.get(key_of(p, b, model), "") for b in bodies}
    return gen


# ---------------------------------------------------------------- run one variant
def r6(x):
    return float(f"{x:.6f}")  # the research runs went through TREC files with 6 decimals


def run_variant(a, name, cfg, enc_cache):
    tr = cfg["track"]
    sub, key = ("track1_tempo", "id") if tr == 1 else ("track2_recor", "doc_id")
    vdir = os.path.join(a.out, name)
    os.makedirs(vdir, exist_ok=True)
    timing = defaultdict(float)
    manifest = {"variant": name, "run_id": cfg["run_id"], "split": a.split, "domains": {}, "config": cfg}
    doms = a.domains or cfg["domains"]
    # 1. topics + LLM (all domains at once, one vLLM start)
    t0 = time.time()
    tops = {dom: topics(a.data, a.split, cfg, dom) for dom in doms}
    plain = cfg.get("variant") == "q"  # rule 14 H0q: no LLM; BM25 on q, dense on e_query(q)
    if plain:
        gen = {p: defaultdict(str) for p in ("reason", "hyde")}
    else:
        gen = generations(cfg, sorted({b for ts in tops.values() for _, _, b, _ in ts}), timing)
    timing["llm_total_s"] += time.time() - t0
    dc = cfg["dense"]
    if dc["model"] not in enc_cache:
        enc_cache.clear()
        enc_cache[dc["model"]] = load_encoder(dc["model"], dc["max_len"])
    enc = enc_cache[dc["model"]]
    rc = cfg["reasonembed"]
    hcfg = cfg["hybrid"]
    pending = {}
    for dom in doms:
        ts = tops[dom]
        qids = [t[0] for t in ts]
        assert len(set(qids)) == len(qids), f"duplicate topic ids in {dom}"
        texts = {t[0]: (t[1], gen["reason"][t[2]], gen["hyde"][t[2]]) for t in ts}
        # 2a. BM25
        t0 = time.time()
        bm, ids = build(os.path.join(a.data, sub, dom, "documents.jsonl"), key, "lucene")
        timing["bm25_index_s"] += time.time() - t0
        t0 = time.time()
        bq = [(q, texts[q][0] if plain else "\n".join(texts[q])) for q in qids]
        bres = search(bm, ids, bq, "lucene", name, k=1000, threads=8)
        bres = {q: [(d, r6(s)) for d, s in v] for q, v in bres.items()}
        timing["bm25_search_s"] += time.time() - t0
        corpus_ids = set(ids)
        del bm
        # 2b. dense
        t0 = time.time()
        if dc.get("maxp"):
            gi = MaxPIndex(domain_dir(rp(dc["emb"]), dc["model"], 512, tr, dom),
                           pdir(rp(dc["passages"]), dc["model"], tr, dom))
        else:
            gi = GpuIndex(domain_dir(rp(dc["emb"]), dc["model"], dc["max_len"], tr, dom))
        timing["dense_index_load_s"] += time.time() - t0
        t0 = time.time()
        eq = enc.encode_queries([texts[q][0] for q in qids]).astype(np.float32)
        if plain:
            mat = eq
        else:
            er = enc.encode_queries([texts[q][1] for q in qids]).astype(np.float32)
            eh = enc.encode_docs([texts[q][2] for q in qids]).astype(np.float32)
            mat = eq + er + eh
        mat = mat / np.linalg.norm(mat, axis=1, keepdims=True)
        hits = gi.search(mat.astype(np.float32), 1000)
        dres = {q: [(d, r6(s)) for d, s in h] for q, h in zip(qids, hits)}
        gi.free()
        timing["dense_search_s"] += time.time() - t0
        # 3. fusion
        t0 = time.time()
        pools = {q: order(fused(Query(bres[q], dres[q]), hcfg)) for q in qids}
        timing["fusion_s"] += time.time() - t0
        pending[dom] = (ts, pools, bres, dres, corpus_ids)
    # 4. ReasonEmbed over the top `pool` (documents cached per domain by id, as a cache key only)
    t0 = time.time()
    cdir = rp(os.path.join(rc["cache"], f"t{tr}"))
    os.makedirs(cdir, exist_ok=True)
    emb = None
    qcache_path = os.path.join(cdir, "queries")
    qcache = load_cache(qcache_path)
    n_new_docs = 0
    scores = {}
    for dom in doms if rc.get("use", True) else []:
        ts, pools, _, _, _ = pending[dom]
        cache = load_cache(os.path.join(cdir, f"docs_{dom}"))
        need = sorted({d for q in pools for d, _ in pools[q][:rc["pool"]]} - set(cache))
        qc = {"2a_hist3q_qonly": "2a_hist3q"}.get(cfg["query"], cfg["query"])
        ins = instruction(tr, cfg["query"], dom, qc if qc.startswith("2a_hist") else None)
        qtext = {t[0]: f"Instruct: {ins}\nQuery: {re_clean(t[3])}" for t in ts}
        qkey = {q: hashlib.sha1(x.encode("utf-8")).hexdigest() for q, x in qtext.items()}
        q_todo = sorted({qkey[q] for q in qkey if qkey[q] not in qcache})
        if need or q_todo:
            if emb is None:
                emb = Embedder(rc["checkpoint"], 4, rc["max_len"])
            if need:
                got = fetch(a.data, tr, dom, set(need))
                for c in range(0, len(need), 2000):
                    part = need[c:c + 2000]
                    vec = emb.encode([got.get(d, "")[:4000] for d in part], 4)
                    for d, v in zip(part, vec):
                        cache[d] = v
                    save_cache(os.path.join(cdir, f"docs_{dom}"), cache)
                n_new_docs += len(need)
            if q_todo:
                by_key = {qkey[q]: qtext[q] for q in qkey}
                for k_, v in zip(q_todo, emb.encode([by_key[k_] for k_ in q_todo], 4)):
                    qcache[k_] = v
                save_cache(qcache_path, qcache)
        scores[dom] = {q: {d: float(np.dot(qcache[qkey[q]].astype(np.float32), cache[d].astype(np.float32)))
                           for d, _ in pools[q][:rc["pool"]]} for q in pools}
    timing["reasonembed_s"] += time.time() - t0
    timing["reasonembed_new_docs"] = n_new_docs
    # 5. LLM reranker over the top N of the final list (rule 16), scores cached by sha1(instruction + query + doc)
    how = (rc["how"], rc["w"]) if rc.get("use", True) else ("none", 0)
    rerank_head = {}
    lr = cfg.get("llm_rerank")
    if lr and lr.get("use", True):
        import llm_rerank as LR
        t0 = time.time()
        cpath = rp(lr["cache"])
        rcache = LR.load_cache(cpath)
        rr = LR.Reranker(lr["name"], lr["bits"], lr["doc_len"], lr["query_len"], load_model=False)
        n_new = 0
        for dom in doms:
            ts, pools, _, _, _ = pending[dom]
            ins = instruction(tr, lr["instruction_cond"], dom, lr.get("instruction_qcond"))
            finals = {q: [(d, r6(x)) for d, x in scored(pools[q][:rc["pool"]], how, scores[dom][q])] for q in pools}
            need = {d for q in finals for d, _ in finals[q][:lr["depth"]]}
            docs = fetch(a.data, tr, dom, need)
            cd = {d: rr.cut(re_clean(docs.get(d, ""))[:6000], lr["doc_len"]) for d in need}
            items = {}
            for q, _, _, qx in ts:
                cq = rr.cut(re_clean(qx), lr["query_len"])
                for d, _ in finals[q][:lr["depth"]]:
                    it = (ins, cq, cd[d])
                    items[(q, d)] = (hashlib.sha1("\n".join(it).encode("utf-8")).hexdigest(), it)
            miss = sorted({k: it for k, it in items.values() if k not in rcache}.items())
            if miss:
                rr.load()
                sc = rr.score([it for _, it in miss], 4)
                with open(cpath, "a") as f:
                    for (k, _), v in zip(miss, sc):
                        rcache[k] = float(v)
                        f.write(f"{k}\t{float(v):.5f}\n")
                n_new += len(miss)
            for q in finals:
                rs = {d: rcache[items[(q, d)][0]] for d, _ in finals[q][:lr["depth"]]}
                rerank_head[(dom, q)] = LR.rerank(finals[q], (lr["how"], lr["depth"], lr["w"]), rs)
        timing["llm_rerank_s"] += time.time() - t0
        timing["llm_rerank_new_pairs"] = n_new
    # 6. write runs
    n_topics = 0
    for dom in doms:
        ts, pools, bres, dres, corpus_ids = pending[dom]
        path = os.path.join(vdir, f"{dom}.txt")
        seen_topics = set()
        dup = unknown = 0
        with open(path, "w", encoding="utf-8") as f:
            for q, _, _, _ in ts:
                if q in seen_topics:
                    continue
                seen_topics.add(q)
                pool = pools[q][:rc["pool"]]
                if (dom, q) in rerank_head:
                    head = rerank_head[(dom, q)]
                else:
                    head = rank(pool, how, scores[dom][q]) if how[0] != "none" else [d for d, _ in pool]  # none: fused order
                lst, seen = [], set()
                for d in head + [d for d, _ in pools[q][rc["pool"]:]] + [d for d, _ in dres[q]] + [d for d, _ in bres[q]]:
                    if d in seen:
                        continue
                    if d not in corpus_ids:
                        unknown += 1
                        continue
                    seen.add(d)
                    lst.append(d)
                    if len(lst) == 1000:
                        break
                dup += len(lst) - len(set(lst))
                for r, d in enumerate(lst, 1):
                    f.write(f"{q} Q0 {d} {r} {1.0 / r:.6f} {cfg['run_id']}\n")
        n_topics += len(seen_topics)
        manifest["domains"][dom] = {"topics": len(seen_topics), "file": path, "duplicates": dup,
                                    "unknown_docs": unknown}
    manifest["timing_s"] = {k: round(v, 1) for k, v in timing.items()}
    manifest["n_topics"] = n_topics
    manifest["per_topic_s"] = {k: round(v / max(1, n_topics), 3) for k, v in timing.items() if k.endswith("_s")}
    json.dump(manifest, open(os.path.join(vdir, "manifest.json"), "w"), indent=1)
    print(f"[{name}] {n_topics} topics, timing {manifest['timing_s']}", flush=True)
    return manifest


def history_stats(data, split, dom):
    """Counters of the history parser over one Track-2 topic file (no qrels)."""
    bench = json.load(open(os.path.join(data, "track2_recor", dom, f"benchmark_{split}.json"), encoding="utf-8"))
    bench = [bench] if isinstance(bench, dict) else bench
    c = defaultdict(int)
    for conv in bench:
        for t in conv["turns"]:
            c["turns"] += 1
            h = t.get("conversation_history", "") or ""
            try:
                k = int(t["turn_id"])
            except (TypeError, ValueError):
                k = 0
            c["normalized_differs"] += H.normalize(h) != h
            if k < 2 and not H.raw(t).strip():
                continue
            r = H.parse(h)
            c["turns_ge2"] += 1
            c["turns_ge2_with_answer"] += any(a.strip() for _, a in r["pairs"])
            c["qa_pairs"] += len(r["pairs"])
            c["empty_answers"] += sum(1 for _, a in r["pairs"] if not a.strip())
            c["summary_questions"] += len(r["summary"])
            c["unparsed_lines"] += len(r["other"])
            c["empty_history"] += not H.raw(t).strip()
    return dict(c)


def auto_2a(a, conf):
    """Per Track-2 domain: earlier answers present (any turn >= 2 with a non-empty parsed answer) -> the main
    history run, else the rule-14 run without answers. Both variants are always built; the chosen file is
    copied to <out>/2a_auto/<domain>.txt with the decision in decision.json."""
    rule = conf["_auto_2a"]
    va, vq = rule["with_answers"], rule["without_answers"]
    doms = a.domains or conf["variants"][va]["domains"]
    dec = {"rule": rule, "split": a.split, "domains": {}}
    for dom in doms:
        st = history_stats(a.data, a.split, dom)
        chosen = va if st.get("turns_ge2_with_answer", 0) > 0 else vq
        dec["domains"][dom] = {"chosen": chosen, **st}
        print(f"[2a_auto] {dom}: {chosen}  ({json.dumps(st)})", flush=True)
    return dec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=os.path.join(ROOT, "configs", "submission.json"))
    ap.add_argument("--variants", nargs="+", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--split", required=True, help="release split name: dev (check) or test")
    ap.add_argument("--domains", nargs="+")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    conf = json.load(open(a.config))
    tiebreak.set_mode(conf.get("tie_key", "sha1"))
    enc_cache = {}
    variants = list(a.variants)
    dec = None
    if "2a_auto" in variants:  # decide first (cheap), then build both 2a variants as usual
        dec = auto_2a(a, conf)
        variants.remove("2a_auto")
        for v in (conf["_auto_2a"]["with_answers"], conf["_auto_2a"]["without_answers"]):
            if v not in variants:
                variants.append(v)
    for v in variants:
        run_variant(a, v, conf["variants"][v], enc_cache)
    if dec is not None:
        adir = os.path.join(a.out, "2a_auto")
        os.makedirs(adir, exist_ok=True)
        rid = conf["_auto_2a"].get("run_id", "UA_2a_auto")
        for dom, d in dec["domains"].items():
            src = os.path.join(a.out, d["chosen"], f"{dom}.txt")
            with open(src, encoding="utf-8") as f, open(os.path.join(adir, f"{dom}.txt"), "w", encoding="utf-8") as g:
                for line in f:  # same ranking, the auto run id
                    p_ = line.split()
                    g.write(" ".join(p_[:5] + [rid]) + "\n")
            d["source_file"] = src
        n = {v: sum(1 for d in dec["domains"].values() if d["chosen"] == v) for v in
             (conf["_auto_2a"]["with_answers"], conf["_auto_2a"]["without_answers"])}
        dec["summary"] = n
        json.dump(dec, open(os.path.join(adir, "decision.json"), "w"), indent=1)
        print(f"[2a_auto] domains per run: {n}; files in {adir}", flush=True)


if __name__ == "__main__":
    main()
