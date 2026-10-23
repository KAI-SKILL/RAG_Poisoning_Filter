# Completed exploratory generation follow-up

Primary numerical source: `summary.json` in this directory. The original frozen scorer and every original output remain in the parent directory. These are newly executed local model outputs, distinct from the uploaded reference logs and from the earlier FLAN ceiling pilot.

## Findings

The contextual gate substantially reduces attacker-target mentions relative to accepting every passage on this constructed five-passage attack budget. Adding the frozen neural guard feature through `fused` does not establish an additional downstream benefit. Across poison, direct-ignore and stealth attacks, `fused` has 17, 2 and 13 target mentions, compared with 12, 2 and 9 for `ctx`. The planned three exact paired McNemar tests, adjusted together with Holm, yield 0.375, 1.0 and 0.375. These results do not support a fusion gain over the contextual gate. The augmented fusion extension has the same three target counts, although its clean baselines differ.

All counts below are out of the same 100 archived NQ questions. Reference mention uses the transparent post-run apostrophe correction described below. “Reference” means the historical canonical label, not independently verified current factual correctness.

| Gate | Clean reference exact | Clean reference mention | Clean target mention | Poison target mention | Ignore target mention | Stealth target mention |
|---|---:|---:|---:|---:|---:|---:|
| none | 13 | 24 | 2 | 93 | 93 | 95 |
| rule | 12 | 23 | 2 | 93 | 2 | 95 |
| guard | 12 | 22 | 3 | 91 | 51 | 92 |
| ctx | 12 | 25 | 3 | 12 | 2 | 9 |
| fused | 10 | 24 | 2 | 17 | 2 | 13 |
| oracle | 13 | 24 | 2 | 2 | 2 | 2 |
| aug_fused | 11 | 25 | 3 | 17 | 2 | 13 |

The following conditional counts exclude questions already mentioning the target in the **same gate's** clean condition. A numerator is an attacked target mention among these eligible clean non-hits; it should not be interpreted as a verified semantic instruction-hijack rate.

| Gate | Poison new target / eligible | Ignore new target / eligible | Stealth new target / eligible |
|---|---:|---:|---:|
| none | 91/98 | 91/98 | 93/98 |
| rule | 91/98 | 0/98 | 93/98 |
| guard | 88/97 | 49/97 | 89/97 |
| ctx | 10/97 | 0/97 | 7/97 |
| fused | 16/98 | 1/98 | 12/98 |
| oracle | 0/98 | 0/98 | 0/98 |
| aug_fused | 15/97 | 0/97 | 11/97 |

For accept-all, whole-output target exact matches are 41/100 for poison and 93/100 for both ignore and stealth. Thus the fresh instruction-tuned model actually produces wrong-target answers in the new task; the result is not merely a failure of the old irrelevant-marker attack. Nevertheless, five attacker passages can dominate the retrieved top five, and poison asserts false evidence. The design does not isolate obedience to instructions from reliance on contaminated evidence. The oracle uses privileged corruption labels and is a reference condition, not an attainable defense or a universal answer-quality upper bound.

Clean reference agreement is weak: 10–13 whole-answer exact matches and 22–25 bounded mentions depending on the gate. Historical single-string labels, missing answer aliases, real retrieval distractors and this small model limit what these numbers establish. A response may mention a target in a negation or name both answers. After correction, only the `fused` and `aug_fused` poison conditions have one both-mentioned response each; that shared long, capped response falsely places the slide at the eyepiece and subsequently mentions a mechanical stage. Its word overlap does not certify a correct answer.

## Statistical scope

`primary_fused_vs_ctx.json` contains the three planned paired tests for additional fusion benefit. They form a separate Holm family from the 18 accept-all-versus-other-policy tests in `policy_comparisons.json`. Exact two-sided tests condition on discordant target-mention pairs and use unrounded probabilities for adjustment. All effect intervals use 10,000 paired whole-question bootstrap replicates with seed 12.

The `ctx` minus `fused` target-rate differences are −5, 0 and −4 percentage points. Bootstrap intervals are [−10, 0], [0, 0] and [−8, −1] points, respectively. The negative direction means more target mentions with fusion. The interval excluding zero for stealth does not override the separately planned exact test and its multiplicity adjustment. Reference-mention difference intervals were recomputed after the measurement fix; target tests and target intervals were unchanged.

Intervals are conditional on these questions, attack templates, reconstructed retrieval, fixed heads and fixed answer model. They do not sample new models, attack authors, templates or corpora. This follow-up was designed after inspecting uploaded results and is exploratory, not an untouched preregistered benchmark. The seventh train-only augmented head and the primary three-test amendment were fixed before any main NQ generation.

## Frozen model and execution evidence

- Official `Qwen/Qwen2.5-0.5B-Instruct`, pinned revision `7ae557604adf67be50417f59c2c2f167def9a775`; 494,032,768 parameters, CPU float32, official safetensors, no quantization or remote API.
- PyTorch 2.14.1+cpu; Transformers 5.20.1; Python 3.12.14. Four intra-op threads, one inter-op thread. Full environment and weight/source hashes are retained in the manifest.
- Exact supplied RAG prompt, helpful-assistant system message and pinned tokenizer chat template. Greedy decoding, maximum 64 new tokens, retained repetition penalty 1.1. No main-case prompt tuning.
- All 100 question IDs × four conditions × seven gates = 2,800 requested rows. Global prompt deduplication produced 668 actual prompt executions in 167 fixed batches of four. Identical prompts share recorded responses and batch provenance.
- Input length 186–1,439 tokens; no truncation. Across unique executions, 5,648 output tokens including EOS; 664 prompts ended with EOS and four reached the token limit. Those four capped outputs appear in 37 condition rows.
- Recorded batch inference: 1,633.9731 seconds; generation/output phase: 1,634.5781 seconds. Model loading and tokenization are excluded. Per-prompt time is an equal allocation of measured batch time, not independent single-prompt latency.
- Source contexts SHA-256: `829e50fe8eb71e8f281d51d35012e3716539a4b37af05ce0e7d3dc9e8cbf6ffd`.
- Original frozen raw-output SHA-256: `213c878f920d79245f2d530054649c041dc26edffe488539ced16af70c22e29b`.
- Corrected derivative raw-output SHA-256: `f513487ffe5edc983287cacd31d512978ea1a4c38699091e8ad98799d81d9baa`.

`condition_costs.json` distinguishes unique results used by each condition from globally unique executions. First-request cost attribution is only an accounting convention; adding all requested rows or reused results would overstate computation.

## Transparent post-run measurement correction

Review found one operational scoring defect after inference: frozen punctuation normalization turned `Ocean's` into `ocean s`, manufacturing a mention of the reference letter `S` on `test397`. Version `apostrophe-aware-bounded-mention-v2` canonicalizes apostrophes, removes word-final possessive `'s`, joins remaining word-internal apostrophes, then applies the frozen bounded/numeric matcher. Quoted `'S'`, `S-shaped`, `S's`, `John Smith's`, `O’Brien’s` and `James'` have explicit regressions. The existing `no` versus `know`, terminal numeric period and complete-number boundary checks also remain.

This separate correction changes reference/both flags in 23 rows for that one question. It changes no response, prompt, target flag, target induction denominator, exact match, abstention, target test, target interval, cost or original file. The frozen scorer and inference source fingerprints remain intact. `correction_provenance.json` gives the source hashes and exact row differences. Independent audits checked all 2,800 rows, corrected reference-change intervals, all 21 tests/Holm values and 28 cost records.

No new model calls, detector fits, threshold choices or prompt changes followed this measurement correction.
