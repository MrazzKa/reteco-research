#!/usr/bin/env python3
"""Check and score submit.py output with the official starter-kit tools (dev only).

For every (variant, domain) run file: starter_kit/format_checker.py (with qrels and corpus), our own
sanity checks (every released topic present, depth, no duplicate doc ids, every doc id in the corpus,
non-increasing scores), then starter_kit/scorer.py --json. The official score is the macro over domains
of the per-domain nDCG@10 (1a: topics; 1b: step topics; 2a: turns), compared with the research number.

    python3 score_submission.py --sub ../research/runs_v13/submit/dev --variants 1a 1b 2a_maxp \
        --data ../../reteco_data_v11 --kit ../../RETECO/starter_kit --out ../research/runs_v13/submit/dev/score.json
"""
import argparse
import json
import os
import subprocess
import sys
from collections import defaultdict


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sub", required=True)
    ap.add_argument("--variants", nargs="+", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--kit", required=True)
    ap.add_argument("--split", default="dev")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    report = {}
    for v in a.variants:
        man = json.load(open(os.path.join(a.sub, v, "manifest.json")))
        cfg = man["config"]
        tr = cfg["track"]
        sub, key = ("track1_tempo", "id") if tr == 1 else ("track2_recor", "doc_id")
        per_dom, checks, by_turn = {}, {}, defaultdict(list)
        for dom in man["domains"]:
            d = os.path.join(a.data, sub, dom)
            run = os.path.join(a.sub, v, f"{dom}.txt")
            qrels = os.path.join(d, f"qrels_steps_{a.split}.txt" if cfg["query"].startswith("1b")
                                 else f"qrels_{a.split}.txt")
            fc = subprocess.run([sys.executable, os.path.join(a.kit, "format_checker.py"), run, "--qrels", qrels,
                                 "--corpus", os.path.join(d, "documents.jsonl"), "--doc-key", key],
                                capture_output=True, text=True)
            # own sanity checks
            rows = defaultdict(list)
            with open(run) as f:
                for ln in f:
                    q, _, doc, r, s, tag = ln.split()
                    rows[q].append((int(r), float(s), doc))
            corpus = set()
            with open(os.path.join(d, "documents.jsonl"), encoding="utf-8") as f:
                for ln in f:
                    if ln.strip():
                        corpus.add(json.loads(ln)[key])
            judged = set()
            with open(qrels) as f:
                for ln in f:
                    if ln.strip():
                        judged.add(ln.split()[0])
            dups = sum(len(x) - len({doc for _, _, doc in x}) for x in rows.values())
            unknown = sum(doc not in corpus for x in rows.values() for _, _, doc in x)
            nonmono = sum(any(x[i][1] < x[i + 1][1] for i in range(len(x) - 1)) for x in rows.values())
            depth = sorted({len(x) for x in rows.values()})
            checks[dom] = {"format_checker_exit": fc.returncode,
                           "format_checker_tail": fc.stdout.strip().splitlines()[-1:] if fc.stdout else [],
                           "topics_in_run": len(rows), "topics_released": man["domains"][dom]["topics"],
                           "judged_missing": len(judged - set(rows)), "duplicates": dups, "unknown_docs": unknown,
                           "nonincreasing_violations": nonmono, "depth_min_max": [depth[0], depth[-1]]}
            sc = subprocess.run([sys.executable, os.path.join(a.kit, "scorer.py"), "--track", str(tr), "--run", run,
                                 "--qrels", qrels, "--json"], capture_output=True, text=True, check=True)
            res = json.loads(sc.stdout)
            per_dom[dom] = res["nDCG@10"]
            if tr == 2:
                for t, x in res["by_turn"].items():
                    by_turn[t].append(x)
            print(f"{v:<10} {dom:<20} nDCG@10 {res['nDCG@10']:.4f}  checker exit {fc.returncode}  "
                  f"missing {checks[dom]['judged_missing']} dup {dups} unknown {unknown} depth {depth[0]}-{depth[-1]}",
                  flush=True)
        macro = sum(per_dom.values()) / len(per_dom)
        report[v] = {"official_macro_ndcg10": round(macro, 4), "per_domain": per_dom, "checks": checks,
                     "research_dev": cfg.get("dev_research"),
                     "diff_vs_research": (round(macro - cfg["dev_research"], 4) if cfg.get("dev_research") else None),
                     "timing_s": man["timing_s"], "per_topic_s": man["per_topic_s"], "n_topics": man["n_topics"]}
        print(f"== {v}: official macro {macro:.4f} (research {cfg.get('dev_research')})", flush=True)
    json.dump(report, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
