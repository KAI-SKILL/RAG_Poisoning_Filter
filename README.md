# RAG Poisoning Filter

Research and experiments on detecting adversarial retrieved contexts in retrieval-augmented generation (RAG).


This repository contains the implementation, frozen experimental inputs, archived model responses, scoring code and scientific verification checks. It includes the main SQuAD transfer study and its NQ development evidence, plus a separately identified expanded attack study. Presentation and report deliverables are excluded.

## Main research question

Does a frozen neural injection guard add useful protection to fixed instruction rules and retrieval-context features, while preserving legitimate evidence and ordinary answers?

The passage filter combines four signals in a logistic head: a frozen DeBERTa injection score, fixed instruction cues, within-pool relevance, and maximum peer similarity. The direct attribution comparison is **fusion versus a separately fitted no-guard head**. Context-only, guard-only, TF-IDF logistic regression and unfiltered generation provide additional comparisons.

The main study fits on archived features from 70 Natural Questions (NQ) training questions. It uses article-disjoint SQuAD groups: 30 development articles, 100 clean calibration articles and 100 locked test articles. Thresholds are fixed on clean calibration passages, with a primary 1% false-positive budget. The generator is the pinned Qwen2.5-3B-Instruct Q4_K_M model, run on CPU through llama-cpp-python. Full model revisions, inference settings, splits and thresholds are retained in the manifests and frozen protocols.

## Main archived findings

The table gives **reference exact matches / target exact matches**, each out of 100 questions. These are string-based measurements, not independently adjudicated semantic accuracy.

| Policy | Clean | Factual counterfactual | Instruction injection |
|---|---:|---:|---:|
| Unfiltered | 61 / 0 | 41 / 27 | 57 / 25 |
| Context-only | 55 / 0 | 3 / 0 | 5 / 0 |
| No-guard | 53 / 0 | 2 / 0 | 9 / 0 |
| Fusion | 53 / 0 | 2 / 0 | 9 / 0 |
| TF-IDF LR | 61 / 0 | 40 / 26 | 58 / 11 |
| Guard-only | 60 / 0 | 40 / 27 | 61 / 15 |

Fusion and no-guard deliver identical contexts in all 300 E1 question-condition pairs. Thus the neural guard has no observed incremental effect at this operating point. Under factual counterfactuals, fusion removes target answers but retains the annotated supporting paragraph in 0/100 contexts, with 89/100 abstentions. Attack suppression must therefore be interpreted alongside evidence loss and answer utility.

The 25-question E2 controls examine benign echoes/copies and attack multiplicity. The additional 125 unfiltered E2 requests are a **separately frozen post-hoc extension** and remain separate from the original 2,175-row generation archive.

## Start with offline verification

From this directory, using Python 3.11 or later:

```bash
python -X utf8 run_project.py --verify-only
```

This checks the saved NQ evidence, main SQuAD decisions/contexts/raw answer scores, and the E2 extension. It requires no model weights, network access or neural inference. The repository entry point runs numerical consistency checks with explicit public-release metadata references; document-production checks are excluded.

Individual scientific checks can write separate verification files:

```bash
python -X utf8 revised_experiment/verify_new.py --output .verification/main.json
python -X utf8 extensions/e2_unfiltered/verify.py --output .verification/e2.json
```

The main check reconstructs 42,500 test probabilities, 10,000 calibration probabilities, 10 thresholds and 2,175 contexts representing 432 distinct prompts. The extension check reconstructs and rescores 700 matched analysis rows. These are archived-row and prompt counts, not newly executed generation calls.

## Run a fresh main-study experiment

Install the pinned main-study environment, then use a new output directory:

```bash
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
python -m pip install -r revised_experiment/requirements.txt
python -X utf8 revised_experiment/run.py --download-models --output output/my_new_run --threads 6
```

This downloads the pinned weights and recomputes SQuAD retrieval, new-text features, fitting, filtering and generation. It deliberately reuses the archived old70 neural training features. It requires a new output directory, preserving the supplied results. Hardware, dependency availability and runtime depend on the execution machine; the original environment versions are retained rather than silently replaced.

See [`revised_experiment/README.md`](revised_experiment/README.md) and [`extensions/e2_unfiltered/README.md`](extensions/e2_unfiltered/README.md) for stage commands and protocol details.

## Repository map

| Path | Purpose |
|---|---|
| `revised_experiment/` | Main SQuAD source selection, frozen protocol, features, fitting, generation and scoring |
| `output/revised_experiment/` | Main frozen cases, features, decisions, raw answers and evaluation outputs |
| `extensions/e2_unfiltered/` | Separately frozen post-hoc unfiltered E2 controls |
| `improved_experiment/`, `improved_generation/` | NQ development and supporting experiments |
| `development_pilot/` | Earlier pilot code and its explicitly separate records |
| `evidence/` | Scientific audits, source checks and supporting measurements |
| `expanded_study/` | Later expanded NQ attack suite, real sparse/Q CPU records and GPU execution code |
| `DATA_ATTRIBUTION.md` | Original data and model provenance |
| `UPLOAD_中文.md` | PowerShell commands for uploading this directory |

## Expanded-study data and execution status

The expanded study is separate from the main SQuAD study. It contains real sparse detection/retrieval outputs and a closed Q CPU generation run. The 12-slot multi-model GPU suite is execution code and frozen inputs; it is **not a claim that those 12 GPU runs were completed**. Read [`expanded_study/README.md`](expanded_study/README.md) before running it.

Large expanded JSONL files are supplied as lossless gzip files so the repository can be pushed with ordinary Git. Restore them locally before expanded-study commands:

```bash
python tools/restore_artifacts.py
```

Restoration verifies each file's archived uncompressed SHA-256 and does not modify the supplied gzip copies. Restored files are ignored by Git. The large frozen E3 generation-input database is preserved as ordered gzip parts and is restored byte-for-byte, retaining the archived registry and token-receipt hashes. The exact procedures and original manifests are retained in `expanded_study/`.

## Interpretation and provenance

The study uses exact retrieval over a declared small subcorpus with target-specific insertions. It does not establish full-Wikipedia, persistent cross-query or adaptive robustness. Recorded execution paths are generalized provenance; installation paths are resolved relative to this repository. This public release generalizes personal, review and local-system metadata. Frozen prompts, model responses, numeric results and binary/compressed experiment inputs remain unchanged. Model weights are obtained from their original repositories. Dataset/model licenses and attributions remain with their respective records; no new blanket license is assigned to third-party material.

The repository's `.gitattributes` disables automatic newline conversion so frozen file hashes remain valid when cloning on Windows or Linux.

## Public-release metadata integrity

Personal and local-system metadata are generalized in this distribution. `PUBLIC_RELEASE_MANIFEST.json` distinguishes historical file references from the actual published SHA-256 and byte count of each changed file. Historical hashes in frozen records are retained; they are not rewritten to pretend that redacted metadata has its original bytes. The verification helper first validates the published file against this release mapping, then checks the historical reference while independently reconstructing experiment numbers. Verification output explicitly labels this derivative scope and separates current verifier hashes from historical identifiers.

```bash
python tools/public_release_integrity.py
```

This is public-release numerical consistency checking, not a new model execution or a claim that redacted metadata is byte-identical to the original archive. The review records still identify single-review limitations and the absence of blinded independent annotation. Cluster connection details are entered at execution time; no account or credential is embedded.
