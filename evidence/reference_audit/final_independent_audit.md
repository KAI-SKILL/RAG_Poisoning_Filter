# Final independent audit of the fresh NQ experiment

The fresh detector and generator records pass independent reconstruction. This conclusion concerns the retained run artifacts; the uploaded HF-tagged logs remain separately reanalysed evidence with unverified generator provenance.

| Check | Independently verified scope |
|---|---|
| Feature-to-decision calculations | 48,000 candidate rows × 9 methods = 432,000 risk decisions |
| Fitting and calibration | 35 learned heads and 45 frozen validation thresholds; train-only scaling and augmentation |
| Retrieval provenance | 2,000 original clean scores plus 3,429 main and 687 supplied-single attack scores agree with fresh pinned Contriever vectors within floating-point error |
| Benign controls | Title-preserving echo ranking and 500 modified/copied records per control; actual full pool has 2,000 records |
| Frozen transfer | Same-five strongest-attack selection for 700 question/family cases; no single-attack refitting |
| Context reconstruction | All 2,800 selected passage lists and generator prompts |
| Generator execution | 2,800 unique question/policy/setting records, 668 distinct rendered chats, 167 fixed batches; model, code, input, cache and batch hashes |
| Raw answer scoring | Every exact, bounded mention, abstention and both-label flag under the original frozen scorer |
| Measurement correction | Exactly 23 rows of test397, only reference/both flags; all original responses and inference fingerprints preserved; corrected outputs separately retained |
| Corrected paired statistics | PRIMARY3 and secondary18 exact McNemar tests, separate Holm families, all reference/target bootstrap intervals; 28 cost records |
| Output caps | No input truncation; 4 unique capped answers affect 37 reused condition records; 664 unique answers end with EOS |

The apostrophe correction independently passes 22 regression examples, including Ocean's/Ocean’s, isolated quoted S, S-shaped, S's, Smith's, O'Brien, no/know, terminal decimal punctuation, and numeric substring boundaries. Original frozen files match the hashes recorded by the correction. Corrected raw SHA256 is `f513487ffe5edc983287cacd31d512978ea1a4c38699091e8ad98799d81d9baa`.

## Scientific interpretation

Unfiltered target mentions under poison/ignore/stealth are 93/93/95 of 100; context-only yields 12/2/9; fusion yields 17/2/13, and augmented fusion also yields 17/2/13. The three primary fusion-versus-context Holm-adjusted values are .375/1/.375. This supports lower target-string output versus unfiltered generation, without demonstrating fusion superiority over context-only.

The corrected unfiltered clean reference-mention count is 24/100 and whole-answer exact count is 13/100. These canonical-string measures are not semantic factual accuracy. Two or three clean target mentions occur depending on policy, so new-target denominators are 98 or 97. Neither raw target mentions nor new-target counts alone establish attack causation.

Guard omission leaves all 8,000 passage decisions in the four primary generation settings unchanged. It does **not** leave all 16,000 main-suite decisions unchanged: three decisions in fake_comp/combine/escape differ. The all-family differences favour omission in that limited comparison. Five supplied-single decisions also differ. Fusion-versus-context therefore combines rule and neural changes and cannot by itself attribute a benefit to the neural guard.

The benign controls and frozen transfer reveal the main trade-off: fusion's 31.4% echo and 99.6% copied-document false-positive rates accompany stronger single-attack recall than context-only. Training echo augmentation lowers echo error by 2.2 percentage points while sacrificing nine points of matched-single poison recall and fourteen of stealth recall. There is no across-condition improvement claim.

Two full-prompt examples were cross-checked against final raw outputs: test192 poison/context mentions “yes” while retaining the poison's alien-planet content; test1 clean/poison fusion answers 24/132 against reference 23 although neither selected context contains an attack. They show why string matches and changed target counts require interpretation.

## Reproduction of this audit

```bash
python improvement_audit/audit_fresh_results.py
python improvement_audit/audit_fresh_statistics.py
python improvement_audit/verify_fresh_retrieval_anchor.py
python improvement_audit/audit_fresh_generation.py
python improvement_audit/audit_fresh_generation_statistics.py
python improvement_audit/audit_apostrophe_correction.py improved_generation/output/corrected
python improvement_audit/audit_fresh_generation_statistics.py improved_generation/output/corrected
```

These scripts perform no new generator calls and execute no code from the uploaded reference archive. Model files are read for integrity verification; only the local tokenizer is used in chat-template validation.

Final student contribution confirmation, personal understanding, timed rehearsal, actual MP4 recording and Canvas submission remain human tasks. Final report page/reference/layout checks must refer to the newly built PDF, not the earlier pilot version.
