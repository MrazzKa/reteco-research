#!/usr/bin/env python3
"""Test day (N6): format check and counters of every submitted run file written by submit.py.

For every <out>/<variant>/<domain>.txt: the official starter_kit/format_checker.py (with the corpus, so unknown doc
ids fail), plus: every released topic present, 1000 lines per topic (or the corpus size), no duplicate doc ids. Then
the counters: topics per domain, 2a_auto choices and history-parser counters (unparsed lines, summary questions,
turns with answers), stage timings, new ReasonEmbed documents / reranker pairs. No qrels are read.

    python3 test_summary.py --release <test release> --split test --out <out dir> \
        --kit ~/semeval-reteco/RETECO/starter_kit --config ../configs/submission.json
"""
import argparse
import json
import os
import subprocess
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import submit  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--release", required=True)
    ap.add_argument("--split", default="test")
    ap.add_argument("--out", required=True)
    ap.add_argument("--kit", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--variants", nargs="+", required=True)
    a = ap.parse_args()
    conf = json.load(open(a.config))
    rep = {"release": os.path.abspath(a.release), "split": a.split, "variants": {}, "problems": []}
    for v in a.variants:
        cfgv = conf["variants"].get(v) or conf["variants"][conf["_auto_2a"]["with_answers"]]
        tr = cfgv["track"]
        sub, key = ("track1_tempo", "id") if tr == 1 else ("track2_recor", "doc_id")
        vdir = os.path.join(a.out, v)
        row = {"domains": {}, "files": 0, "format_checker_fail": 0}
        for dom in cfgv["domains"]:
            path = os.path.join(vdir, f"{dom}.txt")
            if not os.path.exists(path):
                row["domains"][dom] = {"missing_file": True}
                rep["problems"].append(f"{v}/{dom}: run file missing")
                continue
            row["files"] += 1
            corpus = os.path.join(a.release, sub, dom, "documents.jsonl")
            fc = subprocess.run([sys.executable, os.path.join(a.kit, "format_checker.py"), path, "--corpus", corpus,
                                 "--doc-key", key], capture_output=True, text=True)
            want = [t[0] for t in submit.topics(a.release, a.split, cfgv, dom)]
            per_q, dup = Counter(), 0
            seen = set()
            for ln in open(path, encoding="utf-8"):
                p = ln.split()
                if not p:
                    continue
                per_q[p[0]] += 1
                dup += (p[0], p[2]) in seen
                seen.add((p[0], p[2]))
            miss = sorted(set(want) - set(per_q))
            extra = sorted(set(per_q) - set(want))
            short = sum(1 for q in want if 0 < per_q[q] < 1000)
            d = {"format_checker_exit": fc.returncode, "topics_released": len(set(want)), "topics_in_file": len(per_q),
                 "missing_topics": len(miss), "extra_topics": len(extra), "topics_below_1000": short, "duplicates": dup}
            row["domains"][dom] = d
            if fc.returncode != 0:
                row["format_checker_fail"] += 1
                rep["problems"].append(f"{v}/{dom}: format_checker exit {fc.returncode}: "
                                       f"{(fc.stdout or fc.stderr).strip().splitlines()[-1:]}")
            if miss or extra or dup:
                rep["problems"].append(f"{v}/{dom}: missing {len(miss)} extra {len(extra)} duplicates {dup}")
        man = os.path.join(vdir, "manifest.json")
        if os.path.exists(man):
            m = json.load(open(man))
            row["timing_s"] = m.get("timing_s")
            row["n_topics"] = m.get("n_topics")
            for k in ("sr_summary", "guidance_summary"):
                if k in m:
                    row[k] = m[k]
        dec = os.path.join(vdir, "decision.json")
        if os.path.exists(dec):
            d = json.load(open(dec))
            row["auto_2a"] = d.get("summary")
            c = Counter()
            for x in d["domains"].values():
                for k in ("turns", "turns_ge2", "turns_ge2_with_answer", "unparsed_lines", "summary_questions",
                          "empty_answers", "normalized_differs", "empty_history"):
                    c[k] += x.get(k, 0)
            row["history_counters"] = dict(c)
            row["auto_2a_per_domain"] = {k: x["chosen"] for k, x in d["domains"].items()}
        rep["variants"][v] = row
    pre = os.path.join(a.out, "pregenerate_timing.json")
    if os.path.exists(pre):
        rep["pregenerate_timing_s"] = json.load(open(pre))
    json.dump(rep, open(os.path.join(a.out, "test_summary.json"), "w"), indent=1)
    print(f"{'variant':<16} files  fc_fail  topics  timing(s)")
    for v, r in rep["variants"].items():
        tot = sum((r.get("timing_s") or {}).get(k, 0) for k in (r.get("timing_s") or {}) if k.endswith("_s"))
        print(f"{v:<16} {r['files']:>5}  {r['format_checker_fail']:>7}  {str(r.get('n_topics')):>6}  {tot:>9.0f}")
        if "auto_2a" in r:
            print(f"  2a_auto: {r['auto_2a']}  history counters: {r['history_counters']}")
    print("PROBLEMS:" if rep["problems"] else "no problems found")
    for p in rep["problems"]:
        print("  " + p)
    sys.exit(1 if rep["problems"] else 0)


if __name__ == "__main__":
    main()
