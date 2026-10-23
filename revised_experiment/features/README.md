# Fresh fixed-model features and declared-subcorpus retrieval

This is new neural feature execution when explicitly run. It does not retrain the encoder or guard and does not itself fit filters or generate attacks.

## Setup

Use a separate virtual environment and install `requirements.txt`. For the authoring session only, dependencies were installed privately in sibling `encoder_runtime/`; this folder is not required when the environment already has the pinned packages. Model weights are downloaded by `python download_models.py`; every byte count and SHA-256 is checked against `source_manifest.json`. Weights and dependency installations are excluded from the delivered source package.

## Shared subcorpus retrieval

```bash
python retrieve.py --corpus path/to/corpus.jsonl --queries path/to/records.jsonl --output output/retrieval --separate-corpus-by-split
```

`corpus.jsonl` rows contain `id`, `title`, `text`, `split`, and `source_group`. Query rows contain `qid`, `question`, and the same split/source metadata. The flag restricts each query to its declared split's complete small corpus. Encoder computation is shared, but documents are not mixed across train/development/calibration/test subcorpora. This is exact dot-product retrieval over the declared subcorpus, never a full NQ/Wikipedia retrieval claim. No query performance is used to pick questions.

## Pool features

```bash
python run_features.py --input path/to/pools.jsonl --output output/features --stage all
```

Each pool row has `qid`, `question`, `setting`, optional split/source fields and `pool`, a list of `id`, `title`, `text`, optional `label`/`family`. The module recomputes title+text query relevance and stably retains top20. Density uses text-only mean-pooled Contriever vectors and max cosine against other untrusted peers. Guard uses text only. Rules and z standardization exactly match the archived implementation.

For memory-aware scheduling, use stages `prepare`, `contriever`, `guard`, `assemble` in that order. `prepare` and `assemble` perform no model inference. Use `--reuse-feature-cache output/retrieval` to reuse previously computed exact model/text vectors, infer only new attack/control texts, and preserve the source array hash and reused/new counts. Source metadata and newly inferred timings stay distinct. Cache configuration is immutable and includes exact texts, model revision, dependency versions, batch size, threads and token cap; mismatches require a new output directory.

No more than512 encoder tokens per text are represented. Original token lengths and truncation counts are recorded. Labels are carried for later evaluation but are not used by retrieval, guard or feature construction. `feature_equivalence.json` is a zero-difference algebra regression against the archived author's feature function, not proof of new neural execution. Only completed inference metadata and complete output manifests establish which new features ran.

## Delivered evidence and offline checks

The revised project entry point is `python revised_experiment/run.py --download-models`, which writes a new run directory and keeps delivered results intact. The initial fitted heads reuse the declared old70 training feature records; this module reruns only the new corpus/attack/control features.

The delivered full-corpus vectors are in `output/revised_experiment/retrieval/cache/`. Canonical525-case outputs and the strict direct-rank proof are in `output/revised_experiment/fresh_features/`. The numerical-revision folder retains the initial float32 matrix/tie failure and quantitative impact; no test answer output drove that correction.

`audit_guard_lengths.py` is tokenizer-only and never calls a neural classifier. It reports attempted-versus-retrieved explicit-injection command visibility, plus by-setting/source-supported token counts. It cannot infer semantic guard understanding from token visibility.
