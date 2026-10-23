# Reproducible passage-filter experiment

This folder contains an **executed CPU neural-detector pilot**. All local visitor
records are fictional. This is a controlled passage-filter experiment; detector
recall and evidence retention must not be reported as generator attack success,
factual verification, or real-world RAG accuracy. Separate downstream generation
results, when present in `../generation/`, have their own protocol and limitations.

## Run

Python 3.12 was used. From the project root:

```bash
python -m pip install -r experiment/requirements.txt
python experiment/download_model.py
python experiment/benchmark.py --generate
python experiment/benchmark.py --run
python experiment/export_generation.py
python experiment/evaluate_public.py
python experiment/diagnostics.py
python experiment/audit_implementation.py
```

The 268 MB safetensors weights are intentionally downloaded separately. The downloader
pins an immutable model revision and verifies SHA-256 hashes. It sends no local
data to a model API. Inference uses local PyTorch CPU, with Hugging Face telemetry disabled and
model/tokenizer loading restricted to local files. Model downloads are a separate
step. Intermediate model files can be deleted and downloaded again.

Results are written to `output/experiment/` relative to the project root:

- `results.json`: frozen settings, thresholds, coefficients, metrics, latency,
  query-cluster confidence intervals and family-specific recall.
- `metrics.csv`: compact test results.
- `predictions.jsonl`: every passage, label, risk score and decision.
- `generation_contexts.jsonl`: clean/attacked contexts under six frozen gates.
- `public_results.json`, `public_predictions.jsonl`: external stress test.
- `diagnostics.json`: explicitly post-hoc fixed-0.5 reference and neural-constant
  ablation; primary settings are unchanged.
- `implementation_audit.json`: loading keys, checkpoint/tokenizer hashes,
  evaluation mode, dtype and natural-language sanity probes.
- `joint_detection.png` and `threat_transfer.png`: measured result figures.

## Fixed protocol

Seed: 764. The code allocates 24 topics before creating any text: 12 training,
4 development and 8 held out. Each group has one malicious passage and five
benign passages: two answer-bearing records, a procedural manual, a quotation of
an attack, and a legitimate minority note. Candidate order is shuffled.

| Suite | Query groups | Passages | Purpose |
|---|---:|---:|---|
| Train | 144 | 864 | Fit lexical detector and two-feature fusion |
| Development | 48 | 288 | Select operating thresholds |
| Topic shift | 96 | 576 | New topics, four familiar attack families |
| Joint shift | 96 | 576 | New topics and four withheld attack families |
| Aligned factual poisoning | 48 | 288 | Different answer value, no instruction |

Training/development/test topics, questions and exact passage strings are
disjoint. The three test suites reuse the eight held-out topics and some queries
and benign passages, so they are reported separately and never pooled as
independent observations. Joint-shift attack families do not occur in training
or development. The familiar-family suite does reuse authored templates; it is
**not** an unseen-template evaluation. Every suite is generated from a small,
hand-authored template bank, not naturally retrieved web documents.

The two primary features are:

1. Frozen pretrained neural risk from
   `fmops/distilbert-prompt-injection`, revision
   `c5da1fefd33c98c447b50dd806fe86aeb9e8c26c`. This is a genuine six-layer
   DistilBERT classifier; it is not fine-tuned on our data. CPU PyTorch inference
   uses four threads, batch 16, dynamic padding and a 256-token cap. The exported
   configuration omits `id2label`; the binary label convention and fixed
   non-evaluation probes establish class 1 as injection. See
   `label_mapping_sanity.json`. Its original model card lists
   `deepset/prompt-injections` as training data.
2. A cheap **lexical retrieval inconsistency proxy**, not a semantic encoder:
   `r_i = 1 - 0.5 cos(q,p_i) - 0.5 mean_{j!=i} cos(p_i,p_j)`.
   Vectors use fixed nonnegative hashing of word unigrams and bigrams into
   2^18 dimensions with L2 normalization. All other candidate passages are peers;
   neither their gold labels nor an oracle trusted set enters the score.

Fusion is `sigmoid(b + w1*neural_risk + w2*retrieval_proxy)`. Logistic regression
uses `C=1`, balanced classes and training rows only. This is a learned combination
of existing signals; neither the detector nor the feature family is claimed new.
Baselines are a fixed keyword rule, a training-only TF-IDF logistic classifier,
retrieval alone, and the frozen neural detector alone. No test-stage feature
selection, hyperparameter search, model selection or threshold tuning occurs.

For every learned score, the development threshold maximizes attack recall
subject to at most 5% benign false positives; ties prefer precision and then a
higher threshold. The keyword rule uses a fixed 0.5 cutoff, and therefore is
not guaranteed to meet this budget. The budget is an empirical development
constraint, not a certified test false-positive guarantee. Scores are uncalibrated
risk scores, not calibrated confidence estimates.

## Evaluation and interpretation

Attack recall is the fraction of malicious **passages blocked**. Attack retention
is one minus recall; it is exposure remaining after the gate, not downstream
attack success. Benign FPR is the fraction of benign passages discarded. The
report also separates FPR for manuals, quoted instructions, minority evidence,
and answer-bearing documents. At-least-one-gold-evidence coverage only checks
whether one of the two labeled benign answer records survives; it does not check
whether a generator will use it correctly.

AUROC and AUPRC use the continuous score. AUPRC and precision depend on the
artificial 1/6 attack prevalence. The 95% percentile intervals use 1,000 paired
bootstrap replicates of whole query groups, preserving all six candidates and
all methods together. These intervals are conditional on this authored topic
and template bank; they do not quantify uncertainty over arbitrary future
attack families. We also report paired combined-minus-neural recall intervals.

The timing definition includes tokenizer work and the PyTorch forward pass, excludes warm-up
and model loading, and reports batch size, threads and token lengths. This is
local detector cost only. It must not be interpreted as end-to-end RAG latency
or compared directly with published GPU measurements.

## Downstream-generation export

`export_generation.py` exports accept-all, keyword, lexical, retrieval, neural and
combined gates for both conditions. Clean conditions remove the one malicious
passage, then recompute peer consistency and fusion against the five remaining
passages using the same frozen weights and thresholds. Text-only detector scores
do not change. Candidate order is preserved.

Benign attack quotations **remain in clean contexts**. For instruction-injection
groups these quotations reproduce the attack's target phrase. Therefore a
generator's target-phrase occurrence on an attacked context must be interpreted
alongside the corresponding clean occurrence. The quotation challenge is
intentional, not proof that an inserted malicious document caused every target
response. Empty-context counts are exported explicitly.

## Public external stress test

`public_data/` preserves the official MIT-licensed NotInject and BIPIA attack
assets, their source revisions, checksums, loader and provenance notes. Evaluation
uses all 339 NotInject benign prompts and 125 unique BIPIA held-out attack
payloads (75 text, 50 code), without fitting or retuning thresholds. Downloaded
copies of identical BIPIA files are not counted twice. NotInject contains 84
items in its Multilingual category; that category is a proxy, not detected
language, and is reported separately from the other 255 items.

These are standalone prompts/payloads. Some BIPIA strings become malicious only
when embedded in an external task, so this test measures detector response to
the released payloads, not full contextual label validity or RAG ASR. Retrieval
and fusion are not evaluated without actual queries and peer context. Dataset
mixtures are not used to claim a source-independent aggregate accuracy. Temporal
and training-overlap caveats are in the data provenance notes.

## Limits

The pilot does not establish robustness to adaptive attacks, multi-document
poisoning, new languages, natural web sources, or real deployment distributions.
The lexical proxy measures alignment, not truth or contradiction. Aligned factual
poisoning is deliberately retained as a failure probe. Pretraining overlap is
not fully observable. Synthetic quotation wrappers and repeated writing styles
can provide shortcuts; high within-bank scores do not demonstrate deep semantic
understanding. The experiment supports a narrowly scoped empirical comparison
and identifies which claims still require a larger external RAG evaluation.

The actual frozen neural scores saturate near one on the authored visitor-guide
passages. Independent loading/hash/evaluation-mode checks pass; ordinary factual
sentences can receive low scores while similar visitor-guide wrappers receive
high scores. This suggests distribution or writing-style sensitivity, and limits
what the synthetic result establishes. The fusion uses unstandardized scores;
the neural feature's training standard deviation is much smaller than the
retrieval feature's. Regularization and score collapse may therefore suppress
its contribution. A post-hoc ablation holding the neural score at its training
mean changes no held-out decisions. This is evidence about this implementation,
not a rejection of every possible hybrid detector.
