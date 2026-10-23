# Executed experiment findings

The primary empirical hypothesis is not supported by this configuration.

| Gate | Attack recall | Benign FPR | Answer evidence coverage |
|---|---:|---:|---:|
| keyword | 0.00% | 0.00% | 100.00% |
| lexical | 4.17% | 0.00% | 100.00% |
| retrieval | 0.00% | 0.00% | 100.00% |
| neural | 0.00% | 0.00% | 100.00% |
| combined | 5.21% | 4.38% | 100.00% |

Joint test: 96 query groups resampled conditionally on the authored bank, 96 malicious and 480 benign passages; eight topics and four attack families held out from fitting.

The neural and retrieval-only development thresholds are positive infinity: both gates accept all passages under the selected 5% empirical benign-FPR constraint. This is not evidence that their raw scores contain no signal. Combined blocks 5 attacks and 21 benign passages, all 21 from the 192 answer-bearing records. Two answer copies per query preserve the at-least-one-evidence proxy.

Fusion weights: intercept 6.401405, neural 0.047653, retrieval -11.616855. Holding the neural feature at its training mean changes zero decisions on all three test suites. The learned reversal of the retrieval proxy and raw-feature scale mismatch undermine any claim of useful neural/retrieval complementarity.

The post-hoc fixed-0.5 neural reference yields 100% synthetic joint recall and 100% benign FPR. On standalone public data, it detects 108/125 BIPIA payloads (86.4%) but rejects 243/339 NotInject benign prompts (71.68%). The frozen primary neural threshold rejects none of either source. These public tests are detector behavior, not contextual RAG ASR.

Actual local neural cost: 31.87 ms/passage (batch16, four CPU threads, tokenization plus PyTorch forward, load/warmup excluded). All synthetic inputs <=83 tokens; none reaches the 256-token cap. Retrieval feature computation takes 0.461s over 2592 passages.

Checkpoint loading/hash/evaluation-mode checks pass. Natural factual sentences score low, while similar visitor-guide wrappers can score high. Synthetic style sensitivity, a small authored template bank, unstandardized saturated neural scores and source differences limit interpretation. No threshold was retuned after inspecting the test.

Separate generation results in output/generation/ use a genuine frozen FLAN-T5-small model. All 96 clean and attacked joint-shift queries are correct under every gate, and no attack target is produced. This ceiling demonstrates an inconclusive downstream defense test, not a protection gain or a guarantee.
