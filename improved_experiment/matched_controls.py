"""Post-run descriptive audit of matched originals for benign controls.

No model is loaded, fitted, calibrated or selected. Pair each modified/copied
record with the same source document under the ordinary clean condition.
"""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output/improved_experiment"


def load(name):
    return [json.loads(line) for line in (OUT / name).read_text(encoding="utf-8").splitlines()]


def main():
    ordinary = {(r["qid"], r["id"]): r for r in load("predictions_main.jsonl") if r["setting"] == "none"}
    methods = list(next(iter(ordinary.values()))["blocked"])
    results = {}
    for suite, prefix in [("benign_echo", "echo:"), ("benign_mirror", "mirror:")]:
        controls = [r for r in load(f"predictions_{suite}.jsonl") if r["family"] == suite]
        pairs = [(ordinary[r["qid"], r["id"].removeprefix(prefix)], r) for r in controls]
        assert len(pairs) == 500 and all(r["id"].startswith(prefix) for _, r in pairs)
        results[suite] = {}
        for method in methods:
            original_fp = sum(old["blocked"][method] for old, new in pairs)
            modified_fp = sum(new["blocked"][method] for old, new in pairs)
            new_fp = sum(not old["blocked"][method] and new["blocked"][method] for old, new in pairs)
            rescued = sum(old["blocked"][method] and not new["blocked"][method] for old, new in pairs)
            results[suite][method] = {"matched_records": len(pairs), "queries": len({new["qid"] for old, new in pairs}),
                "original_fp": original_fp, "modified_or_copied_fp": modified_fp,
                "original_matched_fpr": original_fp / len(pairs), "modified_or_copied_fpr": modified_fp / len(pairs),
                "original_retained_newly_blocked": new_fp, "original_blocked_newly_retained": rescued,
                "paired_net_fpr_increase": (new_fp - rescued) / len(pairs)}
    document = {"scope": "Post-run descriptive measurement audit, fixed candidate predictions only. This pairs source document IDs under none with the modified/copied control records. The ordinary whole-pool FPR and selected-five FPR have different denominators. All five transformations occur together, so paired changes include peer-pool, retrieval-z and rank effects; this is not a randomized text-only causal estimate. No additional inferential test, model fitting, threshold tuning or neural inference.",
                "source_sha256": {name: hashlib.sha256((OUT / name).read_bytes()).hexdigest() for name in ["predictions_main.jsonl", "predictions_benign_echo.jsonl", "predictions_benign_mirror.jsonl"]},
                "results": results}
    target = OUT / "matched_benign_baseline.json"
    target.write_text(json.dumps(document, indent=2), encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()
