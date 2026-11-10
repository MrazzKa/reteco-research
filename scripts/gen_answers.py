#!/usr/bin/env python3
"""A2 (analysis, LOG 2026-11-10 08:13): earlier answers written by our LLM instead of the reference ones.

For every target turn (the rule-8 train subsample of Track 2 and all dev turns) the earlier turns of its
conversation are answered by Qwen3-4B (temperature 0, <= 256 new tokens, prompt asks for <= 150 words),
turn by turn: the model sees the current question and <= 3 earlier turns with OUR earlier answers, never a
reference answer and never a document. Then a synthetic release is written in which each target turn's
`conversation_history` keeps its released layout but every answer is replaced by the generated answer of
that turn, so the frozen main 2a pipeline (submit.py) can run on it unchanged.

  phase "generate" (LLM venv):  answers cached in <out>/answers.jsonl (key = sha1 of prompt + model + body)
  phase "build"    (main venv): <out>/data_gen/track2_recor/<dom>/benchmark_{trainsub,dev}.json  (+ documents symlink)
                                <out>/data_ref/...  the same target turns with the reference answers (control)
                                <out>/targets.json

    ~/semeval-reteco/.venv-llm/bin/python gen_answers.py --phase generate --data ../../reteco_data_v11 --out R/a2
    python3 gen_answers.py --phase build --data ../../reteco_data_v11 --out R/a2
"""
import argparse
import hashlib
import json
import os
import random
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from llm_expand import MODEL, T2, clean  # noqa: E402

SYSTEM = "You are a helpful assistant in a conversation. Answer in plain English text only."
PROMPT = ("Answer the current question below as a knowledgeable assistant would, in at most 150 words. "
          "Do not ask questions back.\n\n{body}")
HIST_TURNS = 3


def load_qrels(path):
    g = {}
    with open(path) as f:
        for ln in f:
            p = ln.split()
            if len(p) >= 4 and int(p[3]) > 0:
                g.setdefault(p[0], set()).add(p[2])
    return g


def bench(data, dom, split):
    b = json.load(open(os.path.join(data, "track2_recor", dom, f"benchmark_{split}.json"), encoding="utf-8"))
    return [b] if isinstance(b, dict) else b


def targets(data, per_domain=30):
    """{(split, dom): set(topic ids)}: train = the rule-8 subsample (reason_rerank.py), dev = all judged turns."""
    out = {}
    for dom in T2:
        for split in ("train", "dev"):
            gold = load_qrels(os.path.join(data, "track2_recor", dom, f"qrels_{split}.txt"))
            tids = {f"{c['id']}_turn_{t['turn_id']}" for c in bench(data, dom, split) for t in c["turns"]}
            qids = sorted(q for q in gold if q in tids)
            if split == "train" and len(qids) > per_domain:
                qids = sorted(random.Random(20260921).sample(qids, per_domain))
            out[(split, dom)] = set(qids)
    return out


def body_of(question, prev):
    """prev: [(question, generated answer)] of the earlier turns, oldest first (<= 3 used)."""
    b = ""
    if prev:
        ctx = "\n".join(f"Q: {clean(q)}\nA: {clean(a)}" for q, a in prev[-HIST_TURNS:])
        b = f"Earlier in the same conversation (oldest first):\n{ctx}\n\n"
    return (b + f"Current question: {clean(question)}")[-3000:]


def key_of(body):
    return hashlib.sha1(f"answer\n{MODEL}\n{body}".encode("utf-8")).hexdigest()


def plan(data, tg):
    """conversations that need generated answers: {(split, dom, conv id): number of earlier turns needed}"""
    need = {}
    for (split, dom), qids in tg.items():
        for c in bench(data, dom, split):
            ks = [int(t["turn_id"]) for t in c["turns"] if f"{c['id']}_turn_{t['turn_id']}" in qids]
            if ks and max(ks) > 1:
                need[(split, dom, c["id"])] = max(ks) - 1
    return need


def generate(a):
    from vllm import LLM, SamplingParams
    tg = targets(a.data)
    need = plan(a.data, tg)
    convs = {}
    for s_, d_ in {(s_, d_) for s_, d_, _ in need}:
        for c in bench(a.data, d_, s_):
            if (s_, d_, c["id"]) in need:
                convs[(s_, d_, c["id"])] = c
    path = os.path.join(a.out, "answers.jsonl")
    os.makedirs(a.out, exist_ok=True)
    cache = {}
    if os.path.exists(path):
        for ln in open(path, encoding="utf-8"):
            if ln.strip():
                r = json.loads(ln)
                cache[r["key"]] = r["output"]
    llm = LLM(model=MODEL, gpu_memory_utilization=a.gpu_util, max_model_len=2048, enforce_eager=True, seed=0,
              max_num_seqs=64, max_num_batched_tokens=2048)
    tok = llm.get_tokenizer()
    sp = SamplingParams(temperature=0.0, max_tokens=256, seed=0)
    gen = {k: [] for k in need}  # (split, dom, conv) -> [(q, generated a)]
    t_all = time.time()
    for r in range(1, max(need.values()) + 1):
        todo = []
        for k, n in need.items():
            if n >= r:
                turns = sorted(convs[k]["turns"], key=lambda t: int(t["turn_id"]))
                q = turns[r - 1]["query"]
                todo.append((k, q, body_of(q, gen[k])))
        fresh = sorted({key_of(b): b for _, _, b in todo if key_of(b) not in cache}.items())
        for s in range(0, len(fresh), 256):
            part = fresh[s:s + 256]
            msgs = [tok.apply_chat_template([{"role": "system", "content": SYSTEM},
                                             {"role": "user", "content": PROMPT.format(body=b)}],
                                            tokenize=False, add_generation_prompt=True) for _, b in part]
            res = llm.generate(msgs, sp, use_tqdm=False)
            with open(path, "a", encoding="utf-8") as f:
                for (kk, b), o in zip(part, res):
                    cache[kk] = o.outputs[0].text.strip()
                    f.write(json.dumps({"key": kk, "input": b, "output": cache[kk],
                                        "n_tokens": len(o.outputs[0].token_ids),
                                        "finish": o.outputs[0].finish_reason}) + "\n")
        for k, q, b in todo:
            gen[k].append((q, cache[key_of(b)]))
        print(f"round {r}: {len(todo)} answers ({len(fresh)} generated), {time.time() - t_all:.0f}s", flush=True)
    json.dump({"model": MODEL, "system": SYSTEM, "prompt": PROMPT, "temperature": 0, "max_new_tokens": 256,
               "hist_turns": HIST_TURNS}, open(os.path.join(a.out, "answers_meta.json"), "w"), indent=1)


def swap_answers(h, new):
    """Replace the answers of the released history string, keeping its layout. new: answers of the
    Q/A pairs in the string, in order (the pairs are the last len(new) earlier turns)."""
    out, i, in_ans = [], -1, False
    for ln in h.splitlines():
        s = ln.strip()
        if s.startswith("Q:"):
            i += 1
            in_ans = False
            out.append(ln)
        elif s.startswith("A:") and i >= 0:
            out.append("A: " + re.sub(r"\s+", " ", new[i]).strip())
            in_ans = True
        elif in_ans and (s == "" or not (s.lower().startswith("recent conversation")
                                        or s.lower().startswith("earlier discussion"))):
            continue  # continuation / blank line of a replaced answer
        else:
            in_ans = False
            out.append(ln)
    return "\n".join(out)


def build(a):
    import history as H
    tg = targets(a.data)
    cache = {}
    for ln in open(os.path.join(a.out, "answers.jsonl"), encoding="utf-8"):
        if ln.strip():
            r = json.loads(ln)
            cache[r["key"]] = r["output"]
    stats = {"turns": 0, "pairs_replaced": 0, "question_match": 0, "missing_answers": 0}
    for kind in ("gen", "ref"):
        for dom in T2:
            ddir = os.path.join(a.out, f"data_{kind}", "track2_recor", dom)
            os.makedirs(ddir, exist_ok=True)
            link = os.path.join(ddir, "documents.jsonl")
            if not os.path.exists(link):
                os.symlink(os.path.abspath(os.path.join(a.data, "track2_recor", dom, "documents.jsonl")), link)
            for split, name in (("train", "trainsub"), ("dev", "dev")):
                qids = tg[(split, dom)]
                convs = []
                for c in bench(a.data, dom, split):
                    turns = sorted(c["turns"], key=lambda t: int(t["turn_id"]))
                    gen, keep = [], []
                    for t in turns:
                        tid = f"{c['id']}_turn_{t['turn_id']}"
                        if tid in qids:
                            t2 = dict(t)
                            if kind == "gen":
                                n = len(H.parse(t["conversation_history"])["pairs"])
                                new = [x for _, x in gen[-n:]] if n else []
                                if n and len(new) < n:
                                    stats["missing_answers"] += 1
                                if n:
                                    t2["conversation_history"] = swap_answers(t["conversation_history"], new)
                                    pq = [q for q, _ in H.parse(t["conversation_history"])["pairs"]]
                                    stats["question_match"] += sum(clean(x) == clean(y) for x, y in
                                                                   zip(pq, [q for q, _ in gen[-n:]]))
                                    stats["pairs_replaced"] += n
                                    assert len(H.parse(t2["conversation_history"])["pairs"]) == n
                                stats["turns"] += 1
                            keep.append(t2)
                        if kind == "gen":
                            b = body_of(t["query"], gen)
                            if key_of(b) in cache:
                                gen.append((t["query"], cache[key_of(b)]))
                            else:
                                gen.append((t["query"], ""))
                    if keep:
                        convs.append(dict(c, turns=keep))
                json.dump(convs, open(os.path.join(ddir, f"benchmark_{name}.json"), "w", encoding="utf-8"),
                          ensure_ascii=False)
    json.dump({f"{s}/{d}": sorted(v) for (s, d), v in tg.items()}, open(os.path.join(a.out, "targets.json"), "w"))
    print(json.dumps(stats), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", required=True, choices=("generate", "build"))
    ap.add_argument("--data", required=True)
    ap.add_argument("--gpu-util", type=float, default=0.6)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    generate(a) if a.phase == "generate" else build(a)


if __name__ == "__main__":
    main()
