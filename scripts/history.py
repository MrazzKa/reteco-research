#!/usr/bin/env python3
"""Track-2 `conversation_history`: format normalisation, answer detection and answer removal.

Released layouts (train + dev, data v1.1; audit in LOG 2026-11-10 08:09):
  turn 1                "No previous conversation."
  short conversations   "Q: <question>\\nA: <answer>\\nQ: ..." (answers may continue over several lines)
  long conversations    "Earlier discussion covered: Turn 1: <q>; Turn 2: <q>; ...\\n\\nRecent conversation:\\nQ: ...\\nA: ..."

Test may differ (whether earlier answers are present is not announced). `normalize` maps label variants
("Question:", "Answer:", "User:", "Assistant:", any case, extra spaces, full-width colon) to the canonical
"Q: " / "A: " lines and is the identity on every released train/dev history (checked by `audit`), so the
frozen runs are unchanged. `parse` returns the summary questions and the (question, answer) pairs;
`has_answers` decides the 2a run in submit.py; `strip_answers` removes every answer (the rule-14 text);
`assert_answer_free` checks that no earlier answer reaches a given input text.

    python3 history.py --data ../../reteco_data_v11      # parser audit over all train/dev turns
"""
import argparse
import json
import os
import re

NO_PREV = "no previous"
Q_LABEL = re.compile(r"^\s*(?:q|question|user|human|asker)\s*[:：]\s*", re.I)
A_LABEL = re.compile(r"^\s*(?:a|answer|assistant|system|bot|response)\s*[:：]\s*", re.I)
INLINE_A = re.compile(r"\s(?:A|Answer)\s*[:：]\s+")
SUMMARY = re.compile(r"^\s*earlier discussion covered\s*:\s*", re.I)
TURN = re.compile(r"Turn\s+\d+\s*:\s*")


def raw(t):
    h = t.get("conversation_history", "") or ""
    return "" if h.strip().lower().startswith(NO_PREV) else h


def normalize(h):
    """Canonical "Q: " / "A: " line labels; released train/dev strings come back unchanged."""
    if not h or h.strip().lower().startswith(NO_PREV):
        return h
    out = []
    for ln in h.splitlines():
        if ln.startswith("A: ") or (ln.startswith("Q: ") and not INLINE_A.search(ln[3:])):
            out.append(ln)
            continue
        mq, ma = Q_LABEL.match(ln), A_LABEL.match(ln)
        if mq and not SUMMARY.match(ln):
            body = ln[mq.end():]
            m = INLINE_A.search(body)  # "Q: ... A: ..." on one line
            if m:
                out += ["Q: " + body[:m.start()].strip(), "A: " + body[m.end():].strip()]
            else:
                out.append("Q: " + body.strip())
        elif ma:
            out.append("A: " + ln[ma.end():].strip())
        else:
            out.append(ln)
    return "\n".join(out)


def parse(h):
    """{'summary': [questions from 'Earlier discussion covered'], 'pairs': [[q, a]], 'other': [unparsed lines]}"""
    h = normalize(h or "")
    res = {"summary": [], "pairs": [], "other": []}
    if not h or h.strip().lower().startswith(NO_PREV):
        return res
    cur = None
    for ln in h.splitlines():
        s = ln.strip()
        if not s:
            continue
        if SUMMARY.match(s):
            body = SUMMARY.sub("", s)
            parts = [p.strip().rstrip(";").strip() for p in TURN.split(body)]
            res["summary"] += [p for p in parts if p]
            cur = None
        elif s.lower().startswith("recent conversation"):
            cur = None
        elif s.startswith("Q:"):
            cur = [s[2:].strip(), ""]
            res["pairs"].append(cur)
        elif s.startswith("A:"):
            if cur is None:  # an answer without its question
                cur = ["", ""]
                res["pairs"].append(cur)
            cur[1] = (cur[1] + " " + s[2:].strip()).strip()
        elif cur is not None:
            cur[1 if cur[1] else 0] += " " + s
        else:
            res["other"].append(s)
    return res


def answers(t):
    return [a.strip() for _, a in parse(raw(t))["pairs"] if a.strip()]


def has_answers(t):
    return bool(answers(t))


def strip_answers(h):
    """The history string with every answer removed (summary and question lines kept as released)."""
    h = normalize(h or "")
    if not h or h.strip().lower().startswith(NO_PREV):
        return h
    out, in_answer = [], False
    for ln in h.splitlines():
        s = ln.strip()
        if s.startswith("A:"):
            in_answer = True
            continue
        if s.startswith("Q:") or SUMMARY.match(s) or s.lower().startswith("recent conversation"):
            in_answer = False
        if in_answer:
            continue  # continuation (or blank) line inside an answer
        out.append(ln)
    return "\n".join(out).strip()


def without_answers(t):
    """A copy of the turn whose conversation_history has no answers."""
    h = t.get("conversation_history", "") or ""
    return dict(t, conversation_history=h if h.strip().lower().startswith(NO_PREV) else strip_answers(h))


def qonly_qfirst(t):
    """Rule-14 query text: current question, newline, the answer-free history."""
    return (t["query"] + "\n" + strip_answers(raw(t)).strip()).strip()


def answer_probes(ans, questions=(), n=40, min_len=20):
    """40-char windows from the start, middle and end of each answer; windows that also occur in a
    question (answers often echo the question) are dropped, since questions are allowed inputs."""
    qs = [re.sub(r"\s+", " ", q) for q in questions]
    out = []
    for a in ans:
        a = re.sub(r"\s+", " ", a).strip()
        if len(a) < min_len:
            continue
        for i in sorted({0, max(0, len(a) // 2 - n // 2), max(0, len(a) - n)}):
            w = a[i:i + n]
            if not any(w in q for q in qs):
                out.append(w)
    return out


def questions(t):
    r = parse(raw(t))
    return [t.get("query", "")] + r["summary"] + [q for q, _ in r["pairs"]]


def assert_answer_free(text, ans, what="", qs=()):
    flat = re.sub(r"\s+", " ", text)
    for p in answer_probes(ans, qs):
        assert p not in flat, f"earlier answer leaked into {what}: {p!r}"


def audit(data, splits=("train", "dev"), domains=None):
    from collections import Counter
    from llm_expand import T2, history_pairs
    c = Counter()
    for sp in splits:
        for dom in domains or T2:
            p = os.path.join(data, "track2_recor", dom, f"benchmark_{sp}.json")
            if not os.path.exists(p):
                continue
            bench = json.load(open(p, encoding="utf-8"))
            for conv in [bench] if isinstance(bench, dict) else bench:
                for t in conv["turns"]:
                    h = t.get("conversation_history", "") or ""
                    k = int(t["turn_id"])
                    c[f"{sp} turns"] += 1
                    c[f"{sp} normalize_changed"] += normalize(h) != h
                    c[f"{sp} frozen_pairs_changed"] += (
                        history_pairs(dict(t, conversation_history=normalize(h))) != history_pairs(t))
                    if k < 2:
                        c[f"{sp} turn1_no_previous"] += h.strip().lower().startswith(NO_PREV)
                        continue
                    r = parse(h)
                    c[f"{sp} turns>=2"] += 1
                    c[f"{sp} pairs"] += len(r["pairs"])
                    c[f"{sp} summary_questions"] += len(r["summary"])
                    c[f"{sp} turns_with_summary"] += bool(r["summary"])
                    c[f"{sp} empty_answers"] += sum(1 for _, a in r["pairs"] if not a.strip())
                    c[f"{sp} pairs_without_question"] += sum(1 for q, _ in r["pairs"] if not q.strip())
                    c[f"{sp} unparsed_lines"] += len(r["other"])
                    c[f"{sp} all_earlier_turns_found"] += len(r["pairs"]) + len(r["summary"]) == k - 1
                    c[f"{sp} has_answers"] += has_answers(t)
                    s = without_answers(t)
                    c[f"{sp} stripped_has_answers"] += has_answers(s)
                    assert_answer_free(qonly_qfirst(t), answers(t), "qonly_qfirst", questions(t))
    return dict(sorted(c.items()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--splits", nargs="+", default=["train", "dev"])
    a = ap.parse_args()
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    for k, v in audit(a.data, a.splits).items():
        print(f"{k:<34} {v}")


if __name__ == "__main__":
    main()
