#!/usr/bin/env python3
"""Query-side reasoning with a local open LLM: generate a text per query and cache it.

Two fixed prompts (temperature 0, at most --max-new tokens):
  reason  think briefly about what is needed to answer, then describe a relevant document
  hyde    write a short passage that could answer the question (HyDE)
Track 1 prompts also ask for the time the question refers to; 1b adds the research step
(query + step); Track 2 uses the current question only (2a_current).

The model sees only query text: no qid, no doc id, no gold. Generations are cached in
<out>/<prompt>.jsonl, one row per unique input (key = sha1 of prompt name + model + input
text); a restarted job skips rows already present (resumable). Runs in its own venv
(vLLM 0.32, Python 3.14; see README):

    ~/semeval-reteco/.venv-llm/bin/python llm_expand.py --data ../../reteco_data_v11 \
        --track 2 --conditions 2a_current --prompts reason hyde --out ../research/runs_v13/llm
"""
import argparse
import hashlib
import html
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

T1 = ["iota", "quant", "law", "workplace", "cardano", "monero", "economics", "bitcoin",
      "politics", "genealogy", "travel", "hsm", "history"]
T2 = ["drones", "politics", "law", "medicalsciences", "hardware", "economics", "psychology",
      "biology", "sustainable_living", "robotics", "earth_science"]
MODEL = "cyankiwi/Qwen3-4B-Instruct-2507-AWQ-4bit"  # AWQ W4A16 of Qwen/Qwen3-4B-Instruct-2507
# alternative LLMs (contamination ablation, LOG step 4 of 2026-11-02): name -> (checkpoint, vLLM quantization)
LLMS = {"qwen3-4b": (MODEL, None),
        "llama3.2-3b": ("unsloth/Llama-3.2-3B-Instruct", "fp8")}  # ungated mirror of meta-llama/Llama-3.2-3B-Instruct
MAX_INPUT_CHARS = 3000
HIST_TURNS = 3  # history conditions: at most the last 3 earlier turns

SYSTEM = "You help a search engine find documents. Answer in plain English text only."
PROMPTS = {
    "reason": ("Read the question below. First, reason briefly about what knowledge is needed to answer it. "
               "Then describe what a relevant document would look like: its topic, the key concepts, terms "
               "and entities it would mention{time}. Keep the whole answer under 150 words.\n\n{body}"),
    "hyde": ("Write a short passage (about 100 words) that could appear in a document that helps answer the "
             "question below. Write it as factual reference text, not as a reply to the asker{time}.\n\n{body}"),
}
TIME_HINT = {
    "reason": "; if the question refers to a time (years, periods, events), state that time explicitly",
    "hyde": "; if the question refers to a time (years, periods, events), place the passage in that time",
}


def clean(text):
    text = re.sub(r"<[^>]+>", " ", html.unescape(text or ""))
    return re.sub(r"\s+", " ", text).strip()[:MAX_INPUT_CHARS]


def history_pairs(t):
    """[(question, answer)] of the earlier turns, parsed from the released conversation_history string."""
    h = t.get("conversation_history", "") or ""
    if h.lower().startswith("no previous"):
        return []
    pairs, cur = [], None
    for ln in h.splitlines():
        s = ln.strip()
        if s.startswith("Q:"):
            cur = [s[2:].strip(), ""]
            pairs.append(cur)
        elif s.startswith("A:") and cur is not None:
            cur[1] = s[2:].strip()
        elif cur is not None and s:
            cur[1 if cur[1] else 0] += " " + s
    return [(clean(q), clean(a)) for q, a in pairs]


def history_body(t, answers):
    """Track-2 history conditions: current question first, then the last <= 3 earlier turns
    (questions only, or questions with the answers that are part of the released input)."""
    prev = history_pairs(t)[-HIST_TURNS:]
    body = f"Current question: {clean(t['query'])}"
    if prev:
        if answers:
            ctx = "\n".join(f"Q: {q}\nA: {a}" for q, a in prev)
        else:
            ctx = "\n".join(f"- {q}" for q, _ in prev)
        body += ("\n\nEarlier in the same conversation (oldest first; use it only to understand the current "
                 f"question):\n{ctx}")
    return body[:MAX_INPUT_CHARS]


def read_jsonl(p):
    with open(p, encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]


def inputs(data, track, cond):
    """[(domain, split, qid, body)] — body is the text shown to the model."""
    out = []
    for split in ("train", "dev"):
        for dom in (T1 if track == 1 else T2):
            if track == 1:
                d = os.path.join(data, "track1_tempo", dom)
                if cond == "1a":
                    for r in read_jsonl(os.path.join(d, f"examples_{split}.jsonl")):
                        out.append((dom, split, r["id"], f"Question: {clean(r['query'])}"))
                else:
                    for r in read_jsonl(os.path.join(d, f"steps_{split}.jsonl")):
                        for s in r.get("steps", []):
                            out.append((dom, split, s["step_id"],
                                        f"Question: {clean(r['query'])}\n\nCurrent research step "
                                        f"(the document should serve this step): "
                                        f"{clean(s.get('step_instruction', ''))}"))
            else:
                d = os.path.join(data, "track2_recor", dom)
                bench = json.load(open(os.path.join(d, f"benchmark_{split}.json"), encoding="utf-8"))
                bench = [bench] if isinstance(bench, dict) else bench
                for c in bench:
                    for t in c["turns"]:
                        if cond == "2a_hist3q":
                            b = history_body(t, answers=False)
                        elif cond == "2a_hist3qa":
                            b = history_body(t, answers=True)
                        else:
                            b = f"Question: {clean(t['query'])}"
                        out.append((dom, split, f"{c['id']}_turn_{t['turn_id']}", b))
    return out


def key_of(prompt, body, model=MODEL):
    return hashlib.sha1(f"{prompt}\n{model}\n{body}".encode("utf-8")).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data")
    ap.add_argument("--track", type=int, required=True, choices=(1, 2))
    ap.add_argument("--conditions", nargs="+", default=[])
    ap.add_argument("--bodies", help="JSON list of input texts to generate for (submission mode, scripts/submit.py)")
    ap.add_argument("--prompts", nargs="+", default=["reason", "hyde"], choices=sorted(PROMPTS))
    ap.add_argument("--limit", type=int, help="only the first N unique inputs (speed test)")
    ap.add_argument("--max-new", type=int, default=256)
    ap.add_argument("--gpu-util", type=float, default=0.485)
    ap.add_argument("--max-model-len", type=int, default=1536)
    ap.add_argument("--max-seqs", type=int, default=32)
    ap.add_argument("--max-batched", type=int, default=1536)
    ap.add_argument("--chunk", type=int, default=256, help="inputs per generate() call (cache flush)")
    ap.add_argument("--llm", default="qwen3-4b", choices=sorted(LLMS))
    ap.add_argument("--splits", nargs="+", default=["train", "dev"])
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    model, quant = LLMS[a.llm]
    from vllm import LLM, SamplingParams
    from huggingface_hub.constants import HF_HUB_CACHE
    rev_path = os.path.join(HF_HUB_CACHE, "models--" + model.replace("/", "--"), "refs", "main")
    rev = open(rev_path).read().strip() if os.path.exists(rev_path) else None
    if rev is None:  # downloaded by explicit revision: the snapshot directory name is the revision
        snaps = os.path.join(HF_HUB_CACHE, "models--" + model.replace("/", "--"), "snapshots")
        rev = sorted(os.listdir(snaps))[0] if os.path.isdir(snaps) else None
    llm = LLM(model=model, revision=rev, quantization=quant, gpu_memory_utilization=a.gpu_util, max_model_len=a.max_model_len,
              enforce_eager=True, seed=0, max_num_seqs=a.max_seqs,
              max_num_batched_tokens=a.max_batched)
    tok = llm.get_tokenizer()
    sp = SamplingParams(temperature=0.0, max_tokens=a.max_new, seed=0)
    os.makedirs(a.out, exist_ok=True)
    meta = {"model": model, "revision": rev,
            "quant": quant or "AWQ W4A16 (compressed-tensors)", "engine": "vllm",
            "temperature": 0.0, "max_new_tokens": a.max_new, "system": SYSTEM, "prompts": PROMPTS,
            "time_hint": TIME_HINT, "max_input_chars": MAX_INPUT_CHARS}
    json.dump(meta, open(os.path.join(a.out, "meta.json"), "w"), indent=1)
    for prompt in a.prompts:
        path = os.path.join(a.out, f"{prompt}.jsonl")
        done = set()
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                done = {json.loads(x)["key"] for x in f if x.strip()}
        for cond in (a.conditions or ["bodies"]):
            if a.bodies:
                rows = [(None, None, None, b) for b in json.load(open(a.bodies, encoding="utf-8"))]
            else:
                rows = [r for r in inputs(a.data, a.track, cond) if r[1] in a.splits]
            uniq = {}
            for _, _, _, body in rows:
                uniq.setdefault(key_of(prompt, body, model), body)
            todo = [(k, b) for k, b in uniq.items() if k not in done]
            if a.limit:
                todo = todo[:a.limit]
            print(f"[{prompt}/{cond}] {len(rows)} inputs, {len(uniq)} unique, {len(todo)} to generate", flush=True)
            time_hint = TIME_HINT[prompt] if a.track == 1 else ""
            t_all, n_tok = time.time(), 0
            for s in range(0, len(todo), a.chunk):
                part = todo[s:s + a.chunk]
                msgs = [tok.apply_chat_template(
                    [{"role": "system", "content": SYSTEM},
                     {"role": "user", "content": PROMPTS[prompt].format(time=time_hint, body=b)}],
                    tokenize=False, add_generation_prompt=True) for _, b in part]
                t0 = time.time()
                res = llm.generate(msgs, sp, use_tqdm=False)
                with open(path, "a", encoding="utf-8") as f:
                    for (k, b), r in zip(part, res):
                        o = r.outputs[0]
                        n_tok += len(o.token_ids)
                        f.write(json.dumps({"key": k, "prompt": prompt, "track": a.track, "cond": cond,
                                            "input": b, "output": o.text.strip(),
                                            "n_tokens": len(o.token_ids),
                                            "finish": o.finish_reason}) + "\n")
                el = time.time() - t_all
                print(f"  {s + len(part)}/{len(todo)}  chunk {time.time() - t0:.0f}s  "
                      f"{n_tok / max(el, 1e-9):.0f} tok/s  {(s + len(part)) / max(el, 1e-9):.2f} q/s", flush=True)


if __name__ == "__main__":
    main()
