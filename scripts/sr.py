#!/usr/bin/env python3
"""Track-2 `subquestion_reasoning` (SR) helpers for LOG rule 19.

Only the SR text of the current turn is used — never `subquestion_reasoning_metadata` or any other field.
`join_cut` appends SR to a query text and, if a token limit is exceeded, cuts the base text (the history),
never SR.
"""
import json
import os

SEP = "\nReasoning: "


def sr_map(data, dom, split):
    """{qid: SR text ('' if absent)} for one Track-2 domain file."""
    bench = json.load(open(os.path.join(data, "track2_recor", dom, f"benchmark_{split}.json"), encoding="utf-8"))
    bench = [bench] if isinstance(bench, dict) else bench
    out = {}
    for c in bench:
        for t in c["turns"]:
            s = t.get("subquestion_reasoning")
            out[f"{c['id']}_turn_{t['turn_id']}"] = s.strip() if isinstance(s, str) else ""
    return out


def join_cut(tok, base, s, limit, wrap=lambda q: q, special=True, sep=SEP):
    """base + SEP + s, with base cut (token-wise, from the end) so that len(tokens(wrap(text))) <= limit.
    Returns (text, base_was_cut). With an empty s the base alone is returned (still cut to the limit).
    `sep` = "\nGuidance: " for the Track-1 guidance of rule 20 (guidance.SEP); if s alone does not fit, the base is
    dropped and the embedder's own truncation cuts the tail of s."""
    def n(t):
        return len(tok(wrap(t), add_special_tokens=special)["input_ids"])
    tail = (sep + s) if s else ""
    text = base + tail
    if n(text) <= limit:
        return text, False
    ids = tok(base, add_special_tokens=False)["input_ids"]
    keep = max(0, len(ids) - (n(text) - limit) - 2)
    while True:
        cut = tok.decode(ids[:keep]).rstrip()
        text = cut + tail
        if n(text) <= limit or keep == 0:
            return text, True
        keep = max(0, keep - 8)
