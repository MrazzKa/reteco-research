#!/usr/bin/env python3
"""Final systems with the doc-id tie key (runs_v12) vs the sha1 tie key (runs_v13).

Per (system, condition): train and dev macro nDCG@10 under both keys, the per-domain dev
difference, and for the hybrid a paired bootstrap of new - old over dev topics.

    python3 tiebreak_compare.py --out ../research/runs_v13/tiebreak/compare.json
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hybrid import bootstrap  # noqa: E402

OLD, NEW = "../research/runs_v12", "../research/runs_v13"
RUNS = {  # condition -> (bm25 results, dense results, dense condition, hybrid report, ce report)
    "1a": ("bm25/t1", "dense/bge-small_L256/t1", "1a", "hybrid/bge-small_L256_t1.json", None),
    "1b_query+step": ("bm25/t1", "dense/bge-small_L256/t1", "1b_query+step", "hybrid/bge-small_L256_t1.json", None),
    "2a_current": ("bm25/t2", "dense/bge-base_L512/t2", "2a_current", "hybrid/bge-base_L512_t2.json",
                   ("ce_bge-base/t2.json", "ce/t2.json")),
    "2a_history": ("bm25/t2", "dense/bge-base_L512/t2", "2a_history_qfirst", "hybrid/bge-base_L512_t2.json", None),
}


def flat(root, sub, cond):
    """{(split, domain): ndcg10} from a bm25s_run / dense_search results.json."""
    rows = json.load(open(os.path.join(root, sub, "results.json")))
    return {(r["split"], r["domain"]): r["ndcg10"] for r in rows if r["run"] == cond}


def macro(d, split):
    v = [x for (s, _), x in d.items() if s == split]
    return round(sum(v) / len(v), 4) if v else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = {}
    for cond, (bsub, dsub, dcond, hrep, ce) in RUNS.items():
        row = {}
        for name, sub, c in (("bm25", bsub, cond), ("dense", dsub, dcond)):
            o, n = flat(OLD, sub, c), flat(NEW, sub, c)
            row[name] = {"train_old": macro(o, "train"), "train_new": macro(n, "train"),
                         "dev_old": macro(o, "dev"), "dev_new": macro(n, "dev"),
                         "dev_domain_diff": {d: round(n[("dev", d)] - o[("dev", d)], 4)
                                             for s, d in sorted(o) if s == "dev" and ("dev", d) in n}}
        ho = json.load(open(os.path.join(OLD, hrep)))["conditions"][cond]
        hn = json.load(open(os.path.join(NEW, hrep)))["conditions"][cond]
        so, sn = ho["systems"]["linear*"], hn["systems"]["linear*"]
        row["hybrid"] = {"cfg_old": so["cfg"], "cfg_new": sn["cfg"],
                         "train_old": so["train_macro"], "train_new": sn["train_macro"],
                         "dev_old": so["dev_macro"], "dev_new": sn["dev_macro"],
                         "dev_domain_diff": {d: round(sn["dev"][d]["ndcg10"] - so["dev"][d]["ndcg10"], 4)
                                             for d in sorted(so["dev"])},
                         "dev_bootstrap_new_minus_old": bootstrap(hn["dev_per_topic"]["linear*"],
                                                                  ho["dev_per_topic"]["linear*"])}
        if ce:
            co = json.load(open(os.path.join(OLD, ce[0])))[cond]
            cn = json.load(open(os.path.join(NEW, ce[1])))[cond]
            no, nn = str(co["chosen_depth_on_train"]), str(cn["chosen_depth_on_train"])
            row["ce"] = {"N_old": int(no), "N_new": int(nn),
                         "train_old": co["by_depth"][no]["train_macro"], "train_new": cn["by_depth"][nn]["train_macro"],
                         "train_N0_new": cn["by_depth"]["0"]["train_macro"],
                         "dev_old": co["by_depth"][no]["dev_macro"], "dev_new": cn["by_depth"][nn]["dev_macro"],
                         "dev_domain_diff": {d: round(cn["dev_per_domain_chosen"][d] - co["dev_per_domain_chosen"][d], 4)
                                             for d in sorted(co["dev_per_domain_chosen"])},
                         "dev_bootstrap_ce_minus_hybrid_new": cn["dev_bootstrap_ce_minus_hybrid"]}
        out[cond] = row
        for s, r in row.items():
            print(f"{cond:<14} {s:<6} train {r['train_old']} -> {r['train_new']}   dev {r['dev_old']} -> {r['dev_new']}")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(out, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
