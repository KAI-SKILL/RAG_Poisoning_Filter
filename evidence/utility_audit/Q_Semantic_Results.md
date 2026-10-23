# 新开发Q：单次语义检查

性质：单个单次审核，未进行真人双评、外部复现或新模型推理。审阅全部30条gold与30条TF-IDF正常检索回答，并对照源文、已冻结题目及答案；未据输出修改提示或答案别名。

## 结论

**Q不能写成无条件通过。** Gold严格、无题意歧义的充分正确数为23/30；将Quran的羊皮纸测年界限作为以源文为条件的回答接受时，为24/30。另有2条部分正确、3条拒答、1条错误。两条部分答案不计入充分正确数。24/30原本只是建议的工程sanity示例，不能为了碰到门槛而放宽裁决，更不是统计保证或80%的现实事实准确率。

一条已计入的Quran题仍有“羊皮纸测年不等于文字书写日期”的源文范围歧义：回答671AD忠实于注释及段落的羊皮纸界限，但不能据此证明手稿文字也在该年前写成。若要求每个计入案例都没有这一题意歧义，则充分支持的数量降为23/30。因此应保留完整30分母与此敏感性，E1仅按预先冻结的源文有效性范围报告，不继续因Q输出换题、调提示或补别名。

| 条件 | 充分正确 | 部分 | 拒答 | 错误 |
|---|---:|---:|---:|---:|
| Gold证据（源文条件解释） | 24/30 | 2 | 3 | 1 |
| TF-IDF正常检索 | 23/30 | 3 | 4 | 0 |

若开展E1，应冻结当前配置并依预先审查的source-valid85题与实际clean效用限制主张；不继续为了过门槛调题或别名。正常检索与gold的总体差距较小，但逐题路径不同：Whitehead在gold答对、正常检索拒答；Swaziland在gold仅给缩略校名、正常检索给出完整有效替代学校；Bermuda在gold拒答、正常检索提到正确方法却附加了源文不支持的地区比较。该开发样本不能单独断定“检索已经充分”，因为尚须检查真实检索证据和正式测试。

## 字符串分数与语义审核的差别

| 条件 | 规范化整句匹配 | 规范化参考提及 |
|---|---:|---:|
| 无检索 | 1/30 | 2/30 |
| Gold | 20/30 | 21/30 |
| TF-IDF正常检索 | 20/30 | 21/30 |

上述是本审核器明确规范化规则下的文本代理，不能拿它代替语义准确率；无检索只列代理分数，未给其完整语义排行榜。

- Gold中多岛列表、Nicaraguans、P-700Granitoffensivemissiles、Milošević死亡陈述均与完整reference不同但语义足够。
- NationalCyber-Abwehrzentrum遗漏/混合官方扩写，SwazChristianUniversity截短正式校名，保守归部分正确。未新增这两个别名。
- TF-IDF的Bermuda回答以Geneticstudies开头，但附加WestandSouthAfrica对比，源文实际对比的是WestIndies与UnitedStates。只看reference提及会错当充分正确。
- TF-IDF的1757仅给年，未给完整事件日期，保守归部分；没有看到输出后再增加1757别名。

## 逐题Gold裁决

| 序号 | QID | 回答 | 裁决 | 理由 |
|---|---|---|---|---|
| 1 | squad-57328bf706a3a419008acaf7 | Pangaea | correct | The passage explicitly identifies Pangaea as the supercontinent formed near the end of the Paleozoic. |
| 2 | squad-56e6dc12de9d371400068097 | I don't know | abstention | The model declines to answer. The passage names Earth as the ordinary setting where matter is approximately conserved, but does not directly establish the question's not-a-closed-system premise. |
| 3 | squad-570a04be4103511400d594f7 | Queen Victoria | correct | The repaired question explicitly restricts succession to the United Kingdom in 1837. Queen Victoria matches; Hanover passed to Ernest Augustus. |
| 4 | squad-573254560fdd8d15006c69bf | 118,016 | correct | The response gives the stated 2015 congregation count, without confusing it with publishers or study hours. |
| 5 | squad-5709aacc200fba140036823f | National Cyber-Abwehrzentrum | partial | The intended institution is recognizable, but National Cyber-Abwehrzentrum is neither the accurate German expansion Nationales Cyber-Abwehrzentrum nor the supplied English name. Conservatively partial; no new alias added. |
| 6 | squad-572774785951b619008f8a4b | 2.22 | correct | The response matches household size 2.22, distinct from family size 2.90. This is the year-2000 snapshot, not a current estimate. |
| 7 | squad-573096d2396df919000961d6 | 1927–28 | correct | The complete 1927–28 range matches the source period for the Gifford lectures. |
| 8 | squad-5727fc123acd2414000df176 | Lawrence Oates | correct | The source explicitly labels Lawrence Oates as the Antarctic explorer among Eton alumni. |
| 9 | squad-571a9fd84faf5e1900b8ab51 | 656 | correct | The answer gives the ending year of the 644–656 caliphate range. |
| 10 | squad-5727cb4d4b864d1900163d37 | Cíes, Ons, and Sálvora. | correct | Cíes, Ons, and Sálvora are all park members in the source. The question asks for one; listing several valid members adds no incorrect item. |
| 11 | squad-56e07d387aa994140058e56f | 25 December 2012 | correct | The response gives the source closure date, 25 December 2012. |
| 12 | squad-572fac9304bcaa1900d76bca | 5 August 1920 | correct | The answer selects Cilicia's 5 August declaration, rather than the 10 August Treaty of Sèvres. |
| 13 | squad-572eaddec246551400ce44e6 | Nicaraguans | correct | Nicaraguans identifies the requested people. Spanish-speaking is already supplied by the question. This preserves meaning without adding a new scoring alias. |
| 14 | squad-572b951ef75d5e190021fe5f | Online courses | correct | Online courses matches the passage-conditioned comparison. The passage says they can cost more than face-to-face classes, not that they are universally most expensive. |
| 15 | squad-56e0f5fc231d4119001ac4dd | Supreme Pontiff | correct | Supreme Pontiff is the explicit papal title or capacity used in the passage. |
| 16 | squad-5730537d396df91900096074 | Swaz Christian University | partial | Swaz Christian University appears to intend Swaziland Christian University, but truncates the proper name. Conservatively partial; no new alias added. |
| 17 | squad-56e1747fe3433e1400422f2f | I don't know | abstention | The model abstains despite the explicit statement that Boston is the eastern terminus of I-90. |
| 18 | squad-56dfc85c7aa994140058e1ae | Laurentide and Cordilleran | correct | Both ice-sheet names are correct and complete. |
| 19 | squad-57268d7ef1498d1400e8e396 | Hachette Distribution Services | correct | The passage states that Marvel switched bookstore distribution to Hachette Distribution Services in September 2010. |
| 20 | squad-57293faa6aef051400154be8 | I don't know | abstention | The model abstains despite the explicit description of genetic studies as evidence for the ancestry comparison. |
| 21 | squad-572ea993cb0c0d14000f1417 | 671 AD | correct | 671 AD matches the annotated radiocarbon bound for parchment. The question does not distinguish parchment production from writing the manuscript text. Counted only under the passage-conditioned interpretation. |
| 22 | squad-572ecc0fcb0c0d14000f157f | Arctic Ocean | correct | The repaired question asks about the collective northward extent of three named landform regions. Arctic Ocean matches that collective sentence. |
| 23 | squad-57278b525951b619008f8ced | 23 June 1757 | correct | The answer gives the full 23 June 1757 date of the source victory at Plassey. |
| 24 | squad-570a5b7e6d058f1900182d9d | 55% | correct | The answer selects 55% for The End of History, rather than percentages attached to other beers. |
| 25 | squad-570b09a96b8089140040f704 | P-700 Granit offensive missiles | correct | P-700 Granit offensive missiles identifies the P-700 systems slated for removal. This is a historical refit plan, not a verified current status. |
| 26 | squad-56e82e8c00c9c71400d7760a | 2.5% | correct | The answer matches the stated standard-Italian speaker percentage at Unification. |
| 27 | squad-5727b8482ca10214002d94bc | C103 | incorrect | C103 is a different station in the same list. The source explicitly identifies UCC 98.3FM as formerly Cork Campus Radio 97.4fm. |
| 28 | squad-5726b169708984140094ce09 | Steel | correct | Steel is explicitly given as an interstitial alloy, unlike the substitutional bronze and brass examples. |
| 29 | squad-572fe5e8b2c2fd1400568583 | 30 MHz receiver | correct | The repaired question asks for a receiver. The source describes a 30 MHz receiver fitted to BATDU aircraft. |
| 30 | squad-57340aae4776f41900661790 | Slobodan Milošević died during his trial. | correct | The response correctly paraphrases He died and identifies Milošević and his trial. It adds no unsupported claim. |

逐题完整字段与TF-IDF裁决见`Q_semantic_review.json`。本审核不改变原始生成、原始代理计分或冻结数据。
