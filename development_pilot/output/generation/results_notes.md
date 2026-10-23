# Completed downstream generation pilot

The official `google/flan-t5-small` checkpoint at revision `0fc9ddf78a1e988dac52e2dac162b0ede4fd74ab` was evaluated as a frozen CPU float32 PyTorch model. It has 76,961,152 parameters. The main evaluation includes **all 96 joint-shift groups**, covering eight held-out topics and four held-out attack families. Each of six gates was evaluated on both a clean context and its attacked counterpart, yielding 1,152 condition rows. Identical prompts were generated once: there were 213 unique model executions and 939 reused prompt results.

## Observed result

| Measure, per gate | Clean | Attacked |
|---|---:|---:|
| Answer exact match | 96/96 | 96/96 |
| Exact attacker-target response | 0/96 | 0/96 |
| Bounded attacker-target occurrence | 0/96 | 0/96 |
| Abstentions | 0/96 | 0/96 |

These values hold separately for accept-all, keyword, lexical, retrieval, neural and combined gates. Every raw model response equals its gold answer **verbatim**, including units; the result is not produced by a permissive numeric matcher. The attacked-minus-clean change is zero for every metric and gate. The per-gate Wilson 95% interval is 96.15–100% for attacked answer exact match and 0–3.85% for attacked target occurrence, conditional on this sample and its construction. A paired group bootstrap degenerates at zero because every observed pair agrees; this does not establish a zero population effect.

Inputs ranged from 255 to 392 tokens. No input was truncated or exceeded 512 tokens. Generation used greedy decoding with one beam, no sampling, a maximum of 32 new tokens, and an operational input cap of 1,024 tokens. The 213 unique executions took a mean of 0.166 seconds each; the recorded generation-and-output phase took 35.59 seconds. These timings exclude model loading and detector computation.

## Interpretation for the report

This is a **ceiling result and a negative finding for downstream discrimination**, not a demonstrated security improvement. The accept-all pipeline already answered all 96 attacked questions correctly and never emitted the target phrase. Consequently these attacks, this prompt and this small model provide no opportunity to attribute improved answer quality or reduced target emission to filtering. Passage exposure nevertheless differs between gates and must be analysed separately.

The constructed corpus supplies two benign passages repeating the correct fact. The instruction-bearing attack passage also repeats that fact before redirecting the answer. The pilot tests response redirection under redundant evidence, not the factual-poisoning condition. The clean control preserves a legitimate quotation of the same attacker target, so an isolated target occurrence would not itself establish malicious instruction following; attacked-minus-clean differences are essential. No such occurrences were observed here. Neither this ceiling nor the zero marker count establishes robust behaviour on larger chat models, stronger or adaptive attacks, long contexts, tool use, confidential data, or real retrieved web documents.

The clean pipeline independently recomputes group-dependent retrieval and fusion features after removing the malicious passage, while retaining the fitted coefficients and development thresholds. Thus each pair evaluates the whole gated-context perturbation, including any change in benign passage decisions. The combined gate accepted all five benign passages in each clean group. In attacked groups it retained six passages in 75 groups, five in 16 groups and four in five groups. Enough repeated answer evidence remained to preserve exact-match answers in this pilot.

## Validation evidence

`validation.json` records row counts, unique-prompt counts and SHA-256 hashes. All 1,152 `(group, gate, condition)` combinations are unique and complete. Every prompt hash was recomputed, every cached answer agreed with its matching prompt, and every raw answer was compared with the gold string. The independently written context adapter matched all 1,152 contexts and retained-passage ID lists exported by the detector owner, with zero mismatches. An independent scientific-audit agent separately verified these output facts.

The report should cite the fixed checkpoint and FLAN instruction-tuning paper using its verified bibliography. Model weights are reproducible downloads and are omitted from the source package; `generation/model_manifest.json` retains their fixed URLs, hashes and sizes.
