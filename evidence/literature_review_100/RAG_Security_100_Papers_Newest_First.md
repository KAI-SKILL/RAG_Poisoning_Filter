# RAG安全：100篇相关研究核读清单

检索与核对截止：2026-10-20。按首次公开日期从新到旧排序，共100条独立研究线；预印本与发表版本不重复计数。

本轮重新核对100篇主来源，复读方法、评测/结果与局限。前75篇重新取得当前全文；后25篇复读哈希核实的完整归档，其中4篇另核读较新版本的关键变化。

出版证据：正式发表或录用的官方记录已核实（含相关发表版本）33项；另有非归档工作坊报告1项；作者报告发表、尚未独立核实3项；预印本或发表未核实63项。工作坊单列，不计入正式发表或录用数；不能将100篇一概称为已同行评审。

阅读范围为与本项目有关的正文关键章节及选定附录；不声称逐字读完全部证明、附录或复现论文实验。这个定向清单不代表穷尽领域或全球最新100篇。

本项目采用的优化是补齐同25题五种条件的125条无过滤回答，并从冻结结果导出效用与目标字符串的联合视图。它们分别属于明确标记的事后配对补充与描述性重分析。原主实验、评分器和阈值不改。

## 索引

| 编号 | 首次公开 | 研究 | 阅读版本 | 出版证据 |
|---|---|---|---|---|
| [P001](#p001) | 2026-10-16 | [Ignored, Not Refused: What Low Prompt-Injection Success Rates Hide in Small Tool-Using Agents](https://arxiv.org/html/2610.23254v1) | v1 | 预印本/发表未核实 |
| [P002](#p002) | 2026-10-15 | [Poisoning the Neighborhood: A Topology-Aware Topic-Level Attack on Large-Scale HNSW-based RAG Systems](https://arxiv.org/html/2610.21464v1) | v1 | 预印本/发表未核实 |
| [P004](#p004) | 2026-10-06 | [RAG-PIBench: A Leakage-Aware Benchmark for Prompt-Injection Detection in Trustworthy RAG Systems](https://arxiv.org/html/2610.08571v1) | v1 | 预印本/发表未核实 |
| [P003](#p003) | 2026-10-06 | [ASPIRE: Agentic Safety & Prompt Injection Red-teaming Engine](https://arxiv.org/html/2610.08951v1) | v1 | 预印本/发表未核实 |
| [P005](#p005) | 2026-10-05 | [Bounded Provisional Visibility: Controlling Poisoning Exposure in Continuously Ingested RAG Vector Stores](https://arxiv.org/html/2610.05826v1) | v1 | 预印本/发表未核实 |
| [P006](#p006) | 2026-10-02 | [Passing the Test You Trained On: Re-evaluating Prompt-Injection Detectors for LLM Agents](https://arxiv.org/html/2610.03448v1) | v1 | 预印本/发表未核实 |
| [P007](#p007) | 2026-09-29 | [Divide and Inject: Can Agents Reconstruct an Indirect Prompt Injection from Fragments?](https://arxiv.org/html/2609.36576v1) | v1 | 预印本/发表未核实 |
| [P008](#p008) | 2026-09-25 | [Prompt Injection Detection for Email Agents Through Attack Chain Modeling](https://arxiv.org/html/2609.30657v1) | v1 | 预印本/发表未核实 |
| [P009](#p009) | 2026-09-18 | [Micro-Collaborative Poisoning: A Distributed Attack on RAG Systems](https://arxiv.org/html/2609.21573v1) | v1 | 预印本/发表未核实 |
| [P010](#p010) | 2026-09-15 | [InceptionRAG: Stealthy Poisoning Attack Against Retrieval-Augmented Generation](https://arxiv.org/html/2609.16818v1) | v1 | 预印本/发表未核实 |
| [P011](#p011) | 2026-09-14 | [PIDS-Bench: Evaluating Prompt-Injection Detectors Under Over-Defense, Obfuscation, and Distribution Shift](https://arxiv.org/html/2609.15017v1) | v1 | 预印本/发表未核实 |
| [P012](#p012) | 2026-09-08 | [In RAG We Trust? Measuring Robustness of Retrieval-Augmented Generation Under Post-Retrieval Context Tampering](https://arxiv.org/html/2609.09243v2) | v2 | 预印本/发表未核实 |
| [P013](#p013) | 2026-08-28 | [LongPIBench: A Long-Context Benchmark for Prompt Injection](https://arxiv.org/html/2608.28411v1) | v1 | 作者声明，待独立核实 |
| [P015](#p015) | 2026-08-17 | [Coverage Is Not Containment: A Fundamental Limit of Admission-Time Defenses Against Coordinated Poisoning of Vector Retrieval](https://arxiv.org/html/2608.16044v1) | v1 | 预印本/发表未核实 |
| [P014](#p014) | 2026-08-17 | [When Detection Does Not Guarantee Resistance: Reasoning and Poisoned Context in RAG](https://arxiv.org/html/2608.17153v4) | v4 | 预印本/发表未核实 |
| [P016](#p016) | 2026-08-07 | [When Context Bites: Detecting RAG Poisoning via Document-Level Attention Collapse](https://arxiv.org/html/2608.06947v1) | v1 | 预印本/发表未核实 |
| [P017](#p017) | 2026-08-02 | [DenialRAG: Single-Document RAG Poisoning via Embedded Parametric Denial](https://arxiv.org/html/2608.02678v1) | v1 | 预印本/发表未核实 |
| [P018](#p018) | 2026-07-28 | [RAGuard: A Layered Defense Framework for Retrieval-Augmented Generation Systems Against Data Poisoning](https://arxiv.org/html/2607.26339v1) | v1 | 预印本/发表未核实 |
| [P019](#p019) | 2026-07-11 | [NetInjectBench: Benchmarking Indirect Prompt Injection in Tool-Using Large Language Model Agents for Network Operations](https://arxiv.org/html/2607.10490v2) | v2 | 预印本/发表未核实 |
| [P020](#p020) | 2026-07-03 | [CrackedPDFs: A Controlled Benchmark for Hidden Prompt Injection in PDFs](https://arxiv.org/html/2607.19396v2) | v2 | 预印本/发表未核实 |
| [P022](#p022) | 2026-06-25 | [Adaptive Evaluation of Out-of-Band Defenses Against Prompt Injection in LLM Agents](https://arxiv.org/html/2606.26479v1) | v1 | 预印本/发表未核实 |
| [P021](#p021) | 2026-06-25 | [MIRROR: Novelty-Constrained Memory-Guided MCTS Red-Teaming for Agentic RAG](https://arxiv.org/html/2606.26793v1) | v1 | 预印本/发表未核实 |
| [P023](#p023) | 2026-06-24 | [Tracing Target Answers in Poisoned Retrieval Corpora via Token Influence Attribution](https://arxiv.org/html/2606.25721v2) | v2 | 预印本/发表未核实 |
| [P024](#p024) | 2026-06-13 | [Defending against Adaptive Prompt Injection Attacks via Reasoning-enabled Task Alignment](https://arxiv.org/html/2606.15441v1) | v1 | 预印本/发表未核实 |
| [P027](#p027) | 2026-06-09 | [Assessing Automated Prompt Injection Attacks in Agentic Environments](https://arxiv.org/abs/2606.10525) | v1 | 预印本/发表未核实 |
| [P026](#p026) | 2026-06-09 | [When Poison Fails After Retrieval: Revisiting Corpus Poisoning under Chunking and Reranking Pipelines](https://arxiv.org/abs/2606.11265) | v1 | 预印本/发表未核实 |
| [P025](#p025) | 2026-06-09 | [Influence Factors on RAG Poisoning](https://arxiv.org/html/2606.12469v1) | v1 | 预印本/发表未核实 |
| [P028](#p028) | 2026-06-08 | [Document-Authored Control-Signal Impersonation: A Low-Cost Indirect Prompt Attack on RAG Safety Boundaries](https://arxiv.org/abs/2606.09005) | v1 | 预印本/发表未核实 |
| [P029](#p029) | 2026-05-27 | [Measuring Real-World Prompt Injection Attacks in LLM-based Resume Screening](https://arxiv.org/abs/2605.28999) | v1 | 正式发表/录用，官方记录已核 |
| [P031](#p031) | 2026-05-26 | [Cordon-MAS: Defending RAG against Knowledge Poisoning via Information-Flow Control](https://arxiv.org/abs/2605.26754) | v1 | 预印本/发表未核实 |
| [P030](#p030) | 2026-05-26 | [Prompt Injection Detection is Regime-Dependent: A Deployment-Aware Evaluation with Interpretable Structural Signals](https://arxiv.org/abs/2605.26999) | v1 | 预印本/发表未核实 |
| [P032](#p032) | 2026-05-18 | [LivePI: More Realistic Benchmarking of Agents Against Indirect Prompt Injection](https://arxiv.org/abs/2605.17986) | v3 | 预印本/发表未核实 |
| [P034](#p034) | 2026-05-17 | [ASPI: Seeking Ambiguity Clarification Amplifies Prompt Injection Vulnerability in LLM Agents](https://arxiv.org/abs/2605.17324) | v1 | 预印本/发表未核实 |
| [P033](#p033) | 2026-05-17 | [AI Agents May Always Fall for Prompt Injections](https://arxiv.org/abs/2605.17634) | v1 | 预印本/发表未核实 |
| [P035](#p035) | 2026-05-05 | [ARGUS: Defending LLM Agents Against Context-Aware Prompt Injection](https://arxiv.org/abs/2605.03378) | v2 | 预印本/发表未核实 |
| [P036](#p036) | 2026-05-01 | [CleanBase: Detecting Malicious Documents in RAG Knowledge Databases](https://arxiv.org/abs/2605.00460) | v1 | 预印本/发表未核实 |
| [P038](#p038) | 2026-04-01 | [RAGShield: Detecting Numerical Claim Manipulation in Government RAG Systems](https://arxiv.org/abs/2604.00387) | v2 | 预印本/发表未核实 |
| [P037](#p037) | 2026-04-01 | [AgentWatcher: A Rule-based Prompt Injection Monitor](https://arxiv.org/abs/2604.01194) | v2 | 预印本/发表未核实 |
| [P039](#p039) | 2026-03-26 | [PIDP-Attack: Combining Prompt Injection with Database Poisoning Attacks on Retrieval-Augmented Generation Systems](https://arxiv.org/abs/2603.25164) | v1 | 预印本/发表未核实 |
| [P040](#p040) | 2026-03-10 | [Semantic Chameleon: Corpus-Dependent Poisoning Attacks and Defenses in RAG Systems](https://arxiv.org/abs/2603.18034) | v1 | 预印本/发表未核实 |
| [P041](#p041) | 2026-02-25 | [Adversarial Hubness Detector: Detecting Hubness Poisoning in Retrieval-Augmented Generation Systems](https://arxiv.org/abs/2602.22427) | v2 | 预印本/发表未核实 |
| [P042](#p042) | 2026-02-24 | [AdapTools: Adaptive Tool-based Indirect Prompt Injection Attacks on Agentic LLMs](https://arxiv.org/abs/2602.20720) | v1 | 预印本/发表未核实 |
| [P043](#p043) | 2026-02-06 | [Confundo: Learning to Generate Robust Poison for Practical RAG Systems](https://arxiv.org/abs/2602.06616) | v1 | 正式发表/录用，官方记录已核 |
| [P044](#p044) | 2026-02-04 | [Addressing Corpus Knowledge Poisoning Attacks on RAG Using Sparse Attention](https://arxiv.org/abs/2602.04711) | v3 | 预印本/发表未核实 |
| [P045](#p045) | 2026-01-16 | [Hidden-in-Plain-Text: A Benchmark for Social-Web Indirect Prompt Injection in RAG](https://arxiv.org/abs/2601.10923) | v2 | 正式发表/录用，官方记录已核 |
| [P046](#p046) | 2025-12-30 | [RAGPart & RAGMask: Retrieval-Stage Defenses Against Corpus Poisoning in Retrieval-Augmented Generation](https://arxiv.org/abs/2512.24268) | v1 | 非归档工作坊报告，官方记录已核 |
| [P047](#p047) | 2025-12-09 | [Attention is All You Need to Defend Against Indirect Prompt Injection Attacks in LLMs](https://arxiv.org/abs/2512.08417) | v3 | 正式发表/录用，官方记录已核 |
| [P049](#p049) | 2025-11-30 | [Epistemic Bias Injection: Manipulating LLM Opinion via Selective Context Retrieval](https://arxiv.org/abs/2512.00804) | v3 | 预印本/发表未核实 |
| [P048](#p048) | 2025-11-30 | [Mitigating Indirect Prompt Injection via Instruction-Following Intent Analysis](https://arxiv.org/abs/2512.00966) | v1 | 预印本/发表未核实 |
| [P050](#p050) | 2025-11-25 | [BrowseSafe: Understanding and Preventing Prompt Injection Within AI Browser Agents](https://arxiv.org/abs/2511.20597) | v2 | 正式发表/录用，官方记录已核 |
| [P051](#p051) | 2025-11-03 | [Rescuing the Unpoisoned: Efficient Defense against Knowledge Corruption Attacks on RAG Systems](https://arxiv.org/abs/2511.01268) | v1 | 正式发表/录用，官方记录已核 |
| [P052](#p052) | 2025-10-28 | [Secure Retrieval-Augmented Generation against Poisoning Attacks](https://arxiv.org/abs/2510.25025) | v2 | 作者声明，待独立核实 |
| [P053](#p053) | 2025-10-22 | [Defending Against Prompt Injection with DataFilter](https://arxiv.org/abs/2510.19207) | v2 | 正式发表/录用，官方记录已核 |
| [P054](#p054) | 2025-10-20 | [Breaking and Fixing Defenses Against Control-Flow Hijacking in Multi-Agent Systems](https://arxiv.org/abs/2510.17276) | v2 | 预印本/发表未核实 |
| [P055](#p055) | 2025-10-14 | [PromptLocate: Localizing Prompt Injection Attacks](https://arxiv.org/abs/2510.12252) | v2 | 正式发表/录用，官方记录已核 |
| [P056](#p056) | 2025-10-12 | [Steering Over-refusals Towards Safety in Retrieval Augmented Generation](https://arxiv.org/abs/2510.10452) | v1 | 预印本/发表未核实 |
| [P057](#p057) | 2025-10-11 | [ADMIT: Few-shot Knowledge Poisoning Attacks on RAG-based Fact Checking](https://arxiv.org/abs/2510.13842) | v2 | 预印本/发表未核实 |
| [P058](#p058) | 2025-10-10 | [The Attacker Moves Second: Stronger Adaptive Attacks Bypass Defenses Against LLM Jailbreaks and Prompt Injections](https://arxiv.org/abs/2510.09023) | v1 | 预印本/发表未核实 |
| [P060](#p060) | 2025-10-06 | [RL Is a Hammer and LLMs Are Nails: A Simple Reinforcement Learning Recipe for Strong Prompt Injection](https://arxiv.org/abs/2510.04885) | v1 | 预印本/发表未核实 |
| [P059](#p059) | 2025-10-06 | [Indirect Prompt Injections: Are Firewalls All You Need, or Stronger Benchmarks?](https://arxiv.org/abs/2510.05244) | v2 | 预印本/发表未核实 |
| [P061](#p061) | 2025-10-01 | [WAInjectBench: Benchmarking Prompt Injection Detections for Web Agents](https://arxiv.org/abs/2510.01354) | v2 | 预印本/发表未核实 |
| [P062](#p062) | 2025-09-27 | [ReliabilityRAG: Effective and Provably Robust Defense for RAG-based Web-Search](https://arxiv.org/abs/2509.23519) | v2 | 正式发表/录用，官方记录已核 |
| [P063](#p063) | 2025-08-27 | [DisarmRAG: Stealthy Retriever-Centric Poisoning to Disable Self-Correction in Retrieval-Augmented Generation (Extended Version)](https://arxiv.org/abs/2508.20083) | v2 | 正式发表/录用，官方记录已核 |
| [P064](#p064) | 2025-08-04 | [Defending Against Knowledge Poisoning Attacks During Retrieval-Augmented Generation](https://arxiv.org/abs/2508.02835) | v2 | 预印本/发表未核实 |
| [P065](#p065) | 2025-07-21 | [PromptArmor: Simple yet Effective Prompt Injection Defenses](https://arxiv.org/abs/2507.15219) | v1 | 预印本/发表未核实 |
| [P066](#p066) | 2025-07-10 | [Defending Against Prompt Injection With a Few DefensiveTokens](https://arxiv.org/abs/2507.07974) | v2 | 预印本/发表未核实 |
| [P067](#p067) | 2025-07-03 | [Meta-SecAlign: Training LLMs against Prompt Injection for Robust Agents](https://arxiv.org/abs/2507.02735) | v4 | 预印本/发表未核实 |
| [P068](#p068) | 2025-06-04 | [Through the Stealth Lens: Attention-Aware Defenses Against Poisoning in RAG](https://arxiv.org/abs/2506.04390) | v2 | 正式发表/录用，官方记录已核 |
| [P069](#p069) | 2025-05-26 | [CPA-RAG:Covert Poisoning Attacks on Retrieval-Augmented Generation in Large Language Models](https://arxiv.org/abs/2505.19864) | v1 | 预印本/发表未核实 |
| [P070](#p070) | 2025-05-24 | [Benchmarking Poisoning Attacks against Retrieval-Augmented Generation](https://arxiv.org/abs/2505.18543) | v1 | 预印本/发表未核实 |
| [P071](#p071) | 2025-05-23 | [A Critical Evaluation of Defenses against Prompt Injection Attacks](https://arxiv.org/abs/2505.18333) | v1 | 预印本/发表未核实 |
| [P072](#p072) | 2025-05-18 | [Uncovering Competing Poisoning Attacks in Retrieval-Augmented Generation](https://arxiv.org/abs/2505.12574) | v5 | 作者声明，待独立核实 |
| [P073](#p073) | 2025-05-15 | [One Shot Dominance: Knowledge Poisoning Attack on Retrieval-Augmented Generation Systems](https://arxiv.org/abs/2505.11548) | v4 | 正式发表/录用，官方记录已核 |
| [P074](#p074) | 2025-05-10 | [POISONCRAFT: Practical Poisoning of Retrieval-Augmented Generation for Large Language Models](https://arxiv.org/abs/2505.06579) | v1 | 预印本/发表未核实 |
| [P075](#p075) | 2025-05-08 | [Defending against Indirect Prompt Injection by Instruction Detection](https://arxiv.org/abs/2505.06311) | v2 | 正式发表/录用，官方记录已核 |
| [P076](#p076) | 2025-04-30 | [Traceback of Poisoning Attacks to Retrieval-Augmented Generation](https://arxiv.org/abs/2504.21668) | v2 | 正式发表/录用，官方记录已核 |
| [P077](#p077) | 2025-04-16 | [Progent: Securing AI Agents with Privilege Control](https://arxiv.org/abs/2504.11703) | v1；补核v3 | 预印本/发表未核实 |
| [P078](#p078) | 2025-04-04 | [Practical Poisoning Attacks against Retrieval-Augmented Generation](https://arxiv.org/abs/2504.03957) | v2 | 正式发表/录用，官方记录已核 |
| [P079](#p079) | 2025-03-24 | [Defeating Prompt Injections by Design](https://arxiv.org/abs/2503.18813) | v1；补核v2 | 正式发表/录用，官方记录已核 |
| [P080](#p080) | 2025-02-28 | [The RAG Paradox: A Black-Box Attack Exploiting Unintentional Vulnerabilities in Retrieval-Augmented Generation Systems](https://arxiv.org/abs/2502.20995) | v3 | 正式发表/录用，官方记录已核 |
| [P081](#p081) | 2025-02-27 | [Adaptive Attacks Break Defenses Against Indirect Prompt Injection Attacks on LLM Agents](https://arxiv.org/abs/2503.00061) | v1；补核v2 | 正式发表/录用，官方记录已核 |
| [P082](#p082) | 2025-02-07 | [MELON: Provable Defense Against Indirect Prompt Injection Attacks in AI Agents](https://arxiv.org/abs/2502.05174) | v1；补核v4 | 正式发表/录用，官方记录已核 |
| [P083](#p083) | 2025-01-28 | [SafeRAG: Benchmarking Security in Retrieval-Augmented Generation of Large Language Model](https://arxiv.org/abs/2501.18636) | v2 | 正式发表/录用，官方记录已核 |
| [P084](#p084) | 2025-01-25 | [PromptShield: Deployable Detection for Prompt Injection Attacks](https://arxiv.org/abs/2501.15145) | v2 | 正式发表/录用，官方记录已核 |
| [P085](#p085) | 2025-01-01 | [TrustRAG: Enhancing Robustness and Trustworthiness in Retrieval-Augmented Generation](https://arxiv.org/abs/2501.00879) | v3 | 预印本/发表未核实 |
| [P086](#p086) | 2024-12-21 | [The Task Shield: Enforcing Task Alignment to Defend Against Indirect Prompt Injection in LLM Agents](https://arxiv.org/abs/2412.16682) | v1 | 正式发表/录用，官方记录已核 |
| [P087](#p087) | 2024-10-30 | [InjecGuard: Benchmarking and Mitigating Over-defense in Prompt Injection Guardrail Models](https://arxiv.org/abs/2410.22770) | v3 | 正式发表/录用，官方记录已核 |
| [P088](#p088) | 2024-10-07 | [SecAlign: Defending Against Prompt Injection with Preference Optimization](https://arxiv.org/abs/2410.05451) | v3 | 正式发表/录用，官方记录已核 |
| [P089](#p089) | 2024-06-19 | [AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents](https://arxiv.org/abs/2406.13352) | v3 | 正式发表/录用，官方记录已核 |
| [P090](#p090) | 2024-04-19 | [The Instruction Hierarchy: Training LLMs to Prioritize Privileged Instructions](https://arxiv.org/abs/2404.13208) | v1 | 预印本/发表未核实 |
| [P091](#p091) | 2024-03-20 | [Defending Against Indirect Prompt Injection Attacks With Spotlighting](https://arxiv.org/abs/2403.14720) | v1 | 预印本/发表未核实 |
| [P092](#p092) | 2024-03-11 | [Can LLMs Separate Instructions From Data? And What Do We Even Mean By That?](https://arxiv.org/abs/2403.06833) | v3 | 正式发表/录用，官方记录已核 |
| [P093](#p093) | 2024-03-07 | [Automatic and Universal Prompt Injection Attacks against Large Language Models](https://arxiv.org/abs/2403.04957) | v1 | 预印本/发表未核实 |
| [P094](#p094) | 2024-03-05 | [InjecAgent: Benchmarking Indirect Prompt Injections in Tool-Integrated Large Language Model Agents](https://arxiv.org/abs/2403.02691) | v3 | 正式发表/录用，官方记录已核 |
| [P095](#p095) | 2024-02-12 | [PoisonedRAG: Knowledge Corruption Attacks to Retrieval-Augmented Generation of Large Language Models](https://arxiv.org/abs/2402.07867) | v3 | 正式发表/录用，官方记录已核 |
| [P096](#p096) | 2024-02-09 | [StruQ: Defending Against Prompt Injection with Structured Queries](https://arxiv.org/abs/2402.06363) | v2 | 正式发表/录用，官方记录已核 |
| [P097](#p097) | 2023-12-21 | [Benchmarking and Defending Against Indirect Prompt Injection Attacks on Large Language Models](https://arxiv.org/abs/2312.14197) | v4 | 正式发表/录用，官方记录已核 |
| [P098](#p098) | 2023-11-02 | [Tensor Trust: Interpretable Prompt Injection Attacks from an Online Game](https://arxiv.org/abs/2311.01011) | v1 | 正式发表/录用，官方记录已核 |
| [P099](#p099) | 2023-10-19 | [Formalizing and Benchmarking Prompt Injection Attacks and Defenses](https://arxiv.org/abs/2310.12815) | v5 | 正式发表/录用，官方记录已核 |
| [P100](#p100) | 2023-02-23 | [Not what you've signed up for: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection](https://arxiv.org/abs/2302.12173) | v2 | 正式发表/录用，官方记录已核 |

## P001

**Ignored, Not Refused: What Low Prompt-Injection Success Rates Hide in Small Tool-Using Agents**

- 主来源：https://arxiv.org/html/2610.23254v1
- 首次公开：2026-10-16；本轮正文阅读版本：v1。
- 发表状态：arXiv preprint; peer-review acceptance not independently verified。
- 核读章节：3 Study Design；4 Results and Analysis；5 Discussion and Conclusion；Limitations；selected setup and judge appendices。
- 对本项目的具体启发：把同一题上的参考答案匹配与目标出现联合列示，再把拒答单独展开；零目标不能自动称安全成功。
- 结论限制：针对工具代理的轨迹分类和LLM判卷；本项目只能借鉴联合评估结构，字符串代理不能改称语义安全。
- 阅读文本SHA-256：`815864936d071594730af72a9f7ef4af1c5eff178bedabf03c79f6c7513a5ef6`。

## P002

**Poisoning the Neighborhood: A Topology-Aware Topic-Level Attack on Large-Scale HNSW-based RAG Systems**

- 主来源：https://arxiv.org/html/2610.21464v1
- 首次公开：2026-10-15；本轮正文阅读版本：v1。
- 发表状态：arXiv preprint; peer-review acceptance not independently verified。
- 核读章节：III Preliminary Study；IV Threat Model；V Method；VI Evaluation；VII Experimental Results Analysis。
- 对本项目的具体启发：检索进入率、最终入上下文率、生成结果分开报告；当前小库精确排序限定为当前实验，不扩称HNSW大库防御。
- 结论限制：攻击依赖大规模HNSW图、主题查询分布和文档预算；本项目没有对应索引，不能把论文攻击成功率移植过来。
- 阅读文本SHA-256：`e0e7ce30b95a1d570baa9e7dbea879289895a326b0e75f5fbb0a789882e5bf73`。

## P004

**RAG-PIBench: A Leakage-Aware Benchmark for Prompt-Injection Detection in Trustworthy RAG Systems**

- 主来源：https://arxiv.org/html/2610.08571v1
- 首次公开：2026-10-06；本轮正文阅读版本：v1。
- 发表状态：arXiv preprint; peer-review acceptance not independently verified。
- 核读章节：3 Methodology；4 Results and Discussion。
- 对本项目的具体启发：保留稀疏TF-IDF强基线、来源组隔离和冻结测试；攻击检测与最终回答效果继续分表。
- 结论限制：保护测试集是平衡英文检测数据，不是本项目端到端检索投毒任务；跨论文F1不构成同场排名。
- 阅读文本SHA-256：`69369d9dae2a6b8cfd9c53c299daf420a9b6f754b24bbb14b15de738fe0aef3b`。

## P003

**ASPIRE: Agentic Safety & Prompt Injection Red-teaming Engine**

- 主来源：https://arxiv.org/html/2610.08951v1
- 首次公开：2026-10-06；本轮正文阅读版本：v1。
- 发表状态：arXiv preprint; peer-review acceptance not independently verified。
- 核读章节：3 ASPIRE；4 Experiment；5 Conclusion；selected coverage and backbone appendices。
- 对本项目的具体启发：未来自适应测试按攻击反馈预算记录所有尝试、独立成功路径和完整轨迹，避免把重复模板当成新发现。
- 结论限制：这是工具代理的探索式红队框架；行为图与专家组合的优势在特定工具接口和所测模型内成立。
- 阅读文本SHA-256：`58817abb61f6c29899f587a34039b63c3b87b695cf8af8686d9dee166a69a84c`。

## P005

**Bounded Provisional Visibility: Controlling Poisoning Exposure in Continuously Ingested RAG Vector Stores**

- 主来源：https://arxiv.org/html/2610.05826v1
- 首次公开：2026-10-05；本轮正文阅读版本：v1。
- 发表状态：arXiv preprint; peer-review acceptance not independently verified。
- 核读章节：III Problem Formalization；IV System Design；V Implementation；VI Evaluation Setup；VII Results；IX Limitations。
- 对本项目的具体启发：将暴露、检测和阻断定义到真正查询交付点；本项目已有selected IDs，需保持这一可核查层级。
- 结论限制：可见时间边界依赖查询路径执行和验证器不误提升；实时摄取协议不等同于投毒识别器。
- 阅读文本SHA-256：`80a9561182287c09cf618508e67be018790262220ea56228a07be0452c9ff54c`。

## P006

**Passing the Test You Trained On: Re-evaluating Prompt-Injection Detectors for LLM Agents**

- 主来源：https://arxiv.org/html/2610.03448v1
- 首次公开：2026-10-02；本轮正文阅读版本：v1。
- 发表状态：arXiv preprint; peer-review acceptance not independently verified。
- 核读章节：3 Deployment Setting and Threat Model；4 Methodology；5 Results；6 Discussion and Limitations；8 Conclusion。
- 对本项目的具体启发：保留1%正常校准点和任务内误删、证据丢失；不要用外部平衡数据上的准确率替代任务代价。
- 结论限制：代理工具输出格式与任务分布会改变误报；论文静态攻击结果不保证本项目域或自适应攻击。
- 阅读文本SHA-256：`e340cf2e725f666684c653bbeaa84e6ad9f636c318ec2d9045ff7f81d9be46b1`。

## P007

**Divide and Inject: Can Agents Reconstruct an Indirect Prompt Injection from Fragments?**

- 主来源：https://arxiv.org/html/2609.36576v1
- 首次公开：2026-09-29；本轮正文阅读版本：v1。
- 发表状态：arXiv preprint; peer-review acceptance not independently verified。
- 核读章节：3 AdaLCPI；4 Experiments and Results；5 Conclusion；B.2 repeated seeds；B.3 factorial ablations；budget and split-output results。
- 对本项目的具体启发：单段显式指令与五段事实污染之外，分片协同攻击应列为后续独立任务；必须给等预算、等反馈的对照。
- 结论限制：当前实验不含多步工具执行或上万token碎片；此文的自适应结果不能为短上下文过滤器背书。
- 阅读文本SHA-256：`7b35d6a517c394db7b52f54f4ae6fbc7adf263041d7e233be081e9ec6b4ac54f`。

## P008

**Prompt Injection Detection for Email Agents Through Attack Chain Modeling**

- 主来源：https://arxiv.org/html/2609.30657v1
- 首次公开：2026-09-25；本轮正文阅读版本：v1。
- 发表状态：arXiv preprint; peer-review acceptance not independently verified。
- 核读章节：III Problem Formulation；IV Data and Labels；V Framework and Experimental Design；VI Results；VII Error Analysis；VIII Discussion；IX Conclusion。
- 对本项目的具体启发：继续区分检索、过滤、上下文交付与回答，按同一题连接各阶段；简单检测率不等于端到端效果。
- 结论限制：邮件动作链的后期条件指标只在到达该阶段的样本上计算，不能扩大到所有请求。
- 阅读文本SHA-256：`8946f0a59948076bee0e074457aed0006804123c1aba4da0f373d3184d27e8b6`。

## P009

**Micro-Collaborative Poisoning: A Distributed Attack on RAG Systems**

- 主来源：https://arxiv.org/html/2609.21573v1
- 首次公开：2026-09-18；本轮正文阅读版本：v1。
- 发表状态：arXiv preprint; peer-review acceptance not independently verified。
- 核读章节：3 Methodology；4 Results and Discussion。
- 对本项目的具体启发：机制实验中数量与跨文档一致性共同变化，按配对案例解释；不把相同错误目标重复当作独立攻击样本。
- 结论限制：108种配置和多个数据库是该文范围；本项目小库不覆盖持续跨查询分布式写入。
- 阅读文本SHA-256：`020293f9699a9522b6057e8172e15b39cb1439d493f40d32740394c3c3033376`。

## P010

**InceptionRAG: Stealthy Poisoning Attack Against Retrieval-Augmented Generation**

- 主来源：https://arxiv.org/html/2609.16818v1
- 首次公开：2026-09-15；本轮正文阅读版本：v1。
- 发表状态：arXiv preprint; peer-review acceptance not independently verified。
- 核读章节：2. Preliminaries；3. Threat Model and Existing Attacks；4. InceptionRAG；5. Evaluation。
- 对本项目的具体启发：现行固定模板结果明确为非防御感知攻击；保留多文档、等预算自适应作为需要新设计的后续测试。
- 结论限制：攻击联合优化检索和生成并面向多种过滤器，复杂度和反馈条件不同；不可把本项目构造称为其复现。
- 阅读文本SHA-256：`c0be643dc09d1c454c4834ac04eb8dd33a54465df873bff91256337f688a23bf`。

## P011

**PIDS-Bench: Evaluating Prompt-Injection Detectors Under Over-Defense, Obfuscation, and Distribution Shift**

- 主来源：https://arxiv.org/html/2609.15017v1
- 首次公开：2026-09-14；本轮正文阅读版本：v1。
- 发表状态：arXiv preprint; peer-review acceptance not independently verified。
- 核读章节：3 Threat Model；4 Experimental Protocol；5 Benchmark Construction；6–7 results/discussion；8 Limitations；9 Conclusion。
- 对本项目的具体启发：合法echo/copy压力必须与普通误报分别保留；不同阈值政策、内部训练与外部组件不能混排。
- 结论限制：合成和来源匹配的难良性集不代表所有部署输入；高IID指标不能推出压力集低误删。
- 阅读文本SHA-256：`4bf44013247aff577bcd24bb6969a9dfd6f4c3f65959a86c4d364de54e13cf2c`。

## P012

**In RAG We Trust? Measuring Robustness of Retrieval-Augmented Generation Under Post-Retrieval Context Tampering**

- 主来源：https://arxiv.org/html/2609.09243v2
- 首次公开：2026-09-08；本轮正文阅读版本：v2。
- 发表状态：arXiv preprint; peer-review acceptance not independently verified。
- 核读章节：II Threat Model；III Method；IV Experimental Design；V Results；VII Limitations and Reproducibility。
- 对本项目的具体启发：新增E2未过滤配对控制时冻结原始池、完整提示和实际剂量；真实零剂量断言应保留，别只信名义条件。
- 结论限制：该文修改的是检索后上下文，且闭卷提示改变；只从论文观察借鉴控制逻辑，不宣称其检索攻击被本项目覆盖。
- 阅读文本SHA-256：`e121a0bb059cae3815b4e71d05f603dd6373af4848aac2fc43650ae26f334430`。

## P013

**LongPIBench: A Long-Context Benchmark for Prompt Injection**

- 主来源：https://arxiv.org/html/2608.28411v1
- 首次公开：2026-08-28；本轮正文阅读版本：v1。
- 发表状态：arXiv author reports forthcoming Findings of EMNLP 2026; publisher acceptance not independently verified。
- 核读章节：3 Our Datasets；4 Benchmarking Attacks；5 Benchmarking Defenses；6 Conclusion；Limitations；selected segmentation ablation。
- 对本项目的具体启发：模型与guard分别记录实际token覆盖、截断和指令尾部可见性；短上下文结果不扩称长文防御。
- 结论限制：文档中心的一次性静态输入，不覆盖多步代理；作者在arXiv声明将发表于Findings EMNLP26，尚未独立核对出版社。
- 阅读文本SHA-256：`f2bbde5e0e8e3c7fc7ff27e4e6d9c2da9a2e142e20686550698863857ec057c6`。

## P015

**Coverage Is Not Containment: A Fundamental Limit of Admission-Time Defenses Against Coordinated Poisoning of Vector Retrieval**

- 主来源：https://arxiv.org/html/2608.16044v1
- 首次公开：2026-08-17；本轮正文阅读版本：v1。
- 发表状态：arXiv preprint; peer-review acceptance not independently verified。
- 核读章节：III Threat Model and Problem Formulation；IV The Coordinated Poisoning Attack；V Collective Admission Controls；VI A Persistent Fundamental Limit；VII Systems Considerations；VIII Discussion；IX Limitations。
- 对本项目的具体启发：保留合法高相似冗余作为反例；用同数量、同来源的配对控制避免把共同入库当成恶意真相。
- 结论限制：不可分性界限只适用于所定义的摄取盲特征与分布重叠，不适用于所有使用来源或查询需求的防御。
- 阅读文本SHA-256：`aa194b552457060e948915d87498fa6462b69a4bba05b27042366e49fcda36de`。

## P014

**When Detection Does Not Guarantee Resistance: Reasoning and Poisoned Context in RAG**

- 主来源：https://arxiv.org/html/2608.17153v4
- 首次公开：2026-08-17；本轮正文阅读版本：v4。
- 发表状态：arXiv preprint; peer-review acceptance not independently verified。
- 核读章节：2 Approach；3 Experiments；5 Limitations。
- 对本项目的具体启发：把检测、目标出现和回答正确性分别记录；有识别表述仍可能受影响，不能用检测分数代替生成判卷。
- 结论限制：主要200道SciFact、供应商推理开关和自动judge；不是内部推理机制的纯因果干预。
- 阅读文本SHA-256：`5cf473959535eae65ee290650e8944cc144d5ddbf9f24bdb4cd570bdfa5f297a`。

## P016

**When Context Bites: Detecting RAG Poisoning via Document-Level Attention Collapse**

- 主来源：https://arxiv.org/html/2608.06947v1
- 首次公开：2026-08-07；本轮正文阅读版本：v1。
- 发表状态：arXiv preprint; peer-review acceptance not independently verified。
- 核读章节：3. Empirical Study and Solution；4. Experiment。
- 对本项目的具体启发：注意力方法先列为新系统需求而非直接替换现行guard；当前最紧要的仍是匹配控制和效用判定。
- 结论限制：需要生成器内部注意力与多次采样；三个多跳任务及构造替换不能证明本地量化短答生成器有同样信号。
- 阅读文本SHA-256：`85bd76e94e11da1a9d43f27743267a53f814400048734a5210c9353559e95e66`。

## P017

**DenialRAG: Single-Document RAG Poisoning via Embedded Parametric Denial**

- 主来源：https://arxiv.org/html/2608.02678v1
- 首次公开：2026-08-02；本轮正文阅读版本：v1。
- 发表状态：arXiv preprint; author comments say submitted to ACSAC 2026, not an acceptance claim。
- 核读章节：III Threat Model；IV The DenialRAG Attack；V Evaluation。
- 对本项目的具体启发：保留no/know、否定、双答案与目标提及分离；不能把错误目标substring出现自动叫作认可。
- 结论限制：单文档攻击；其目标出现代理与选择clean-correct题目的分母要注明，不能和全部100题结果直接相加。
- 阅读文本SHA-256：`cd7b57c21a18812fde83aeb35d179cfeec0cf2efde3ffaf850f2927c70fff583`。

## P018

**RAGuard: A Layered Defense Framework for Retrieval-Augmented Generation Systems Against Data Poisoning**

- 主来源：https://arxiv.org/html/2607.26339v1
- 首次公开：2026-07-28；本轮正文阅读版本：v1。
- 发表状态：arXiv preprint; peer-review acceptance not independently verified。
- 核读章节：3 Methods；4 Experiments；5 Discussion；Limitations。
- 对本项目的具体启发：若尝试leave-one-out修复，必须增加合法证据移除控制和真实6次生成成本；不在合并时伪称已有该防御。
- 结论限制：LOO对多投毒共同支持可能不敏感；成本k+1次，防御实验单seed且受唯一事实答案假设限制。
- 阅读文本SHA-256：`def35c8913486f599f2e094cc01c54ab1791f068915a7d1b8179b6d7d8465f7f`。

## P019

**NetInjectBench: Benchmarking Indirect Prompt Injection in Tool-Using Large Language Model Agents for Network Operations**

- 主来源：https://arxiv.org/html/2607.10490v2
- 首次公开：2026-07-11；本轮正文阅读版本：v2。
- 发表状态：arXiv preprint with Information Processing & Management journal header; publisher acceptance not independently verified。
- 核读章节：3 Methodology；4 Results；5 Discussion；7 Reproducibility；9 Conclusion。
- 对本项目的具体启发：安全和有效任务必须联合解释；模型/文档的声明不能充当可信来源和实际授权证据。
- 结论限制：v2采用合成单步工具场景和完整元数据假设；零观察不等于零风险，正文Journal标签未独立证实接受。
- 阅读文本SHA-256：`6bef450a5bd0fdfe1b033c81b7805059b06586102e27cd239faa73af98f4260e`。

## P020

**CrackedPDFs: A Controlled Benchmark for Hidden Prompt Injection in PDFs**

- 主来源：https://arxiv.org/html/2607.19396v2
- 首次公开：2026-07-03；本轮正文阅读版本：v2。
- 发表状态：arXiv preprint; peer-review acceptance not independently verified。
- 核读章节：3 Position；4 Methodology；5 Results；6 Conclusion。
- 对本项目的具体启发：保留来源组划分和配对合法变体；如做稀疏特征说明，只在训练数据解释高权重词，不能看测试再清理捷径。
- 结论限制：v2区分1946文档上的95.9%阈值分类与973对上的100%排序；受控PDF与任意OCR/适应攻击不同。
- 阅读文本SHA-256：`0a440e927b5aa72bc01c266930b2d580a12878699ea25b09fc694ddafcb61bd1`。

## P022

**Adaptive Evaluation of Out-of-Band Defenses Against Prompt Injection in LLM Agents**

- 主来源：https://arxiv.org/html/2606.26479v1
- 首次公开：2026-06-25；本轮正文阅读版本：v1。
- 发表状态：arXiv preprint; peer-review acceptance not independently verified。
- 核读章节：3 Threat model；6 Systematization；10 Adaptive protocol；11 Empirical evaluation；12 Limitations；14 Conclusion。
- 对本项目的具体启发：将反馈预算固定的自适应测试列为独立探索性跟进，记录模型弱能力与基础效用，不能仅靠低ASR判防御。
- 结论限制：本次Qwen7B、每套8任务、3重复和单个策略伪装攻击；不是任意系统级边界的鲁棒证明。
- 阅读文本SHA-256：`0c9db562d871beeedb84dcc96e74c60bd9eaae38d6e6a7daaea170fa3d7745b6`。

## P021

**MIRROR: Novelty-Constrained Memory-Guided MCTS Red-Teaming for Agentic RAG**

- 主来源：https://arxiv.org/html/2606.26793v1
- 首次公开：2026-06-25；本轮正文阅读版本：v1。
- 发表状态：arXiv preprint; peer-review acceptance not independently verified。
- 核读章节：III Method；IV Experiments；V Results；VI Discussion。
- 对本项目的具体启发：用规范化hash分开问题数、独特完整提示、策略行和重复攻击；去重应保持语义重复诊断的有限范围。
- 结论限制：精确新颖性不等于语义新颖性；B1改用户查询且B4不执行副作用，威胁边界与本项目不同。
- 阅读文本SHA-256：`9086a47d367610fb1a1c72f0115dbb5519c31cc297776865a358c9ec5d673ced`。

## P023

**Tracing Target Answers in Poisoned Retrieval Corpora via Token Influence Attribution**

- 主来源：https://arxiv.org/html/2606.25721v2
- 首次公开：2026-06-24；本轮正文阅读版本：v2。
- 发表状态：arXiv preprint; peer-review acceptance not independently verified。
- 核读章节：3 Preliminary；4 Method；5 Evaluation；6 Discussion；Limitations。
- 对本项目的具体启发：词/答案高频重复既可能来自投毒也可能来自合法共识；保留copy压力和不同检索深度的校准范围。
- 结论限制：TRACE强调QA与跨文档目标重复，单段或改写目标不在已验证范围；低攻击基率下误报警更重要。
- 阅读文本SHA-256：`f0f551d29e81dbae341e64f5cef1f66022e70c5017d18f2b5392586d8b056532`。

## P024

**Defending against Adaptive Prompt Injection Attacks via Reasoning-enabled Task Alignment**

- 主来源：https://arxiv.org/html/2606.15441v1
- 首次公开：2026-06-13；本轮正文阅读版本：v1。
- 发表状态：arXiv preprint; peer-review acceptance not independently verified。
- 核读章节：2 Background；3 Failure Modes；4 RETA Design；5 Evaluation；6 Discussion and Limitations；7 Conclusion。
- 对本项目的具体启发：若增加训练修复，先锁训练侧攻击策略覆盖，测旧/新攻击转移与正常效用，不靠单一胜出模板反复增强。
- 结论限制：自适应只在40个已脆弱案例而静态420；论文自己不比较改变执行架构的系统防御，不能无条件排名。
- 阅读文本SHA-256：`24f0d1c4fbfc6052c9792ba9b8674b3e5a8702d36183f60bceb5958ef804fca6`。

## P027

**Assessing Automated Prompt Injection Attacks in Agentic Environments**

- 主来源：https://arxiv.org/abs/2606.10525
- 首次公开：2026-06-09；本轮正文阅读版本：v1。
- 发表状态：preprint_unverified_venue。
- 核读章节：3 Threat Model；4 Problem Setting；5 Methodology；6 Experiments；7 Discussion；9 Conclusion。
- 对本项目的具体启发：自动攻击必须固定优化预算与所有尝试，并把正常任务能力与实际状态改变一起报告；先补正常/匹配控制而非增添相似攻击模板。
- 结论限制：只选AgentDojo80任务对，TAP搜索的LLM评分有校准噪声；白盒迁移只有一个源模型，低攻击率可能伴随低任务能力。
- 阅读文本SHA-256：`3c282dcab90175de52b57181f75c5ea9baad67bc7e34ef94c4113e4488146b02`。

## P026

**When Poison Fails After Retrieval: Revisiting Corpus Poisoning under Chunking and Reranking Pipelines**

- 主来源：https://arxiv.org/abs/2606.11265
- 首次公开：2026-06-09；本轮正文阅读版本：v1。
- 发表状态：preprint_unverified_venue。
- 核读章节：III Threat model；IV Methodology；V Experiment。
- 对本项目的具体启发：把攻击进入候选、经过分块/重排和最终回答分开记录；当前小子库实验不能冒称带chunker/reranker的全流程复现。
- 结论限制：作者主实验涉及多个分块和重排配置；其短答/目标字符串计数也有测量边界，不能与本项目别名精确匹配直接排行。
- 阅读文本SHA-256：`41b1601b21ea0234fe9ccd7cf13e5615c9ade8a362daa3ca58dc4e27d1dc710b`。

## P025

**Influence Factors on RAG Poisoning**

- 主来源：https://arxiv.org/html/2606.12469v1
- 首次公开：2026-06-09；本轮正文阅读版本：v1。
- 发表状态：arXiv preprint; peer-review acceptance not independently verified。
- 核读章节：3 Methodology；4 Results and Discussion。
- 对本项目的具体启发：优先补齐一个缺失配对控制，而不是扩大432式参数格；样本仍按题和来源计算，避免配置数制造精度。
- 结论限制：100对经过匹配的题和OLS网格系数是该设置内分析；不代表普遍因果效应或完整数据分布。
- 阅读文本SHA-256：`b0b2d487f047cfc9404054e8ddbf069f689342781cd4f86e34447d123bfdd617`。

## P028

**Document-Authored Control-Signal Impersonation: A Low-Cost Indirect Prompt Attack on RAG Safety Boundaries**

- 主来源：https://arxiv.org/abs/2606.09005
- 首次公开：2026-06-08；本轮正文阅读版本：v1。
- 发表状态：preprint_unverified_venue。
- 核读章节：III Threat Model and Definitions；IV Experimental Design；V Results；VI Cross-Model Interpretation；VII Failure Analysis；VIII Discussion and Security Implications；X Limitations and Validity Threats。
- 对本项目的具体启发：借鉴同模型、提示压力、模板、解码和结果规则的匹配基线原则；E2新增无过滤控制应复用相同完整输入。
- 结论限制：合成canary泄露不是现实账户入侵；仅六个模型设置，API接入层不等同统一供应商部署，源码文档伪造不应认作真实授权。
- 阅读文本SHA-256：`19b184de7341578644d2fab2180b9b862d640bb215c7cd5c6f850a1890de85a6`。

## P029

**Measuring Real-World Prompt Injection Attacks in LLM-based Resume Screening**

- 主来源：https://arxiv.org/abs/2605.28999
- 首次公开：2026-05-27；本轮正文阅读版本：v1。
- 发表状态：verified_peer_reviewed。
- 发表/报告题名：Measuring Real-World Prompt Injection Attacks in LLM-based Resume Screening
- 发表/报告场所：USENIX Security 2026
- 出版核对来源：https://www.usenix.org/conference/usenixsecurity26/presentation/zhang-mohan
- 核读章节：3 Detectors HCD/VDA；4 Datasets；5 Detection Evaluation；6 Measurement；7 Discussion and Limitations；8 Conclusion。
- 对本项目的具体启发：文本/文档属性检测与下游实际作用要分别验证；良性格式和装饰也能触发误报，benign标签不能靠外观判断。
- 结论限制：单平台简历样本；未评估真实筛选决策改变，100条双阴性人工审查不证明全量召回；不能把发现率称攻击成功率。
- 版本差异：Official publication metadata is separate from the stated arXiv reading title/version; publication-specific results are not silently substituted.
- 阅读文本SHA-256：`20c19c869d5b02abeccb35f21f2849ae2291859a3df0d4849de6f28652f8b638`。

## P031

**Cordon-MAS: Defending RAG against Knowledge Poisoning via Information-Flow Control**

- 主来源：https://arxiv.org/abs/2605.26754
- 首次公开：2026-05-26；本轮正文阅读版本：v1。
- 发表状态：preprint_unverified_venue。
- 核读章节：3 Cordon-MAS Architecture；4 Experimental Setup；5 Results；6 Discussion；Limitations。
- 对本项目的具体启发：安全结果同时给出回答覆盖率、条件正确率和全分母正确率；不把拒答后的高条件准确率当总体效用。
- 结论限制：多文档合谋能绕过内部一致性审核；主后端同源，3–4次LLM调用增加成本；其净正确率与拒答率显示效用代价。
- 阅读文本SHA-256：`f4c3ba2f563047502901a5a972f50081a5153c67e11b6a14022d183c90d62cac`。

## P030

**Prompt Injection Detection is Regime-Dependent: A Deployment-Aware Evaluation with Interpretable Structural Signals**

- 主来源：https://arxiv.org/abs/2605.26999
- 首次公开：2026-05-26；本轮正文阅读版本：v1。
- 发表状态：preprint_unverified_venue。
- 核读章节：3 Methodology；4 Experimental Setup；5 Experimental Results；6 Analysis；8 Conclusion。
- 对本项目的具体启发：保留word/char稀疏对照，区分排序指标和低FPR校准阈值，报告测试误报与工作点；不用最好F1格子替代部署判断。
- 结论限制：公开提示集合与有限重复划分；不同OOD分布表现不一致。结构增量依赖设定，不能声称一种组合普遍最优。
- 阅读文本SHA-256：`d0fb296b493903fa3135ed9a80a8428df1ed92a9884b80bcc452148d4b10160c`。

## P032

**LivePI: More Realistic Benchmarking of Agents Against Indirect Prompt Injection**

- 主来源：https://arxiv.org/abs/2605.17986
- 首次公开：2026-05-18；本轮正文阅读版本：v3。
- 发表状态：preprint_unverified_venue。
- 核读章节：3 Setup and Threat Model；4 Evaluation Setup and Results；5 Policy Defense and Results；6 Limitations and Discussion。
- 对本项目的具体启发：结果应与真实执行痕迹和同条件正常工作负载相联；保留渠道/配置分母，不用少数高风险案例外推部署发生率。
- 结论限制：169受控案例中仓库渠道仅4例；防御只在一个后端验证，缺完整重复抽样/区间；LLM评审仍有误差。
- 阅读文本SHA-256：`41923b6d34ba5bf24bac19300617abfb2ce7fd9b87dd030e30e6328ee1d1f872`。

## P034

**ASPI: Seeking Ambiguity Clarification Amplifies Prompt Injection Vulnerability in LLM Agents**

- 主来源：https://arxiv.org/abs/2605.17324
- 首次公开：2026-05-17；本轮正文阅读版本：v1。
- 发表状态：preprint_unverified_venue。
- 核读章节：3 Threat Model；4 Dataset Construction；5 Evaluation；6 Results；7 Discussion。
- 对本项目的具体启发：把混在一起的干预拆成匹配因子：本项目先用相同变换池的无过滤控制，区分输入变化与过滤策略的增量。
- 结论限制：单槽位、单轮合成歧义与特定ask_user接口；固定模型/领域，不涵盖适应性攻击；不能将其状态效应直接搬成RAG密度因果结论。
- 阅读文本SHA-256：`5750ca1599370fd90b9a9c85504b913ed223260358cf32337b9bab25fd3f0a03`。

## P033

**AI Agents May Always Fall for Prompt Injections**

- 主来源：https://arxiv.org/abs/2605.17634
- 首次公开：2026-05-17；本轮正文阅读版本：v1。
- 发表状态：preprint_unverified_venue。
- 核读章节：3 Limitations of Current Views；4 Contextual Integrity；5 CI-grounded Red-Teaming；6 Evaluation Directions。
- 对本项目的具体启发：保留表面相似但授权/来源不同的良性—恶意配对；源文里的标签只能作为数据，不能升级为控制权限。
- 结论限制：“总会失败”是非形式化的不可能性论证；规范与授权有主观和情境差异，有限案例不证明任意系统必然被攻破。
- 阅读文本SHA-256：`211d8d008237a8b52802e1e9c22f62b0772f95a63ce28c8933d9261de358cc88`。

## P035

**ARGUS: Defending LLM Agents Against Context-Aware Prompt Injection**

- 主来源：https://arxiv.org/abs/2605.03378
- 首次公开：2026-05-05；本轮正文阅读版本：v2。
- 发表状态：preprint_unverified_venue。
- 核读章节：2 Background and Threat Model；3 AgentLure；4 ARGUS；5 Evaluation including ablations/adaptive；6.2 Future Work。
- 对本项目的具体启发：区分证据来源和任务不变量；有风险时优先核对可用良性证据与恢复路径，而不是把整个载体一律删除当成成功。
- 结论限制：ARGUS不能证明载体真实性；伪造但内部一致的发票仍构成边界。当前项目未实现其运行时语义溯源层，不应以guard-only冒称复现。
- 阅读文本SHA-256：`9a1a34beb2da092dbf6071d518685ba7116500fd60f8fcaee9f3fdb12f2cb1ce`。

## P036

**CleanBase: Detecting Malicious Documents in RAG Knowledge Databases**

- 主来源：https://arxiv.org/abs/2605.00460
- 首次公开：2026-05-01；本轮正文阅读版本：v1。
- 发表状态：preprint_unverified_venue。
- 核读章节：3 Problem Formulation；4 Our CleanBase；5 Theoretical Analysis；6 Experiments；7 Discussion and Limitations。
- 对本项目的具体启发：完整CleanBase是全库kNN图、边剪枝和clique检测；本项目top20最大peer余弦只能称局部特征，必须保留单条/复制/合法冗余控制。
- 结论限制：强适应性攻击、少数低相似投毒仍是限制；理论界依赖分布/数量假设，不等于实测对所有攻击有保证。
- 阅读文本SHA-256：`0cd1b3904181d60bb31be71477d463607f8a6c86b4e1f0d439d772e21d1c74f1`。

## P038

**RAGShield: Detecting Numerical Claim Manipulation in Government RAG Systems**

- 主来源：https://arxiv.org/abs/2604.00387
- 首次公开：2026-04-01；本轮正文阅读版本：v2。
- 发表状态：preprint_unverified_venue。
- 核读章节：III Threat Model；IV The Embedding Blind Spot；V RAGShield Architecture；VI Implementation；VII Evaluation；VIII Discussion。
- 对本项目的具体启发：数值判分保留单位、实体和年份上下文，并把完整数值等价与substring分开；外部可信登记表核验是不同于相似度过滤的机制。
- 结论限制：领域规则和多数诚实来源假设；430项主表不能替代仅8题TinyLlama端到端演示，存在decimal格式失败，基线部分按文字重写。
- 阅读文本SHA-256：`8891b531d71f9f8406ec6cb36c80ca4a6bf3544dbf64357201639599d1292f4b`。

## P037

**AgentWatcher: A Rule-based Prompt Injection Monitor**

- 主来源：https://arxiv.org/abs/2604.01194
- 首次公开：2026-04-01；本轮正文阅读版本：v2。
- 发表状态：preprint_unverified_venue。
- 核读章节：3 Problem Definition；4 AgentWatcher；5 Evaluation；6 Discussion and Limitation；7 Conclusion；adaptive appendix noted。
- 对本项目的具体启发：把task/action条件、误报和计算成本一同报告；注意力定位/后续监控可作未来方向，不能用一个低成本线性头时间代表全系统。
- 结论限制：监控推理约10秒且长轨迹开销大；选择性触发改变覆盖面。注意力归因证据不自动等同一般因果机制。
- 阅读文本SHA-256：`6c76895ce9b4eac170046955c9622d0f3439df8f45576bdcbea85376cbb36f63`。

## P039

**PIDP-Attack: Combining Prompt Injection with Database Poisoning Attacks on Retrieval-Augmented Generation Systems**

- 主来源：https://arxiv.org/abs/2603.25164
- 首次公开：2026-03-26；本轮正文阅读版本：v1。
- 发表状态：preprint_unverified_venue。
- 核读章节：3 Design of PIDP-Attack；4 Experiment。
- 对本项目的具体启发：冻结威胁权限：本项目攻击者不可改用户query，所以不能把同时篡改query与corpus的更强方案当作同一实验升级。
- 结论限制：复合攻击拥有两种控制面，成功字符串不自动代表语义认可；缓存检索和多配置结果须分清，拒答也能降低ASR。
- 阅读文本SHA-256：`aac03fe6baf63b4ace42d92b8f39c01f48c28aed3ca6e3c37a02fd57058b7575`。

## P040

**Semantic Chameleon: Corpus-Dependent Poisoning Attacks and Defenses in RAG Systems**

- 主来源：https://arxiv.org/abs/2603.18034
- 首次公开：2026-03-10；本轮正文阅读版本：v1。
- 发表状态：preprint_unverified_venue。
- 核读章节：3. Threat Model and Attack Design；4. Detection Framework (Exploratory)；5. Experimental Methodology；6. Results；7. Discussion；9. Ethics and Responsible Disclosure。
- 对本项目的具体启发：跨域效果应单列，混合检索可作独立后续策略，先评估同时适应稀疏/稠密的攻击而非只挑对梯度攻击有利设置。
- 结论限制：两类语料、9/25/50等小样本和初步案例；隐蔽性、共检索与生成结果是不同终点，不能泛化安全保证。
- 阅读文本SHA-256：`d025c99725e49e2f87494f414cfc2c76e1188cd4496c0816f49f3fa656a6cb85`。

## P041

**Adversarial Hubness Detector: Detecting Hubness Poisoning in Retrieval-Augmented Generation Systems**

- 主来源：https://arxiv.org/abs/2602.22427
- 首次公开：2026-02-25；本轮正文阅读版本：v2。
- 发表状态：preprint_unverified_venue。
- 核读章节：III Methodology；IV Detection Algorithms；V Domain-Aware and Modality-Aware Detection；VI Retrieval and Reranking Integration；VII Evaluation；VIII Production Validation: Natural Hub Audit。
- 对本项目的具体启发：alert预算不是FPR；高hubness可能是正常权威文档，应按领域正常对照和query分布解释，不能一律删除高频证据。
- 结论限制：依赖代表性query采样；少量/自适应攻击和恶意比例高时性能受限，少量人工审查预算结果不是总体误报率。
- 阅读文本SHA-256：`c7743e1134804a5496e80c5c65fe5f6da80a7d62b60a9c3cdcbd2d96e75991ba`。

## P042

**AdapTools: Adaptive Tool-based Indirect Prompt Injection Attacks on Agentic LLMs**

- 主来源：https://arxiv.org/abs/2602.20720
- 首次公开：2026-02-24；本轮正文阅读版本：v1。
- 发表状态：preprint_unverified_venue。
- 核读章节：3 IPI-3K；4 Motivation；5 Methodology；6 Experiments including ablations；7 Conclusion。
- 对本项目的具体启发：工具任务的ASR与正常效用一并报告，优化迭代次数和成本明确；本项目短答实验不能借用代理行为的成功定义。
- 结论限制：有限模型、攻击迭代和场景；工具相关性/部分轨迹能力不同，未提供普遍鲁棒性或与当前小子库直接可比的分母。
- 阅读文本SHA-256：`a6874c60ddf9ce9b4248ec589a587bed26df1e767577b2983834b4fc8aab1dcd`。

## P043

**Confundo: Learning to Generate Robust Poison for Practical RAG Systems**

- 主来源：https://arxiv.org/abs/2602.06616
- 首次公开：2026-02-06；本轮正文阅读版本：v1。
- 发表状态：verified_peer_reviewed_published。
- 发表/报告题名：Confundo: Learning to Generate Robust Poison for Practical RAG Systems
- 发表/报告场所：35th USENIX Security Symposium (USENIX Security 2026)
- 出版核对来源：https://www.usenix.org/conference/usenixsecurity26/presentation/hu-haoyang
- 出版核对说明：Official USENIX paper page supplies matching title/authors and proceedings BibTeX for USENIX Security26, pages301–320.
- 出版核对边界：Publication status verified; this pass does not re-run experiments or independently establish result validity.
- 核读章节：3 Threat Model；4 Confundo: Overview；5 Fine-Tuning for Robust Poison Generation；6 Evaluation；7 Case Study: Protecting Web Content From Unauthorized Use in RAG。
- 对本项目的具体启发：将受控单段反事实明确与学习式黑盒投毒分开；分块、重排、query改写都会影响真实交付，不能仅靠高相关评分宣称完整攻击复现。
- 结论限制：用代理模型训练、有限任务和配置迁移；当前项目没有Confundo训练或作者攻击运行，不直接借用其ASR当本项目证据。
- 版本差异：Publication metadata was verified separately; the reviewed arXiv title/version and its version-specific results remain unchanged.
- 阅读文本SHA-256：`717057ff5bd23c4c4663c94608347fca9f0e132282db6cdce3cef4ad6aca5a35`。

## P044

**Addressing Corpus Knowledge Poisoning Attacks on RAG Using Sparse Attention**

- 主来源：https://arxiv.org/abs/2602.04711
- 首次公开：2026-02-04；本轮正文阅读版本：v3。
- 发表状态：preprint_unverified_venue。
- 核读章节：3 Preliminaries；4 RAG Using Sparse Document Attention；5 Experimental Setting；6 Results；Limitations。
- 对本项目的具体启发：保留跨文档注意力/隔离作为不同机制的未来基线；当前GGUF硬删除实验只评估外部选择层，不能冒称实现SDAG。
- 结论限制：须控制attention mask，主要英语闭集QA和较小开放模型；主in-set条件隔离生成，不能与本项目有检索交付的主表混算。
- 阅读文本SHA-256：`714136c78d74e21cc620ff0226e073913a83159df1f9fa00ec4bc7bf5405c048`。

## P045

**Hidden-in-Plain-Text: A Benchmark for Social-Web Indirect Prompt Injection in RAG**

- 主来源：https://arxiv.org/abs/2601.10923
- 首次公开：2026-01-16；本轮正文阅读版本：v2。
- 发表状态：verified_peer_reviewed_short_paper。
- 发表/报告题名：Hidden-in-Plain-Text: A Benchmark for Social-Web Indirect Prompt Injection in RAG
- 发表/报告场所：The Web Conference 2026, short-paper track
- 出版核对来源：https://www2026.thewebconf.org/accepted/short-papers.html
- 核读章节：3. OpenRAG-Soc: Benchmark and Harness；4. Metrics and Baselines；5. Results；6. Discussion。
- 对本项目的具体启发：载体/注入配对、检索排名和生成终点一起记录；清理与规范化也须检查合法资料召回和answerability。
- 结论限制：社交网页载体、固定提示与有限自适应范围；检索ASR/排名变化不同于端到端行为成功，未覆盖所有DOM/OCR变换。
- 版本差异：Official publication metadata is separate from the stated arXiv reading title/version; publication-specific results are not silently substituted.
- 阅读文本SHA-256：`62faa79272cfa08a23e65b61dd6c193a74d120fc74682da3760d49fc0f636635`。

## P046

**RAGPart & RAGMask: Retrieval-Stage Defenses Against Corpus Poisoning in Retrieval-Augmented Generation**

- 主来源：https://arxiv.org/abs/2512.24268
- 首次公开：2025-12-30；本轮正文阅读版本：v1。
- 发表状态：verified_workshop_presentation_nonarchival。
- 发表/报告题名：RAGPart & RAGMask: Retrieval-Stage Defenses Against Corpus Poisoning in Retrieval-Augmented Generation
- 发表/报告场所：AAAI2026 Workshop W41: New Frontiers in Information Retrieval
- 出版核对来源：https://frontier-ir-workshop.github.io/
- 出版核对说明：Official workshop schedule lists exact paper as Pankayaraj Pathmanathan contributed talk2 at14:15–14:30. Workshop organizer states contributions are non-archival. The separate OpenReview forum66iLCQVIoP is an ACL ARR January2026 submission, not acceptance evidence.
- 出版核对边界：Verify workshop presentation only; do not count as AAAI main-conference publication or archival proceedings article. Workshop states single-blind review and also welcomes already accepted/published work, so do not infer a specific review path for this talk.
- 核读章节：3 Method including RAGPart/RAGMask；4 Experiments；5 Results；7 Limitations。
- 对本项目的具体启发：分别报告恶意文档进入topk与正常gold检索成功；比较删文档、局部清理和恢复证据的代价，但新策略须另冻评估。
- 结论限制：ASR是检索到至少一条投毒，不是生成采纳；作者明确同主题错误事实可逃过纯检索防御，工作坊成果不等同AAAI主会论文。
- 版本差异：Publication metadata was verified separately; the reviewed arXiv title/version and its version-specific results remain unchanged. Non-archival workshop presentation only; not AAAI main-conference publication and not counted as a verified archival peer-reviewed paper.
- 阅读文本SHA-256：`c5e54e7212045508ecc99ce1ed6fcff1189c52fe6a6801800b0730de1a46502b`。

## P047

**Attention is All You Need to Defend Against Indirect Prompt Injection Attacks in LLMs**

- 主来源：https://arxiv.org/abs/2512.08417
- 首次公开：2025-12-09；本轮正文阅读版本：v3。
- 发表状态：verified_peer_reviewed。
- 发表/报告题名：Attention is All You Need to Defend Against Indirect Prompt Injection Attacks in LLMs
- 发表/报告场所：NDSS 2026
- 出版核对来源：https://www.ndss-symposium.org/ndss-paper/attention-is-all-you-need-to-defend-against-indirect-prompt-injection-attacks-in-llms/
- 核读章节：IV System model；V Token-level detector and sanitizer；VI Evaluation, transfer, adaptive attacks and ablations；VII Limitations。
- 对本项目的具体启发：局部定位/清理提供保留合法文本的思路，但必须测试清理后任务效用；不把token检测率当最终任务安全。
- 结论限制：依赖内部attention或shadow模型，训练/显存成本不适配当前CPU小项目；残留注入相关内容仍可能使语法等任务效用下降。
- 版本差异：Official publication metadata is separate from the stated arXiv reading title/version; publication-specific results are not silently substituted.
- 阅读文本SHA-256：`9bfdce881a491c10793b03652f0c38e71af4557eef16c3af875117ff00eb60c2`。

## P049

**Epistemic Bias Injection: Manipulating LLM Opinion via Selective Context Retrieval**

- 主来源：https://arxiv.org/abs/2512.00804
- 首次公开：2025-11-30；本轮正文阅读版本：v3。
- 发表状态：preprint_unverified_venue。
- 核读章节：III Threat model；IV EBI attack；V benchmark and experiments；VI BiasDef method and evaluation；VII Discussion。
- 对本项目的具体启发：增加开放意见任务会改变研究问题，不能与本项目短事实答案合并；保留多样合法观点，不能以高相关/一致性直接判恶意。
- 结论限制：极化轴依赖主题anchor和可分布假设；对事实共识强的题边界不同，BiasDef并非通用指令/事实投毒防御。
- 阅读文本SHA-256：`375953986c1a2c7c0086ae6092273d8be7943dc4393a05ca5573a6629b17751d`。

## P048

**Mitigating Indirect Prompt Injection via Instruction-Following Intent Analysis**

- 主来源：https://arxiv.org/abs/2512.00966
- 首次公开：2025-11-30；本轮正文阅读版本：v1。
- 发表状态：preprint_unverified_venue。
- 核读章节：3 IntentGuard and instruction-following intent analyzer；4 Evaluation setup, main results, adaptive attacks and ablations。
- 对本项目的具体启发：区分看似指令与模型实际意图/行为；用来源、正常utility与误报一起评估，不能把所有指令性良性文本直接拦掉。
- 结论限制：意图分析是模型推断的近似，并不读取一个完美“意图真值”；仅两开放reasoning模型和两个基准，零观测误报不保证零总体误报。
- 阅读文本SHA-256：`a3a4175cfa14fc583714e2aa4ff614358f2575d30908c41a7593d47033c96454`。

## P050

**BrowseSafe: Understanding and Preventing Prompt Injection Within AI Browser Agents**

- 主来源：https://arxiv.org/abs/2511.20597
- 首次公开：2025-11-25；本轮正文阅读版本：v2。
- 发表状态：verified_peer_reviewed_conference_accepted。
- 发表/报告题名：BrowseSafe: Understanding and Detecting Prompt Injection Within AI Browser Agents
- 发表/报告场所：Conference on Language Modeling (COLM2026)
- 出版核对来源：https://colm.cc/Conferences/2026/AcceptedPapers
- 出版核对说明：Official COLM2026 accepted-papers list names exact final title and all6 matching authors; poster132, session5. Official old colmweb.org redirects to colm.cc. Final title changes Preventing to Detecting; DOI/arXiv identity retained as the same study.
- 出版核对边界：Acceptance verified from official conference list. OpenReview live document pages remain challenged, so no individual decision text was retrieved; the accepted list supplies independent confirmation.
- 核读章节：III BrowseSafe-Bench construction；IV BrowseSafe architecture and threshold tuning；V Model, latency and generalization case studies。
- 对本项目的具体启发：保持正文全文/截断审计，加入表面似攻击的hard negatives；按未见URL、攻击类型、注入位置分别审查泛化。
- 结论限制：HTML检测基准不是完整代理安全认证；新版本保留策略位置留出F1下降，非文本输入不在范围，OR聚合仍可能放大长文误报。
- 版本差异：Publication metadata was verified separately; the reviewed arXiv title/version and its version-specific results remain unchanged. The formal publication title differs from the reading title shown above.
- 阅读文本SHA-256：`b46cdbe50193918f1f45f52848d8ad13841569899effb6a1cb6b4aa0d9beed6f`。

## P051

**Rescuing the Unpoisoned: Efficient Defense against Knowledge Corruption Attacks on RAG Systems**

- 主来源：https://arxiv.org/abs/2511.01268
- 首次公开：2025-11-03；本轮正文阅读版本：v1。
- 发表状态：verified_official_conference_program。
- 发表/报告题名：Rescuing the Unpoisoned: Efficient Defense against Knowledge Corruption Attacks on RAG Systems
- 发表/报告场所：ACSAC 2025
- 出版核对来源：https://www.acsac.org/2025/program/final/s73.html
- 核读章节：IV RAGDefender System；VI-A Experimental Setup；VII Discussion and Limitations。
- 对本项目的具体启发：分组和识别是两个阶段，聚类紧密性是构造依赖信号；保留单条污染和合法重复对照，不能把四信号头称为RAGDefender复现。
- 结论限制：以答案包含参考/攻击字符串计分；聚类误分与合法稀疏支持仍可能造成效用损失，跨模型表不能外推到本项目。
- 版本差异：Official publication metadata is separate from the stated arXiv reading title/version; publication-specific results are not silently substituted.
- 阅读文本SHA-256：`bc34fb400c37a91b25e34579837879ee9c76703b363dd783af9bc4225e851115`。

## P052

**Secure Retrieval-Augmented Generation against Poisoning Attacks**

- 主来源：https://arxiv.org/abs/2510.25025
- 首次公开：2025-10-28；本轮正文阅读版本：v2。
- 发表状态：author_reported_acceptance_only。
- 发表/报告场所：IEEE BigData 2025
- 核读章节：IV Our RAGuard；V-A Experimental Setup；VI Discussion。
- 对本项目的具体启发：扩大候选池再过滤的收益须与固定检索/上下文预算区分；本项目现有20候选和回填规则应保持固定并报告。
- 结论限制：文本相似和困惑度不验证事实；100题闭合答案及特定攻击构造限制外推。DACC是准确率，不能照抄成precision。
- 阅读文本SHA-256：`0f607bf5b10300ebdcca8e4dddb372052796beff38548c4f6adec7c0f787cb08`。

## P053

**Defending Against Prompt Injection with DataFilter**

- 主来源：https://arxiv.org/abs/2510.19207
- 首次公开：2025-10-22；本轮正文阅读版本：v2。
- 发表状态：verified_official_conference_program。
- 发表/报告题名：Defending Against Prompt Injection with DataFilter
- 发表/报告场所：IEEE SaTML 2026
- 出版核对来源：https://satml.org/2026/program/
- 核读章节：IV DataFilter；IV-C The SFT Dataset to Train the DataFilter；V-D Results Overview；VI Conclusion and Discussions。
- 对本项目的具体启发：新增低成本修复时应优先保存有用证据，而不是把整段删除等同防御成功；匹配无过滤机制条件后再判断效用损失。
- 结论限制：该方法依赖训练过的8B过滤器、用户任务上下文和选择性删除；并非当前公开DeBERTa段落分数。其跨基准结果不能移植。
- 版本差异：Official publication metadata is separate from the stated arXiv reading title/version; publication-specific results are not silently substituted.
- 阅读文本SHA-256：`3d294e30141017f4f687c289827b94bd7bd2cee0dec629d271ea1b6793c71f0c`。

## P054

**Breaking and Fixing Defenses Against Control-Flow Hijacking in Multi-Agent Systems**

- 主来源：https://arxiv.org/abs/2510.17276
- 首次公开：2025-10-20；本轮正文阅读版本：v2。
- 发表状态：preprint_publication_not_independently_verified。
- 核读章节：4 Enforcing contextual flow with ControlValve；Limitations paragraph；5 Experimental setup；6.5 benign performance。
- 对本项目的具体启发：检测层级需要随权限明确：控制流/工具权限防护与段落污染过滤是不同任务，评测应分别定义允许行为和任务效用。
- 结论限制：生成的控制流图和规则可能过松或过紧；仅测试一个主要MAS配置，延迟和自动规划错误不可忽略。
- 阅读文本SHA-256：`e1de3f08c4d4ffdce63edfd55a2ba52c35d2cb06a4e0101c8b0c5d6348563c27`。

## P055

**PromptLocate: Localizing Prompt Injection Attacks**

- 主来源：https://arxiv.org/abs/2510.12252
- 首次公开：2025-10-14；本轮正文阅读版本：v2。
- 发表状态：verified_official_accepted_papers。
- 发表/报告题名：PromptLocate: Localizing Prompt Injection Attacks
- 发表/报告场所：IEEE Symposium on Security and Privacy 2026
- 出版核对来源：https://sp2026.ieee-security.org/accepted-papers.html
- 核读章节：IV Our PromptLocate；V-A Experimental Setup；VII Discussion and Limitations。
- 对本项目的具体启发：后续修复可按污染片段定位保留正常信息；现阶段必须保留原始全文和移除位置，不能只看单个文档二分类。
- 结论限制：定位依赖训练检测oracle和分段；对一个孤立片段检测不足以覆盖分散注入。当地小模型效用不足时原文改用强后端。
- 版本差异：Official publication metadata is separate from the stated arXiv reading title/version; publication-specific results are not silently substituted.
- 阅读文本SHA-256：`26b20a3b5d7cefd0073877f396c25e7b1c9c5099fe977d0b6f4e32d2ccc2c4ce`。

## P056

**Steering Over-refusals Towards Safety in Retrieval Augmented Generation**

- 主来源：https://arxiv.org/abs/2510.10452
- 首次公开：2025-10-12；本轮正文阅读版本：v1。
- 发表状态：preprint_publication_not_independently_verified。
- 核读章节：4 Method；5 Experimental Setup；6 Results；7 Discussion。
- 对本项目的具体启发：将拒答与目标字符串成功分开；评估正常问答、覆盖率与回答错误，而不是把拒答当作安全效果。
- 结论限制：该预印本的steering配置从所称test的验证切片选择，尚有线性可分和域迁移假设；不能借用其低拒答率宣称本模型同样有效。
- 阅读文本SHA-256：`4c17ee1afdb937e9c4931d4bb1ff323c483a6f52ea47a627c080e3cdea03b7d5`。

## P057

**ADMIT: Few-shot Knowledge Poisoning Attacks on RAG-based Fact Checking**

- 主来源：https://arxiv.org/abs/2510.13842
- 首次公开：2025-10-11；本轮正文阅读版本：v2。
- 发表状态：preprint_publication_not_independently_verified。
- 核读章节：3 Proposed Attack；4 Experiments；4.2 Main Results；7 Limitation。
- 对本项目的具体启发：区分真正答案/判决翻转与NEI或拒答；用少量插入检验事实污染，保留完整固定样本和清楚的clean-baseline条件。
- 结论限制：主要为逐claim、proxy引导的事实核查攻击；并非新问答目标替换的完整复现，来源元数据与多claim共同注入未完全覆盖。
- 阅读文本SHA-256：`2623b213b62077272a9fe3190a2e1a6fcc8f219f3a324cdb17d72c908483a6f9`。

## P058

**The Attacker Moves Second: Stronger Adaptive Attacks Bypass Defenses Against LLM Jailbreaks and Prompt Injections**

- 主来源：https://arxiv.org/abs/2510.09023
- 首次公开：2025-10-10；本轮正文阅读版本：v1。
- 发表状态：preprint_publication_not_independently_verified。
- 核读章节：4 General Attack Methods；5 Experiments；6 Lesson and Discussion。
- 对本项目的具体启发：任何新自适应测试都应在运行前固定反馈、查询和token预算并保留全部尝试；固定留出模板不构成自适应安全证据。
- 结论限制：十二防御的原始任务、预算和基准不统一，论文明确反对把它们当跨方法排行榜；人工验证仍是被测试范围内的证据。
- 阅读文本SHA-256：`81aa0fdcf99fb5d4312c998ca462b221fe6998b0a8b384a6b08b327790d82822`。

## P060

**RL Is a Hammer and LLMs Are Nails: A Simple Reinforcement Learning Recipe for Strong Prompt Injection**

- 主来源：https://arxiv.org/abs/2510.04885
- 首次公开：2025-10-06；本轮正文阅读版本：v1。
- 发表状态：preprint_publication_not_independently_verified。
- 核读章节：3 Effective Automated Prompt Injections through RL；4 Experiments；6 Conclusion and Limitation。
- 对本项目的具体启发：攻击训练/搜索成本、目标查询次数和迁移边界需单列；维持固定冻结策略，不因小静态测试低成功率声称鲁棒。
- 结论限制：RL训练依赖大量目标反馈与H200资源；同目标训练成功率和跨目标迁移不同，训练100/验证100/测试100受选定任务限制。
- 阅读文本SHA-256：`e0bcc8d23c5317a19c9b6cdf9bde7a210d45ce6a313f763152c12633dd7313ef`。

## P059

**Indirect Prompt Injections: Are Firewalls All You Need, or Stronger Benchmarks?**

- 主来源：https://arxiv.org/abs/2510.05244
- 首次公开：2025-10-06；本轮正文阅读版本：v2。
- 发表状态：preprint_publication_not_independently_verified。
- 核读章节：3 Method；4 Experiments；5 Results；7 Assessment of Current Benchmarks。
- 对本项目的具体启发：补齐E2同条件无过滤输出是最高优先级；同时报告正常效用、受攻击效用与攻击结果，检查是否缺少任务所需证据。
- 结论限制：替换任务关键内容会让任务本身不可解；有些对照未能复现而引用原数，不能当相同环境公平排名。
- 阅读文本SHA-256：`d4847d59fa69e6dee8f5de75367c33c9a9135a1eb9b82946f1bb8c5364dfa001`。

## P061

**WAInjectBench: Benchmarking Prompt Injection Detections for Web Agents**

- 主来源：https://arxiv.org/abs/2510.01354
- 首次公开：2025-10-01；本轮正文阅读版本：v2。
- 发表状态：preprint_publication_not_independently_verified。
- 核读章节：4. Data Collection；5. Detecting Prompt Injection Attacks；6. Benchmarking Results；7. Discussion and Limitations。
- 对本项目的具体启发：已有段落误报应再汇总为同题任一误删/关键支持丢失，实际按qid聚合；不能由单段FPR假定独立推算整题安全。
- 结论限制：step级静态检测未覆盖完整交互、成本或自适应攻击；网页/问题含多个相关片段时整体误报可明显高于sample FPR。
- 阅读文本SHA-256：`af8e43b07f6f1844576654ca27472593d5d4c49b952713dcb592f4382e64a00c`。

## P062

**ReliabilityRAG: Effective and Provably Robust Defense for RAG-based Web-Search**

- 主来源：https://arxiv.org/abs/2509.23519
- 首次公开：2025-09-27；本轮正文阅读版本：v2。
- 发表状态：verified_official_proceedings。
- 发表/报告题名：ReliabilityRAG: Effective and Provably Robust Defense for RAG-based Web-Search
- 发表/报告场所：NeurIPS 2025
- 出版核对来源：https://proceedings.neurips.cc/paper_files/paper/2025/hash/41457d56a2fdd20b4c072190290a549b-Abstract-Conference.html
- 核读章节：3 Ordinal-Reliability Setting；5 Evaluation；D.3 Limitations and Future Work。
- 对本项目的具体启发：证据一致性图和可靠排名提供另一类基线；如只做精确去重或soft demotion，应明确为本项目诊断，不称复现MIS认证方法。
- 结论限制：保证依赖可靠性顺序、NLI矛盾检测和一致多数；LLM判卷、隔离生成成本及域外假设限制实用认证。
- 版本差异：Official publication metadata is separate from the stated arXiv reading title/version; publication-specific results are not silently substituted.
- 阅读文本SHA-256：`849892f8c9a288774004383d7f9e999f4089c511e28250dff48ea2af2b8772e7`。

## P063

**DisarmRAG: Stealthy Retriever-Centric Poisoning to Disable Self-Correction in Retrieval-Augmented Generation (Extended Version)**

- 主来源：https://arxiv.org/abs/2508.20083
- 首次公开：2025-08-27；本轮正文阅读版本：v2。
- 发表状态：verified_peer_reviewed_accepted_forthcoming。
- 发表/报告题名：DisarmRAG: Stealthy Retriever Poisoning to Disable Self-Correction in Retrieval-Augmented Generation
- 发表/报告场所：ACM SIGSAC Conference on Computer and Communications Security (CCS2026)
- 出版核对来源：https://www.sigsac.org/ccs/CCS2026/program/accepted-papers.html
- 出版核对说明：Official ACM SIGSAC CCS2026 accepted-papers list includes matching method, title and all5 authors. Conference scheduled Nov15–19,2026; as-ofOct20 classify accepted/forthcoming. ArXiv extended version gives DOI10.1145/3830454.3832598, but ACM DOI page could not be opened in this tool.
- 出版核对边界：Accepted status independently verified; do not claim conference has already occurred or that publisher record was accessed.
- 核读章节：5. Threat Model；6. Design；7. Evaluation Setup and Configuration；11. Conclusion。
- 对本项目的具体启发：将检索器供应链投毒单独归类；现有威胁模型不许修改权重，因此不扩充成已经覆盖此攻击的主实验。
- 结论限制：最新扩展版明确需要可编辑/再分发检索器；与仅能向语料追加文档的对手权限不同，短答和模型编辑范围限制外推。
- 版本差异：Publication metadata was verified separately; the reviewed arXiv title/version and its version-specific results remain unchanged. The formal publication title differs from the reading title shown above.
- 阅读文本SHA-256：`5b78fa613e3a6c29654578dd42983b0ceb10d68c3633cca84ba720773c68540b`。

## P064

**Defending Against Knowledge Poisoning Attacks During Retrieval-Augmented Generation**

- 主来源：https://arxiv.org/abs/2508.02835
- 首次公开：2025-08-04；本轮正文阅读版本：v2。
- 发表状态：preprint_publication_not_independently_verified。
- 核读章节：III Methodology；IV Experiments；V Experimental Results。
- 对本项目的具体启发：统计相关性过滤必须报告正常答案损失和训练来源，查询/生成中间词重合不应解释为事实可信性。
- 结论限制：SLM先生成中间答案增加成本；100目标和同题生成攻击/训练构造可能提供捷径，不能等同来源隔离泛化。
- 阅读文本SHA-256：`3a03628b20bd47c413386b99875726901ff7934566d19651bcdfe4eccd0e6286`。

## P065

**PromptArmor: Simple yet Effective Prompt Injection Defenses**

- 主来源：https://arxiv.org/abs/2507.15219
- 首次公开：2025-07-21；本轮正文阅读版本：v1。
- 发表状态：preprint_publication_not_independently_verified。
- 核读章节：3 PromptArmor；4 Evaluation；4.5 Adaptive Attacks。
- 对本项目的具体启发：区分段落概率过滤与任务条件的文本清理；保留任务上下文、数据改动和utility-under-attack结果才有意义。
- 结论限制：强guardrail LLM和fuzzy删除属于另一个系统；自适应仅限所测fuzzer/top5模板，公开指标不能当普遍安全保证。
- 阅读文本SHA-256：`1ea9700cce2d3864420dfbc5eae0a83cd55e012a6b1d88e0efa072fac4050b8a`。

## P066

**Defending Against Prompt Injection With a Few DefensiveTokens**

- 主来源：https://arxiv.org/abs/2507.07974
- 首次公开：2025-07-10；本轮正文阅读版本：v2。
- 发表状态：preprint_publication_not_independently_verified。
- 核读章节：3.3. Methodology；4.1. Setup；4.4. Analyzing the Utility-Security Trade-Off。
- 对本项目的具体启发：安全与效用应在相同任务上成对报告；新增5个token并不意味着训练成本低或当前模型可直接使用。
- 结论限制：优化需全模型反传及四张A100；模型专用tokenembedding和边界标记不适用于没有相同训练的冻结3B。
- 阅读文本SHA-256：`00d47ad00d999426417b9b17369867dac20747f6fbb6118ec05ba9107257f174`。

## P067

**Meta-SecAlign: Training LLMs against Prompt Injection for Robust Agents**

- 主来源：https://arxiv.org/abs/2507.02735
- 首次公开：2025-07-03；本轮正文阅读版本：v4。
- 发表状态：preprint_publication_not_independently_verified。
- 核读章节：3 Meta-SecAlign；4 Experiments；5.2 Limitations。
- 对本项目的具体启发：加入合法指令、位置变化和空输出检查可发现捷径；避免把模型因不会任务而产生的低攻击率当作神经增量。
- 结论限制：最新v4明确不能修复基模本来不会的任务，依赖已知信任边界且不能抵抗强自适应攻击；多消息协同未全面评估。
- 阅读文本SHA-256：`ad965e9cc9ae3521c97d95ba45a9c045c295f2cea0640c8e3ba149e79a98f666`。

## P068

**Through the Stealth Lens: Attention-Aware Defenses Against Poisoning in RAG**

- 主来源：https://arxiv.org/abs/2506.04390
- 首次公开：2025-06-04；本轮正文阅读版本：v2。
- 发表状态：verified_peer_reviewed_published。
- 发表/报告题名：Through the Stealth Lens: Attention-Aware Defenses Against Poisoning in RAG
- 发表/报告场所：43rd International Conference on Machine Learning (ICML2026), PMLR306
- 出版核对来源：https://proceedings.mlr.press/v306/choudhary26b.html
- 出版核对说明：Official PMLR paper page gives matching final title/authors, ICML2026 proceedings, volume306, pages20543–20565. Earlier version subtitle Rethinking Attacks and Defenses in RAG is the same arXiv2506.04390 study.
- 出版核对边界：Fresh confirmation of prior verified status, not a new paper or an additional count.
- 核读章节：4 Attention Variance Breaks Stealth；5 Evaluation；6 Limitations。
- 对本项目的具体启发：保留唯一正确支持段和正常冗余对照，检验异常检测是否误伤真实证据；注意attention只能是代理而非因果归因。
- 结论限制：少数正确文档也会吸引高注意并被误删；一致多数、QA特性及可访问内部状态是其边界，自适应可部分压低信号。
- 版本差异：Publication metadata was verified separately; the reviewed arXiv title/version and its version-specific results remain unchanged.
- 阅读文本SHA-256：`515efac2198812bad6613bccfc379621e34dd02c04e6c0b264b2e9bf9cee83ff`。

## P069

**CPA-RAG:Covert Poisoning Attacks on Retrieval-Augmented Generation in Large Language Models**

- 主来源：https://arxiv.org/abs/2505.19864
- 首次公开：2025-05-26；本轮正文阅读版本：v1。
- 发表状态：preprint_publication_not_independently_verified。
- 核读章节：4 Design of CPA-RAG；5 Experimental Comparisons；6 Defenses。
- 对本项目的具体启发：完整记录攻击检索交付与生成目标两阶段；不同文本优化器/预算不能因为都称poison而合并为同一实验。
- 结论限制：依赖多模型生成和retriever评价，默认五条插入；表面自然或低困惑度不证明内容合法，当前单段替换不是其复现。
- 阅读文本SHA-256：`56e103c236602f59e4e7ef43a56f7bfb3ed39cbbd780f13fde9eba68f4d410de`。

## P070

**Benchmarking Poisoning Attacks against Retrieval-Augmented Generation**

- 主来源：https://arxiv.org/abs/2505.18543
- 首次公开：2025-05-24；本轮正文阅读版本：v1。
- 发表状态：preprint_publication_not_independently_verified。
- 核读章节：3 Threat Model；5 Evaluation；7 Conclusion, Limitations, and Future Work。
- 对本项目的具体启发：把定向错误、拒答型DoS和条件触发DoS分开，保留正常任务表现；固定100题并在声明的检索库上验证交付。
- 结论限制：扩展证据库、选择clean时不输出攻击目标和LLM判卷改变分母/难度；15数据变体不是15个独立来源或相同难度。
- 阅读文本SHA-256：`38baf6fc81ea72c32e10697e514581be48d435ebe431b088cc5f9f0c12b1c4cc`。

## P071

**A Critical Evaluation of Defenses against Prompt Injection Attacks**

- 主来源：https://arxiv.org/abs/2505.18333
- 首次公开：2025-05-23；本轮正文阅读版本：v1。
- 发表状态：preprint_publication_not_independently_verified。
- 核读章节：4 Evaluation Methodology；5 Case Studies；6 Conclusion。
- 对本项目的具体启发：必须测绝对任务效用及对应检测FPR/FNR；相对win-rate或单一目标Hacked不能证明正常能力和广泛防御。
- 结论限制：本文主要反例来自选定任务、模型和攻击，不能据此断言所有防御失败；主项目也应保留直接匹配的神经增量对照。
- 阅读文本SHA-256：`bcdcf446953360936938b3bb8450dc4e552dfd0115bd638ba0616a05a090df55`。

## P072

**Uncovering Competing Poisoning Attacks in Retrieval-Augmented Generation**

- 主来源：https://arxiv.org/abs/2505.12574
- 首次公开：2025-05-18；本轮正文阅读版本：v5。
- 发表状态：author_reported_acceptance_only。
- 发表/报告场所：KDD 2026
- 核读章节：2. Threat Model；3. Evaluating from a Competitive Perspective；4.1. Experimental Setup；5. Discussion。
- 对本项目的具体启发：把单目标独立插入与多攻击者共享语料隔开；未来共享库实验要测交叉检索与竞争，不能将逐题600段排序称全局稳健。
- 结论限制：竞争系数来自模拟与特定攻击组合，单攻击ASR不等于绝对上界的普遍定理；不能从当前单对手样本推算该系数。
- 阅读文本SHA-256：`7f4f7cf1a69515861f2c55da74e5c15dc8151d0041af85a2d901151c62353905`。

## P073

**One Shot Dominance: Knowledge Poisoning Attack on Retrieval-Augmented Generation Systems**

- 主来源：https://arxiv.org/abs/2505.11548
- 首次公开：2025-05-15；本轮正文阅读版本：v4。
- 发表状态：verified_peer_reviewed_published。
- 发表/报告题名：One Shot Dominance: Knowledge Poisoning Attack on Retrieval-Augmented Generation Systems
- 发表/报告场所：Findings of the Association for Computational Linguistics: EMNLP2025
- 出版核对来源：https://aclanthology.org/2025.findings-emnlp.1023/
- 出版核对说明：Official ACL Anthology record names exact title/all8 authors and AuthChain method in abstract, with Findings EMNLP2025 proceedings metadata.
- 出版核对边界：Classify Findings EMNLP, not main EMNLP proceedings. One publication/study only; AuthChain is a method name, not an additional paper.
- 核读章节：3 Methodology；4 Experimental Setup；6 Discussion。
- 对本项目的具体启发：自然单文档污染可兼有检索与权威性线索；只删除冗余authority模板不会意味着覆盖此多阶段攻击，保持受控构造标签。
- 结论限制：复用PoisonedRAG100题和多agent生成；ASR由具体提示/预算决定，原文模型开源闭源分类有明显倒置，不照搬。
- 版本差异：Publication metadata was verified separately; the reviewed arXiv title/version and its version-specific results remain unchanged.
- 阅读文本SHA-256：`5d81e91622c569b31484899029ab3561cc77dbc6d31b5b6ea3e707ca8bb8f433`。

## P074

**POISONCRAFT: Practical Poisoning of Retrieval-Augmented Generation for Large Language Models**

- 主来源：https://arxiv.org/abs/2505.06579
- 首次公开：2025-05-10；本轮正文阅读版本：v1。
- 发表状态：preprint_publication_not_independently_verified。
- 核读章节：IV Method；V Experiments；VIII Conclusion。
- 对本项目的具体启发：区分事实错误与恶意链接推荐等输出污染；即使答案正确也可能存在另一个攻击目标，因此保留多维结果字段。
- 结论限制：该攻击有white-box retriever和shadow查询分布、全库注入预算；当前文章子库及固定目标不支持其query-agnostic主张。
- 阅读文本SHA-256：`c5647392f0503566b8ca5481f53ed51931d6ddec5cdfb0deb1837323a0190cc5`。

## P075

**Defending against Indirect Prompt Injection by Instruction Detection**

- 主来源：https://arxiv.org/abs/2505.06311
- 首次公开：2025-05-08；本轮正文阅读版本：v2。
- 发表状态：verified_official_proceedings。
- 发表/报告题名：Defending against Indirect Prompt Injection by Instruction Detection
- 发表/报告场所：Findings of EMNLP 2025
- 出版核对来源：https://aclanthology.org/2025.findings-emnlp.1060/
- 核读章节：3 Methodology；4 Experiment；4.4 Overall Results；6 Limitation。
- 对本项目的具体启发：前向DeBERTa分数不能标成使用LLM梯度/隐藏状态的InstructDetector；报告计算成本与误删有用内容的实际结果。
- 结论限制：LLM前向加反向计算较重，二分类整体删除可能丢失有用数据；论文也提出分段保存内容，但不保证所有攻击/域覆盖。
- 版本差异：Official publication metadata is separate from the stated arXiv reading title/version; publication-specific results are not silently substituted.
- 阅读文本SHA-256：`bac4d0ab03e9fb3dffcdfc080f95ff69588298c4f57be76d43541dcc0945b82f`。

## P076

**Traceback of Poisoning Attacks to Retrieval-Augmented Generation**

- 主来源：https://arxiv.org/abs/2504.21668
- 首次公开：2025-04-30；本轮正文阅读版本：v2。
- 发表状态：official_publisher_record_verified。
- 发表/报告题名：Traceback of Poisoning Attacks to Retrieval-Augmented Generation
- 发表/报告场所：Proceedings of the ACM on Web Conference 2025
- 出版核对来源：https://dl.acm.org/doi/10.1145/3696410.3714756
- 出版核对说明：Official ACM publisher search record and publisher-deposited Crossref metadata
- 核读章节：4 RAGForensics；5 Experiments；6 Discussion。
- 对本项目的具体启发：Add a wrong-answer diagnostic separate from attack success; do not treat every retained incorrect answer as an injection.
- 结论限制：Experiments condition on successful attack feedback; traceback precision on that selected set is not unconditional prevention.
- 版本差异：Publication metadata checked only; prior arXiv reading version is preserved separately. Do not transfer version-specific results without comparison.
- 阅读文本SHA-256：`b874160426f918414e4caefbea46b61f2a448cdbb2ce1b4c939cfdf19774f79d`。

## P077

**Progent: Securing AI Agents with Privilege Control**

- 主来源：https://arxiv.org/abs/2504.11703
- 首次公开：2025-04-16；本轮正文阅读版本：v1。
- 发表状态：preprint_publication_unverified。
- 核读章节：3 Threat model；4 Policy language and enforcement；5 Three use cases and ablations；6 Discussion。
- 较新版本补充核读：v3；具体章节与哈希见逐篇来源JSON。
- 对本项目的具体启发：Preserve the trusted-user/external-content boundary in the threat model; do not claim a text filter reproduces least-privilege enforcement.
- 结论限制：Guarantee covers allowed tool-call sets, not truth of textual answers; ambiguous initial policies and erroneous approvals remain risks.
- 阅读文本SHA-256：`b981cb909d5618e866cf29414b135705e57a6f23faa79593fcbfea9e81f8e278`。

## P078

**Practical Poisoning Attacks against Retrieval-Augmented Generation**

- 主来源：https://arxiv.org/abs/2504.03957
- 首次公开：2025-04-04；本轮正文阅读版本：v2。
- 发表状态：official_publisher_record_verified。
- 发表/报告题名：Practical Poisoning Attacks against Retrieval-Augmented Generation
- 发表/报告场所：Proceedings of the 31st ACM Symposium on Access Control Models and Technologies
- 出版核对来源：https://dl.acm.org/doi/10.1145/3750555.3811900
- 出版核对说明：Official ACM publisher search record and publisher-deposited Crossref metadata
- 核读章节：3 Threat model；4 Our Attacks；5 Experiments；7 Discussion。
- 对本项目的具体启发：Keep single- and five-document controls with actual retrieval validation; label our fixed counterfactual as an adapted construction, not full CorruptRAG.
- 结论限制：Closed-ended targeted queries and local attack construction restrict generalization; published numeric ASR is not comparable across our corpus/model.
- 版本差异：Publication metadata checked only; prior arXiv reading version is preserved separately. Do not transfer version-specific results without comparison.
- 阅读文本SHA-256：`4b24c1cf0fc3e48ef40e521aa44b5359882900585eef7a79ed7f8e6b1f800b00`。

## P079

**Defeating Prompt Injections by Design**

- 主来源：https://arxiv.org/abs/2503.18813
- 首次公开：2025-03-24；本轮正文阅读版本：v1。
- 发表状态：official_conference_accepted_program_verified。
- 发表/报告题名：Defeating Prompt Injections by Design
- 发表/报告场所：4th IEEE Conference on Secure and Trustworthy Machine Learning (SaTML2026)
- 出版核对来源：https://satml.org/2026/accepted-papers/
- 出版核对说明：Official IEEE SaTML2026 accepted-paper list and conference program match title and all10authors; independent of author/arXiv declarations
- 核读章节：3 Threat model and explicit non-goals；4 CaMeL design；5 Utility/security evaluation；8 Discussion and limitations。
- 较新版本补充核读：v2；具体章节与哈希见逐篇来源JSON。
- 对本项目的具体启发：Keep tool-flow guarantees separate from textual factual-poison resistance; exact context and answer provenance can be retained without adopting an agent architecture.
- 结论限制：Explicitly excludes text-to-text corruption with no control/data-flow consequence; capability implementation, side channels and user declassification have costs.
- 版本差异：Official conference program abstract stillreports67%AgentDojo utility, whereas arXivv2hasnewermodels/differentutility. Venue acceptance is verified; do not treat the program abstract as a version-independent result or invent a DOI/page range.
- 阅读文本SHA-256：`b4305c948c746199088af7f9cde0f179bcc859a27b2833c2f5d5970c1f15dbff`。

## P080

**The RAG Paradox: A Black-Box Attack Exploiting Unintentional Vulnerabilities in Retrieval-Augmented Generation Systems**

- 主来源：https://arxiv.org/abs/2502.20995
- 首次公开：2025-02-28；本轮正文阅读版本：v3。
- 发表状态：official_publisher_record_verified。
- 发表/报告题名：The RAG Paradox: A Black-Box Attack Exploiting Unintentional Vulnerabilities in Retrieval-Augmented Generation Systems
- 发表/报告场所：Findings of the Association for Computational Linguistics: EMNLP 2025
- 出版核对来源：https://aclanthology.org/2025.findings-emnlp.1291/
- 出版核对说明：Official ACL Anthology publication page and publisher-provided BibTeX
- 核读章节：3 Realistic Black-box Attack；4 Experiments；Limitations；Appendix A/B。
- 对本项目的具体启发：State available attacker observations and ingestion assumptions; naturalness judgments are separate from poisoning delivery and answer truth.
- 结论限制：Naive-RAG experiments and subjective LLM naturalness scoring do not establish resistance against a specific defended deployment.
- 版本差异：Publication metadata checked only; use formal-version author list separately from previously read arXiv version.
- 阅读文本SHA-256：`e3d521624d0440f72799108125ce3b1d9520744e2173f775f6f398dc6511f5eb`。

## P081

**Adaptive Attacks Break Defenses Against Indirect Prompt Injection Attacks on LLM Agents**

- 主来源：https://arxiv.org/abs/2503.00061
- 首次公开：2025-02-27；本轮正文阅读版本：v1。
- 发表状态：verified_Findings_NAACL2025。
- 发表/报告题名：Adaptive Attacks Break Defenses Against Indirect Prompt Injection Attacks on LLM Agents
- 发表/报告场所：Findings of NAACL 2025
- 出版核对来源：https://aclanthology.org/2025.findings-naacl.395/
- 核读章节：3 Defenses；4 Adaptive objectives；5 Experiments；6 Analysis and limitations。
- 较新版本补充核读：v2；具体章节与哈希见逐篇来源JSON。
- 对本项目的具体启发：Retain fixed attacks as scoped tests; any future adaptive search must freeze feedback/token budget and retain unsuccessful attempts.
- 结论限制：White-box first-step focus and absence of normal-utility evaluation limit defense ranking; no inference that our static holdout family is adaptive.
- 版本差异：Official publication metadata is separate from the stated arXiv reading title/version; publication-specific results are not silently substituted.
- 阅读文本SHA-256：`8ae88aaf762ec6d03345fb06588a90d0ffea09bfe4b399c5f3d5b78ff6753481`。

## P082

**MELON: Provable Defense Against Indirect Prompt Injection Attacks in AI Agents**

- 主来源：https://arxiv.org/abs/2502.05174
- 首次公开：2025-02-07；本轮正文阅读版本：v1。
- 发表状态：verified_ICML2025_PMLR。
- 发表/报告题名：MELON: Provable Defense Against Indirect Prompt Injection Attacks in AI Agents
- 发表/报告场所：ICML 2025, PMLR
- 出版核对来源：https://proceedings.mlr.press/v267/zhu25z.html
- 核读章节：3 MELON methodology；4 AgentDojo evaluation, ablations, false positives and failures；5 Conclusion。
- 较新版本补充核读：v4；具体章节与哈希见逐篇来源JSON。
- 对本项目的具体启发：Report security and attacked utility together; do not import MELON guarantees for our text-only answer task or single-pass classifier.
- 结论限制：Bounds require separation of benign/malicious mean similarity and concentration assumptions; tool-call matching misses response-only attacks and can flag authorized external instructions.
- 版本差异：Official publication metadata is separate from the stated arXiv reading title/version; publication-specific results are not silently substituted.
- 阅读文本SHA-256：`67a64b92a7b82151ae279b0eefd90691b050ce94d688556cc827706c68dbd2ea`。

## P083

**SafeRAG: Benchmarking Security in Retrieval-Augmented Generation of Large Language Model**

- 主来源：https://arxiv.org/abs/2501.18636
- 首次公开：2025-01-28；本轮正文阅读版本：v2。
- 发表状态：official_publisher_record_verified。
- 发表/报告题名：SafeRAG: Benchmarking Security in Retrieval-Augmented Generation of Large Language Model
- 发表/报告场所：Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)
- 出版核对来源：https://aclanthology.org/2025.acl-long.230/
- 出版核对说明：Official ACL Anthology publication page and publisher-provided BibTeX
- 核读章节：3 Threat framework；4 Metrics；5 Experiments。
- 对本项目的具体启发：Keep retrieval delivery, evidence retention and generation measures distinct; add matched unfiltered outputs for transformed benign contexts.
- 结论限制：Chinese curated news QA and fixed injection ratios are a particular benchmark; an aggregate retrieval metric cannot replace denominator-level utility checks.
- 版本差异：Publication metadata checked only; use formal-version author list separately from previously read arXiv version.
- 阅读文本SHA-256：`4f8a060527c77995eca18a9b96a4eaf70e647759376825afa81618cc1b457f80`。

## P084

**PromptShield: Deployable Detection for Prompt Injection Attacks**

- 主来源：https://arxiv.org/abs/2501.15145
- 首次公开：2025-01-25；本轮正文阅读版本：v2。
- 发表状态：official_publisher_record_verified。
- 发表/报告题名：PromptShield: Deployable Detection for Prompt Injection Attacks
- 发表/报告场所：Proceedings of the Fifteenth ACM Conference on Data and Application Security and Privacy
- 出版核对来源：https://dl.acm.org/doi/10.1145/3714393.3726501
- 出版核对说明：Official ACM publisher indexed record, official CODASPY2025 accepted list/program/proceedings TOC, and ACM-deposited Crossref metadata
- 出版元数据差异：Crossref published date-parts reports2024-06-19, conflicting with the official CODASPY2025 proceedings and publisher PDF header June4–6,2025. Use venue year2025; retain the raw registry field only as an explicitly discrepant field.
- 核读章节：2 Threat model and deployment requirements；3 Dataset split and threshold scheme；4 Setup；5 Ablations；7 Limitations。
- 对本项目的具体启发：Retain normal-only calibrated thresholds, source-disjoint roles, sparse baselines and test FPR alongside nominal budgets.
- 结论限制：Concept drift, optimized adaptive attacks and multimodal inputs are not covered; calibration FPR is not a deployment guarantee.
- 版本差异：Publication metadata checked only; prior arXiv reading version is preserved separately. Do not transfer version-specific results without comparison.
- 阅读文本SHA-256：`1bdb84b77d319fbd586f920586308a03a2f6d3baf7d411233fe2da9cd67126b8`。

## P085

**TrustRAG: Enhancing Robustness and Trustworthiness in Retrieval-Augmented Generation**

- 主来源：https://arxiv.org/abs/2501.00879
- 首次公开：2025-01-01；本轮正文阅读版本：v3。
- 发表状态：preprint_publication_unverified。
- 核读章节：2 Formulation；3 TrustRAG framework；4 Experiment；Limitations；Appendix B。
- 对本项目的具体启发：Do not label a maximum-peer-similarity feature as a reproduction of a full clustering-plus-knowledge defense; preserve benign repetition controls.
- 结论限制：Single and multiple insertions behave differently; cluster filtering can remove clean evidence and internal knowledge need not be factually correct.
- 阅读文本SHA-256：`5f8ed86b80e80c97f94fc1bc34a5faadf48283f61a5b13289de9698f67996c28`。

## P086

**The Task Shield: Enforcing Task Alignment to Defend Against Indirect Prompt Injection in LLM Agents**

- 主来源：https://arxiv.org/abs/2412.16682
- 首次公开：2024-12-21；本轮正文阅读版本：v1。
- 发表状态：official_publisher_record_verified。
- 发表/报告题名：The Task Shield: Enforcing Task Alignment to Defend Against Indirect Prompt Injection in LLM Agents
- 发表/报告场所：Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)
- 出版核对来源：https://aclanthology.org/2025.acl-long.1435/
- 出版核对说明：Official ACL Anthology publication page and publisher-provided BibTeX
- 核读章节：§3任务对齐定义；§4框架；§5实验设置和主要结果；§7局限。
- 对本项目的具体启发：Keep legitimate task instructions among benign controls, and preserve normal utility when assessing a defense.
- 结论限制：LLM extraction/alignment can be evaded or fail with weaker models; one benchmark/model-family and one trial per task limit conclusions.
- 版本差异：Publication metadata checked only; use formal-version author list separately from previously read arXiv version.
- 阅读文本SHA-256：`03f56d7caf006129d942d324b74a6af567b87ea9b998dc226da612154ddbefcb`。

## P087

**InjecGuard: Benchmarking and Mitigating Over-defense in Prompt Injection Guardrail Models**

- 主来源：https://arxiv.org/abs/2410.22770
- 首次公开：2024-10-30；本轮正文阅读版本：v3。
- 发表状态：related_PIGuard_verified_ACL2025_original_InjecGuard_preprint。
- 发表/报告题名：PIGuard: Prompt Injection Guardrail via Mitigating Overdefense for Free
- 发表/报告场所：ACL 2025
- 出版核对来源：https://aclanthology.org/2025.acl-long.1468/
- 核读章节：InjecGuard arXivv3 §3 NotInject construction；§4 training/MOF；§5 evaluation；Limitations。
- 对本项目的具体启发：Use difficult benign instruction-bearing examples and distinguish public guard-only inference from the complete published training method.
- 结论限制：Related preprint and ACL publication have different titles/authors and must not share numeric results silently; NotInject is not all benign deployment traffic.
- 版本差异：Related publication has a different title/author list. The current core reading remains the stated InjecGuard arXiv version; prior PIGuard fulltext reading is historical, while this round reverified its publication metadata. Versions/results are not interchangeable; one study line is counted conservatively.
- 阅读文本SHA-256：`d4f8a2a2ecd2d43074759547ba0e8add270d9d115e4b6bfff11da51b37e3709c`。

## P088

**SecAlign: Defending Against Prompt Injection with Preference Optimization**

- 主来源：https://arxiv.org/abs/2410.05451
- 首次公开：2024-10-07；本轮正文阅读版本：v3。
- 发表状态：official_publisher_record_verified。
- 发表/报告题名：SecAlign: Defending Against Prompt Injection with Preference Optimization
- 发表/报告场所：Proceedings of the 2025 ACM SIGSAC Conference on Computer and Communications Security
- 出版核对来源：https://dl.acm.org/doi/10.1145/3719027.3744836
- 出版核对说明：Official ACM publisher search record and publisher-deposited Crossref metadata
- 核读章节：§3方法；§4设置、攻击预算与结果；§6局限。
- 对本项目的具体启发：Stronger methods require matching access and training budgets; do not append an untrained preference-defense label as a baseline.
- 结论限制：Requires explicit instruction/data separation; future multi-turn attacks, further fine-tuning and different injection positions can change results.
- 版本差异：Publication metadata checked only; prior arXiv reading version is preserved separately. Do not transfer version-specific results without comparison.
- 阅读文本SHA-256：`543ef8ce3a43ecf36eaeb193e6a9d0a5272bd8f36448f0537c61ef42a025de21`。

## P089

**AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents**

- 主来源：https://arxiv.org/abs/2406.13352
- 首次公开：2024-06-19；本轮正文阅读版本：v3。
- 发表状态：verified_NeurIPS2024_DatasetsBenchmarks。
- 发表/报告题名：AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents
- 发表/报告场所：NeurIPS 2024, Datasets and Benchmarks track
- 出版核对来源：https://proceedings.nips.cc/paper_files/paper/2024/hash/97091a5177d8dc64b1da8bf3e1f6fb54-Abstract-Datasets_and_Benchmarks_Track.html
- 核读章节：§3环境设计与评测定义；§4攻击、防御与效用结果；§5局限方向。
- 对本项目的具体启发：Highest-priority extension is E2 same-condition no-filter generation; pair the same questions and retain unsuccessful legitimate tasks.
- 结论限制：Simulated environments and initially simple attacks are not broad deployment coverage; a low-capability agent can appear secure by failing both tasks.
- 版本差异：Official publication metadata is separate from the stated arXiv reading title/version; publication-specific results are not silently substituted.
- 阅读文本SHA-256：`c106a90dbc2e93ab259a058e75acc5dbfaf92d9d6ac0d1f8c490c2296ff04d6b`。

## P090

**The Instruction Hierarchy: Training LLMs to Prioritize Privileged Instructions**

- 主来源：https://arxiv.org/abs/2404.13208
- 首次公开：2024-04-19；本轮正文阅读版本：v1。
- 发表状态：preprint_publication_unverified。
- 核读章节：§3层级与合成训练；§4主要与过拒绝结果；§5–6讨论。
- 对本项目的具体启发：A benign instruction-looking document must not be called malicious merely for lexical resemblance; over-refusal belongs in the outcome panel.
- 结论限制：Learned hierarchy is empirical model behavior, not a deterministic trust boundary; selected over-refusal evaluations still regress.
- 阅读文本SHA-256：`99db2c591b3f639fb317d5966aecddd6faf6049482823985bae1590b28a0e076`。

## P091

**Defending Against Indirect Prompt Injection Attacks With Spotlighting**

- 主来源：https://arxiv.org/abs/2403.14720
- 首次公开：2024-03-20；本轮正文阅读版本：v1。
- 发表状态：preprint_publication_unverified。
- 核读章节：§III三种Spotlighting；§IV实验协议；§V结果；§VI讨论。
- 对本项目的具体启发：Prompt-based prevention could be a separately frozen future baseline, but first fix the missing matched utility controls.
- 结论限制：Synthetic keyword payloads, older models and model-specific token transformations do not prove robustness to natural counterfactual facts or adaptive attacks.
- 阅读文本SHA-256：`379fb3f094fb3a59146337f801e60f065089471e0fe7b4ce4dc4b64311f0db9f`。

## P092

**Can LLMs Separate Instructions From Data? And What Do We Even Mean By That?**

- 主来源：https://arxiv.org/abs/2403.06833
- 首次公开：2024-03-11；本轮正文阅读版本：v3。
- 发表状态：verified_ICLR2025_official_PDF_search_forum_challenge。
- 发表/报告题名：Can LLMs Separate Instructions From Data? And What Do We Even Mean By That?
- 发表/报告场所：ICLR 2025
- 出版核对来源：https://openreview.net/pdf?id=8EtSBX41mt
- 核读章节：§3分离定义；§4SEP构建；§5评价；§6缓解与限制。
- 对本项目的具体启发：Use paired controls where wording is held fixed and authorization changes; maintain the direct no-guard attribution comparison.
- 结论限制：Role labels and prompt engineering alone do not guarantee separation; utility trade-offs and proxy estimation remain model/task dependent.
- 版本差异：Official publication metadata is separate from the stated arXiv reading title/version; publication-specific results are not silently substituted.
- 阅读文本SHA-256：`8836ee504185f7f002128194c680c450d1668b660033a54a9f8155493f133f3a`。

## P093

**Automatic and Universal Prompt Injection Attacks against Large Language Models**

- 主来源：https://arxiv.org/abs/2403.04957
- 首次公开：2024-03-07；本轮正文阅读版本：v1。
- 发表状态：preprint_publication_unverified。
- 核读章节：§2目标与优化；§3评价与自适应结果；§5局限。
- 对本项目的具体启发：Do not treat any appearance of a target as successful semantic adoption; predeclare the goal-specific scoring rule.
- 结论限制：Keyword evaluation can credit quoted or negated strings; white-box universal optimization and constrained seven-task tests differ from our local construction.
- 阅读文本SHA-256：`ad4fbdc609e3788fa94c4dd4ee2b7750566ad71304d2a9904ec9b057f3239722`。

## P094

**InjecAgent: Benchmarking Indirect Prompt Injections in Tool-Integrated Large Language Model Agents**

- 主来源：https://arxiv.org/abs/2403.02691
- 首次公开：2024-03-05；本轮正文阅读版本：v3。
- 发表状态：verified_Findings_ACL2024。
- 发表/报告题名：InjecAgent: Benchmarking Indirect Prompt Injections in Tool-Integrated Large Language Model Agents
- 发表/报告场所：Findings of ACL 2024
- 出版核对来源：https://aclanthology.org/2024.findings-acl.624/
- 核读章节：§2构造与判分；§3实验；§4分析；§8局限。
- 对本项目的具体启发：Preserve all-question denominators and report invalid, abstaining and task-failing responses; do not discard them as secure failures.
- 结论限制：Single-turn tool-response assumptions and a fixed enhanced hacking prefix limit realism; validity-conditioned ASR is not unconditional success.
- 版本差异：Official publication metadata is separate from the stated arXiv reading title/version; publication-specific results are not silently substituted.
- 阅读文本SHA-256：`91f78bd365ca1f063976b856f7f2b941dc130543c81ec13887acc363366bef81`。

## P095

**PoisonedRAG: Knowledge Corruption Attacks to Retrieval-Augmented Generation of Large Language Models**

- 主来源：https://arxiv.org/abs/2402.07867
- 首次公开：2024-02-12；本轮正文阅读版本：v3。
- 发表状态：verified_USENIX_Security2025。
- 发表/报告题名：PoisonedRAG: Knowledge Corruption Attacks to Retrieval-Augmented Generation of Large Language Models
- 发表/报告场所：USENIX Security 2025
- 出版核对来源：https://www.usenix.org/conference/usenixsecurity25/presentation/zou-poisonedrag
- 核读章节：§3威胁模型；§4构造；§5设置与结果；§7防御；§8局限及附录J评分核对。
- 对本项目的具体启发：Retain actual insertion ranking validation, the declared corpus size, target budget and original failures; never call post-retrieval replay full-corpus reproduction.
- 结论限制：Closed-ended targets, small selected query sets and independently crafted query attacks do not cover joint persistent corpus poisoning.
- 版本差异：Official publication metadata is separate from the stated arXiv reading title/version; publication-specific results are not silently substituted.
- 阅读文本SHA-256：`790738fc07c26c04713f4468c12e5adf5cae61b5add1731a7ad5c74ca4dcef1e`。

## P096

**StruQ: Defending Against Prompt Injection with Structured Queries**

- 主来源：https://arxiv.org/abs/2402.06363
- 首次公开：2024-02-09；本轮正文阅读版本：v2。
- 发表状态：verified_USENIX_Security2025。
- 发表/报告题名：StruQ: Defending Against Prompt Injection with Structured Queries
- 发表/报告场所：USENIX Security 2025
- 出版核对来源：https://www.usenix.org/conference/usenixsecurity25/presentation/chen-sizhe
- 核读章节：§4结构化查询；§5评测与消融；§6限制。
- 对本项目的具体启发：Explicitly distinguish our prompt boundary from a trained structured-query model, and keep the same generator/prompt when attributing filter increments.
- 结论限制：Not a generic chatbot or jailbreak defense; optimization attacks retain nonzero success, and training/access costs differ from our frozen component experiment.
- 版本差异：Official publication metadata is separate from the stated arXiv reading title/version; publication-specific results are not silently substituted.
- 阅读文本SHA-256：`69216326ac859e77bd041c20b084d60c08f7498b9b622914b2be04e93ce94abc`。

## P097

**Benchmarking and Defending Against Indirect Prompt Injection Attacks on Large Language Models**

- 主来源：https://arxiv.org/abs/2312.14197
- 首次公开：2023-12-21；本轮正文阅读版本：v4。
- 发表状态：official_publisher_record_verified。
- 发表/报告题名：Benchmarking and Defending against Indirect Prompt Injection Attacks on Large Language Models
- 发表/报告场所：Proceedings of the 31st ACM SIGKDD Conference on Knowledge Discovery and Data Mining V.1
- 出版核对来源：https://dl.acm.org/doi/10.1145/3690624.3709179
- 出版核对说明：Official ACM publisher search record and publisher-deposited Crossref metadata
- 核读章节：§3威胁模型；§4构造；§6方法；§7实验；§8结论。
- 对本项目的具体启发：Keep a matched clean/transformed no-filter control and avoid multiplying positions/templates without a distinct hypothesis.
- 结论限制：Public benchmark exposure, task-specific lexical metrics and synthetic constructions do not establish untouched deployment transfer.
- 版本差异：Publication metadata checked only; prior arXiv reading version is preserved separately. Do not transfer version-specific results without comparison. The formal publication title differs from the reading title shown above.
- 阅读文本SHA-256：`0b694194dc88c07acbe7abe5f2b882f3ad6a1b770445c4402e7ebde765f96ce2`。

## P098

**Tensor Trust: Interpretable Prompt Injection Attacks from an Online Game**

- 主来源：https://arxiv.org/abs/2311.01011
- 首次公开：2023-11-02；本轮正文阅读版本：v1。
- 发表状态：verified_ICLR2024。
- 发表/报告题名：Tensor Trust: Interpretable Prompt Injection Attacks from an Online Game
- 发表/报告场所：ICLR 2024
- 出版核对来源：https://proceedings.iclr.cc/paper_files/paper/2024/hash/519c51529c3544b3430bd8b17d400365-Abstract-Conference.html
- 核读章节：§3清洗和指标；§4攻击策略；§5模型评测；§6迁移与局限。
- 对本项目的具体启发：Always show authorized-task success beside attacker failure; do not interpret refusing everything as a successful defense.
- 结论限制：Adversarial filtering conditions the sample, literal leakage misses paraphrases, and final ICLR dataset counts exceed arXiv v1 counts; versions must stay explicit.
- 版本差异：Official ICLR2024 record lists563000attacks/118000defenses; original arXivv1 lists126000/46000. No counts imported into Group9 results.
- 阅读文本SHA-256：`6d7ad1763142b078280b970869a6cf255a5215bebb30e83d33ae1842cf5bfd1e`。

## P099

**Formalizing and Benchmarking Prompt Injection Attacks and Defenses**

- 主来源：https://arxiv.org/abs/2310.12815
- 首次公开：2023-10-19；本轮正文阅读版本：v5。
- 发表状态：verified_USENIX_Security2024。
- 发表/报告题名：Formalizing and Benchmarking Prompt Injection Attacks and Defenses
- 发表/报告场所：USENIX Security 2024
- 出版核对来源：https://www.usenix.org/conference/usenixsecurity24/presentation/liu-yupei
- 核读章节：§3威胁模型；§4攻击框架；§5防御；§6评测；§8局限。
- 对本项目的具体启发：Consolidate attack variants sharing the same hypothesis, preserve a strong sparse comparator, and discuss recovery rather than only blocking.
- 结论限制：Heuristic task-bank evidence is not adaptive robustness; closed-model parameter estimates and cross-paper ASR must not be copied as facts about our run.
- 版本差异：Official publication metadata is separate from the stated arXiv reading title/version; publication-specific results are not silently substituted.
- 阅读文本SHA-256：`4872a5954351c4d248f68cb4280bf3fc0577636a45ddd3c1b0d4a8b08ba8dbf3`。

## P100

**Not what you've signed up for: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection**

- 主来源：https://arxiv.org/abs/2302.12173
- 首次公开：2023-02-23；本轮正文阅读版本：v2。
- 发表状态：publisher_record_search_confirms_AISec2023_DOI_open_failed。
- 发表/报告题名：Not what you've signed up for: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection
- 发表/报告场所：ACM Workshop on Artificial Intelligence and Security (AISec 2023)
- 出版核对来源：https://doi.org/10.1145/3605764.3623985
- 核读章节：§3攻击面；§4受控及真实应用演示；§5评测局限。
- 对本项目的具体启发：Describe attacker-controlled external text as data and preserve source provenance; keep our controlled QA claim distinct from real tool compromise.
- 结论限制：Proof-of-concept synthetic interfaces and browser/sidebar examples do not quantify prevalence or general worst-case ASR.
- 版本差异：Official publication metadata is separate from the stated arXiv reading title/version; publication-specific results are not silently substituted.
- 阅读文本SHA-256：`7995f22e978533631046b0e5ad092a07c47ff06bb6f338d84816d3e370c928ed`。
