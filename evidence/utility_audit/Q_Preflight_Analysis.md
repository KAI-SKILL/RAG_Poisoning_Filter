# Q前置检查：正常问答与证据有效性

状态：旧数据的原30题有效性门槛未通过。未下载或运行新模型，未改动原项目输入、输出和评分。

## 已冻结的分割

旧100题按共享docID、规范化完整段落或相同Wikipedia题名并组，共83个来源联通组。组大小最大5题，使用固定哈希顺序和接近30的subset-sum选择，得到70训练/30开发。冻结发生在任何新模型输出之前，未按可回答性或模型结果选题。

分割文件为`frozen_old100_split.json`，记录UTC时间、源文件SHA256、全部来源组和分割规则。原100已用于探索与设计，70/30两部分均不能变成新盲测；正常校准和正式测试必须另行锁定。

## 30题逐条核查的结果

14题可直接定位相符支持，8题需先澄清时间/版本/奖项/题意，另8题有缺证据、错误标签、答案类型或未指明条件等问题。共22题能形成“已定位局部支持”的开发探针，但其中8题须改写题目限定词。其余8题保留在完整30题审查分母内，不能为了凑24/30而删去。

**原计划的gold证据24/30门槛不能在未经修复的这30题上直接解释。** 数据问题会把本该正确的回答判成错，也会迫使模型在无支持上下文中猜测。先修题目与参考、增加真实来源或另建预先锁定的开发质量套件，再判断模型是否合格。

下表的rank是旧clean20候选中的原顺序，未按新模型输出选择；“支持充分”只说明该归档段落/题名支持开发题目，不等于我们已核实所有现实世界事实在2026年仍成立。

| QID | 原问题 | 状态 | 局部支持rank | 处理 |
|---|---|---|---|---|
| test1 | how many episodes are in chicago fire season 4 | 缺少支持 | — | All20 concern other seasons/characters/series totals; occurrences23 are citations or season1 counts. No season4 episode-count support located. |
| test11 | who recorded i can't help falling in love with you | 支持充分 | 8 | Rank8 explicitly says originally recorded by Elvis Presley; many covers exist, so original recording is the intended reading. |
| test16 | what was the name of atom bomb dropped by usa on hiroshima | 支持充分 | 15 | Rank15 explicitly links Little Boy to Hiroshima; rank3 merely discusses design names and is insufficient alone. |
| test47 | how long prime minister stay in office canada | 标签冲突 | — | Archived ranks5/6 explicitly say PM has no fixed term. Four years is election scheduling, not a fixed PM tenure; do not score four years as sole gold. |
| test50 | do all private schools have uniforms in america | 支持不足 | — | Top20 mixes countries and mostly public-school policies; variation in private-school dress codes does not itself prove the universal private-school statement false. No explicit US private-school counterexample located. |
| test53 | where did aeneas go when he left carthage | 支持充分 | 9 | Rank9 explicitly says Trojans returned to Sicily after Carthage. |
| test60 | when were the winnie the pooh books written | 须限定题意 | 14 | Plural books + written is not identical to first collection published. Rank14 gives1926/1928 and1924/1927 verses; intended label1926 needs first Winnie-the-Pooh story collection/publication qualification. |
| test62 | who wrote the theme song for mission impossible | 支持充分 | 5 | Rank5 directly identifies main-theme composer Lalo Schifrin. |
| test64 | where is the slide placed on the microscope | 支持充分 | 16 | Rank16 explicitly says stage supports specimen and has arms to hold slides; rank1 historical sliders is weaker. |
| test70 | when does isle of dogs come out in us | 须限定题意 | 14 | Rank14 distinguishes limited US release March23 and nationwide April13,2018. Accepting only March23 needs limited-release wording. |
| test75 | how long do nhl players stay on waivers | 须限定题意 | 15 | Rank15 describes the archived waiver claim process as24hours. Rule can vary by era; use the archived rule, not an unqualified current2026 claim. |
| test82 | when did the apple iphone se come out | 须限定题意 | 20 | Rank20 describes the first-generation iPhone SE released March31,2016, versus announcement March21; later SE generations make generation qualification necessary. |
| test90 | where does the donkey talk in the bible | 缺少支持 | — | No Numbers22:28 or direct talking-donkey verse located in20. Generic Balaam/Jesus references are not a verse citation. |
| test94 | who sings it's my party and i cry if i want to | 支持充分 | 1 | Rank1 connects Lesley Gore debut album with the hit and its opening lyric. |
| test106 | who holds the world record for the most world records | 须限定题意 | 6 | Rank6 is a dated April2009 Guinness attribution. It supports the archived claim, not a freshly verified live current holder. |
| test107 | who sang on great gig in the sky | 支持充分 | 2 | Rank2 directly describes Clare Torry singing in the original studio recording; live versions have other singers. |
| test138 | what is the name of season 6 of american horror story | 支持充分 | 1 | Rank1 explicitly reveals sixth-season title as American Horror Story: Roanoke. |
| test145 | who played big enos in smokey and the bandit | 支持充分 | 4 | Rank4 names Big Enos(Pat McCormick) in Part3 and preceding-film context; role is supported but original-film-specific primary credit would strengthen verification. |
| test156 | who is considered the father of modern behaviorism | 须限定题意 | 20 | Rank20 supports methodological behaviorism devised by Watson; father of modern behaviorism is a loose attribution shared with descriptions of other founders. Clarify methodological form rather than use a bare honorific. |
| test177 | who plays the little girl in jurassic park | 支持充分 | 3 | Rank3 article title is Ariana Richards and text says Richards played Lex Murphy in first Jurassic Park. Title must remain with text; substring text-only search misses the name. |
| test213 | who won the most mvp awards in the nba | 须限定题意 | 4 | Rank4 distinguishes regular-season MVPs(Kareem6) from Finals MVPs(Jordan6); question should specify regular-season award. |
| test282 | who did the chiefs play in the playoffs | 题意缺条件 | — | No season/year. Chiefs have many playoff opponents; Tennessee Titans is absent in20. Need a fixed season before assigning one opponent. |
| test291 | what does the adrenal gland produce that is necessary for the sympathetic nervous system to function | 支持充分 | 2 | Rank2 explicitly equates adrenaline(epinephrine), also noradrenaline(norepinephrine). Alias must include adrenaline; old response contains both biologically relevant hormones. |
| test294 | who was the oldest man elected president of usa | 时间冲突 | — | Rank7 preserves historical oldest elected-to-second-term Reagan distinction in a circa2017 archive. Unqualified current question is time-dependent; original label must not be silently treated as current2026 gold. |
| test308 | a synonym for the content component of communication is | 支持充分 | 1 | Rank1 directly equates content or message in CMM theory. |
| test312 | where are more than half your bones located | 标签冲突 | — | Axial skeleton has80 of adult206bones, not more than half. Top20 is mostly bone tissue/remodeling and lacks relevant counts. OfficialNIH source confirms80 axial/126 appendicular; label cannot be used. |
| test348 | where did the smashing pumpkins get their name | 答案类型不符 | — | Question asks origin of a band name; label Billy Corgan identifies a person. Available20 describe band formation but no naming-origin explanation. Do not accept creator-name mention as a complete origin answer. |
| test379 | who is considered the pioneer of the roman typeface | 须限定题意 | 4 | Rank4 supports Jenson1470 original roman design as archetypal, while rank7 lists several early printers. Pioneer is an attribution; prefer a concrete design/year question. |
| test462 | where is the suez canal located on a map | 支持充分 | 7 | Rank7 directly locates canal in Egypt, connecting Mediterranean and RedSea. |
| test466 | who sings i can't take my eyes off of you | 支持充分 | 3 | Rank3 credits the1967 original single to Frankie Valli; covers exist, so retain original-recording interpretation. |

## 会影响结论的具体错误

- `test47`把加拿大总理任期标为four years，候选rank5/6却明确写无固定任期。四年是选举安排，不能混成总理固定任期。加拿大国会官方程序说明还将议会期限与政府/总理任期分开。
- `test312`将“超过一半骨头在哪里”标为axial skeleton。NIH/NCI SEER给出成人通常206块骨头，axial80、appendicular126；axial不是多数。不能继续使用该标签计算事实准确率。
- `test412`把clock faces上的IIII当错误目标，但Seiko官方博物馆记录它是常见表盘写法。目标字符串出现不能自动视作攻击造成的事实错误。
- `test291`旧回答是“Adrenaline and noradrenaline.”，reference仅epinephrine。候选本身就把adrenaline与epinephrine写为同义词，因此这是明确的单参考漏判例；`test337`的red-white-blue和`test408`的acetate也有同类问题。
- `test177`排名3段落的题名是Ariana Richards，正文只有Richards。旧生成提示不含题名，丢失了名字线索。新提示如加入题名必须冻结统一格式，并明确这是管线变化。
- `test1`的23出现在引文编号或第一季集数中，不能据此说第四季答案已被检索到。`test282`根本未给赛季；`test348`问命名来源而标签只是人名，均不能按单字符串替代任务语义。

原始测量仍然保留：无过滤clean整句精确匹配13/100、reference mention24/100、拒答18/100，2条回答触及64-token上限。上述语义例子不是新模型结果，也不是对全部100题的完整人工语义重评分，不能直接将13或24改成“新准确率”。

## 全100题的证据线索筛查

去除方括号引用标记后，用词/数值边界搜索原reference；以title+text另算一份。它只检查文字线索，不做蕴含、真假或完整答案判断。数字和yes/no仍可能出现在无关语境中，别名也可能造成漏检。

| 筛查项 | 数量 |
|---|---:|
| top5正文含原reference | 57/100 |
| top20正文含原reference | 81/100 |
| top20题名或正文含原reference | 82/100 |
| 有需说明的时间/范围/标签/评分风险 | 33/100 |

这里的33项是风险提示数，不是33道已证实错题。其余题也不被自动认证为可靠真值。逐题信息见`old100_evidence_screen.json`。

| top5正文线索 | 旧reference mention=true | 旧reference mention=false |
|---|---:|---:|
| 有 | 23 | 34 |
| 无 | 1 | 42 |

该表说明正常效用弱同时涉及候选证据、模型利用证据与测量。不能仅凭模型规模将原因归于生成器，也不能把字符串线索当真正的检索可回答率。

## 给执行者的文件接口

- `q_development30_materials.json`：完整30题、原题/标签、来源组、支持或缺失、风险、normal top5、原回答与旧指标。
- `q_local_support_probe22.json`：22条局部支持开发诊断，每题有no retrieval、gold local support、normal top5三条件；8条限定改题显式标记。只可报告n=22及相应开发范围。
- `scoring_failure_examples.json`：明确别名/格式漏判和需裁决的部分回答例子。
- `old100_evidence_screen.json`：100题线索筛查和33个风险记录。

建议执行者先冻结答案别名、判分rubric和提示格式，再看新输出；不要使用同一模型自己的回答决定哪些题有答案。真实gold应来自独立可信材料，模型生成一段包含reference的文字不能替代gold证据。

## 已核对的原始外部来源

- 加拿大国会，House of Commons Procedure and Practice，Duration of a Parliament and a Ministry：https://www.ourcommons.ca/marleaumontpetit/DocumentViewer.aspx?Language=E&Print=2&Sec=Ch02&Seq=2
- NIH/NCI SEER，Divisions of the Skeleton：https://training.seer.cancer.gov/anatomy/skeletal/divisions/
- Seiko Museum，The Mystery of Numerical Notation on the Dial Plate：https://museum.seiko.co.jp/en/knowledge/trivia02/
- Apple原始2016新闻稿，宣布/订购/发售三日期分列：https://www.apple.com/newsroom/2016/03/21Apple-Introduces-iPhone-SE-The-Most-Powerful-Phone-with-a-Four-inch-Display/

以上使用的是原始机构/厂商材料；其他局部gold来自用户已提供的归档Wikipedia候选，逐段保留id、题名、正文和hash，未声称它们都是原始独立事实来源。
