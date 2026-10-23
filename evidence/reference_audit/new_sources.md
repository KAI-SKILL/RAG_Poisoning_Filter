# Primary sources for the revised NQ experiment

Verified 19 October 2026. Dataset packaging details and the BEIR/NQ4.0 versus original NQ3.0 source declarations are recorded in `data_license_notes.md`. Seven new references are in `new_refs.bib`; reuse the existing `zou2025poisonedrag` and `li2025piguard` entries for PoisonedRAG and NotInject. No paid API or ONNX model is needed for the revised experiment. Citations below describe source designs; **none of their published performance numbers is a result of this project**.

## Source claims and exact citations

| Key | Verified primary source | What it supports | Limit on project interpretation |
|---|---|---|---|
| `thakur2021beir` | [Official NeurIPS 2021 record](https://datasets-benchmarks-proceedings.neurips.cc/paper/2021/hash/65b9eea6e1cc6bb9f0cd2a47751a186f-Abstract-round2.html), [official dataset wiki](https://github.com/beir-cellar/beir/wiki/Datasets-available) | BEIR is an evaluation framework with originally 18 retrieval datasets. Official NQ table lists 3,452 test queries and about 2.68M corpus documents. | The project uses the BEIR-formatted NQ subset, not all BEIR tasks. Cached top-k lists are not a fresh full-corpus retrieval run. |
| `kwiatkowski2019nq` | [TACL record](https://aclanthology.org/Q19-1026/), [paper PDF](https://aclanthology.org/Q19-1026.pdf) | Natural Questions originates from real search queries with Wikipedia answer annotations. | BEIR-NQ is an adapted retrieval dataset; the original long-/short-answer evaluation is not the metric reproduced here. The paper PDF explicitly prints pp.453–466; ACL HTML/BibTeX has an inconsistent starting page452, so the new entry follows the PDF. |
| `izacard2022contriever` | [Author paper](https://arxiv.org/abs/2112.09118), [official model card](https://huggingface.co/facebook/contriever), [official code](https://github.com/facebookresearch/contriever) | Contriever is an unsupervised contrastive dense retriever. The official model card prescribes attention-mask mean pooling; the code compares embeddings by dot product. | Do not silently normalize embeddings if merging with stored raw dot scores. Recomputing only attack embeddings against cached clean rankings is a bounded ranking replay, not full indexing/retrieval reproduction. |
| `qwen2024qwen25_05b` | [Official model card](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct) | An instruction-tuned causal model, about0.49B parameters; this checkpoint has32,768 context length. Official usage applies its chat template and extracts continuation tokens after the input. | The family introduction's128K claim does not apply to this0.5B checkpoint. Report actual experiment truncation, output token budget, dtype and decoding; small-model results do not estimate larger-model robustness. |
| `protectai2024deberta_v2` | [Official model card](https://huggingface.co/protectai/deberta-v3-base-prompt-injection-v2) | English prompt-injection classifier fine-tuned from DeBERTa-v3-base;0=benign,1=injection. Its example truncates at512 tokens. | It is a prompt-injection guard, not a factual-poisoning detector. Card says it does not handle non-English/jailbreak attacks and can overflag system prompts. Published guard accuracy cannot be borrowed as our result; training-source overlap is not ruled out. |
| `jin2026cleanbase` | [Author arXiv record](https://arxiv.org/abs/2605.00460), [official repository](https://github.com/WeifeiJin/CleanBase) | A real May2026 preprint, by Jin/Wang/Zou/Jia/Gong. Constructs a similarity graph and detects cliques associated with groups of malicious documents. | Cite it as a preprint; a peer-reviewed venue has not been verified. Reusing its attack templates does not implement its graph defense or reproduce its experiments. |
| `liu2024promptinjection` | [USENIX Security2024 record](https://www.usenix.org/conference/usenixsecurity24/presentation/liu-yupei), [official toolkit](https://github.com/liu00222/Open-Prompt-Injection) | Original framework/toolkit for naive, escape, ignore, fake-completion and combined prompt-injection strategies. | Template adaptations are inspired by this taxonomy. Do not claim that the full original tasks, LLMs or attack optimization were reproduced. |

Contriever's final publication is TMLR2022; OpenReview's record at `jKN1pXi7b0` is currently browser-challenged. Author arXiv and official code/model sources were successfully read, and the final title/authors/year were corroborated. The old anonymous ICLR2022 submission has the earlier title *Towards Unsupervised...*; do not cite that submission as an accepted ICLR paper.

## IEEE-ready entries

1. N. Thakur, N. Reimers, A. Rücklé, A. Srivastava, and I. Gurevych, “BEIR: A Heterogeneous Benchmark for Zero-shot Evaluation of Information Retrieval Models,” in *Proc. Neural Information Processing Systems Track on Datasets and Benchmarks*, vol.1, 2021.
2. T. Kwiatkowski et al., “Natural Questions: A Benchmark for Question Answering Research,” *Transactions of the Association for Computational Linguistics*, vol.7, pp.453–466, 2019, doi:10.1162/tacl_a_00276.
3. G. Izacard et al., “Unsupervised Dense Information Retrieval with Contrastive Learning,” *Transactions on Machine Learning Research*, 2022.
4. Qwen Team, “Qwen2.5-0.5B-Instruct,” *Hugging Face model repository*, 2024. Accessed: Oct.19,2026. Available: https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct
5. Protect AI, “Fine-Tuned DeBERTa-v3-base for Prompt Injection Detection,” *Hugging Face model repository*, 2024. Accessed: Oct.19,2026. Available: https://huggingface.co/protectai/deberta-v3-base-prompt-injection-v2
6. W. Jin, X. Wang, W. Zou, J. Jia, and N. Gong, “CleanBase: Detecting Malicious Documents in RAG Knowledge Databases,” *arXiv preprint arXiv:2605.00460*, 2026.
7. Y. Liu, Y. Jia, R. Geng, J. Jia, and N. Z. Gong, “Formalizing and Benchmarking Prompt Injection Attacks and Defenses,” in *33rd USENIX Security Symposium*, pp.1831–1847, 2024.

## Official source commit verification

The three short commits in the uploaded prototype README resolve to these actual commits in the stated official repositories:

| Repository | Short commit | Verified full commit | Pin check |
|---|---|---|---|
| `sleeepeer/PoisonedRAG` | `f660d72` | `f660d72174f06b13fae5163ce656e7b235db858f` | Official GitHub commit HTML resolved the full SHA; pinned README matches uploaded README byte-for-byte. |
| `WeifeiJin/CleanBase` | `72561aa` | `72561aa902dab57f7428cfd337fb25ad3d11a955` | Official commit HTML resolved SHA; pinned `attacks/gen_prompt_injection.py` matches uploaded file byte-for-byte. |
| `liu00222/Open-Prompt-Injection` | `fbed5cc` | `fbed5cca347488f88363790ae3ae97c56116da6a` | Official GitHub API resolved SHA; pinned `CombineAttacker.py` matches uploaded file byte-for-byte. |

Raw snapshot matches are recorded with both remote/local SHA-256 hashes in `source_records/*_sample_match.json`. This validates these selected source files and commit identities, **not every file in the uploaded archive**. Archive-generated `rag_trust` code and cached outputs remain project material requiring their own audit.

## Licenses and artifact handling

| Component | Verified declaration | Scope to preserve |
|---|---|---|
| PoisonedRAG at the pinned commit | MIT, copyright2024 Runpeng Geng | Keep source license/attribution with reused code/data; does not override third-party corpus terms. |
| Open-Prompt-Injection at the pinned commit | MIT | Preserve its license for copied/adapted templates/code. |
| CleanBase at the pinned commit | Apache-2.0 | Preserve license and attribution; identify modifications. |
| Contriever official repository | CC BY-NC4.0 | This is **not MIT/Apache**. Preserve research-use attribution and license; official HF card does not add a different explicit license declaration. |
| Qwen2.5-0.5B-Instruct | Apache-2.0 | Preserve model license; pin weights/config/tokenizer snapshot. |
| ProtectAI DeBERTa-v2 | Apache-2.0 | Preserve model license/card; pin snapshot. |
| BEIR | Framework code and per-dataset content have separate terms | The official wiki explicitly refers users to each dataset owner rather than granting a blanket dataset license. |
| Natural Questions data / BEIR NQ conversion | BEIR card declares CC BY-SA4.0; original NQ declares CC BY-SA3.0 per [official NQ-Open README](https://github.com/google-research-datasets/natural-questions/blob/master/nq_open/README.md) | Do not confuse the Google utility-code repository's Apache license with the dataset's terms. Preserve source attribution on redistributed passages. |

License files were downloaded as text to `source_records/`; no large model or dataset download was performed for this source check. This table records published declarations; it is not an assertion that each third-party passage has a new uniform license.

## Inputs and pinning needed for the executed experiment

- **Contriever:** tokenize query and document using the same pinned checkpoint, attention-mask mean-pool last hidden states, use raw dot-product for ranking if matching the cached PoisonedRAG scores. Preserve title/text concatenation conventions: the supplied prototype says clean stored scores used `title + text` while generator context uses document text. Document all truncation and text normalization.
- **Guard:** input is each untrusted passage, not the system prompt. Preserve class1 probability/logit definition, max token count and windowing. A single512-token truncation can hide injection beyond the visible prefix; report this as a coverage limit if no windowing is implemented.
- **Generator:** use the Qwen chat template, trusted instructions in system/user roles and untrusted retrieved context explicitly marked in the prompt. Report greedy/sampled decoding, random seed, input truncation and output limit. Do not count the entire prompt as generated output.
- **Model pins:** record the actual executed full revision hashes in the experiment manifest and SHA-256 per downloaded file. New source-check metadata is a current snapshot suggestion, not evidence that an experiment used that snapshot. Reuse the same fixed model for every compared defense.
- **Data pins:** save selected query IDs, original clean retrieved passage IDs/scores, attack family/template IDs, correct/target answer strings, source corpus provenance and split assignments. Cache hashes should accompany newly computed scores and outputs.
- **Claims:** a replay that combines cached clean top-k results with newly scored attacks establishes performance for that restricted candidate pool. It does not test new corpus-wide retrieval or prove robustness against adaptive attackers. Repeated passages across query splits should be checked independently of grouped query IDs.

### Verified model source snapshots

These current revisions were independently resolved from official Hugging Face model APIs, followed by successful downloads of each pinned README and config (no weights):

| Model | Verified source snapshot |
|---|---|
| `Qwen/Qwen2.5-0.5B-Instruct` | `7ae557604adf67be50417f59c2c2f167def9a775` |
| `protectai/deberta-v3-base-prompt-injection-v2` | `90c9989b1a342275dd0d1a95aad283c04e075671` |
| `facebook/contriever` | `2bd46a25019aeea091fd42d1f0fd4801675cf699` |

Model metadata and pinned source text are in `source_records/`. The Qwen and guard cards declare Apache-2.0; Contriever's card has no explicit license metadata, so the official repository's CC BY-NC4.0 declaration is retained. These are source-check snapshots; confirm they match the final execution manifests before claiming the run used them.
