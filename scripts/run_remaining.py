#!/usr/bin/env python3
"""Run fixed week-1 conditions for domains absent from the first pilot."""
import argparse
import concurrent.futures
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


def run_one(domain, args):
    folder = args.out / domain
    folder.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, str(Path(__file__).with_name("week1_run.py")),
               "--data", str(args.data), "--kit", str(args.kit), "--split", "dev",
               f"--track{args.track}", domain, "--cases", "5", "--seed", "20260921",
               "--out", str(folder)]
    started = time.time()
    env = dict(os.environ, PYTHONUTF8="1")
    with ((folder / "console.log").open("w", encoding="utf-8") as stdout,
          (folder / "error.log").open("w", encoding="utf-8") as stderr):
        result = subprocess.run(command, stdout=stdout, stderr=stderr, env=env, check=False)
    elapsed = time.time() - started
    complete = (folder / "results.json").exists() and (folder / "results.md").exists()
    return domain, command, (0 if complete else result.returncode), elapsed, folder


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--track", type=int, choices=(1, 2), required=True)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--kit", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--log", type=Path, required=True)
    ap.add_argument("--skip", nargs="*", default=[])
    ap.add_argument("--only", nargs="*", help="run only these domains")
    a = ap.parse_args()
    root = a.data / ("track1_tempo" if a.track == 1 else "track2_recor")
    domains = [p.name for p in sorted(root.iterdir()) if p.is_dir() and p.name not in a.skip
               and (a.only is None or p.name in a.only)
               and not (a.out / p.name / "results.json").exists()]
    print(f"track {a.track}: {len(domains)} domains, {a.workers} workers", flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:
        futures = {pool.submit(run_one, domain, a): domain for domain in domains}
        for future in concurrent.futures.as_completed(futures):
            domain, command, code, elapsed, folder = future.result()
            print(f"{domain}: exit {code}, {elapsed:.0f}s -> {folder}", flush=True)
            rows = json.loads((folder / "results.json").read_text(encoding="utf-8")) if code == 0 else []
            scores = "; ".join(f"{r['run']}={r['ndcg10']:.4f} (n={r['n']})" for r in rows)
            entry = (f"\n## {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M %Z')} — "
                     f"Track {a.track} {domain} dev run\n"
                     f"split: dev    domains: {domain}\n"
                     f"command: `{' '.join(command)}`\n"
                     f"system: FastBM25 k1=0.9 b=0.4, top 100; fixed seed 20260921\n"
                     f"result: {scores if code == 0 else 'FAILED (see error.log)'}\n"
                     f"runtime: {elapsed:.0f}s    peak RAM: not measured\n"
                     f"notes: console and errors in `{folder}`; exit code {code}.\n"
                     f"conclusion: {'Completed fixed dev conditions.' if code == 0 else 'No result; investigate failure.'}\n")
            with a.log.open("a", encoding="utf-8") as f:
                f.write(entry)
    failed = [d for d in domains if not (a.out / d / "results.json").exists()]
    if failed:
        raise SystemExit(f"failed domains: {', '.join(failed)}")


if __name__ == "__main__":
    main()
