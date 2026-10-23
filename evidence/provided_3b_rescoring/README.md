# Supplied historical 3B rescoring and recovered raw answers

The later Drive attachment supplies the original **4,800 historical NQ response records** that were absent from the earlier three-file merge. They cover 100 previously inspected questions, six policies and eight conditions. This archive remains supporting evidence, separate from the current pinned article-disjoint SQuAD evaluation with 2,175 requested rows.

## One canonical copy

| Content | Retained location |
|---|---|
| 48 logical historical sources stored in 33 unique physical JSONL files | `raw/` |
| All 48 R/T summary cells | `../reference_audit/provided_corrected_metrics.csv`, bounded columns |
| All 120 paired tests under three scoring rules | `../reference_audit/provided_paired_statistics.csv` |
| Historical three-hypothesis Holm family | `primary_family.csv` |
| 43 substring-to-bounded label changes | `recovered_changed_rows.csv` |
| One same-prompt/different-answer group, preserved | `recovered_prompt_conflicts.json` |
| Recovery/source hashes and omitted bounded-copy hashes | `recovered_source_provenance.json` |
| Earlier attachment hashes and two advanced historical source scripts | `provenance.json`, `source_scripts/` |
| Minimal historical generation declarations | `runtime_declarations/` |

The 48 original logical sources share 33 distinct whole-file contents. `recovered_source_provenance.json` explicitly maps each defense/setting to its retained physical file and original byte hash; no response is edited. The 48 bounded JSONL derivatives repeat the full original prompts/answers and are omitted. The verifier reconstructs their 38,400 flags and checks the semantic digest captured from the supplied files. Existing summary CSVs are reused instead of duplicated. Downloaded third-party code, trial copies and historical runtime artifacts are not promoted into a second current implementation.

## Verified recovery

Independent checks reproduce all 4,800 raw substring labels, all 48 corrected result rows, all 120 directional paired comparisons and their six broader Holm families. The supplied 43 changed rows match exactly. Historical tokenised mentions and the trusted apostrophe-aware mention scorer agree on these 4,800 responses; this does not prove the algorithms equivalent on arbitrary inputs, nor turn mention into semantic endorsement. Whole-answer exact and new-study alias matching retain their distinct definitions.

The archive has 1,207 distinct complete prompt strings. One prompt for `test110` occurs 31 times with two different saved answers: thirty `I don't know` answers and one fusion/clean answer saying `There are four seasons from dusk till dawn.` Both are retained. Deduplicating by prompt and overwriting answers would change the source evidence. The number of unique prompt strings is not a verified count of actual historical executions.

On historical target mention, fusion/context give 14/10 for poison and 12/8 for stealth, each out of 100. Both have four fusion-only and zero context-only hits, exact McNemar p=0.125. Their named three-test historical Holm family gives 0.375/1/0.375 for poison/ignore/stealth. The existing broader correction family has different adjusted values and must remain labelled separately. Neither supports fusion superiority or equivalence.

## Model provenance remains limited

The source backend defaults to `Qwen/Qwen2.5-3B-Instruct`, greedy decoding and 64 new tokens. The workflow describes a T4 GPU. However, its 19 code cells have no execution counts or saved outputs, and the archive lacks the loaded checkpoint revision, weight/tokenizer hashes and immutable runtime manifest. Raw answers are now verifiable data; the declared3B identity and T4 execution are still not independently attested. No model generation took place during recovery.

## Reproduce offline

From the project root, standard-library Python is sufficient:

```bash
python -B -S evidence/provided_3b_rescoring/verify_summaries.py
```

This also runs `verify_raw.py`, checks raw file hashes and canonical targets, rebuilds all score flags, validates both canonical result tables, and regenerates the compact change/conflict reports. `raw_validation.json` and `validation.json` describe the current scope. The default root `run_project.py --verify-only` includes this check.

To additionally compare the earlier source rescoring attachment:

```bash
python -B -S evidence/provided_3b_rescoring/verify_summaries.py --source-zip /path/to/3B_rescoring.zip
```

`source_attachment_validation.json` is the preserved **earlier summary-only receipt**, from before the Drive recovery. Its `raw_4800_answers_present=false` described that earlier input scope, not this current archive. Current verification uses `validation.json` and `raw_validation.json`.

## Historical scripts and attribution

The two original source scripts remain byte-preserved for attribution. The source scorer has documented boundary limitations: zero-equivalence failure and loss of sign/percent distinctions. The statistics script can collapse duplicate qids, intersect unequal sets and round tiny p-values. Current verification checks exact 100 qid sets and uses full-precision arithmetic independently; no impact of those edge cases on the recovered response labels is invented.

The formal new-study evaluator remains `../../revised_experiment/evaluate_new.py`. Its frozen scores and primary families are unchanged. The source README attributes the older rescoring contribution to Project contributor; it does not establish personal allocations for the later study. Data/source attribution remains in `../../DATA_ATTRIBUTION.md` and the existing upstream license records. The retained notebook/driver are historical declarations, not current runnable entry points.
