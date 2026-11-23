#!/usr/bin/env python3
"""Track-1 query-side guidance (LOG 2026-11-23, N2a / rule 20).

The organisers release `query_guidance` with the test questions (mail of 18.11 / 21.11), without anything tied to
gold. Our use is stricter than theirs:
  * `gold_passage_annotations` is never read: rows are parsed and that key is popped unread;
  * `gold_ids` of `retrieval_plan` are dropped before any text is built;
  * g = guidance_text(...) uses only `key_time_anchors`, `temporal_intent`, `retrieval_reasoning` and the `action`
    strings of `retrieval_plan` (plan order); every g is checked with `assert_no_ids` against the corpus ids.
"""
import json
import os
import re

FIELDS = ("key_time_anchors", "temporal_intent", "retrieval_reasoning", "retrieval_plan")
SEP = "\nGuidance: "  # ReasonEmbed query = query text + SEP + g (rule 20)
LLM_SEP = "\n\nSearch guidance (task annotation): "  # G2 LLM input
HEXID = re.compile(r"\b[0-9a-f]{8,}_\d+\b|\b\d+_[0-9a-f]{12,}\b", re.I)
TXT = re.compile(r"\.txt\b", re.I)
TOKEN = re.compile(r"[A-Za-z0-9_./\-]+")


def _clean(t):
    return re.sub(r"\s+", " ", str(t or "")).strip()


def read_guidance(path):
    """{query id: query_guidance with the plan's gold_ids removed}; gold_passage_annotations popped unread."""
    out = {}
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            r.pop("gold_passage_annotations", None)
            qg = dict(r.get("query_guidance") or {})
            if isinstance(qg.get("retrieval_plan"), list):
                qg["retrieval_plan"] = [{k: v for k, v in st.items() if k != "gold_ids"} if isinstance(st, dict)
                                        else st for st in qg["retrieval_plan"]]
            out[str(r.get("id"))] = qg
    return out


def guidance_text(qg):
    """g: the query-side text of one query's guidance ('' if nothing is there)."""
    if not isinstance(qg, dict):
        return ""
    parts = []
    anchors = [_clean(x) for x in (qg.get("key_time_anchors") or []) if _clean(x)]
    if anchors:
        parts.append("Time anchors: " + "; ".join(anchors) + ".")
    intent = _clean(qg.get("temporal_intent"))
    if intent:
        parts.append("Temporal intent: " + intent.replace("_", " ") + ".")
    reason = _clean(qg.get("retrieval_reasoning"))
    if reason:
        parts.append("Reasoning: " + reason)
    plan = qg.get("retrieval_plan") or []
    acts = []
    for st in plan:
        a = _clean(st.get("action")) if isinstance(st, dict) else _clean(st)
        if a:
            acts.append(a)
    if acts:
        parts.append("Plan: " + " ".join(f"{i}. {a}" for i, a in enumerate(acts, 1)))
    return " ".join(parts)


def corpus_ids(data, dom):
    """Lookup set of the domain's doc ids, with and without the domain prefix and the .txt suffix."""
    ids = set()
    with open(os.path.join(data, "track1_tempo", dom, "documents.jsonl"), encoding="utf-8") as f:
        for line in f:
            m = re.search(r'"id"\s*:\s*"([^"]+)"', line)
            if not m:
                continue
            i = m.group(1).lower()
            base = i.split("/", 1)[-1]
            ids.update({i, base, re.sub(r"\.txt$", "", base), re.sub(r"\.txt$", "", i)})
    return ids


def assert_no_ids(g, ids, where=""):
    """Fail if g contains a corpus id (any form) or an id-like pattern."""
    if not g:
        return
    assert not TXT.search(g), f"guidance contains '.txt' ({where})"
    assert not HEXID.search(g), f"guidance contains an id-like token {HEXID.search(g).group(0)!r} ({where})"
    for tok in TOKEN.findall(g.lower()):
        t = tok.strip("./-")
        assert t not in ids, f"guidance contains a corpus id {t!r} ({where})"


def guidance_map(data, dom, split, ids=None):
    """{query id: g} for one Track-1 domain and split (empty dict if the guidance file is absent); every g is
    checked against the domain's corpus ids."""
    rows = read_guidance(os.path.join(data, "track1_tempo", dom, f"guidance_{split}.jsonl"))
    if ids is None:
        ids = corpus_ids(data, dom)
    out = {}
    for q, qg in rows.items():
        g = guidance_text(qg)
        assert_no_ids(g, ids, f"{dom}/{split}/{q}")
        out[q] = g
    return out


def llm_body(body, g, limit=3000):
    """G2: the LLM body with g appended; the body (question part) is cut so the whole stays <= limit; g never cut."""
    if not g:
        return body
    tail = LLM_SEP + g
    return body[:max(0, limit - len(tail))] + tail


def topic_guidance(data, dom, split, cond, ids=None):
    """{topic id: g} for a Track-1 condition: 1a topics are queries; 1b topics are steps, each with its query's g."""
    gm = guidance_map(data, dom, split, ids)
    if not cond.startswith("1b"):
        return gm
    out = {}
    path = os.path.join(data, "track1_tempo", dom, f"steps_{split}.jsonl")
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                for s in r.get("steps", []):
                    out[s["step_id"]] = gm.get(str(r["id"]), "")
    return out
