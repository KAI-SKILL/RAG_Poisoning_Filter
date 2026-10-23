# 当前报告与README的只读一致性审查

对象是报告代理仍在编辑的LaTeX源及当前两个README；未写入这些文件，未读取正在进行的主生成输出。以下是本次读取时的编辑建议，不是最终版签核。

## 已一致的部分

- `q_results.tex`明确区分gold的20/30 alias exact、源文条件24/30与严格23/30，并保留Quran羊皮纸测年与文字书写的区别；未无条件宣布达到可靠性门槛。
- 单次审核没有冒称两位真人评审。正常检索是开发TF-IDF诊断，与正式Contriever管线分开。
- `design.tex`、两个README保留原100测试的完整文本代理分母，85题为输出前源文审查确定的敏感性子集，15题未被悄悄删除。
- `fresh_results.tex`已说明retention只识别注释gold及声明的合法echo/copy变体，不代表语料中所有等价支持；零保留不证明所有有用证据都消失。

## 定稿前需要澄清

1. **E2没有同条件无过滤控制。** 新E2只比较context、no_guard、fusion，复用的E1 clean与single-counterfactual基线不是echo/copy条件下的unfiltered反事实。因此可报告三策略在机制条件中的证据/回答表现和与各自clean的配对变化，不能独立把回答损失归因于过滤，或声称无过滤在同一echo/copy条件下保留了效用。建议在design、机制结果与revised README明确这一限制。
2. **题名使用的内部文字冲突。** `method.tex`称title仅用于ranking，但`design.tex`及README明确生成提示含title。建议表述为peer特征只编码正文；title参与retrieval与generator格式，且不进入peer/guard正文视图。这个建议只解决文字冲突；最终应与实际代码检查一致。
3. **retention术语应统一。** 使用known-support或annotated-support retention，避免宽泛写成所有有用证据保留率。保留fresh-results已有的等价支持遗漏与注释缺陷限制。
4. **审核时间限定到最终测试。** 根README“审查在模型输出之前进行”可能被读成在任何开发推理之前；建议精确写测试源文/目标审核在读取最终test输出之前冻结，开发修订的原90+新9/复用81另按记录说明。
5. **精简阅读入口应更新。** 100篇证据现已逐字节复制进`evidence/literature_review_100/`，根README末句可直接链接该目录索引。原实施前重设计建议置于其`pre_revision_analysis/`中，不能作为新增实验已经执行的证明。

摘要与结论目前更多强调旧NQ探索结果。等实际新执行全部冻结后，应让摘要的主发现反映最终新E1/E2，而不是只给旧数据的有利工作点；这不是要求提前填入未完成结果。
