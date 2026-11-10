#!/usr/bin/env python3
"""A synthetic "test" release from the dev topic files (A1 check of the 2a automation; B3 cold run).

Copies the dev topic files under the split name "test" with every gold / reference field removed:
Track 1 `gold_ids`, `gold_answers` (and the step `gold_ids`); Track 2 per turn `gold_doc_ids`, `answer`
(the current turn's reference answer), `subquestion_reasoning(_metadata)`, per conversation
`original_answer` and the gold count in `metadata`. No qrels are written; documents are symlinked.
With --strip-answers every earlier answer is removed from `conversation_history` (history.strip_answers).

    python3 make_test_release.py --data ../../reteco_data_v11 --out /tmp/rel_with  --tracks 2
    python3 make_test_release.py --data ../../reteco_data_v11 --out /tmp/rel_without --tracks 2 --strip-answers
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import history as H  # noqa: E402
from llm_expand import T1, T2  # noqa: E402

T1_DROP = {"gold_ids", "gold_answers"}
T2_TURN_DROP = {"gold_doc_ids", "answer", "subquestion_reasoning", "subquestion_reasoning_metadata"}


def link(src, dst):
    if not os.path.lexists(dst):
        os.symlink(os.path.abspath(src), dst)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--tracks", nargs="+", type=int, default=[1, 2])
    ap.add_argument("--domains", nargs="+")
    ap.add_argument("--src-split", default="dev")
    ap.add_argument("--strip-answers", action="store_true")
    a = ap.parse_args()
    n = {"t1_topics": 0, "t1_steps": 0, "t2_turns": 0, "t2_turns_with_answers_after": 0}
    for tr in a.tracks:
        sub = "track1_tempo" if tr == 1 else "track2_recor"
        for dom in [d for d in (T1 if tr == 1 else T2) if not a.domains or d in a.domains]:
            sd, od = os.path.join(a.data, sub, dom), os.path.join(a.out, sub, dom)
            os.makedirs(od, exist_ok=True)
            link(os.path.join(sd, "documents.jsonl"), os.path.join(od, "documents.jsonl"))
            if tr == 1:
                for name in ("examples", "steps"):
                    rows = [json.loads(x) for x in open(os.path.join(sd, f"{name}_{a.src_split}.jsonl"), encoding="utf-8")
                            if x.strip()]
                    with open(os.path.join(od, f"{name}_test.jsonl"), "w", encoding="utf-8") as f:
                        for r in rows:
                            r = {k: v for k, v in r.items() if k not in T1_DROP}
                            if "steps" in r:
                                r["steps"] = [{k: v for k, v in s.items() if k not in T1_DROP} for s in r["steps"]]
                                n["t1_steps"] += len(r["steps"])
                            else:
                                n["t1_topics"] += 1
                            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            else:
                bench = json.load(open(os.path.join(sd, f"benchmark_{a.src_split}.json"), encoding="utf-8"))
                bench = [bench] if isinstance(bench, dict) else bench
                out = []
                for c in bench:
                    c = {k: v for k, v in c.items() if k != "original_answer"}
                    c["metadata"] = {k: v for k, v in (c.get("metadata") or {}).items() if "gold" not in k}
                    turns = []
                    for t in c["turns"]:
                        t = {k: v for k, v in t.items() if k not in T2_TURN_DROP}
                        if a.strip_answers:
                            t = H.without_answers(t)
                        n["t2_turns"] += 1
                        n["t2_turns_with_answers_after"] += H.has_answers(t)
                        turns.append(t)
                    c["turns"] = turns
                    out.append(c)
                json.dump(out, open(os.path.join(od, "benchmark_test.json"), "w", encoding="utf-8"), ensure_ascii=False)
    print(json.dumps(n))


if __name__ == "__main__":
    main()
