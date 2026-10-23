# Fresh NQ trust-filter experiment

This experiment replaces the earlier fictional pilot as the main empirical study.
It uses the exact 100 target questions and genuine Wikipedia-derived retrieval
candidates supplied with the reference project. Every neural embedding and guard
score is recomputed locally from pinned public checkpoints. Supplied generation
answers and defense flags are not used to fit these heads or choose thresholds.

## Reproduce

Python3.12, CPU PyTorch, four inference threads and batch12 are used. From the
project root:

```bash
python -m pip install -r improved_experiment/requirements.txt
python improved_experiment/download_models.py
python improved_experiment/run.py
python improved_experiment/analyse.py
python improved_experiment/public_guard.py
python improved_experiment/measure_latency.py
python improved_experiment/make_figures.py
python improved_experiment/verify_outputs.py
```

The compact `inputs/` directory preserves the exact 100-query subset and the
supplied attack strings. Its manifest records both original full-file hashes and
the bundled subset hashes. Raw source documents are not rewritten or replaced
with generated facts. Model downloads are separate from inference; after download
the model and tokenizer loaders use `local_files_only=True`. Hugging Face
telemetry is disabled. No model API, credentials, paid service or ONNX Runtime is
used. Contriever's official pinned checkpoint exists as a PyTorch state_dict;
loading explicitly uses `weights_only=True` with the recorded current CPU PyTorch.
The injection guard uses safetensors. Original model cards and licenses are in
`licenses/`; Contriever's upstream license is CC-BY-NC4.0.

The output directory is `output/improved_experiment/`. Checkpoints in `models/`
and numerical inference caches in `output/improved_experiment/cache/` are optional
large local intermediates. They are excluded from the deliverable package;
raw passage features, predictions, fitted fold heads and download manifests are
included for audit and cheap statistical reanalysis.

## Frozen design

The 100 questions are partitioned into five folds with seed12. For test fold f,
fold(f+1) is clean validation and the remaining three folds train the head:
60/20/20 questions. Every question's examples across families stay in its fold.
Stealth is excluded from all fitting and threshold selection. Question grouping
does not establish topic or strict-document holdout: two genuine source document
IDs occur across different question folds, and their affected questions are
explicitly listed by the overlap audit.

The candidate pool contains20 passages; filters reject candidates and backfill
up to5 contexts. All clean and attack scores are freshly computed with the same
Contriever checkpoint, masked mean pooling and unnormalised query/document dot
product. Clean ranking uses title+text; attacks have no source title. The audit
compares all2,000 genuine records against the supplied scores. This evaluates
merging attacks into a fixed pre-retrieved candidate pool; it does not rebuild or
search the complete NQ corpus index.

The features are:

- `guard`: frozen DeBERTa injection probability, class1=`INJECTION`.
- `rule`: fraction of10 fixed injection-cue regexes matched.
- `score_z`: `(score_i - mean(pool_scores))/(std(pool_scores)+1e-6)`.
- `density`: maximum cosine with any other untrusted candidate. Density vectors
  use the generator-visible text, L2-normalised masked-mean Contriever embeddings.

Heads: rule, guard, score-only, density-only, context(score+density),
content(guard+rule), fused(all4), no-guard(rule+score+density), and exploratory augmented fusion. The no-guard ablation was explicitly added before fresh metrics or generation to isolate the neural contribution; its timestamp and code hash are preserved in protocol_amendment.json. Learned heads
use training-only `StandardScaler` and logistic regression with C=1, balanced
classes and max_iter2000. Rule/guard retain their raw score. Each threshold is
the95th percentile of the400 clean no-attack validation candidates, with
`method='higher'`; rejection is strictly `risk > threshold`. The code checks that
empirical validation FPR≤5%. This is a development constraint, not a guarantee
that test or shifted benign FPR is≤5%.

`frozen_fold_models.joblib`, `coefficients.json` and `calibration.json` preserve
the exact heads, scaler parameters and unrounded thresholds. The heads are saved
before scoring additional attack-count/control conditions. `runtime.json`
fingerprints the actual code, protocol, input manifest, model manifests and heads.

## Transfer and counterfactual benign controls

All ordinary heads fit only the five-attack training conditions. They are then
applied unchanged to:

- **Matched one attack:** retain the highest-retrieval-score attack among the same
  five main attacks for that query/family. Selection uses retrieval score, never
  the detector decision or generator answer. This isolates attack cardinality
  while preserving a strong retrievable attack.
- **Supplied one attack:** use the uploaded independently sampled single attack.
  This includes a template-sampling shift and is not a pure count-only test.
- **Benign question echo:** prefix the literal question to the visible text of
  five genuine records. Their original title is preserved in the ranking string;
  their factual body and the other15 passages remain unchanged. Ranking and pool
  features are recomputed. Compare with the corresponding original clean pool.
- **Benign mirrors:** add exact copies of five genuine source records and retain
  top20. Every record is benign. This probes whether high density is being treated
  as intrinsic malice.

The controls are deliberately constructed stress tests. Their FPR estimates are
not estimates of how frequently such sources occur on the web. Report both FPR
on the modified/control records and on the entire resulting pool.

`aug_fused` is a separately declared exploratory extension: each fold appends
exactly300 negative rows (five modified echo records for each of60 TRAIN
questions). It excludes the15 unchanged rows, every validation/test question,
and all mirror/single/stealth examples. Calibration still uses only ordinary
clean validation pools. Its effect on unseen questions is compared with ordinary
fusion; no settings are selected using those test outcomes.

## Generation interface and metrics

`generation_contexts.jsonl` contains2,800 exact prompts:100questions×4settings
(clean, poison, ignore, stealth)×7gates(no filter, rule, guard, context, fused,
augmented fusion, corruption-removal reference). The final reference uses gold
corruption labels and is a privileged diagnostic, **not a formal upper bound**
on accuracy or a guarantee of zero target answers. The separate generator module
records a pinned free local causal instruct model and fixed greedy decoding.

Passage recall means the fraction of adversarial candidates actually reaching
the pool that are rejected. A crafted attack outside that pool is not scored as
a detector false negative; its retrieval exposure is reported separately.
Benign FPR is discarded genuine content. Passage metrics do not constitute
generator ASR or truth verification.

The original target-hit metric is a substring check and can fire on existing
clean errors or unrelated numbers. The independent generator analysis reports
normalised/reference matches and bounded target mentions alongside the source
metric, and compares attacked target outputs with each gate's paired clean
baseline. The historical NQ reference answers are not claims about current-world
facts in2026.

`analyse.py` resamples whole queries, pairing all candidates/methods within each
of10,000 bootstrap replicates (seed12; identical sorted-question draws across conditions). Intervals are conditional on this small question and
authored-family collection and the fixed fitted heads; they do not quantify
uncertainty across arbitrary new attack families or repeat the complete training
procedure. Exact duplicates and whitespace variants among the five attack
records are reported, rather than counting them as independent attacks.

## External benign prompts and cost

`public_guard.py` scores all339 official NotInject prompts with the fresh pinned
guard. The five frozen validation thresholds are applied separately; repeated
application does not create1,695 independent prompts. Multilingual category
items are separated from the other items. This is standalone over-defense, not
a fusion/RAG test without queries and peer context; no threshold is retuned.

Bulk inference metadata includes tokenisation+forward time, dynamic padding,
batch size, threads and input-cap counts. It is not per-query deployment latency.
The independent latency script measures fresh20-passage feature construction
without caches, separates guard and density-encoder work, excludes model loading
and records shared-host conditions. Selection from already computed flags is a
separate cheap operation. No GPU/CPU or source/current-run latency comparison is
made without naming the different environment.

## Scope

This is an exploratory evaluation of authored, question-prefixed corruption in a
fixed natural retrieval pool. The supplied outputs were inspected during design,
so the fresh run is not a blind confirmatory replication. New generator outcomes
and fresh test metrics never select hyperparameters or thresholds. A small
family bank, query echoes, repeated wrong-answer strings and attack redundancy
can create strong shortcuts. Success here does not demonstrate factual
verification, adaptive security, cross-domain robustness, tool-execution safety
or certified protection. Negative control/transfer findings remain part of the
result rather than being removed by further test-driven tuning.
