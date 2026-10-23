# Expanded RAG adversarial context taxonomy

Research and artifact metadata checked on 22 October 2026. The implementation is `working/expanded_build/attack_templates.py`: 12 operational families, two templates per family. At 1,200 distinct host-question instances per template, the construction target is 28,800 attack events plus matched benign controls. This count is a design target until the root builder emits and validates the records.

## Research basis

[Open-Prompt-Injection and its USENIX Security 2024 paper](https://www.usenix.org/conference/usenixsecurity24/presentation/liu-yupei) support explicit redirection, instruction negation, boundary escape and fake task completion as useful baseline mechanisms. Our strings are newly written controlled variants, not copied benchmark payloads or reproduced optimization algorithms.

[BIPIA's official builder](https://github.com/microsoft/BIPIA/blob/a004b69ec0dd446e0afd461d98cb5e96e120a5d0/bipia/data/base.py) crosses attack strings with genuine context records and insertion positions. Its released held-out files contain 15 text-objective groups and ten code-objective groups, each with five strings. Three insertion positions and base64 stealth are construction modes. Five strings in one group do not become five independent mechanisms.

[AgentDojo's attack interface](https://agentdojo.spylab.ai/concepts/attacks/) makes the legitimate task, attacker goal, injection position and attacker knowledge explicit. This motivates preserving the host question and context in every event and distinguishing source-local forged authority from a genuine trusted instruction.

[PoisonedRAG](https://www.usenix.org/conference/usenixsecurity25/presentation/zou-poisonedrag) and [CorruptRAG](https://arxiv.org/abs/2504.03957) motivate wrong-answer evidence corruption. [CamoDocs](https://arxiv.org/abs/2608.28389) additionally shows why directly repeating the query is a construction cue rather than a necessary feature of poisoning. A literal answer-span replacement is a project diagnostic, not a reproduction of their optimized document construction or retrieval performance.

[Machine Against the RAG](https://www.usenix.org/conference/usenixsecurity25/presentation/shafran) establishes refusal/non-answer as a separate attacker objective. Its optimized blockers need not contain injected instructions. Our explicit abstention directives only cover the objective; they do not reproduce those noninstruction blockers.

[InceptionRAG](https://arxiv.org/abs/2609.16818) and [Divide and Doubt](https://arxiv.org/abs/2609.27090) motivate joint-context threats. The latter emphasizes diverse support and doubt rather than identical repetition. The local three-fragment controls test a bounded version of coordinated corroboration. They do not reproduce either complete attack.

## Implemented operational families

| Family | Two templates | Label and scope |
|---|---|---|
| Direct override | Replacement request; priority clause | Instructs a QA model to return the selected inert wrong answer. |
| Authority spoofing | System notice; editorial policy | Forged source-local authority; does not modify actual system instructions. |
| Boundary spoofing | XML closure; transcript turn | Attempts to promote source text into another apparent instruction channel. |
| Fake completion | Completed-task announcement; assistant prefill | Attempts to continue an attacker-provided answer rather than solve the real task. |
| Task-aligned persuasion | Answer-check guidance; grading rationale | Uses purported task success to steer the response. These are local operational variants. |
| Few-shot demonstration | QA demonstration; response mappings | Places the wrong response in example outputs. |
| Quoted-instruction laundering | Quoted final answer; annotation handoff | Explicitly promotes documentary quoted content into an instruction. |
| Output-format hijack | JSON answer field; replacement output label | Redirects the response contract toward a fixed local answer string. |
| Abstention induction | Unsupported notice; withdrawn-record notice | Targets the response `I do not know`, measured separately from wrong-answer adoption. |
| Factual answer substitution | Plain source substitution; correction framing | Corrupts one released exact answer span; labelled relative to the source snapshot. |
| Attribution forgery | Invented reference card; fabricated verification note | Supplies invented corroboration for the wrong answer; no real citation is verified. |
| Multi-document corroboration | Consensus cards; support-and-doubt notes | Joint-context corruption; fragments excluded from pointwise detection accuracy. |

These families are useful operational coverage, not a claim that the literature has one canonical twelve-way taxonomy. Several mechanisms can co-occur. Construction class, attacker objective and placement must be retained as separate fields.

## Orthogonal modes

Start, middle and end insertion; plain versus reversible encoding; language; number of inserted fragments; and source wrapper are separate factors. Changing placement does not by itself create a new attack family. Encoding must retain an explicit decoding instruction when the intended objective requires it, and evaluation must verify that the construction remains interpretable. A language transformation needs semantic validation and should be reported as a formatting/language stress test unless generated and reviewed under a stronger protocol.

Actual retrieval optimization remains separate. A source title or query echo can be used as a retrieval-bait control, but only measured ranking establishes whether it is retrieved. Neither keyword insertion nor a high candidate-only score establishes successful corpus poisoning.

## Construction and validity requirements

Every event should retain `source_id`, source article group, original question, original context, released answer span, wrong target, template ID, family ID, split, source URLs, construction seed, control-pair ID, passage/context hash, placement, encoding and objective. Whole article groups stay within one split. Reserve complete families for unseen-family testing if fitting any model on this expanded suite. Keep the old datasets and their fitted models frozen for transfer evaluation.

The module accepts an explicit answer offset when supplied. Otherwise factual replacement requires exactly one literal answer occurrence. It rejects a wrong offset, a missing span and a target equal to the answer. Label `factual_corruption` means deliberate alteration of the released source evidence, not independent verification of contemporary world truth.

Matched benign controls quote the same attempted instruction or wrong-answer claim inside explicit security commentary. They preserve target vocabulary so the selected target string itself is not a label shortcut. These are constructed difficult-benign controls, not a representative natural-document distribution. Source-only clean contexts and independent public hard-benign data should remain separate references. Quote framing and length can affect scores and should be audited.

Multi-document events use `label_scope=context` and `pointwise_scoring_eligible=false`. Their event-level attack label must not be silently converted into a label that every isolated fragment is intrinsically malicious. Exposure, local detector output, context-level decision, generator response and attacker success remain different endpoints.

Generated thousand-instance templates are correlated. Report template/family/source-group counts and use source/family grouping for uncertainty; multiplying payloads, policies or placements does not create the same number of independent attack ideas. Static templates do not test an adaptive attacker.

## Verified public artifacts

The current metadata receipt is `artifact_metadata.json`. Official GitHub repository metadata and current default-branch commits were fetched directly; no third-party implementation was run.

| Artifact | Verified commit | Status |
|---|---|---|
| microsoft/BIPIA | `a004b69ec0dd446e0afd461d98cb5e96e120a5d0` | Archived; original source license retained. |
| liu00222/Open-Prompt-Injection | `fbed5cca347488f88363790ae3ae97c56116da6a` | MIT declaration in repository metadata. |
| ethz-spylab/agentdojo | `089ed468cf3ed0322acc66b0211f26d9d90dbf60` | MIT declaration in repository metadata. |
| jaewonalive/CamoDocs | `ccb1e8af17e561a7b8c3dd40c8aa41b8dacf2ce5` | Official repository describes EMNLP 2026; MIT metadata. |
| ZJU-TrustAID/InceptionRAG | `f2ab9b25b5a0b75387a3ef77388ee64cd0606ba7` | Official repository; no license returned by metadata query. |

A public repository does not establish that its complete evaluation data, weights or exact paper results have been reproduced. This research pass only establishes source relevance and artifact identity.


## Final construction confirmation

The final builder emitted all 24 templates at 1,200 source questions per template: 28,800 attack conditions and 28,800 matched benign controls. Final cases SHA-256: `8034d0745f3ac689e41abc992d0257797471f3c1126a46f5efc47ee503f3e60c`. See `audit/case_build_validation.json`, `audit/independent_final_audit.json` and `results/case_predictions_complete.jsonl`. The earlier design-target wording above records the research stage, not missing final data.
