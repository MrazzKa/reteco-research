#!/usr/bin/env python3
"""How much does a system lean on "foreign gold"? (LOG 2026-11-02, step 1 and rule 10)

On test, every train/dev gold document is a negative (News 17.10: test queries are built on
documents that are not positive for any train/dev query). A component that favours "documents
that look like gold" (e.g. MaxP and the long BRIGHT documents, most of which are train/dev gold)
can therefore look better on train/dev than it will be on test.

Definitions (written in the LOG before this ran):
  group        the topic's query: 1a id; 1b `<query_id>` of `<query_id>_step<n>`; 2a `<conversation>` of
               `<conversation>_turn_<n>`; keyed by (split, group).
  foreign gold for topic q (domain D): a train or dev gold document (1a + 1b qrels on Track 1, 2a qrels on
               Track 2) of another group of D, that is not gold for q. Gold of the same group (other steps of
               the query, other turns of the conversation) is not foreign: on test those are test gold too.
  test-like    topic none of whose gold is gold for any topic of the other split.
  long         document with more than one 510-token passage in the MaxP index (bge tokenizer).

Per stage and split it reports macro nDCG@10 (topics -> domain -> mean over domains), the share of top-10
slots taken by foreign gold vs their share of the corpus, the same restricted to long documents, macro
nDCG@10 on the test-like topics, and nDCG@10 after removing all foreign gold from the ranking.

Stages are TREC run files or (hybrid.py report, condition) pairs; see STAGES. Reads no doc id for ranking:
ids are only used to look documents up in the qrels and the length table.

    python3 foreign_gold.py --data ../../reteco_data_v11 --kit ../../RETECO/starter_kit \
        --runs ../research/runs_v13 --out ../research/runs_v13/foreign/report.json
"""
import argparse
import json
import os
import re
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bm25s_run import ndcg_fn  # noqa: E402
from dense_index import T1, T2  # noqa: E402
from hybrid import Query, bootstrap, read_run  # noqa: E402
from tie_study import fused, order  # noqa: E402
from week1_run import load_qrels  # noqa: E402
import tiebreak  # noqa: E402

BRIGHT = {"psychology", "biology", "sustainable_living", "robotics", "earth_science", "economics"}


def group_of(qid):
    return re.sub(r"(_step\d+|_turn_\d+)$", "", qid)


def stages(R):
    """condition -> [(stage name, spec)]; spec = ("hyb", report, cond) or ("run", dir, name)."""
    F = os.path.join(R, "foreign", "runs")
    return {
        "1a": [("week4 hybrid", ("hyb", f"{R}/hybrid/bge-small_L256_t1.json", "1a")),
               ("+ q+r+h", ("hyb", f"{R}/qexp/t1/hybrid_1a.json", "1a__q+r+h")),
               ("+ ReasonEmbed", ("run", F, "1a_rerun__best"))],
        "1b": [("week4 hybrid", ("hyb", f"{R}/hybrid/bge-small_L256_t1.json", "1b_query+step")),
               ("+ q+r+h", ("hyb", f"{R}/qexp/t1/hybrid_1b.json", "1b_query+step__q+r+h")),
               ("+ ReasonEmbed", ("run", F, "1b_rerun__best"))],
        "2a_current": [("week4 hybrid", ("hyb", f"{R}/hybrid/bge-base_L512_t2.json", "2a_current")),
                       ("+ q+r+h", ("hyb", f"{R}/qexp/t2/hybrid_2a_current.json", "2a_current__q+r+h")),
                       ("+ MaxP", ("hyb", f"{R}/maxp/t2/hybrid_2a_current.json", "2a_current__q+r+h")),
                       ("+ ReasonEmbed (MaxP pool) = A", ("run", F, "2a_maxp__best")),
                       ("+ ReasonEmbed (no MaxP) = B", ("run", F, "2a_nomaxp__best"))],
        "2a_history": [("week4 hybrid", ("hyb", f"{R}/hybrid/bge-base_L512_t2.json", "2a_history"))]
                      + [(n, ("run", F, x)) for n, x in (("hist q+r+h hybrid (rule 11)", "2ah_hybrid__none"),
                                                          ("hist + ReasonEmbed (rule 11)", "2ah_hybrid__best"))],
    }


def track_of(cond):
    return 1 if cond.startswith("1") else 2


def qrels_file(cond, split):
    return f"qrels_steps_{split}.txt" if cond == "1b" else f"qrels_{split}.txt"


class Domain:
    """Gold of every train/dev topic of a domain, groups, corpus size and long-document set."""

    def __init__(self, a, track, dom):
        sub = "track1_tempo" if track == 1 else "track2_recor"
        d = os.path.join(a.data, sub, dom)
        files = (["qrels_{}.txt", "qrels_steps_{}.txt"] if track == 1 else ["qrels_{}.txt"])
        self.gold = {}  # (split, qid) -> set
        for sp in ("train", "dev"):
            for f in files:
                for q, g in load_qrels(os.path.join(d, f.format(sp))).items():
                    self.gold.setdefault((sp, q), set()).update(g)
        self.by_doc = defaultdict(set)  # doc -> {(split, group)}
        self.split_of_doc = defaultdict(set)
        for (sp, q), g in self.gold.items():
            for doc in g:
                self.by_doc[doc].add((sp, group_of(q)))
                self.split_of_doc[doc].add(sp)
        self.all_gold = set(self.by_doc)
        model = "bge-small" if track == 1 else "bge-base"
        first = os.path.join(a.runs, "..", "runs_v12", "emb", f"{model}_L512", f"t{track}", dom)
        man = json.load(open(os.path.join(first, "manifest.json")))
        ids = []
        for s in range(man["shards"]):
            ids += json.load(open(os.path.join(first, f"shard_{s:05d}.ids.json")))
        self.n_docs = len(ids)
        pdir = os.path.join(a.runs, "emb", f"{model}_P510s382", f"t{track}", dom)
        pm = json.load(open(os.path.join(pdir, "manifest.json")))
        idx = set()
        for s in range(pm["shards"]):
            idx.update(np.unique(np.load(os.path.join(pdir, f"shard_{s:05d}.map.npy"))).tolist())
        self.long = {ids[i] for i in idx}
        self.long_gold = len(self.long & self.all_gold)

    def foreign(self, split, qid, own):
        grp = (split, group_of(qid))
        return {d for d in self.all_gold if d not in own and any(g != grp for g in self.by_doc[d])}

    def test_like(self, split, own):
        other = "dev" if split == "train" else "train"
        return not any(other in self.split_of_doc[d] for d in own)


def load_stage(spec, track, dom, split, cond_q):
    """{qid: ranked doc list}."""
    kind = spec[0]
    if kind == "run":
        p = os.path.join(spec[1], f"t{track}_{dom}_{split}_{spec[2]}.tsv")
        if not os.path.exists(p):
            return None
        return {q: [d for d, _ in lst] for q, lst in read_run(p).items()}
    rep = json.load(open(spec[1]))
    hc = rep["conditions"][spec[2]]
    cfg = hc["systems"]["linear*"]["cfg"]
    pre = f"t{track}_{dom}_{split}"
    bm = read_run(os.path.join(rep["bm25"], f"{pre}_{spec[2]}.tsv"))
    de = read_run(os.path.join(rep["dense"], f"{pre}_{hc['dense_condition']}.tsv"))
    return {q: [d for d, _ in order(fused(Query(bm.get(q, []), de.get(q, [])), cfg))] for q in cond_q}


def macro(per_dom):
    vals = [sum(v) / len(v) for v in per_dom.values() if v]
    return round(sum(vals) / len(vals), 4) if vals else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--kit", required=True)
    ap.add_argument("--runs", required=True, help="research/runs_v13")
    ap.add_argument("--conditions", nargs="+", default=["1a", "1b", "2a_current", "2a_history"])
    ap.add_argument("--out", required=True)
    tiebreak.add_arg(ap)
    a = ap.parse_args()
    tiebreak.set_mode(a.tiebreak)
    a.runs = os.path.abspath(a.runs)
    os.chdir(os.path.dirname(os.path.abspath(__file__)))  # hybrid reports hold paths relative to scripts/
    ndcg = ndcg_fn(a.kit)
    report = json.load(open(a.out)) if os.path.exists(a.out) else {}
    doms_cache = {}
    st = stages(a.runs)
    for cond in a.conditions:
        tr = track_of(cond)
        doms = T1 if tr == 1 else T2
        sub = None  # train topic subsample = topics of the ReasonEmbed runs (rule-8 subsample)
        rows = {}
        # per stage, split: per-domain lists
        acc = {}
        for name, spec in st[cond]:
            for split in ("train", "dev"):
                A = defaultdict(lambda: defaultdict(list))
                for dom in doms:
                    if (tr, dom) not in doms_cache:
                        doms_cache[(tr, dom)] = Domain(a, tr, dom)
                    D = doms_cache[(tr, dom)]
                    sub_ = "track1_tempo" if tr == 1 else "track2_recor"
                    gold = load_qrels(os.path.join(a.data, sub_, dom, qrels_file(cond, split)))
                    ranked = load_stage(spec, tr, dom, split, sorted(gold))
                    if ranked is None:
                        break
                    for q in sorted(gold):
                        if spec[0] == "run" and q not in ranked:
                            continue  # ReasonEmbed runs: train subsample only
                        g = gold[q]
                        lst = ranked.get(q, [])
                        top = lst[:10]
                        fg = D.foreign(split, q, g)
                        nd = ndcg(lst, g, 10)
                        A["ndcg"][dom].append(nd)
                        A["foreign_top10"][dom].append(sum(d in fg for d in top) / 10)
                        A["foreign_corpus"][dom].append(len(fg) / D.n_docs)
                        A["long_top10"][dom].append(sum(d in D.long for d in top) / 10)
                        A["n_long_top10"][dom].append(sum(d in D.long for d in top))
                        A["n_long_foreign_top10"][dom].append(sum(d in D.long and d in fg for d in top))
                        A["ndcg_removed"][dom].append(ndcg([d for d in lst if d not in fg], g, 10))
                        A["qids"][dom].append(q)
                        if D.test_like(split, g):
                            A["ndcg_testlike"][dom].append(nd)
                else:
                    acc[(name, split)] = A
        # train subsample = topics of the first "run" stage (ReasonEmbed), used for every stage
        subs = {}
        for (name, split), A in acc.items():
            spec = dict(st[cond])[name]
            if spec[0] == "run" and split == "train" and not subs:
                subs = {dom: set(v) for dom, v in A["qids"].items()}
        out = {}
        for (name, split), A in acc.items():
            views = [(split, None)]
            if split == "train" and subs:
                views.append(("train_sub", subs))
            for view, keep in views:
                spec = dict(st[cond])[name]
                if view == "train" and spec[0] == "run":
                    continue
                B = {k: {} for k in A}
                for dom in A["qids"]:
                    m = [i for i, q in enumerate(A["qids"][dom]) if keep is None or q in keep.get(dom, ())]
                    for k in A:
                        if k == "ndcg_testlike":
                            continue
                        B[k][dom] = [A[k][dom][i] for i in m]
                    D = doms_cache[(tr, dom)]
                    B["ndcg_testlike"][dom] = []
                    gold = load_qrels(os.path.join(a.data, "track1_tempo" if tr == 1 else "track2_recor", dom,
                                                   qrels_file(cond, "train" if view != "dev" else "dev")))
                    sp = "dev" if view == "dev" else "train"
                    B["ndcg_testlike"][dom] = [B["ndcg"][dom][j] for j, q in enumerate(B["qids"][dom])
                                               if D.test_like(sp, gold[q])]
                nl = sum(sum(v) for v in B["n_long_top10"].values())
                nlf = sum(sum(v) for v in B["n_long_foreign_top10"].values())
                long_corpus = (sum(doms_cache[(tr, d)].long_gold for d in B["qids"])
                               / max(1, sum(len(doms_cache[(tr, d)].long) for d in B["qids"])))
                tl = {d: v for d, v in B["ndcg_testlike"].items() if v}
                row = {"n_topics": sum(len(v) for v in B["qids"].values()),
                       "ndcg10": macro(B["ndcg"]),
                       "foreign_share_top10": macro(B["foreign_top10"]),
                       "foreign_share_corpus": round(macro(B["foreign_corpus"]), 6),
                       "long_share_top10": macro(B["long_top10"]),
                       "foreign_share_of_long_in_top10": round(nlf / nl, 4) if nl else None,
                       "gold_share_of_long_in_corpus": round(long_corpus, 4),
                       "n_testlike": sum(len(v) for v in tl.values()),
                       "ndcg10_testlike": macro(tl),
                       "ndcg10_foreign_removed": macro(B["ndcg_removed"]),
                       "by_source": ({s: macro({d: v for d, v in B["ndcg"].items() if (d in BRIGHT) == (s == "bright")})
                                      for s in ("bright", "stackexchange")} if tr == 2 else None),
                       "foreign_by_source": ({s: macro({d: v for d, v in B["foreign_top10"].items()
                                                        if (d in BRIGHT) == (s == "bright")})
                                              for s in ("bright", "stackexchange")} if tr == 2 else None),
                       "_per_topic": B["ndcg"], "_per_topic_testlike": tl, "_foreign": B["foreign_top10"]}
                out.setdefault(name, {})[view] = row
                print(f"{cond:<11} {name:<32} {view:<9} n={row['n_topics']:<5} nDCG {row['ndcg10']}  "
                      f"foreign@10 {row['foreign_share_top10']} (corpus {row['foreign_share_corpus']})  "
                      f"long@10 {row['long_share_top10']} foreign-of-long {row['foreign_share_of_long_in_top10']}"
                      f" (corpus {row['gold_share_of_long_in_corpus']})  test-like n={row['n_testlike']} "
                      f"{row['ndcg10_testlike']}  removed {row['ndcg10_foreign_removed']}", flush=True)
        report[cond] = out
        # rule 10 (2a current): A vs B on the train subsample
        if cond == "2a_current" and "+ ReasonEmbed (MaxP pool) = A" in out and "+ ReasonEmbed (no MaxP) = B" in out:
            A_, B_ = out["+ ReasonEmbed (MaxP pool) = A"], out["+ ReasonEmbed (no MaxP) = B"]
            res = {}
            for view in ("train_sub", "dev"):
                ra, rb = A_[view], B_[view]
                tla, tlb = ra["_per_topic_testlike"], rb["_per_topic_testlike"]
                common = sorted(set(tla) & set(tlb))
                res[view] = {
                    "foreign_share_diff_pp": round(100 * (ra["foreign_share_top10"] - rb["foreign_share_top10"]), 2),
                    "all_A_minus_B": bootstrap(ra["_per_topic"], rb["_per_topic"]),
                    "testlike_A_minus_B": bootstrap({d: tla[d] for d in common}, {d: tlb[d] for d in common}),
                    "n_testlike": ra["n_testlike"]}
            t = res["train_sub"]
            keep = (t["foreign_share_diff_pp"] < 1.0 and t["testlike_A_minus_B"]["diff"] >= 0.005
                    and t["testlike_A_minus_B"]["ci95"][0] > 0)
            res["decision"] = "keep MaxP (main = A)" if keep else "main = B (no MaxP), A = fallback"
            report["rule10"] = res
            print("rule 10:", json.dumps(res), flush=True)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(report, open(a.out, "w"), indent=1)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
