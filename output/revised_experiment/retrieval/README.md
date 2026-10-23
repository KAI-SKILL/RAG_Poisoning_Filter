# Frozen small-corpus retrieval and feature cache

The Contriever and guard arrays are actual completed CPU executions with pinned original project checkpoints. Original neural metadata and the exact helper source used during inference are preserved. The later canonical float64 ranking correction reused the same vectors and did not rerun model inference.

`clean_retrieval.jsonl` is a source-safe schema export of canonical normal top20 results. It omits the deprecatedv1 attack-target fields. The frozen case builder uses v2 target records separately. Source subcorpora contain179development,600calibration and600test passages. No query searches another split's corpus.

`cache/` includes exact text lists, complete arrays and progress/configuration records for offline numerical checks. The corpus encoder cache holds2988 unique representations; the guard cache holds1604 texts. Formal525-pool feature assembly reused these and encoded only450 additional title/text representations. Full model weights and Python dependency installations are not part of this archive.

The stored inference timings describe batched shared-CPU feature work, not end-to-end RAG latency. Current canonical pool/rank evidence is in sibling`fresh_features/`, including the retained failed float32 order check and the pre-test correction's impact report.
