"""Step 7 - Statistics for the end-to-end results (step 4 outputs).

Two things the report needs on top of raw percentages:
  1. Uncertainty: 95% Wilson confidence interval for every ASR / accuracy (n = 100 questions).
  2. Significance of differences between defenses: exact McNemar test on the SAME questions
     (paired design: each question is answered under both defenses, so we only look at the
     questions where the two defenses disagree).

  3. Holm correction for a pre-specified primary family (default: fused vs ctx under
     poison, ignore, stealth - the family used in the final report).

Outputs (results/{ds}/):
  stats_ci.csv        defense, setting, metric, value, ci_low, ci_high
  stats_mcnemar.csv   setting, metric, defense_a, defense_b, a_only, b_only, p_value, p_holm_primary
                      (p_holm_primary is filled only for the primary-family rows)

Self-contained (no import from common.py), so it runs from any folder:
  python step7_stats.py --results_dir results_bounded
"""
import argparse
import csv
import json
import math
import os


def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def holm(pvals):
    """Holm step-down adjusted p-values, returned in the input order."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj, running = [0.0] * m, 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * pvals[i]))
        adj[i] = running
    return adj


def wilson(k, n, z=1.96):
    if n == 0:
        return float("nan"), float("nan")
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0.0, centre - half), min(1.0, centre + half)


def mcnemar_exact(b, c):
    """Two-sided exact McNemar p-value from the discordant counts b and c."""
    n = b + c
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, i) for i in range(0, min(b, c) + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="nq")
    ap.add_argument("--results_dir", default="results")
    ap.add_argument("--suffix", default="_hf", help="folder suffix written by step 4, e.g. _hf or _openai")
    ap.add_argument("--defenses", default="none,trust_rule,trust_guard,trust_ctx,trust_fused,oracle")
    ap.add_argument("--compare_to", default="trust_fused", help="defense compared against all others")
    ap.add_argument("--primary_vs", default="trust_ctx", help="primary family: compare_to vs this defense")
    ap.add_argument("--primary_settings", default="poison,ignore,stealth", help="primary family settings (Holm)")
    args = ap.parse_args()

    root = os.path.join(args.results_dir, args.dataset)
    defs = [d for d in args.defenses.split(",") if os.path.isdir(os.path.join(root, d + args.suffix))]
    res = {}  # (defense, setting) -> {qid: record}
    for d in defs:
        folder = os.path.join(root, d + args.suffix)
        for f in sorted(os.listdir(folder)):
            if f.endswith(".jsonl"):
                res[(d, f[:-6])] = {r["qid"]: r for r in load_jsonl(os.path.join(folder, f))}
    settings = sorted({s for _, s in res}, key=lambda s: (s != "none", s))

    def metric_of(setting):  # ASR under attack, accuracy without attack
        return ("Acc", "correct_hit") if setting == "none" else ("ASR", "attack_success")

    ci_rows = []
    for d in defs:
        for s in settings:
            if (d, s) not in res:
                continue
            name, key = metric_of(s)
            vals = [r[key] for r in res[(d, s)].values()]
            lo, hi = wilson(sum(vals), len(vals))
            ci_rows.append({"defense": d, "setting": s, "metric": name, "n": len(vals),
                            "value": round(100 * sum(vals) / len(vals), 1),
                            "ci_low": round(100 * lo, 1), "ci_high": round(100 * hi, 1)})

    mc_rows = []
    a = args.compare_to
    for b in defs:
        if b == a:
            continue
        for s in settings:
            if (a, s) not in res or (b, s) not in res:
                continue
            name, key = metric_of(s)
            qids = sorted(set(res[(a, s)]) & set(res[(b, s)]))
            a_only = sum(res[(a, s)][q][key] and not res[(b, s)][q][key] for q in qids)
            b_only = sum(res[(b, s)][q][key] and not res[(a, s)][q][key] for q in qids)
            mc_rows.append({"setting": s, "metric": name, "defense_a": a, "defense_b": b,
                            "a_only": a_only, "b_only": b_only, "p_value": round(mcnemar_exact(a_only, b_only), 4),
                            "p_holm_primary": ""})

    prim_settings = args.primary_settings.split(",")
    prim = [r for r in mc_rows if r["defense_b"] == args.primary_vs and r["setting"] in prim_settings]
    if prim:
        raw = [mcnemar_exact(r["a_only"], r["b_only"]) for r in prim]
        for r, adj in zip(prim, holm(raw)):
            r["p_holm_primary"] = round(adj, 4)

    for fname, rows in [("stats_ci.csv", ci_rows), ("stats_mcnemar.csv", mc_rows)]:
        with open(os.path.join(root, fname), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)

    print(f"McNemar: {a} vs others  (a_only / b_only = questions where only that defense 'succeeds' on the metric;"
          " for ASR lower is better, for Acc higher is better)")
    for r in mc_rows:
        star = " *" if r["p_value"] < 0.05 else ""
        print(f"  {r['setting']:10s} {r['metric']:3s} vs {r['defense_b']:12s}  {r['a_only']:3d} / {r['b_only']:3d}"
              f"   p={r['p_value']:.4f}{star}")
    if prim:
        print(f"\nPrimary family ({a} vs {args.primary_vs}, Holm over {len(prim)} tests):")
        for r in prim:
            print(f"  {r['setting']:10s} {r['a_only']:3d} / {r['b_only']:3d}   p={r['p_value']:.4f}"
                  f"   Holm p={r['p_holm_primary']:.4f}")
    print(f"\nSaved -> {root}/stats_ci.csv, {root}/stats_mcnemar.csv")


if __name__ == "__main__":
    main()
