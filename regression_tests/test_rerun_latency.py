"""Exercise archived-timing handling without models or third-party packages.

Runs in isolated copies of the small supporting records. Original experiment,
generation and timing files are never modified.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
FILES = [
    "output/improved_experiment/matched_benign_baseline.json",
    "output/improved_experiment/predictions_main.jsonl",
    "output/improved_experiment/predictions_benign_echo.jsonl",
    "output/improved_experiment/predictions_benign_mirror.jsonl",
    "improved_experiment/inputs/clean_target_candidates.json",
    "improved_experiment/inputs/notinject.json",
    "output/improved_experiment/notinject_predictions.jsonl",
    "output/improved_experiment/notinject_results.json",
    "output/improved_experiment/calibration.json",
    "output/improved_experiment/protocol.json",
    "output/improved_experiment/pools_main.jsonl",
    "output/improved_experiment/latency_cold_pools.json",
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    before = {name: digest(ROOT / name) for name in FILES}
    spec = importlib.util.spec_from_file_location("latency_regression_verifier", ROOT / "verify_project.py")
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    with tempfile.TemporaryDirectory(prefix="group9_latency_regression_") as td:
        fixture = Path(td)
        for name in FILES:
            target = fixture / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, target)
        verifier.ROOT = fixture
        verifier.EXP = fixture / "output/improved_experiment"
        baseline = verifier.check_supporting_records()
        assert baseline["archived_latency"]["source_pool_match"]
        pools = verifier.EXP / "pools_main.jsonl"
        original = pools.read_bytes()
        assert b"\r\n" not in original
        parsed_before = verifier.rows(pools)
        pools.write_bytes(original.replace(b"\n", b"\r\n"))
        assert verifier.rows(pools) == parsed_before
        try:
            verifier.check_supporting_records()
        except AssertionError as exc:
            assert "Archived latency source-pool hash" in str(exc)
        else:
            raise AssertionError("Strict verification accepted an unlinked archived timing source")
        timing_path = verifier.EXP / "latency_cold_pools.json"
        timing_bytes = timing_path.read_bytes()
        fresh = verifier.check_supporting_records(allow_stale_latency=True)
        timing = fresh["archived_latency"]
        assert not timing["source_pool_match"] and not timing["ordered_source_texts_verified"]
        assert timing["stale_source_explicitly_allowed"] and not timing["newly_measured_by_rerun"]
        assert timing["status"] == "not_revalidated_against_current_pools"
        assert timing_path.read_bytes() == timing_bytes
        damaged = json.loads(timing_bytes)
        key = next(iter(damaged["per_query_pool_seconds"]))
        damaged["per_query_pool_seconds"][key]["median"] += 1
        timing_path.write_text(json.dumps(damaged), encoding="utf-8")
        try:
            verifier.check_supporting_records(allow_stale_latency=True)
        except AssertionError:
            pass
        else:
            raise AssertionError("Rerun mode skipped corrupted timing statistics")
    guarded = subprocess.run([sys.executable, "-S", str(ROOT / "verify_project.py"), "--allow-stale-latency"],
                             text=True, encoding="utf-8", capture_output=True)
    assert guarded.returncode == 2 and "requires --skip-manifest" in guarded.stderr
    spec = importlib.util.spec_from_file_location("rerun_wrapper_regression", ROOT / "run_project.py")
    wrapper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wrapper)
    with tempfile.TemporaryDirectory(prefix="group9_cache_regression_") as td:
        fixture = Path(td)
        cache = fixture / "improved_generation/output/responses_cache.jsonl"
        cache.parent.mkdir(parents=True)
        first_content = b'{"archived_execution": 1}\n'
        cache.write_bytes(first_content)
        first_backup = wrapper.archive_generation_cache(fixture)
        assert not cache.exists() and first_backup.read_bytes() == first_content
        second_content = b'{"partial_new_execution": 2}\n'
        cache.write_bytes(second_content)
        second_backup = wrapper.archive_generation_cache(fixture)
        assert second_backup != first_backup and second_backup.read_bytes() == second_content
        assert first_backup.read_bytes() == first_content
        assert wrapper.archive_generation_cache(fixture) is None
    assert before == {name: digest(ROOT / name) for name in FILES}
    print(json.dumps({"status": "passed", "neural_inference": False,
                      "scenarios": ["Unchanged archive source validates strictly",
                                    "Semantically identical LF-to-CRLF pool rewrite fails strict source linkage",
                                    "Explicit rerun mode marks old timing as archived and not remeasured",
                                    "Corrupted timing statistics fail even in rerun mode",
                                    "Stale timing option is forbidden in default archive mode",
                                    "Explicit full-run cache backups preserve bytes and use unique paths"],
                      "all_original_supporting_files_unchanged": True}, indent=2))


if __name__ == "__main__":
    main()
