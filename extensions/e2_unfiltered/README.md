# Matched unfiltered mechanism extension

The original frozen E2 executed three filtered policies on 25 fixed source-supported questions. This follow-up adds only its missing unfiltered policy for the same five conditions, yielding 125 additional requests. Existing clean and single-counterfactual baselines and original filtered outputs are reused. The combined mechanism analysis contains 700 policy-condition rows from 25 articles, not 700 independent cases.

This extension was motivated after viewing the original results. Requests, analysis code and definitions were frozen before the additional answers. It is a post-hoc diagnostic, not a retroactive confirmatory preregistration. No model, threshold, question, answer alias, wrong target or scoring rule is tuned on the new outcomes. Original E1/E2 archives remain separate and unchanged.

## Canonical files

| File | Role |
|---|---|
| `requests.jsonl`, `request_manifest.json` | 125 unfiltered requests and original pool/configuration links |
| `analysis_protocol.json`, `execution_freeze.json` | Before-additional-output analysis and source fingerprints |
| `prepare_requests.py` | Reconstruct requests from the original pools and validate all 375 filtered requests |
| `token_preflight.py`, `token_preflight.json` | Optional model/tokenizer preflight, without generation |
| `analyse.py` | Frozen answer proxies, matched summaries, paired interactions and joint E1 outcomes |
| `verify.py` | Independent offline reconstruction and optional deep bootstrap verification |
| `../../output/revised_experiment/e2_unfiltered/generation/` | Actual additional generation, cache and runtime manifest |
| `../../output/revised_experiment/e2_unfiltered/analysis/` | Completed 700-row mechanism analysis and original E1 joint text-proxy view |

Existing pools, original responses and model/scorer sources are referenced at their canonical paths rather than copied. There are 125 distinct new complete prompts and no matching prompt in the original 432-entry cache. Exact-repeat outputs inside the original run continue to count as shared execution.

## Verify without models

From the project root:

```bash
python -S extensions/e2_unfiltered/verify.py
python extensions/e2_unfiltered/verify.py --deep
```

The first command uses the standard library. Deep checking additionally needs NumPy and reproduces all 10,000-resample paired confidence intervals. Default project verification includes the standard check. These commands check the delivered data and computations; they do not run the model again.

## Repeat this controlled extension

The archived generator and configuration are intentionally fixed to the recorded model, llama-cpp-python version, six threads and runtime fingerprint. After installing the same requirements and downloading the pinned model, use a new empty destination:

```bash
python revised_experiment/download_generator.py
python revised_experiment/gguf_generate.py --model revised_experiment/models/Qwen2.5-3B-Instruct-GGUF/qwen2.5-3b-instruct-q4_k_m.gguf --input extensions/e2_unfiltered/requests.jsonl --output ../Group9_Extension_Repeat/generation --threads 6
python extensions/e2_unfiltered/analyse.py --generation ../Group9_Extension_Repeat/generation --output ../Group9_Extension_Repeat/analysis
```

The analyzer rejects a mismatched configuration rather than mixing it with the original paired outputs. A different runtime or model belongs to a new paired study. It never replaces the original formal scores or report automatically. Installed dependencies and weights are separate from this package.

## Interpretation

For each question, the main descriptive interaction is

`[U(filtered,condition)-U(filtered,clean)]-[U(none,condition)-U(none,clean)]`.

The same 25 article identities are resampled together across conditions and policies. Intervals are descriptive; no new confirmatory p-values or wins are added to the original Holm family. The comparison measures the fixed pipeline's relative change under these constructions. It does not isolate one feature's causal effect or establish natural-world robustness. Alias exact and target mention remain text proxies; the latter includes negated or quoted occurrences. Known-support indicators do not enumerate every useful passage.
