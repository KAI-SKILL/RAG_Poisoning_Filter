# Fresh natural-data findings

The fresh experiment reproduces the supplied retrieval mechanism but exposes limits in what high passage-detection scores establish. The current frozen four-signal fusion is useful against these authored, highly retrieved attacks; it is not an intrinsic truth or trust detector.

## Data and execution

One hundred targeted NQ questions, 20 candidates per pool and five selected contexts. All 2,000 supplied clean scores match a fresh pinned Contriever calculation: mean absolute difference 2.22e-7, maximum 1.07e-6. Both clean and attack scores are freshly recomputed. Frozen DeBERTa guard and Contriever encodings run locally in CPU PyTorch. Five question folds use 60 train / 20 clean-validation / 20 test questions, with stealth excluded from fitting and calibration. Query grouping is not strict document/topic holdout: two genuine document IDs cross query folds.

The final protocol has nine passage heads and seven generation gates. All 432,000 saved risk/decision pairs and all 2,800 exported prompts pass offline reconstruction. Independent audit additionally refits the 35 learned heads and checks all 45 quantile thresholds.

## Passage exposure before generation

Percentage of the 100 queries admitting at least one adversarial passage in the selected top five:

| Gate | Factual poison | Ignore injection | Held-out stealth |
|---|---:|---:|---:|
| No filter | 100 | 94 | 96 |
| Rules | 100 | 0 | 96 |
| Guard | 99 | 54 | 96 |
| Context | 17 | 0 | 8 |
| Fusion | 21 | 0 | 12 |
| Augmented fusion | 19 | 0 | 12 |
| Corruption removal reference | 0 | 0 | 0 |

These values are exposure, not generator ASR. The privileged reference uses gold corruption labels and is not a formal upper bound on answer accuracy.

Main fusion blocks 467/500 factual-poison candidates (93.4%), 487/487 ignore candidates (100%), and 449/492 stealth candidates (91.26%). Its ordinary clean FPR is 95/2,000 (4.75%). Context-only recall is 94.6%, 98.15%, and 93.50%, respectively, so fusion does not dominate context on every threat/metric.

## Incremental guard value

The pre-result no-guard ablation retains rules, score z and density. Its flags are exactly identical to fusion on all 8,000 candidate instances of the four primary generation settings (clean, poison, ignore, stealth), every matched single-attack pool and both benign controls. Across all 16,000 main instances there are three differences, all favouring no-guard: one extra attack rejected and two fewer benign false positives. This establishes no measured guard decision benefit at these operating points; it does not prove the neural score contains no information or that every neural guard is unnecessary.

## Frozen five-to-one transfer

The one retained attack is the highest retrieval-score passage from the same five, selected without detector or generator outputs. No head or threshold is refitted. Fusion passage recall falls from 93.4% to 90% for factual poison and from 91.26% to 73% for stealth. Augmented fusion falls further to 81% and 59%, respectively.

Query admission is threat-dependent: fusion factual-poison admission changes 21%→10% because there are fewer attack opportunities, while stealth changes 12%→23%. Context-only stealth admission changes 8%→66%. Therefore the result is not a universal claim that fewer attacks are always more successful; it identifies a marked cardinality dependence in the density-based defense.

## Benign controls and augmentation

Question-echo controls preserve the source title in ranking and the original factual body, adding only the literal question to five genuine records. Fusion falsely rejects 157/500 modified records (31.4%); augmented fusion rejects 146/500 (29.2%). The paired whole-query difference is -2.2 percentage points, 95% conditional bootstrap CI [-3.8,-0.8]. On exact benign mirrors, fusion rejects 498/500 copied records (99.6%) and augmented fusion 500/500 (100%).

Augmentation was declared before fresh results: each fold adds only the five modified negatives for each of its 60 training questions (300 extra rows), with the same clean-only calibration policy. Its small echo benefit has a transfer cost: matched-single factual-poison recall changes 90%→81%, difference CI [-15,-4] points; stealth 73%→59%, CI [-21,-8]. It is a targeted trade-off rather than a general robustness improvement.

## External benign prompts and computation

Across all 339 unique NotInject prompts, the fresh guard's mean FPR under its five frozen Wikipedia-validation thresholds is 50.56% (fold range 49.26–51.92%). The Multilingual-category subset is 79.29%, other categories 41.10%; these are dataset categories, not detected languages. A fixed 0.5 reference rejects 43.36%. No threshold is tuned on NotInject, and no fusion/RAG claim is made for standalone prompts without queries/peers.

Ten deterministic cold 20-passage pools, without feature caches, take a median 10.794s for feature construction (guard 6.071s; density encoder+cosine 4.331s) under a shared CPU host with four inference threads. p95 total is 13.180s. Loading/warm-up are excluded; concurrent workload and the technical serialization retry are recorded. This is not demonstrated low-latency CPU deployment. Reusing index/feature caches may reduce cost, but such an optimization is not measured here.

## Statistical and generalisation limits

Intervals use 10,000 identical seed12 whole-question bootstrap draws across methods and conditions, conditional on fixed fitted heads and this authored bank. Attack templates, question echoes, repeated target strings and exact duplicates provide shortcuts. One withheld family does not establish adaptive or general cross-domain security. The natural-data run is exploratory because supplied outputs were inspected during design, although no fresh test/generator metric selects a model, hyperparameter or threshold. Fresh generator outcomes are reported independently in improved_generation/output/ and must not be inferred from passage exposure.
