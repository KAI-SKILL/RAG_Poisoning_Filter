# Final independent design and portability review

Scope: the frozen source/target audits, protocol, case preparation, detector fitting/calibration, detection summaries, retrieval/rank manifests and source code. No partial or completed new-generation responses were inspected. No frozen question, reference, target, split, selected case, learned parameter or historical manifest was changed.

## Design checks passed

- The delivered100-question source audit is byte-identical to the independently prepared pre-output copy. Its85supported IDs match both the case-freeze list and target-v2 eligibility. The target freeze also matches the earlier prepared copy.
- Recomputing `SHA256('Group9-E2-fixed25-v1:' + qid)` ordering over the85supported IDs reproduces all25E2 IDs and their order exactly. This is not selection by a method's success.
- Source-role counts are30/100/100 questions and179/600/600 passages. Article/source-group intersections between development, calibration and test are empty. The retrieval manifest explicitly enables split-specific corpora. Encoding all documents with the same frozen encoder does not train on test labels.
- All525pure-insertion cases passed direct declared-subcorpus versus top20-union-insertion ranking checks, including actual feature-pipeline selected IDs. Normal texts/titles remain unchanged. This supports the declared target-specific small-corpus delivery claim; it does not support fullWikipedia, jointly persistent attacks, approximate-index or web acquisition claims.
- Detector fitting uses9,800old70train rows, excluding stealth. Calibration uses2,000normal candidates from100new calibration questions. `freeze_detectors` receives test rows only for disjoint-ID assertions and calls fitting with train/calibration only. No gold/support/attack labels are input features. The generated prompt contains question and selected title/text only.
- The main working point is calibrated at1%, with strict-greater quantile thresholds and ties documented. Observed calibration FPRs are0.95% for ctx/no_guard/fused and0.6% for TF-IDF. They are budgets on calibration candidates, not guarantees of matching task utility or test FPR.

## Interpretation limits that remain necessary

No frozen-data correction or experimental rerun is required by this review. The report's current design/discussion already disclose the following material limits and should retain them in final figures and speaking text:

1. The85mask means source-supported under a single source-text review, not85independently verified universally true questions with globally false alternatives. Broad or historical questions can admit other facts. All100annotation-proxy records remain, with the85subset separately labelled.
2. Targets are plausible same-type, source-relative controlled alternatives, constructed independently of test outcomes. They are not a strong adaptive attack bank, an original-author CorruptRAG-AK reproduction, or proof of global wrongness. Known raw-target problems were fixed before formal use, and producer history is retained.
3. Single counterfactuals are near-copies of legitimate gold. Every main source-supported counterfactual is blocked by the context heads, while legitimate copies/echoes are heavily rejected too. This tests a repetition/context cue and its utility cost; it does not establish truth verification. E2changes count, peer set, pool statistics and rank competition together.
4. Detection-summary benign FPR uses all normal candidates in that condition. For example,150/500=30% under five-copy controls is a whole-pool FPR, not the rejection fraction of only the125inserted copies. If a figure labels inserted-copy rejection, derive and report that distinct denominator explicitly. Match clean comparison to the same fixed25questions.
5. TF-IDF and standalone guard are component baselines, not equivalent reproductions of complete external defenses. The word/character baseline is trained on the allowed old material, and pure factual corruption is distinct from instruction detection.
6. Exact/alias matching, target mention, target exactness and semantic endorsement remain different outcomes. Type/format aliases do not make a substring an independent semantic judgement. No adaptive robustness, reliable current-world factual accuracy or Windows16GB performance claim follows.

## Portability repairs completed without changing historic bytes

The primary `revised_experiment/run.py` already resolves project paths. Three historical helper paths referred to the original preparation layout. The feature regression helper has a valid project-relative fallback, so it was left unchanged.

Added, without modifying original scripts or the frozen data manifest:

- `data/portable_build_frozen_squad.py`: explicit full-source/old-input/new-output CLI, project-relative old-input default, source hash check, UTF-8/LF output, frozen-data and nonempty-output protection. AST and `--help` checked; a new full-source rebuild was not run.
- `data/portable_finalize_targets_v2.py`: explicit records/source-audit/proposals/new-output CLI, frozen input hashes, UTF-8/LF, same output protection.
- `data/source_records/target_proposals.json`: exact proposal bytes with SHA256 `47d201a2bf55c04846849cf1db6f8d0573134be523a9a52020ed7da175a5c337`, matching the existing target freeze.
- `data/PORTABLE_REBUILD.md`: original helpers are historic producers; the main experiment does not require source reconstruction; reviews are not automatically recreated as new independent judgement.

The portable finalizer was run in a temporary directory from an unrelated working directory. Its230-record v2file,100-record test v2file and target-freeze JSON all matched the delivered files byte for byte. A repeated nonempty destination and an attempted destination inside frozen data were rejected. All original data-manifest entries still match their recorded hashes.
