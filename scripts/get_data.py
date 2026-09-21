#!/usr/bin/env python3
"""Download only the domains you need from the RETECO release (not all 4.73 GB).

    python get_data.py --list                                  # see what's in the repo
    python get_data.py --track1 iota --track2 drones biology   # just these domains
    python get_data.py --all                                   # everything

Prints the folder to pass as --data to the other scripts.
"""
import argparse
import os
import sys

REPO = "DataScience-UIBK/RETECO-SemEval2027"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="reteco_data")
    ap.add_argument("--track1", nargs="*", default=[])
    ap.add_argument("--track2", nargs="*", default=[])
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    try:
        from huggingface_hub import list_repo_files, snapshot_download
    except ImportError:
        sys.exit("pip install huggingface_hub   (inside the venv)")

    files = list_repo_files(REPO, repo_type="dataset")
    t1 = [f for f in files if "track1_tempo/" in f]
    t2 = [f for f in files if "track2_recor/" in f]
    print(f"repo has {len(files)} files ({len(t1)} track1, {len(t2)} track2)")

    def domains(paths, marker):
        out = set()
        for p in paths:
            rest = p.split(marker, 1)[1]
            if "/" in rest:
                out.add(rest.split("/", 1)[0])
        return sorted(out)

    d1, d2 = domains(t1, "track1_tempo/"), domains(t2, "track2_recor/")
    if a.list or not (a.all or a.track1 or a.track2):
        print("track1 domains:", ", ".join(d1))
        print("track2 domains:", ", ".join(d2))
        print("top-level files:", ", ".join(f for f in files if "/" not in f) or "-")
        prefix = t1[0].split("track1_tempo/")[0] if t1 else ""
        print(f"path prefix before track folders: '{prefix}'")
        return

    for d in a.track1:
        if d not in d1:
            sys.exit(f"unknown track1 domain '{d}'. choose from: {', '.join(d1)}")
    for d in a.track2:
        if d not in d2:
            sys.exit(f"unknown track2 domain '{d}'. choose from: {', '.join(d2)}")

    if a.all:
        patterns = None
    else:
        patterns = [f"*track1_tempo/{d}/*" for d in a.track1] + \
                   [f"*track2_recor/{d}/*" for d in a.track2] + \
                   ["*manifest*", "README.md"]  # split manifest + card only
    snapshot_download(REPO, repo_type="dataset", local_dir=a.out, allow_patterns=patterns)

    # locate the folder that directly contains track1_tempo / track2_recor
    root = None
    for dirpath, dirnames, _ in os.walk(a.out):
        if "track1_tempo" in dirnames or "track2_recor" in dirnames:
            root = dirpath
            break
    print("\ndone. pass this as --data:\n   ", os.path.abspath(root or a.out))


if __name__ == "__main__":
    main()
