# Public external evaluation data

This directory contains original public data and a standard-library Python loader. None of these records is used to fit models, choose thresholds, calibrate probabilities, or select fusion weights.

```python
from public_data.load_public_data import load_records
records = load_records()              # 464 dictionaries
hard_benign = load_records('notinject') # 339
attack_payloads = load_records('bipia') # 125
# Every dictionary has text, label, dataset, subset, family, source, license.
```

A normalized export is already available as `public_eval.jsonl`. Labels are 0 = benign and 1 = attack payload. The text is evaluation input and is never executed. `python public_data/load_public_data.py` rebuilds the export and verifies counts and duplicate checks.

## Sources and scope

| Source | Original items | Labels | Scope |
|---|---:|---|---|
| [NotInject](https://huggingface.co/datasets/leolee99/NotInject), author [JSON release](https://github.com/leolee99/PIGuard/tree/main/datasets) | 339: one/two/three trigger-word groups of 113 | All benign | Over-defense stress test; prompts deliberately include words associated with attacks |
| [Microsoft BIPIA text test attacks](https://github.com/microsoft/BIPIA/blob/main/benchmark/text_attack_test.json) | 75: 15 families x 5 | All attack payloads | Original released test payloads, without task context |
| [Microsoft BIPIA code test attacks](https://github.com/microsoft/BIPIA/blob/main/benchmark/code_attack_test.json) | 50: 10 families x 5 | All attack payloads | Original released test payloads, without task context |

NotInject is MIT licensed, as declared in its dataset card. BIPIA attack files are covered by the repository MIT license; BIPIA's contextual benchmark contains separately licensed sources, which are not included here. Original license notices are retained. The BIPIA test files match PIGuard's BIPIA JSON files byte-for-byte. Those copies are retained only for source comparison.

NotInject includes 84 records in its `Multilingual` category and 255 in other categories. This is a category-based cohort, not automatic language identification. Report the cohorts separately if evaluating an English-only detector. The current DistilBERT source card tags English/German/Spanish, which does not establish support for every language in NotInject.

BIPIA payloads become indirect attacks by their placement in untrusted context. Some are ordinary requests when read as direct user instructions. A context-free score on these strings evaluates a payload detector; it does not demonstrate full RAG protection, attack success rate, answer quality, or knowledge-poisoning detection. Dataset origin is confounded with label in the combined export; report source-specific results rather than interpreting its aggregate accuracy as deployment accuracy.

## Reproducibility and contamination

`download_manifest.json` preserves source URLs, byte counts, and SHA-256 hashes of original downloaded assets. The NotInject card/metadata snapshot identifies dataset revision `847ae76cf8fea5ed325429e569ae8cfef022d2e0`.

The selected neural baseline is `fmops/distilbert-prompt-injection`, pinned to revision `c5da1fefd33c98c447b50dd806fe86aeb9e8c26c`, running locally with PyTorch on CPU from a `model.safetensors` checkpoint. Its source card declares `deepset/prompt-injections` as training data. The original model's end-of-training commit is dated 17 July 2023; the selected safetensors-upload commit is dated 28 July 2023. The checkpoint downloaded for the experiment has SHA-256 `2e4646e1f03c0ced285c67a52353b829ff6d76a1bf35ab5ee0beb19dd4447eef` (267,832,560 bytes), matching the Hugging Face LFS object at that pinned 2023 revision. This is direct temporal evidence for the final checkpoint, which predates NotInject's October 2024 release. It reduces the risk of deliberate training on the released benchmark; it does not establish novelty of every phrase or absence of underlying source overlap.

The archived `DistilBERT_ONNX_*` evidence concerns a separately investigated ONNX conversion of the same source model. The final experiment uses the original safetensors checkpoint with PyTorch; ONNX Runtime was not used to produce the reported final results. The ONNX object's November 2023 timestamp is historical supporting context, not the temporal proof for the final checkpoint.

`contamination_audit.json` records zero exact and zero normalized overlaps of NotInject (0/339) or BIPIA test payloads (0/125) with either the currently disclosed deepset training split (546 rows) or test split (116 rows). Normalization uses Unicode NFKC, case folding, and whitespace collapse. The current disclosed dataset is not proven identical to the historical training snapshot; paraphrase overlap, undisclosed training records, and base-model pretraining exposure remain unmeasured. This is an overlap audit, not proof of no contamination. The dataset card's top-level Apache-2.0 and nested CC-BY-4.0 declarations conflict; its text was read for the audit but is not redistributed here.

BIPIA's released train and test payload sets have zero normalized overlaps. Within the external combined export, there are zero normalized duplicate rows. Synthetic train/dev/test overlap must be audited separately by the experiment runner. Use BIPIA family-level summaries or uncertainty estimates because each family contains five related payloads.

`audit_contamination.py` reruns the network audit against the currently served deepset dataset. It never trains or tunes a model. Model cards, metadata, and commit/tree records are retained as provenance evidence. No model weights are stored in this directory.
