# Revised experiment implementation

The delivered study uses old70 NQ questions for fitting and newly frozen SQuAD article groups for normal calibration and transfer testing. No old question is relabelled as a new blind test. Full protocol: `protocol_frozen.json`; actual inputs and case hashes: `../output/revised_experiment/cases/case_freeze.json`.

## Stages and saved evidence

| Stage | Implementation | Delivered evidence |
|---|---|---|
| Source quality and split | `data/` and `../evidence/utility_audit/` | Original questions, repaired development mapping, source-supported85 mask, wrong-targetv2 audit |
| Exact subcorpus retrieval | `features/retrieve.py` | `../output/revised_experiment/retrieval/` |
| Fixed insertion cases | `prepare_pools.py` | `cases/input_pools.jsonl`, `case_freeze.json` |
| New neural features | `features/run_features.py` | `fresh_features/` candidate/pool rows, caches and execution manifests |
| Full insertion rank check | `features/validate_insert_rank.py` | `fresh_features/insert_rank_validation.json` |
| New linear fitting/calibration | `fit_and_select.py` | `selection/fit_frozen.json`, pureJSON model parameters, decisions and context requests |
| Actual3B generation | `gguf_generate.py` | `generation/` full prompts, raw responses, cache and model/config hashes |
| Fixed scoring/paired analysis | `evaluate_new.py` | `new_scores/` raw scored rows, summaries and paired intervals |
| Unified integrity check | `verify_new.py` | `../output/revised_validation.json` |

Evidence paths in the last seven rows are relative to `../output/revised_experiment/`. Archived execution metadata retain the actual work-directory paths used at execution time. Portable tools resolve bundled inputs relative to this project; the original recorded paths are provenance, not required installation directories.

## Exact scope

Normal documents remain unchanged. Each targeted case appends one false-evidence or instruction document to its declared600-paragraph test subcorpus. The25-case mechanism suite appends legitimate copies/echoes or five identical false paragraphs. The normal top20 plus inserted documents is checked against direct search over the complete declared subcorpus. This is a controlled small-corpus case, not full Wikipedia retrieval or a corpus jointly containing every target's attack at once.

The four feature definitions match the archived system: frozen guard score, fixed rule count, query-score z within the current pool, and maximum peer text cosine. Retrieval accumulation is fixed-axis float64 for deterministic duplicate ordering. The old float32-BLAS tie diagnosis is preserved separately. Every new pool recomputes its peer statistics. Guard sees paragraph text; retrieval sees title+text. Feature/tokenizer diagnostics record input lengths; generator preflight refuses truncation.

The public guard-only baseline is a standalone component. It is not a reproduction of a complete external defense. The TF-IDF LR baseline uses fixed word1–2 and character3–5 features on the same allowed old training records. Sparse inputs and guard token limits are documented separately. The primary incremental comparison is fused versus no_guard; fused versus context changes two components.

## Reproduce a new run

Use Python3.11 or later. From the project root, install `revised_experiment/requirements.txt` in a clean Python environment, then:

```bash
python run_project.py --rerun-revised --download-models
```

Or specify a new empty output directory:

```bash
python revised_experiment/run.py --output output/my_new_run --threads 6
```

This runs new retrieval/features/generation. It deliberately reuses archived old70 training features. Downloaded weights stay under this project and are hash-checked; they are not bundled. Installation and inference time depend on the user's machine. The delivered run used CPU execution, with measured Linux memory/cost metadata; no Windows16GB benchmark is asserted.

The delivered normal/new-text encoder stages used2 threads, the guard stage4, and the generator6. The convenience runner uses one configurable thread count for a fresh run, so it is a protocol rerun rather than a guarantee of byte-identical floating-point results. Exact delivered-stage configurations are retained in their manifests.

Each stage runner accepts explicit paths. Generation resumes only under an identical model/config/producer fingerprint. The top-level new-run command requires an empty destination, protecting the delivered results. Changed-platform or changed-code caches must not be reused.

Re-run the custom development requests separately:

```bash
python revised_experiment/gguf_generate.py --model revised_experiment/models/Qwen2.5-3B-Instruct-GGUF/qwen2.5-3b-instruct-q4_k_m.gguf --input revised_experiment/dev_q_v2_requests.jsonl --output output/my_dev_repeat
```

The original developmental producer source is preserved in `archive/gguf_generate_q_v1.py`. The current portable runner includes all-prompt token preflight and platform metadata. Neither command upgrades partial source support or string matching into independently human-adjudicated factual accuracy.

## Offline verification and interpretation

```bash
python run_project.py --verify-only
python revised_experiment/verify_new.py --deep
```

The default check reconstructs saved decisions, contexts, hashes and measurement integers without neural weights or pickle. Deep checking additionally needs NumPy and uses the small bundled embedding arrays for direct ranking/statistical reconstruction. These checks establish internal evidence consistency and provenance limits, not a cryptographic proof of model execution or an independent replication of every paper.

To audit a complete fresh transfer run, use `python -X utf8 revised_experiment/verify_new.py --run-dir output/my_new_run --output output/my_new_run/verification.json`. Its frozen development diagnosis is checked in the delivered archive; all newly requested main-test generations and scores must exist in the new run. Use `-X utf8` when invoking individual stage scripts directly on Windows. The two top-level runners already pass this setting to child stages.

All100 test cases remain in annotation-proxy results. The85source-supported questions are a pre-output sensitivity subset. The25mechanism questions come from a fixed hash of this subset, not from any model's successes/failures. Responses are short, but reference or target mention can still be quoted, negated or incomplete. Alias exact match, tokenF1, exact target answer, abstention and conflicts are separate fields. Main claims must consider clean utility and retained annotated evidence as well as target suppression.

The small development set did not provide an unconditional reliability pass. New experiments therefore support bounded diagnostic comparisons. No adaptive worst-case robustness or verified current-world fact accuracy is claimed. All generated answers, failures, code and input checks are retained; selected figures must not omit unfavorable controls.

The original frozen E2 lacked unfiltered echo/copy/five-insertion controls. The merged study adds the five missing unfiltered conditions on the same25questions as a separately frozen post-hoc extension, documented in `../extensions/e2_unfiltered/README.md`. Its outputs and analysis are kept outside the original2,175-row run, under `../output/revised_experiment/e2_unfiltered/`. The original code, data, thresholds and formal scores remain unchanged. Matched comparisons address the missing-control gap but still do not identify density alone or general effects of natural repetition. Known-support retention identifies only the annotated gold paragraph and its declared legitimate copies/echoes; zero retention does not establish that every useful passage was removed.
