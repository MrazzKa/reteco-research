#!/usr/bin/env python3
"""Answer the three open questions about the release, immediately after download.

    python check_open_questions.py --data ../../reteco_data

1. Do Track-1 `examples_*.jsonl` still carry `excluded_ids`? (upstream TEMPO
   applies it; the RETECO starter kit never mentions the field)
2. Are 1b steps nested inside the query record, and under which key / text field?
3. Does every released Track-2 turn carry `subquestion_reasoning` and its
   metadata? (this decides whether "+Reasoning" is reproducible at all)

Read-only. Streams one line per file, so it is fast even on the full release.
"""
import argparse
import json
import os
from collections import Counter


def first_record(path):
    with open(path, encoding="utf-8") as f:
        for ln in f:
            if ln.strip():
                return json.loads(ln)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    a = ap.parse_args()

    t1 = os.path.join(a.data, "track1_tempo")
    t2 = os.path.join(a.data, "track2_recor")

    print("=" * 70)
    print("Q1/Q2 — Track 1 field inventory")
    print("=" * 70)
    if not os.path.isdir(t1):
        print(f"  !! {t1} not found")
    for dom in sorted(os.listdir(t1))[:3] if os.path.isdir(t1) else []:
        d = os.path.join(t1, dom)
        for fn in ("examples_train.jsonl", "steps_train.jsonl", "guidance_train.jsonl"):
            p = os.path.join(d, fn)
            if not os.path.exists(p):
                print(f"  {dom}/{fn}: MISSING")
                continue
            r = first_record(p)
            print(f"  {dom}/{fn}: keys = {sorted(r.keys())}")
            if "excluded_ids" in r:
                print(f"     -> excluded_ids PRESENT, n={len(r['excluded_ids'])} "
                      f"(upstream TEMPO zeroes these before ranking; "
                      f"RETECO's baseline does not)")
            for k, v in r.items():
                if isinstance(v, list) and v and isinstance(v[0], dict):
                    print(f"     -> nested list under '{k}', "
                          f"item keys = {sorted(v[0].keys())}")

    # count excluded_ids coverage across all of track 1
    if os.path.isdir(t1):
        n_rec = n_excl = 0
        for dom in sorted(os.listdir(t1)):
            for split in ("train", "dev"):
                p = os.path.join(t1, dom, f"examples_{split}.jsonl")
                if not os.path.exists(p):
                    continue
                with open(p, encoding="utf-8") as f:
                    for ln in f:
                        if ln.strip():
                            n_rec += 1
                            if json.loads(ln).get("excluded_ids"):
                                n_excl += 1
        print(f"\n  ANSWER Q1: {n_excl}/{n_rec} Track-1 records carry a non-empty "
              f"excluded_ids list.")

    print()
    print("=" * 70)
    print("Q3 — Track 2: is the gold reasoning annotation released?")
    print("=" * 70)
    if not os.path.isdir(t2):
        print(f"  !! {t2} not found")
        return
    turn_keys = Counter()
    n_turns = has_reason = has_meta = 0
    for dom in sorted(os.listdir(t2)):
        for split in ("train", "dev"):
            p = os.path.join(t2, dom, f"benchmark_{split}.json")
            if not os.path.exists(p):
                continue
            bench = json.load(open(p, encoding="utf-8"))
            if isinstance(bench, dict):
                bench = [bench]
            for c in bench:
                for t in c.get("turns", []):
                    n_turns += 1
                    turn_keys.update(t.keys())
                    if t.get("subquestion_reasoning"):
                        has_reason += 1
                    if t.get("subquestion_reasoning_metadata"):
                        has_meta += 1
    print(f"  turn keys seen: {sorted(turn_keys)}")
    print(f"\n  ANSWER Q3: {has_reason}/{n_turns} turns carry "
          f"subquestion_reasoning; {has_meta}/{n_turns} carry its metadata.")
    print("\n  If these are ~100%: the oracle condition is reproducible on dev,")
    print("  and the open question becomes whether the HIDDEN TEST ships the")
    print("  same field. That one has to be asked, not grepped.")


if __name__ == "__main__":
    main()
