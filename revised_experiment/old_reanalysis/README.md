# Grouped linear reanalysis and reusable detector API

`output/RESULTS_中文.md` is the executed result summary. The old100 analysis is exploratory. It contains 20 new linear fits and reuses archived neural features. It contains no new neural inference, new blind test, or new answer generation.

From a complete project root, after placing these scripts under `revised_experiment/old_reanalysis/`:

```bash
python revised_experiment/old_reanalysis/reanalyse.py --project . --group-file revised_experiment/frozen_old100_split.json --output output/revised_experiment/old_reanalysis --save-models
python revised_experiment/old_reanalysis/validate_reanalysis.py --project . --output output/revised_experiment/old_reanalysis
python revised_experiment/old_reanalysis/summarize.py --output output/revised_experiment/old_reanalysis
```

The output directory must be new or deliberately selected; the source project is never mutated by these commands. `--save-models` writes this run's own trusted fitted sklearn objects for optional auditing. Loading external pickle/joblib artifacts is unnecessary for the default JSON verification.

The historical Q development split lives separately. Pass its exact `frozen_old100_split.json` to use the same 83 source-group definition; the exploratory five-fold allocation is derived from whole groups without labels or outcomes. The fold file in `output/protocol.json` records the actual allocation.

For separately locked new E1 data, import `detectors.py`:

```python
train = archived_training_rows(project_root, old_split['train_qids'])
states = freeze_detectors(train, new_clean_calibration_rows, new_test_rows)
test_predictions = apply_detectors(new_test_rows, states, point='1pct')
```

Every row has `qid`, `setting`, `text`, `label`, and `features` with `guard`, `rule`, `score_z`, `density`. New-pool features must be computed from its actual query and peer set. All calibration rows must be clean `setting='none'`. Source-article/near-duplicate independence must be checked by the caller in addition to the API's QID checks. `fit_summary(states)` gives JSON-safe provenance including the raw normal-calibration probabilities.

The hyperparameters are fixed: word TF-IDF 1–2, character TF-IDF 3–5, 25k+35k feature caps, min_df=2, sublinear TF, LogisticRegression C=1, balanced classes, liblinear solver. The sparse model sees passage text only. Context-head fits use the same training rows and weighting, and StandardScaler fits train only. Thresholds use the higher 99th/95th clean calibration quantile and strict `risk > threshold` blocking. The two operating points are distinct frozen analyses, and only the 1% point exports optional generation inputs.

Matched-single, echo and copy are combined in a mechanism summary. Their old evidence is retained. A new 25-question eight-cell matrix requires verified new document material and newly computed features; the code does not fabricate such features by reusing a changed pool's old density.

No failed or negative results are dropped. TF-IDF's advantage changes with the work point. Top5 malicious exposure is a retrieval-stage outcome, not semantic attack success. Identical observed binary outcomes give a degenerate paired bootstrap interval and do not establish equivalence or future robustness.
