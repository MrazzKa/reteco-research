#!/usr/bin/env python3
"""N1 (LOG 2026-11-23 12:58; analysis, no choice): query variants through the whole final system, recall@k of the
q+r+h hybrid and the cost of the ReasonEmbed pool.

Final system of a variant = its train-chosen hybrid (`linear*` of the hybrid report) + ReasonEmbed over the top 50
with the way chosen on the rule-8 train subsample (reason_rerank.py score dumps `runs_v13/scores/<name>.json`).
Every number is recomputed from the dumps / run files with the official nDCG@10 and checked against the
reason_rerank report.

    python3 n1_report.py --root .. --data ../../reteco_data_v11 --kit ../../RETECO/starter_kit \
        --out ../research/runs_v13/n1/report.json
"""
import argparse
import json
import os
import random
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bm25s_run import ndcg_fn  # noqa: E402
from dense_index import T1, T2  # noqa: E402
from hybrid import Query, bootstrap, qrels_for, read_run  # noqa: E402
from tie_study import fused, order  # noqa: E402
import tiebreak  # noqa: E402

R = "research/runs_v13"
# condition -> track, qrels condition, {variant: (hybrid report, hybrid condition, reason entry / dump name)}
SPEC = {
    "1a": (1, "1a", {"q": ("qexp/t1/hybrid_1a.json", "1a__q", "n1_1a_q"),
                     "q+r": ("qexp/t1/hybrid_1a.json", "1a__q+r", "n1_1a_qr"),
                     "q+h": ("qexp/t1/hybrid_1a.json", "1a__q+h", "n1_1a_qh"),
                     "q+r+h": ("qexp/t1/hybrid_1a.json", "1a__q+r+h", "1a_rerun")}),
    "1b": (1, "1b_query+step", {"q": ("qexp/t1/hybrid_1b.json", "1b_query+step__q", "n1_1b_q"),
                                "q+r": ("qexp/t1/hybrid_1b.json", "1b_query+step__q+r", "n1_1b_qr"),
                                "q+h": ("qexp/t1/hybrid_1b.json", "1b_query+step__q+h", "n1_1b_qh"),
                                "q+r+h": ("qexp/t1/hybrid_1b.json", "1b_query+step__q+r+h", "1b_rerun")}),
    "2a_current": (2, "2a_current", {"q": ("qexp/t2/hybrid_2a_current.json", "2a_current__q", "2a_cur_q"),
                                     "q+r": ("qexp/t2/hybrid_2a_current.json", "2a_current__q+r", "n1_2a_qr"),
                                     "q+h": ("qexp/t2/hybrid_2a_current.json", "2a_current__q+h", "n1_2a_qh"),
                                     "q+r+h": ("qexp/t2/hybrid_2a_current.json", "2a_current__q+r+h", "2a_nomaxp")}),
    "2a_history": (2, "2a_history", {"q": ("hist/t2/hybrid_h0.json", "2a_history", "2ah_h0"),
                                     "q+r": ("hist/t2/hybrid_n1.json", "2a_hist3qa__q+r", "n1_2ah_qr"),
                                     "q+h": ("hist/t2/hybrid_n1.json", "2a_hist3qa__q+h", "n1_2ah_qh"),
                                     "q+r+h": ("hist/t2/hybrid.json", "2a_hist3qa__q+r+h", "2ah_hybrid")}),
}
KS = (10, 20, 50, 100, 200, 1000)
POOLS = (50, 100, 200, 1000)
SEED = 20260921


def macro(d):
    return sum(sum(v) / len(v) for v in d.values()) / len(d)


def ci_macro(d, n=10000, seed=SEED):
    rng = random.Random(seed)
    doms = sorted(d)
    vals = []
    for _ in range(n):
        tot = 0.0
        for k in doms:
            x = d[k]
            tot += sum(x[rng.randrange(len(x))] for _ in x) / len(x)
        vals.append(tot / len(doms))
    vals.sort()
    return [round(vals[int(0.025 * n)], 4), round(vals[int(0.975 * n)], 4)]


def full_list(q, cfg):
    """The submission order: fused pool, then the rest of dense, then BM25 (submit.py), depth 1000."""
    lst, seen = [], set()
    for d in [d for d, _ in order(fused(q, cfg))] + [d for d, _ in q.de] + [d for d, _ in q.bm]:
        if d not in seen:
            seen.add(d)
            lst.append(d)
            if len(lst) == 1000:
                break
    return lst


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--kit", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--boot", type=int, default=10000)
    a = ap.parse_args()
    tiebreak.set_mode("sha1")
    ndcg = ndcg_fn(a.kit)
    rr = {1: json.load(open(os.path.join(a.root, R, "reason", "t1_reasonembed-4b.json"))),
          2: json.load(open(os.path.join(a.root, R, "reason", "t2_reasonembed-4b.json")))}
    rep = {"variants": {}, "recall": {}, "cost": {}}
    for cname, (tr, qcond, rows) in SPEC.items():
        doms = T1 if tr == 1 else T2
        out = {}
        per = {}
        for var, (hpath, hcond, name) in rows.items():
            hyb = json.load(open(os.path.join(a.root, R, hpath)))
            hc = hyb["conditions"][hcond]
            dump = json.load(open(os.path.join(a.root, R, "scores", f"{name}.json")))
            row = rr[tr][name]
            res = {}
            for sp in ("train", "dev"):
                fin, hyb_, bm = {}, {}, {}
                for dom in doms:
                    if dom not in dump["scores"].get(sp, {}):
                        continue
                    gold = qrels_for(a.data, tr, dom, sp, qcond)
                    qids = sorted(dump["scores"][sp][dom])
                    bmr = read_run(os.path.join(a.root, hyb["bm25"].replace("../", "", 1)
                                                if hyb["bm25"].startswith("../") else hyb["bm25"],
                                                f"t{tr}_{dom}_{sp}_{hcond}.tsv")) if var == "q" else {}
                    fin[dom] = [ndcg([d for d, _ in dump["scores"][sp][dom][q]], gold[q], 10) for q in qids]
                    hyb_[dom] = [ndcg([d for d, _ in dump["none"][sp][dom][q]], gold[q], 10) for q in qids]
                    if var == "q":
                        bm[dom] = [ndcg([d for d, _ in bmr.get(q, [])], gold[q], 10) for q in qids]
                res[sp] = {"final": fin, "hybrid": hyb_, "bm25": bm}
            best = row["best_on_train"]
            chk = {sp: round(macro(res[sp]["final"]), 4) for sp in ("train", "dev")}
            assert chk == {sp: row["by_how"][best][sp] for sp in ("train", "dev")}, (name, chk, row["by_how"][best])
            tb = row.get("train_bootstrap_best_minus_none") or {}
            out[var] = {
                "name": name, "hybrid_cfg": hc["systems"]["linear*"]["cfg"], "reasonembed_way": best,
                "rule8_margin_met": bool(tb) and tb["diff"] >= 0.005 and tb["ci95"][0] > 0,
                "train": chk["train"], "dev": chk["dev"],
                "train_ci": ci_macro(res["train"]["final"], a.boot), "dev_ci": ci_macro(res["dev"]["final"], a.boot),
                "hybrid_train": round(macro(res["train"]["hybrid"]), 4), "hybrid_dev": round(macro(res["dev"]["hybrid"]), 4),
                "dev_per_domain": {d: round(sum(v) / len(v), 4) for d, v in res["dev"]["final"].items()},
                "n_topics": {sp: sum(len(v) for v in res[sp]["final"].values()) for sp in ("train", "dev")}}
            if var == "q":
                out["_bm25_q"] = {"train": round(macro(res["train"]["bm25"]), 4), "dev": round(macro(res["dev"]["bm25"]), 4),
                                  "dev_ci": ci_macro(res["dev"]["bm25"], a.boot)}
                out["_hybrid_q"] = {"train": out["q"]["hybrid_train"], "dev": out["q"]["hybrid_dev"],
                                    "dev_ci": ci_macro(res["dev"]["hybrid"], a.boot)}
            per[var] = res
            print(f"[{cname}] {var:<6} {name:<12} train {chk['train']:.4f} dev {chk['dev']:.4f} ({best})", flush=True)
        for var in ("q", "q+r", "q+h"):
            out[var]["delta_vs_qrh"] = {sp: bootstrap(per[var][sp]["final"], per["q+r+h"][sp]["final"], n=a.boot)
                                        for sp in ("train", "dev")}
        out["_bm25_q"]["delta_vs_qrh"] = {"dev": bootstrap(per["q"]["dev"]["bm25"], per["q+r+h"]["dev"]["final"], n=a.boot)}
        out["_hybrid_q"]["delta_vs_qrh"] = {"dev": bootstrap(per["q"]["dev"]["hybrid"], per["q+r+h"]["dev"]["final"], n=a.boot)}
        rep["variants"][cname] = out
        # recall@k of the q+r+h hybrid (full train / dev, submission order) and the ReasonEmbed cost on dev
        hpath, hcond, _ = rows["q+r+h"]
        hyb = json.load(open(os.path.join(a.root, R, hpath)))
        hc = hyb["conditions"][hcond]
        cfg = hc["systems"]["linear*"]["cfg"]
        bdir = os.path.join(a.root, hyb["bm25"].replace("../", "", 1))
        ddir = os.path.join(a.root, hyb["dense"].replace("../", "", 1))
        rec = {}
        cost = {"topics": 0, **{f"pool{p}": 0 for p in POOLS}, "corpus_docs": 0}
        for sp in ("train", "dev"):
            rk = {k: [] for k in KS}
            dom_rec = {}
            gold_rank = defaultdict(int)
            for dom in doms:
                gold = qrels_for(a.data, tr, dom, sp, qcond)
                bm = read_run(os.path.join(bdir, f"t{tr}_{dom}_{sp}_{hcond}.tsv"))
                de = read_run(os.path.join(ddir, f"t{tr}_{dom}_{sp}_{hc['dense_condition']}.tsv"))
                dk = {k: [] for k in KS}
                uni = {p: set() for p in POOLS}
                for q, g in sorted(gold.items()):
                    lst = full_list(Query(bm.get(q, []), de.get(q, [])), cfg)
                    pos = {d: i for i, d in enumerate(lst, 1)}
                    for k in KS:
                        dk[k].append(len(set(lst[:k]) & g) / len(g))
                    for d in g:
                        r = pos.get(d)
                        gold_rank["1-10" if r and r <= 10 else "11-50" if r and r <= 50 else "51-100" if r and r <= 100
                                  else "101-200" if r and r <= 200 else "201-1000" if r else "not retrieved"] += 1
                    for p in POOLS:
                        uni[p].update(lst[:p])
                for k in KS:
                    rk[k].append(sum(dk[k]) / len(dk[k]))
                dom_rec[dom] = {k: round(sum(dk[k]) / len(dk[k]), 4) for k in KS}
                if sp == "dev":
                    cost["topics"] += len(gold)
                    for p in POOLS:
                        cost[f"pool{p}"] += len(uni[p])
                    with open(os.path.join(a.data, "track1_tempo" if tr == 1 else "track2_recor", dom,
                                           "documents.jsonl"), encoding="utf-8") as f:
                        cost["corpus_docs"] += sum(1 for ln in f if ln.strip())
                del bm, de
            rec[sp] = {"macro_recall": {k: round(sum(v) / len(v), 4) for k, v in rk.items()},
                       "gold_rank_buckets": dict(gold_rank), "per_domain": dom_rec}
        rep["recall"][cname] = {"hybrid_cfg": cfg, **rec}
        c = {"topics_dev": cost["topics"], "corpus_docs": cost["corpus_docs"]}
        for p in POOLS:
            n = cost[f"pool{p}"]
            c[f"pool{p}"] = {"distinct_docs": n, "docs_per_topic": round(n / cost["topics"], 1),
                             "minutes_at_7_per_s": round(n / 7 / 60, 1), "minutes_at_10_per_s": round(n / 10 / 60, 1),
                             "share_of_corpus": round(n / cost["corpus_docs"], 4)}
        rep["cost"][cname] = c
        print(f"[{cname}] recall dev {rec['dev']['macro_recall']}  cost {json.dumps(c)}", flush=True)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(rep, open(a.out, "w"), indent=1)
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
