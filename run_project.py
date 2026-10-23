"""Portable entry point for Group 9 retrieval-context filtering research.

The default verifies archived records without network access or neural inference.
Legacy model execution is explicit because it replaces legacy result files.
The revised source-disjoint study uses --rerun-revised in a separate run directory.
"""
from pathlib import Path
import argparse
import datetime
import os
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parent

def archive_generation_cache(project_root=ROOT):
    """Keep prior cached execution evidence before an explicit new full run."""
    cache = project_root / "improved_generation/output/responses_cache.jsonl"
    if not cache.exists():
        return None
    archive_dir = project_root / "improved_generation/cache_archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup = archive_dir / f"responses_cache_{stamp}_{uuid.uuid4().hex}.jsonl"
    cache.rename(backup)
    print("Archived prior generation resume cache:", str(backup), flush=True)
    return backup

def run(*args):
    print("Running:", " ".join(args), flush=True)
    interpreter_flags = (["-S"] if sys.flags.no_site else []) + ["-X", "utf8"]
    subprocess.run([sys.executable, *interpreter_flags, *args], cwd=ROOT, check=True)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--verify-only", action="store_true", help="Audit bundled records with the Python standard library; this is also the default.")
    actions.add_argument("--rerun-revised", action="store_true", help="Execute the revised source-disjoint small-corpus evaluation in a new run directory.")
    actions.add_argument("--rerun", action="store_true", help="Execute fresh pinned CPU models and replace fresh experiment/generation outputs.")
    parser.add_argument("--download-models", action="store_true", help="With either rerun action, download and verify its pinned public weights first (about 3.3 GB for the revised run).")
    args = parser.parse_args()
    if args.download_models and not (args.rerun or args.rerun_revised):
        parser.error("--download-models requires --rerun or --rerun-revised")
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    os.environ["PYTHONUTF8"] = "1"
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    if args.rerun_revised:
        extra = ["--download-models"] if args.download_models else []
        run("revised_experiment/run.py", *extra)
        return
    if not args.rerun:
        run("verify_project.py")
        run("revised_experiment/verify_new.py")
        run("evidence/provided_3b_rescoring/verify_summaries.py")
        run("extensions/e2_unfiltered/verify.py")
        return
    if args.download_models:
        run("improved_experiment/download_models.py")
        run("improved_generation/download_qwen.py")
    run("improved_experiment/run.py")
    run("improved_experiment/analyse.py")
    run("improved_experiment/additional_metrics.py")
    run("improved_experiment/matched_controls.py")
    run("improved_experiment/public_guard.py")
    run("improved_experiment/make_figures.py")
    run("improved_generation/scoring.py")
    archive_generation_cache()
    run("improved_generation/run_generation.py", "--input", "output/improved_experiment/generation_contexts.jsonl", "--output", "improved_generation/output")
    run("improved_generation/recompute_statistics.py", "--output", "improved_generation/output")
    run("improved_generation/apostrophe_sensitivity.py")
    run("improved_generation/apply_scoring_correction.py")
    run("improved_generation/validate_completed.py", "--input", "output/improved_experiment/generation_contexts.jsonl", "--output", "improved_generation/output")
    run("verify_project.py", "--skip-manifest", "--allow-stale-latency")
    print("Independent latency was not remeasured; verification records whether its archived source pools still match.")
    print("Fresh execution completed. Archived package hashes describe the delivered run; compare new results before replacing its manifest.")

if __name__ == "__main__":
    main()
