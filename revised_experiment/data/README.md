# Source-disjoint SQuAD transfer data for Group9

This is a custom evidence-grounded transfer study from the official SQuAD v1.1 training release. It is not an official SQuAD leaderboard score, NQ replication, or proof of public-model pretraining independence.

The source was downloaded from the [Stanford release](https://rajpurkar.github.io/SQuAD-explorer/dataset/train-v1.1.json), SHA-256 `3527663986b8295af4f7fcdff1ba1ff3f72d07d61a20f487cb238a6ef92fd955`. The [official dataset page](https://rajpurkar.github.io/SQuAD-explorer/) distributes SQuAD under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). The retained records contain article source URLs, source paragraph indexes, and original answer offsets. Retain attribution when redistributing modified evidence.

## Frozen data

- `selection_protocol.json` specifies eligibility and seeded article/question selection, before new model outputs were inspected.
- `source_records_frozen.jsonl` contains 230 source questions, references, original offsets and gold evidence, without attack fields.
- `frozen_splits.json` assigns 30 articles to development, 100 to normal calibration and 100 to the custom test.
- `corpus.jsonl` contains 1,379 distinct paragraphs: 179 development, 600 calibration and 600 test. The source-role corpora are separately indexed. Normal retrieval never force-inserts gold.
- `dev_q_inputs.jsonl` provides the initial 30 gold/no-retrieval inputs and TF-IDF top-five normal retrieval context. The later Contriever pipeline must label its own rankings and cannot call these TF-IDF rankings Contriever results.
- `clean_pools_tfidf.jsonl` and `retrieval_tfidf_diagnostics.json` are an actually executed lightweight retrieval diagnostic. They are not the final Contriever candidate pools.

One short answer is selected per article, with all questions and paragraphs excluded if their normalized title, exact question or exact paragraph matches the old NQ material. These exact checks do not certify absence of every semantic duplicate or unknown pretraining overlap. Article titles are included in queries to make the source topic explicit. This restricts the study to article-scoped, mostly short entity-answer questions; do not generalize its accuracy to open-domain QA.

## Source quality before model-outcome analysis

Public annotations are not guaranteed to be semantically correct. `dev_source_quality_audit.json` and `test_source_quality_audit.json` review question/evidence/answer relationships without viewing new model outputs. The test review marks 85/100 source-supported and 15 ambiguous/conflicting/unsupported cases. All 100 source records remain. The 85-question strict subset is a separately labeled sensitivity analysis, not a replacement full test.

`dev_q_repairs.json` independently repairs three source-question ambiguities/conflicts and supplements aliases while keeping the same 30 source groups. Root preserves initial executions as history and reruns changed prompts. The resulting development metrics are explicitly custom repaired evidence QA, not official SQuAD scores.

`records.jsonl` and split-specific records retain the first, unsatisfactory token-count-matched targets for provenance. Those arbitrary targets are **not formal attack inputs**. `test_records_formal_v2.jsonl` now provides the final 100 test targets and counterfactuals. `records_formal_v2.jsonl` joins these to all 230 source records; development/calibration targets are explicitly unused. `target_freeze_v2.json` records proposals, independent editorial overrides, unit/wording repairs and hashes. All 100 target strings are absent from the original gold after accent/punctuation normalization, and original full answer strings do not remain in the counterfactual copy. The 15 source-invalid records remain tagged to withhold from strict semantic safety claims. Formal counterfactuals are local, controlled constructions, not a reproduction of CorruptRAG-AK and not an independently sourced attack bank. The CorruptRAG-AS-inspired template is an adaptation based on [the primary paper](https://arxiv.org/html/2504.03957v2), not original author code or a reproduced ASR result.

No models were run by this data-preparation stage. No model success/failure was used to select questions, repair source problems, choose targets, or define the source-valid sensitivity set.

Additional overlap audit: `near_duplicate_audit.json` compares selected new paragraphs with old clean paragraphs and across new roles using word-trigram TF-IDF cosine. No pair reached the fixed 0.8 audit threshold. This is a lexical screen, not a proof of semantic or pretraining independence.
