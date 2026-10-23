# Additional public benchmark sources

**Delivery note:** This package contains the pinned downloader, manifests and MIT AgentDojo outputs. InjecAgent raw files and derived full-context text are not redistributed here. Run `python fetch_primary_sources.py` in this folder to retrieve the pinned public bytes and recreate those contexts before replaying external scoring. The lists below document what was actually downloaded and scored during the recorded research run; optional discovery files are not all included in this release.

Retrieved on 22 October 2026 for the COMPSCI 764 RAG adversarial-context project. Retrieval was passive. No victim agent, external tool, benchmark environment, or model inference was executed.

## Immediate usable diagnostics

| Dataset view | Saved records | Independent-parent information | Appropriate use |
|---|---:|---|---|
| InjecAgent base contextual tool outputs | 1,054 malicious-context cases | Exactly 62 attacker payload seeds crossed with 17 user tasks | External context-format detector transfer; no agent ASR claim |
| AgentDojo clean tool outputs, all occurrences | 348 | 96 user-task groups from 97 archived clean runs | Descriptive clean tool-output false positives |
| AgentDojo clean tool outputs, exact unique text | 141 | Retains every original task group and occurrence ID | Headline false-positive denominator with duplicate text removed |

InjecAgent source: https://github.com/uiuc-kang-lab/InjecAgent , revision `f19c9f2c79a41046eb13c03c51a24c567a8ffa07`; paper https://aclanthology.org/2024.findings-acl.624/ . The 510 direct-harm and 544 data-stealing cases are released base configurations. The six `Attack Type` labels describe objectives (physical harm, financial harm, data security harm, physical data, financial data, others), not six independent linguistic attack mechanisms. Base and enhanced configurations are not added together. The downloaded payload and user parent hashes expose the 62-by-17 construction rather than presenting 1,054 unrelated attack ideas. No standalone LICENSE was found in the pinned repository tree; the manifest retains source attribution without claiming a permissive data license.

AgentDojo source: https://github.com/ethz-spylab/agentdojo , revision `089ed468cf3ed0322acc66b0211f26d9d90dbf60`; paper https://arxiv.org/abs/2406.13352 . The selected archived pipeline is exactly `gpt-4o-2024-05-13`, with `attack_type=null`, empty `injections`, and no injection-task ID. The 97 no-injection user-task files span banking, Slack, travel and workspace. We extract nonempty string tool outputs with no recorded tool error; six error tool messages are excluded. One user task contributes no eligible tool output, leaving 96 task groups. These labels mean no injected attacker content under the benchmark setup, not independently reviewed factual correctness or universal safety. The repository MIT LICENSE is downloaded unchanged. All data are archived observations, not a fresh deterministic environment replay.

The unique AgentDojo file removes 207 repeated output occurrences. It retains `all_source_groups` and `all_original_ids`, so repeated calendar/date/database responses do not silently lose their source relationships. Neither the 348 occurrences nor 141 unique strings should be treated as that many independent real-world environments. These traces are detector diagnostics, not an execution-level replication of the AgentDojo paper.

## Files

- `injecagent_base_contexts.jsonl`: complete released base contexts, user question, payload, attack objective, user tool, upstream revision, original row, and parent hashes.
- `agentdojo_clean_tool_outputs_all.jsonl`: all 348 eligible clean tool-output occurrences.
- `agentdojo_clean_tool_outputs_unique.jsonl`: 141 exact-unique strings with all duplicate memberships retained.
- `primary_download_manifest.json`: 106 exact pinned raw URLs, byte sizes and SHA-256 values.
- `source_summary.json`, `source_validation.json`: counts and successful byte/hash checks.
- `fetch_primary_sources.py`, `agentdojo_clean_paths.json`: compact reproducible downloader and extractor. It uses only the Python standard library. The original large repository-tree snapshots are research discovery metadata and are not needed to rerun the downloader.
- `InjecAgent/README.md`, `InjecAgent/data/`: the pinned raw source material.
- `agentdojo/README.md`, `agentdojo/LICENSE`, `agentdojo/runs/`: the pinned archived clean traces and license.
- `additional/additional_sources_audit.md`: Tensor Trust and AgentDyn suitability/label-semantics audit.

Running `python fetch_primary_sources.py` retrieves these fixed revisions and recreates the derived diagnostics. It downloads files only; it never calls tools described in any untrusted benchmark text.

## Other inspected sources

Tensor Trust's original-author mirrored hijacking set contains 776 rows but only 478 normalized distinct attack strings. Its boundary is a direct prompt-security game. Keep it separate from RAG poisoning. Its extraction-detection labels describe model outputs revealing a secret, not malicious versus benign input prompts; False-labelled outputs must not become a hard-benign input test set. Explicit data-license status was not established.

AgentDyn's current MIT repository documents 60 dynamic tasks and 560 injection cases, including helpful third-party instructions. Its task authorization requires the complete environment. The present audit downloaded metadata, README and LICENSE, without rebuilding or executing the 560 cases.

The independently sourced diagnostics should remain separate from the new thousand-per-template constructed suite. Passing a fixed constructed template grid does not demonstrate adaptive-attack robustness; failing an external text probe does not alone establish generator compromise.
