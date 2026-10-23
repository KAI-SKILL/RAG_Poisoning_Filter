# Expanded stress-test code and actual CPU results

This supplementary suite reuses the frozen LR and LinearSVC text classifiers and
adds 24 controlled attack templates. It is separate from the main article-disjoint
SQuAD transfer study in the repository root. Code, frozen small inputs, classifier
artifacts, source attribution, and actual 2026-10-22 CPU outputs are retained.

The 28,800 attack cases and 28,800 benign controls reuse the same 1,200 test
questions across templates (138 articles). They are not 57,600 independent tasks.
Retrieval uses the separately declared exact lexical TF-IDF harness.

## Included execution evidence

- `results/fresh_sparse/`: complete final sparse scoring and retrieval outputs,
  a published execution receipt, closed-output hashes, and archived executed code.
  Each classifier scored 74,577 texts in 292 calls. Outputs contain 67,200 inserted
  document records, 57,600 case-condition records, 57,600 retrieval deliveries,
  1,200 clean retrievals, and 1,195 passively scored external contexts. This run
  performed zero generator calls, neural calls, or detector fits.
- `results/fresh_q_cpu/`: actual standalone Q30 answerability generation, 90/90
  distinct prompts, pinned Qwen2.5-3B Q4 CPU model. Reference exact matches are
  1/30 without retrieval, 19/30 with gold evidence, and 19/30 with TF-IDF retrieval.
  Q has no attack condition and supplies no attack success rate.
- `generation/all_experiments/`: Q/E1/E2/E3 runners and original frozen registry
  for three models. These scripts are planned execution support. They do not
  establish completion of the 12 cluster GPU result slots.
- `prior_study/original_project/`: frozen subset used by these runners, with generalized review metadata,
  retained at its original relative paths. The complete main study is elsewhere
  in the repository root.

## Restore archived text files and verify final sparse results

From the repository root, run `python tools/restore_artifacts.py`. This restores
the losslessly compressed text files using `compressed_artifacts.json` and
checks their SHA-256 hashes. It performs no model execution or network access.
Then, from this directory:

```bash
python code/verify_portable.py --root . --results results/fresh_sparse
```

Verification uses only the Python standard library. It reconstructs saved
decisions, confusion counts, ranking metrics, and retrieval aggregates. It does
not rerun the classifiers, regenerate answers, or recompute confidence intervals.

The historical `run_manifest.json` includes four unfinished hidden temporary
serialization files. They are omitted from this distribution. The historical hashes are retained; local-system metadata is generalized in
the public release. `verify_portable.py` verifies their binding through the
explicit `PUBLIC_RELEASE_MANIFEST.json` mapping and checks every final closed
output. It excludes only those four named temporary entries in memory and
retains the original numerical reconstruction.
The archived `audit/verify_fresh.py` retains original machine-specific paths;
use the portable command above for this distribution.

To rerun sparse classification/retrieval, use Python 3.12 and the execution
versions in `requirements.txt`. Read `code/evaluate_expanded.py --help` before
choosing a new output directory; retain the frozen results as evidence.

## Frozen E3 input database and optional new input builds

The original 1.36 GB `generation/input/generation_inputs.sqlite` is preserved
losslessly as ordered independent gzip chunks in
`generation/input/generation_inputs.sqlite.parts/`. Each chunk represents at most
32 MiB of original data. The root restore command joins their decompressed bytes
and checks the complete original database SHA-256 before installing the file.
Its original input manifest, token receipts, and token-count database are kept.
The smaller frozen Q/E1/E2 SQLite inputs are included directly. This preserves
the original frozen registry bindings after restoration; it supplies prepared
inputs, not completed GPU-generation results.

For a separate input-only rebuild using the included fresh CPU-result
provenance, this optional command creates a new derived database:

```bash
python code/generation/prepare_inputs.py --root . --output-dir generation/rebuilt_input
```

It performs no tokenization, inference, model loading, or network calls and
requires a new output directory. The archived preparation expects 176,400 request
rows and 56,373 distinct E3 prompts. This separate rebuild is not promised to have
the original SQLite file hash: the fresh CPU execution-freeze receipt differs
from the older receipt bound into the archived registry. Use the new build's
manifest and rerun the applicable tokenizer/protocol preflight before registering
or launching a generation experiment from these newly rebuilt inputs. Restoring
the original chunks is sufficient when using the original frozen inputs.

Compatibility copies at `results/normal_retrieval.jsonl`,
`results/thresholds_frozen.json`, `results/execution_freeze.json`, and the restored
`results/retrieval_delivery.jsonl` allow the original input builder to read its
expected paths. The full actual-result archive remains under `results/fresh_sparse`.

Neural weights, environment caches, unfinished temporary files, academic reports,
and slides are not distributed. Original source attribution and license records
are retained under `raw/` and `external/`.

The Windows launcher accepts `-ClusterHost` or prompts for the hostname at execution time. Configure your own cluster account and connection details locally.
