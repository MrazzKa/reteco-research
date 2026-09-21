#!/usr/bin/env python3
"""Pipeline smoke test on the curated sample data shipped in the RETECO repo.

PURPOSE: prove the read -> BM25 -> run-file -> scorer path works BEFORE
downloading 4.5 GB.  The sample corpus contains ONLY gold passages, so the
resulting nDCG is meaningless as a score.  We assert only that the plumbing
runs and that qids line up with qrels.
"""
import json, os, subprocess, sys, tempfile, shutil

REPO = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "/home/claude/reteco")
KIT  = os.path.join(REPO, "starter_kit")
SMP  = os.path.join(REPO, "docs", "sample_data")
OUT  = os.path.abspath("smoke_out")
shutil.rmtree(OUT, ignore_errors=True); os.makedirs(OUT)

# --- normalise the sample into the release-ish shapes the starter kit expects
t1_ex = os.path.join(SMP, "track1_tempo", "examples.jsonl")
t1_doc = os.path.join(SMP, "track1_tempo", "documents.jsonl")
t1_qrels = os.path.join(SMP, "track1_tempo", "qrels.txt")

bench = [json.loads(l) for l in open(os.path.join(SMP, "track2_recor", "benchmark.jsonl"))]
t2_bench = os.path.join(OUT, "benchmark.json")
json.dump(bench, open(t2_bench, "w"))
t2_doc = os.path.join(SMP, "track2_recor", "documents.jsonl")

# sample qrels use <conv>#turn<N>; release/starter kit use <conv>_turn_<N>
t2_qrels = os.path.join(OUT, "qrels_t2.txt")
n_fixed = 0
with open(t2_qrels, "w") as w:
    for ln in open(os.path.join(SMP, "track2_recor", "qrels.txt")):
        if not ln.strip(): continue
        qid, z, doc, rel = ln.split()
        if "#turn" in qid:
            qid = qid.replace("#turn", "_turn_"); n_fixed += 1
        w.write(f"{qid} {z} {doc} {rel}\n")
print(f"[normalise] rewrote {n_fixed} track-2 qids  '#turnN' -> '_turn_N'")

def sh(cmd):
    r = subprocess.run(cmd, cwd=KIT, capture_output=True, text=True)
    if r.returncode: print(r.stdout, r.stderr); raise SystemExit(f"FAILED: {' '.join(cmd)}")
    return r.stdout.strip()

py = sys.executable
runs = {}
runs["1a"] = (os.path.join(OUT, "run_1a.txt"),
              [py, "bm25_baseline.py", "--track", "1", "--corpus", t1_doc,
               "--queries", t1_ex, "--out", os.path.join(OUT, "run_1a.txt")])
for strat in ("current", "history"):
    p = os.path.join(OUT, f"run_2a_{strat}.txt")
    runs[f"2a_{strat}"] = (p, [py, "bm25_baseline.py", "--track", "2", "--strategy", strat,
                               "--corpus", t2_doc, "--queries", t2_bench, "--out", p])

for name, (path, cmd) in runs.items():
    print(f"\n[run {name}] {' '.join(cmd[1:])}")
    print(sh(cmd) or "(no stdout)")
    print(f"  -> {sum(1 for _ in open(path))} run lines")

print("\n[score 1a]");  print(sh([py, "scorer.py", "--track", "1", "--run", runs["1a"][0], "--qrels", t1_qrels]))
for strat in ("current", "history"):
    print(f"\n[score 2a_{strat}]")
    print(sh([py, "scorer.py", "--track", "2", "--run", runs[f"2a_{strat}"][0], "--qrels", t2_qrels]))
print("\nNOTE: sample corpus = gold passages only. Scores here validate plumbing, not retrieval quality.")
