#!/usr/bin/env python3
"""Dense retrieval baselines (CPU) for RETECO, plus RRF hybrid with a BM25 run.

Models are small MTEB-leaderboard encoders that fit a 16 GB CPU machine. The task
rules permit open, proprietary and API models when disclosed; nothing here is
trained or tuned — these are off-the-shelf checkpoints used zero-shot.

    python3 dense_run.py --data ../../reteco_data_v11 --kit ../../RETECO/starter_kit \
        --split dev --track 1 --domains iota --model bge-small \
        --fuse ../research/runs_v11/track1_lucene/runs --out ../research/runs_v11/dense

Conditions match week1_run.py / bm25s_run.py, so results.json and runs/*.tsv are
drop-in comparable.
"""
import argparse
import json
import os
import sys
import time
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from week1_run import REF, load_qrels, read_jsonl, write_run  # noqa: E402
from bm25s_run import by_turn, ndcg_fn, score  # noqa: E402

# name -> (checkpoint, query prefix, doc prefix). Prefixes are the ones the model
# cards prescribe; using the wrong prefix silently costs several nDCG points.
MODELS = {
    "minilm": ("sentence-transformers/all-MiniLM-L6-v2", "", ""),
    "bge-small": ("BAAI/bge-small-en-v1.5",
                  "Represent this sentence for searching relevant passages: ", ""),
    "bge-base": ("BAAI/bge-base-en-v1.5",
                 "Represent this sentence for searching relevant passages: ", ""),
    "e5-small": ("intfloat/e5-small-v2", "query: ", "passage: "),
    "e5-base": ("intfloat/e5-base-v2", "query: ", "passage: "),
    "gte-small": ("thenlper/gte-small", "", ""),
    "arctic-s": ("Snowflake/snowflake-arctic-embed-s",
                 "Represent this sentence for searching relevant passages: ", ""),
}


def load_model(name, max_len, device=None):
    """device: None -> cuda if available, else cpu. Pass "cpu"/"cuda" to force."""
    from sentence_transformers import SentenceTransformer
    import torch
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    ckpt, qp, dp = MODELS[name]
    print(f"    model {ckpt} on {device}", flush=True)
    model = SentenceTransformer(ckpt, device=device)
    model.max_seq_length = max_len
    return model, qp, dp


def encode(model, texts, prefix, batch, label):
    t0 = time.time()
    emb = model.encode([prefix + t for t in texts], batch_size=batch,
                       normalize_embeddings=True, convert_to_numpy=True,
                       show_progress_bar=False).astype(np.float32)
    rate = len(texts) / max(time.time() - t0, 1e-9)
    print(f"    encoded {label}: {len(texts):,} texts, {time.time() - t0:.0f}s "
          f"({rate:.0f}/s)", flush=True)
    return emb


def read_run(path):
    out = defaultdict(list)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                qid, _, doc, rank, *_ = line.split()
                out[qid].append(doc)
    return out


def rrf(lists, k=60, depth=100):
    """Reciprocal rank fusion of ranked doc-id lists."""
    scores = defaultdict(float)
    for ranked in lists:
        for rank, doc in enumerate(ranked[:depth], 1):
            scores[doc] += 1.0 / (k + rank)
    top = sorted(scores.items(), key=lambda x: (-x[1], x[0]))[:depth]
    return top


def dense_search(doc_emb, ids, model, queries, qprefix, batch, label, k=100):
    uniq = sorted({q for _, q in queries})
    qemb = encode(model, uniq, qprefix, batch, f"{label} queries")
    t0 = time.time()
    by_text = {}
    step = 64
    for s in range(0, len(uniq), step):
        sims = qemb[s:s + step] @ doc_emb.T
        idx = np.argpartition(-sims, min(k, sims.shape[1] - 1), axis=1)[:, :k]
        for r, i in enumerate(range(s, min(s + step, len(uniq)))):
            order = idx[r][np.argsort(-sims[r, idx[r]])]
            by_text[uniq[i]] = [(ids[j], float(sims[r, j])) for j in order]
    print(f"    search {label}: {len(uniq)} unique queries, {time.time() - t0:.0f}s", flush=True)
    return {qid: by_text[q] for qid, q in queries}


def corpus(path, key):
    ids, texts = [], []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                d = json.loads(line)
                ids.append(d[key])
                texts.append(d.get("content", "") or "")
    return ids, texts


def plan_track1(d, split):
    recs = read_jsonl(os.path.join(d, f"examples_{split}.jsonl"))
    steps = read_jsonl(os.path.join(d, f"steps_{split}.jsonl"))
    g1a = load_qrels(os.path.join(d, f"qrels_{split}.txt"))
    g1b = load_qrels(os.path.join(d, f"qrels_steps_{split}.txt"))
    out = [("1a", [(r["id"], r["query"]) for r in recs], g1a)]
    fns = {
        "1b_query+step": lambda r, s: f"{r['query']}\n\nStep: {s.get('step_instruction', '')}",
        "1b_step_only": lambda r, s: s.get("step_instruction", ""),
        "1b_query+all": lambda r, s: r["query"] + "\n\nSteps:\n" + "\n".join(
            x.get("step_instruction", "") for x in r.get("steps", [])),
    }
    for name, fn in fns.items():
        out.append((name, [(s["step_id"], fn(r, s)) for r in steps
                           for s in r.get("steps", [])], g1b))
    return out


def plan_track2(d, split):
    bench = json.load(open(os.path.join(d, f"benchmark_{split}.json"), encoding="utf-8"))
    bench = [bench] if isinstance(bench, dict) else bench
    gold = load_qrels(os.path.join(d, f"qrels_{split}.txt"))
    turns = [(f"{c['id']}_turn_{t['turn_id']}", t) for c in bench for t in c["turns"]]

    def hist(t):
        h = t.get("conversation_history", "") or ""
        return "" if h.lower().startswith("no previous") else h

    def part(t, which):
        keep, cur = [], None
        for ln in hist(t).splitlines():
            s = ln.strip()
            if s.startswith("Q:"):
                cur, s = "Q", s[2:]
            elif s.startswith("A:"):
                cur, s = "A", s[2:]
            if cur == which:
                keep.append(s.strip())
        return " ".join(keep)

    return [
        ("2a_current", [(q, t["query"]) for q, t in turns], gold),
        ("2a_history", [(q, (hist(t) + " " + t["query"]).strip()) for q, t in turns], gold),
        ("2a_hist_questions_only",
         [(q, (part(t, "Q") + " " + t["query"]).strip()) for q, t in turns], gold),
        ("2a_hist_answers_only",
         [(q, (part(t, "A") + " " + t["query"]).strip()) for q, t in turns], gold),
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--kit", required=True)
    ap.add_argument("--split", default="dev", choices=("train", "dev"))
    ap.add_argument("--track", type=int, required=True, choices=(1, 2))
    ap.add_argument("--domains", nargs="+", required=True)
    ap.add_argument("--model", default="bge-small", choices=sorted(MODELS))
    ap.add_argument("--max-len", type=int, default=512)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--device", help='force "cpu" or "cuda"; default: cuda when available')
    ap.add_argument("--fuse", help="directory with BM25 run files, for the RRF hybrid")
    ap.add_argument("--conditions", nargs="*", help="only these condition names")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    ndcg = ndcg_fn(a.kit)
    runs_dir = os.path.join(a.out, "runs")
    os.makedirs(runs_dir, exist_ok=True)
    results_path = os.path.join(a.out, "results.json")
    results = json.load(open(results_path, encoding="utf-8")) if os.path.exists(results_path) else []
    model, qprefix, dprefix = load_model(a.model, a.max_len, a.device)
    tag, prefix = a.model, "t1" if a.track == 1 else "t2"

    for dom in a.domains:
        sub = "track1_tempo" if a.track == 1 else "track2_recor"
        d = os.path.join(a.data, sub, dom)
        print(f"\n[track{a.track} / {dom} / {a.model}]", flush=True)
        ids, texts = corpus(os.path.join(d, "documents.jsonl"),
                            "id" if a.track == 1 else "doc_id")
        doc_emb = encode(model, texts, dprefix, a.batch, f"{dom} corpus")
        del texts
        plan = plan_track1(d, a.split) if a.track == 1 else plan_track2(d, a.split)
        for name, queries, gold in plan:
            if not queries or (a.conditions and name not in a.conditions):
                continue
            run = dense_search(doc_emb, ids, model, queries, qprefix, a.batch, name)
            write_run(os.path.join(runs_dir, f"{prefix}_{dom}_{a.split}_{name}.tsv"),
                      run, f"{tag}_{name}")
            m, per = score(run, gold, ndcg)
            row = {"track": a.track, "domain": dom, "split": a.split, "run": name,
                   "n": len(gold), "ndcg10": round(m, 4), "system": f"dense-{a.model}"}
            if a.track == 2:
                row["by_turn"] = by_turn(per)
            results.append(row)
            print(f"      -> {name} dense {m:.4f}", flush=True)

            if a.fuse:
                bm = read_run(os.path.join(a.fuse, f"{prefix}_{dom}_{a.split}_{name}.tsv"))
                if bm:
                    fused = {q: rrf([[doc for doc, _ in run[q]], bm.get(q, [])])
                             for q in run}
                    write_run(os.path.join(runs_dir,
                                           f"{prefix}_{dom}_{a.split}_{name}_hybrid.tsv"),
                              fused, f"hybrid_{tag}_{name}")
                    mh, perh = score(fused, gold, ndcg)
                    rowh = {"track": a.track, "domain": dom, "split": a.split,
                            "run": f"{name}_hybrid", "n": len(gold), "ndcg10": round(mh, 4),
                            "system": f"hybrid-rrf-{a.model}+bm25s"}
                    if a.track == 2:
                        rowh["by_turn"] = by_turn(perh)
                    results.append(rowh)
                    print(f"      -> {name} hybrid {mh:.4f}", flush=True)
            with open(results_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=1)
        del doc_emb
    print(f"\nwrote {results_path}", flush=True)


if __name__ == "__main__":
    main()
