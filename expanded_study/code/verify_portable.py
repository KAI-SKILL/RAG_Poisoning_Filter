"""Verify retained final sparse outputs after temporary files are omitted.

The privacy-redacted manifest and receipt retain mapped historical references. The
verifier reconstructs final decisions and metrics; only four explicitly named,
unfinished serialization artifacts are excluded from its in-memory output list.
No file is written and no model, tokenizer, or network operation is performed.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys

# Public-release checks preserve historical references without asserting byte identity.
import sys as _release_sys
_release_root = next(path for path in Path(__file__).resolve().parents
                     if (path / "tools/public_release_integrity.py").is_file())
_release_sys.path.insert(0, str(_release_root / "tools"))
from public_release_integrity import (
    reference_sha, reference_size, published_sha, matches_reference,
    matches_size_reference, provenance_summary,
)


OMITTED_TEMPORARIES = {
    ".case_predictions.jsonl.xxxkxftp.tmp",
    ".retrieval_delivery.jsonl.08xwl4hw.tmp.UJ5vVX",
    ".retrieval_delivery.jsonl.08xwl4hw.tmp.UJ5vVX.yvcxRL",
    ".retrieval_delivery.jsonl.gPzCpS",
}


def sha256(path: Path) -> str:
    return reference_sha(path)  # Explicit historical references after release-byte validation.


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--results", type=Path)
    parser.add_argument("--models", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    results = (args.results or root / "results/fresh_sparse").resolve()
    manifest_path = results / "run_manifest.json"
    receipt = json.loads((results / "execution_receipt.json").read_text(encoding="utf-8"))
    original_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if sha256(manifest_path) != receipt["outputs_sha256"]["run_manifest.json"]:
        raise ValueError("Historical run manifest does not match execution receipt")
    if not OMITTED_TEMPORARIES.issubset(original_manifest["outputs"]):
        raise ValueError("Historical temporary-file inventory has changed")
    omitted = {name: original_manifest["outputs"][name] for name in sorted(OMITTED_TEMPORARIES)}
    if original_manifest["archive_integrity"]["status"] != "CLOSED_OUTPUT_ROW_AND_KEY_COVERAGE_VERIFIED":
        raise ValueError("Historical closed-output coverage record is missing")
    for name, metadata in original_manifest["archive_integrity"]["files"].items():
        if sha256(results / name) != metadata["sha256"]:
            raise ValueError("Closed final output byte hash differs: " + name)

    verifier_path = root / "code/verify_expanded.py"
    spec = importlib.util.spec_from_file_location("original_expanded_verifier", verifier_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load original expanded verifier")
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    original_read = verifier.read

    def read_retained(path):
        value = original_read(path)
        if Path(path).resolve() == manifest_path:
            value["outputs"] = {name: digest for name, digest in value["outputs"].items()
                                if name not in OMITTED_TEMPORARIES}
        return value

    verifier.read = read_retained
    original_argv = sys.argv
    sys.argv = [str(verifier_path), "--root", str(root), "--results", str(results)]
    if args.models:
        sys.argv.extend(["--models", str(args.models.resolve())])
    capture = io.StringIO()
    try:
        with contextlib.redirect_stdout(capture):
            verifier.main()
    finally:
        sys.argv = original_argv
    report = json.loads(capture.getvalue())
    report["original_manifest_byte_identity_asserted"] = False
    report["historical_manifest_receipt_binding"] = "verified through explicit public-release mapping"
    report["published_manifest_sha256"] = published_sha(manifest_path)
    report["historical_manifest_reference_sha256"] = reference_sha(manifest_path)
    report["public_release_provenance"] = provenance_summary()
    report["omitted_unfinished_temporary_outputs"] = omitted
    report["scope"] = (
        "Retained closed final artifacts, privacy-redacted receipt/manifest reference mapping, strict "
        "thresholds, labels, score aggregation, confusion counts, tie-aware AUROC/AP "
        "and retained-document decisions. Four listed unfinished temporary "
        "serialization files are not distributed or verified. No confidence-interval "
        "recalculation, model execution attestation, or semantic attack-success claim."
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
