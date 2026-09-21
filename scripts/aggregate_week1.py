#!/usr/bin/env python3
"""Aggregate fixed RETECO week-1 runs, including paired bootstrap intervals."""
import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

from week1_run import BRIGHT_DOMAINS, REF


def qrels(path):
    out = defaultdict(set)
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                qid, _, doc, rel = line.split()
                if int(rel) > 0:
                    out[qid].add(doc)
    return out


def rankings(path):
    out = defaultdict(list)
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                qid, _, doc, *_ = line.split()
                if len(out[qid]) < 10:
                    out[qid].append(doc)
    return out


def mean(values):
    return sum(values) / len(values) if values else 0.0


def interval(values):
    ordered = sorted(values)
    return ordered[int(.025 * len(ordered))], ordered[int(.975 * len(ordered))]


def fmt(value):
    return f"{value:.4f}"


def collect(root, track, initial=None):
    out = {}
    paths = ([initial / "results.json"] if initial else []) + sorted(root.glob("*/results.json"))
    for path in paths:
        if not path.exists():
            continue
        rows = json.loads(path.read_text(encoding="utf-8"))
        rows = [r for r in rows if r["track"] == track]
        for domain in sorted({r["domain"] for r in rows}):
            out[domain] = (path.parent, {r["run"]: r for r in rows if r["domain"] == domain})
    return out


def per_topic(data, kit, data_root, track):
    import sys
    sys.path.insert(0, str(kit))
    from ir_metrics import ndcg_at_k

    per = {}
    for domain, (folder, rows) in data.items():
        source = data_root / ("track1_tempo" if track == 1 else "track2_recor") / domain
        topic_rel = qrels(source / "qrels_dev.txt")
        step_rel = qrels(source / "qrels_steps_dev.txt") if track == 1 else topic_rel
        scores = {}
        for name in rows:
            # 1a is scored per query; 1b per step; Track 2 per turn.
            rel = step_rel if name.startswith("1b") else topic_rel
            prefix = "t1" if track == 1 else "t2"
            run_path = folder / "runs" / f"{prefix}_{domain}_dev_{name}.tsv"
            if not run_path.exists():
                continue
            ranked = rankings(run_path)
            scores[name] = {q: ndcg_at_k(ranked.get(q, []), gold, 10)
                            for q, gold in rel.items()}
            if abs(mean(list(scores[name].values())) - rows[name]["ndcg10"]) > .0001:
                raise ValueError(f"Run-file score disagrees with results.json: {domain} {name}")
        per[domain] = scores
    return per


def bootstrap(per, left, right, seed=0, n=10000):
    rng = random.Random(seed)
    diffs = []
    by_domain = []
    for scores in per.values():
        if left in scores and right in scores:
            common = sorted(scores[left].keys() & scores[right].keys())
            if common:
                by_domain.append([scores[left][q] - scores[right][q] for q in common])
    if not by_domain:
        return None
    for _ in range(n):
        diffs.append(mean([mean([values[rng.randrange(len(values))]
                                 for _ in values]) for values in by_domain]))
    return mean([mean(v) for v in by_domain]), interval(diffs), len(by_domain)


def track2(data, per):
    names = ["2a_current", "2a_hist_questions_only", "2a_hist_answers_only",
             "2a_history", "2a_ORACLE_hist+reasoning", "2a_ORACLE_prev_turn_gold"]
    lines = ["# Track 2: dev summary", "",
             "Pure-Python BM25, nDCG@10. Official references use pyserini. "
             "Oracle columns require gold annotations and are not deployable systems.", "",
             "| domain | source | n | current | questions | answers | history | reasoning oracle | prior-gold oracle | recycled gold | official current/history |",
             "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |"]
    for domain, (_, rows) in sorted(data.items()):
        values = [fmt(rows[name]["ndcg10"]) if name in rows else "" for name in names]
        ref = f"{REF['2a_current'][domain][1]:.4f} / {REF['2a_history'][domain][1]:.4f}"
        recycled = rows.get("DIAG_gold_recycling", {}).get("ndcg10")
        source = "BRIGHT" if domain in BRIGHT_DOMAINS else "StackExchange"
        lines.append(f"| {domain} | {source} | {rows['2a_current']['n']} | "
                     + " | ".join(values) + f" | {fmt(recycled) if recycled is not None else ''} | {ref} |")
    lines += ["", "## Macro averages", "",
              "| group | n domains | " + " | ".join(names) + " | history - current |",
              "| --- | ---: |" + " ---: |" * (len(names) + 1)]
    groups = {"all": sorted(data), "BRIGHT": sorted(set(data) & BRIGHT_DOMAINS),
              "StackExchange": sorted(set(data) - BRIGHT_DOMAINS)}
    for label, domains in groups.items():
        if not domains:
            continue
        vals = [mean([data[d][1][name]["ndcg10"] for d in domains if name in data[d][1]])
                for name in names]
        gains = [data[d][1]["2a_history"]["ndcg10"] - data[d][1]["2a_current"]["ndcg10"]
                 for d in domains]
        lines.append(f"| {label} | {len(domains)} | " + " | ".join(map(fmt, vals))
                     + f" | {fmt(mean(gains))} |")
    bright = [data[d][1]["2a_history"]["ndcg10"] - data[d][1]["2a_current"]["ndcg10"]
              for d in groups["BRIGHT"]]
    se = [data[d][1]["2a_history"]["ndcg10"] - data[d][1]["2a_current"]["ndcg10"]
          for d in groups["StackExchange"]]
    if bright and se:
        lines += ["", f"Complete source separation: {'yes' if min(bright) > max(se) else 'no'} "
                  f"(min BRIGHT {min(bright):+.4f}; max StackExchange {max(se):+.4f})."]
    lines += ["", "## Paired bootstrap", "",
              "10,000 resamples of turns within each domain, seed 0; then macro average across domains. "
              "Turns in one conversation are dependent, so these intervals may be too narrow for new conversations.", "",
              "| contrast | delta | 95% CI | domains |", "| --- | ---: | --- | ---: |"]
    for label, a, b in [("history - current", "2a_history", "2a_current"),
                        ("answers - questions", "2a_hist_answers_only", "2a_hist_questions_only"),
                        ("history - answers", "2a_history", "2a_hist_answers_only")]:
        result = bootstrap(per, a, b)
        if result:
            delta, (lo, hi), count = result
            lines.append(f"| {label} | {delta:+.4f} | [{lo:+.4f}, {hi:+.4f}] | {count} |")
    lines += ["", "## Turn depth", "",
              "Each cell is the macro average of available per-domain depth means."
              " Domain counts vary at deeper turns.", "",
              "| condition | T1 | T2 | T3 | T4 | T5+ |",
              "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for name in names[:5]:
        cells = []
        for depth in ("T1", "T2", "T3", "T4", "T5+"):
            values = [rows[name]["by_turn"][depth] for _, rows in data.values()
                      if name in rows and depth in rows[name].get("by_turn", {})]
            cells.append(fmt(mean(values)) if values else "")
        lines.append(f"| {name} | " + " | ".join(cells) + " |")
    lines += ["", "## Reading", "",
              "Compare the paired contrasts above before attributing the history gain. "
              "Prior answers are reference answers derived from gold passages, and gold recycling "
              "is common. These are associations, not proof of a causal mechanism. "
              "The hidden-test history and reasoning fields have not been verified.", ""]
    return "\n".join(lines)


def track1(data, per):
    names = ["1a", "1b_query+step", "1b_step_only", "1b_query+all"]
    lines = ["# Track 1: dev summary", "",
             "Pure-Python BM25, nDCG@10. The official 1a and 1b references use pyserini.", "",
             "| domain | n queries / steps | 1a | Query+Step | Step-Only | Query+All | official 1a / 1b |",
             "| --- | --- | ---: | ---: | ---: | ---: | --- |"]
    for domain, (_, rows) in sorted(data.items()):
        vals = [fmt(rows[name]["ndcg10"]) if name in rows else "" for name in names]
        ref = f"{REF['1a'][domain][1]:.4f} / {REF['1b'][domain][1]:.4f}"
        lines.append(f"| {domain} | {rows['1a']['n']} / {rows.get('1b_query+step', {}).get('n', 0)} | "
                     + " | ".join(vals) + f" | {ref} |")
    lines += ["", "Macro averages over available domains: " + ", ".join(
        f"{name} {mean([r[name]['ndcg10'] for _, r in data.values() if name in r]):.4f}"
        for name in names) + ".", "", "## Paired bootstrap", "",
        "10,000 resamples of steps within each domain, seed 0; then macro average across domains.", "",
        "| contrast | delta | 95% CI | domains |", "| --- | ---: | --- | ---: |"]
    for label, a in [("Step-Only - Query+Step", "1b_step_only"),
                     ("Query+All - Query+Step", "1b_query+all")]:
        result = bootstrap(per, a, "1b_query+step")
        if result:
            delta, (lo, hi), count = result
            lines.append(f"| {label} | {delta:+.4f} | [{lo:+.4f}, {hi:+.4f}] | {count} |")
    lines += ["", "Query+All assigns the same ranking to every step of a query. "
              "The corpus is shared across train and dev; only topics are split.", ""]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--track", type=int, choices=(1, 2), required=True)
    ap.add_argument("--runs", type=Path, required=True)
    ap.add_argument("--initial", type=Path, help="optional combined first-pass results folder")
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--kit", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    data = collect(a.runs, a.track, a.initial)
    if not data:
        raise SystemExit("No domain result files found")
    per = per_topic(data, a.kit.resolve(), a.data, a.track)
    report = track1(data, per) if a.track == 1 else track2(data, per)
    a.out.write_text(report, encoding="utf-8")
    print(f"wrote {a.out}: {len(data)} domains")


if __name__ == "__main__":
    main()
