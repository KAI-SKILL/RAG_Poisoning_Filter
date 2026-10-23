from pathlib import Path
import json,re,string,hashlib,datetime,collections,unicodedata
OUT=Path('revision_work/utility_audit');raw_path=Path('revision_work/Group9_Project/output/revised_experiment/dev_q_v2/raw_generations.jsonl')
rows=[json.loads(s) for s in raw_path.read_text().splitlines()];gold=[r for r in rows if r['setting']=='gold'];normal=[r for r in rows if r['setting']=='tfidf_retrieval'];dev={r['qid']:r for r in [json.loads(s) for s in Path('revision_work/new_eval_data/dev_records.jsonl').read_text().splitlines()]}
assert len(rows)==90 and len(gold)==len(normal)==30
# Single source-and-response review. These decisions are not new aliases.
gold_labels=['correct','abstention','correct','correct','partial','correct','correct','correct','correct','correct','correct','correct','correct','correct','correct','partial','abstention','correct','correct','abstention','correct','correct','correct','correct','correct','correct','incorrect','correct','correct','correct']
gold_reasons=[
 "The passage explicitly identifies Pangaea as the supercontinent formed near the end of the Paleozoic.",
 "The model declines to answer. The passage names Earth as the ordinary setting where matter is approximately conserved, but does not directly establish the question's not-a-closed-system premise.",
 "The repaired question explicitly restricts succession to the United Kingdom in 1837. Queen Victoria matches; Hanover passed to Ernest Augustus.",
 "The response gives the stated 2015 congregation count, without confusing it with publishers or study hours.",
 "The intended institution is recognizable, but National Cyber-Abwehrzentrum is neither the accurate German expansion Nationales Cyber-Abwehrzentrum nor the supplied English name. Conservatively partial; no new alias added.",
 "The response matches household size 2.22, distinct from family size 2.90. This is the year-2000 snapshot, not a current estimate.",
 "The complete 1927–28 range matches the source period for the Gifford lectures.",
 "The source explicitly labels Lawrence Oates as the Antarctic explorer among Eton alumni.",
 "The answer gives the ending year of the 644–656 caliphate range.",
 "Cíes, Ons, and Sálvora are all park members in the source. The question asks for one; listing several valid members adds no incorrect item.",
 "The response gives the source closure date, 25 December 2012.",
 "The answer selects Cilicia's 5 August declaration, rather than the 10 August Treaty of Sèvres.",
 "Nicaraguans identifies the requested people. Spanish-speaking is already supplied by the question. This preserves meaning without adding a new scoring alias.",
 "Online courses matches the passage-conditioned comparison. The passage says they can cost more than face-to-face classes, not that they are universally most expensive.",
 "Supreme Pontiff is the explicit papal title or capacity used in the passage.",
 "Swaz Christian University appears to intend Swaziland Christian University, but truncates the proper name. Conservatively partial; no new alias added.",
 "The model abstains despite the explicit statement that Boston is the eastern terminus of I-90.",
 "Both ice-sheet names are correct and complete.",
 "The passage states that Marvel switched bookstore distribution to Hachette Distribution Services in September 2010.",
 "The model abstains despite the explicit description of genetic studies as evidence for the ancestry comparison.",
 "671 AD matches the annotated radiocarbon bound for parchment. The question does not distinguish parchment production from writing the manuscript text. Counted only under the passage-conditioned interpretation.",
 "The repaired question asks about the collective northward extent of three named landform regions. Arctic Ocean matches that collective sentence.",
 "The answer gives the full 23 June 1757 date of the source victory at Plassey.",
 "The answer selects 55% for The End of History, rather than percentages attached to other beers.",
 "P-700 Granit offensive missiles identifies the P-700 systems slated for removal. This is a historical refit plan, not a verified current status.",
 "The answer matches the stated standard-Italian speaker percentage at Unification.",
 "C103 is a different station in the same list. The source explicitly identifies UCC 98.3FM as formerly Cork Campus Radio 97.4fm.",
 "Steel is explicitly given as an interstitial alloy, unlike the substitutional bronze and brass examples.",
 "The repaired question asks for a receiver. The source describes a 30 MHz receiver fitted to BATDU aircraft.",
 "The response correctly paraphrases He died and identifies Milošević and his trial. It adds no unsupported claim."
]
normal_labels=['correct','abstention','correct','correct','partial','correct','abstention','correct','correct','correct','correct','correct','correct','correct','correct','correct','abstention','correct','correct','partial','correct','correct','partial','correct','correct','correct','abstention','correct','correct','correct']
normal_overrides={7: 'The model abstains with retrieved context but answers correctly with gold. This is a context-condition difference, not proof that it cannot answer the question.', 10: 'Cortegada Island is a source-listed park member and a frozen accepted answer.', 16: 'Limkokwing University of Creative Technology is explicitly another institution in the source and a frozen accepted answer.', 20: 'Genetic studies is the correct method, but the added comparison with West and South Africa is unsupported. The source instead contrasts ancestry with the West Indies and United States. Conservatively partial despite the correct phrase.', 23: '1757 gives the correct year but omits the day and month of the full source date. Conservatively partial for precision; no 1757 alias added after outputs.', 27: 'The model abstains rather than selecting UCC 98.3FM. The gold condition instead selected the wrong station, C103.'}

def norm(x):
 x=unicodedata.normalize('NFKC',x).casefold()
 x=''.join(' ' if ch in string.punctuation or unicodedata.category(ch).startswith('P') else ch for ch in x)
 x=re.sub(r'\b(a|an|the)\b',' ',x)
 return ' '.join(x.split())
def exact(r):return any(norm(r['response'])==norm(a) for a in r['answers'])
def mention(r):
 txt=' '+norm(r['response'])+' '
 return any(' '+norm(a)+' ' in txt for a in r['answers'])
reviews=[]
for setting,rs,labels in [('gold',gold,gold_labels),('tfidf_retrieval',normal,normal_labels)]:
 for i,(r,label) in enumerate(zip(rs,labels),1):
  q=r['qid'];reasons=gold_reasons[i-1] if setting=='gold' else normal_overrides.get(i,gold_reasons[i-1])
  if setting=='tfidf_retrieval' and i==5:reasons=gold_reasons[4]
  if setting=='tfidf_retrieval' and i==17:reasons='The model abstains. The source answer is I-90, and the gold condition also abstains.'
  if setting=='tfidf_retrieval' and i==2:reasons=gold_reasons[1]
  # Originalgoldcontext is thesemantictaskreference. Thisreview doesnotcertify everyretrievedcontextgroundingrelation.
  reviews.append({'index_1based':i,'qid':q,'setting':setting,'question':r['question'],'response':r['response'],'frozen_answers':r['answers'],'judgment':label,'passage_conditioned_adequate':label=='correct','strict_source_scope_judgment':('source_scope_uncertain' if i==21 and label=='correct' else label),'strict_fully_correct':label=='correct' and i!=21,'normalized_exact_proxy':exact(r),'normalized_mention_proxy':mention(r),'reason':reasons,'source_document_id':dev[q]['gold_document_id'],'source_passage_sha256':hashlib.sha256(dev[q]['gold_passage'].encode()).hexdigest(),'scope_flags':(['parchment_date_not_necessarily_writing_date'] if i==21 else [])+(['question_presupposition_not_directly_entailed'] if i==2 else [])+(['passage_comparison_not_universal_school_cost_ranking'] if i==14 else [])+(['year2000_snapshot_not_current2026'] if i==6 else [])+(['historical_refit_plan_not_current_status'] if i==25 else []),'reviewer':'single review; no human panel or second human rater'})
counts={k:dict(collections.Counter(r['judgment'] for r in reviews if r['setting']==k)) for k in ['gold','tfidf_retrieval']}
proxy={setting:{'n':30,'normalized_exact':sum(exact(r) for r in rows if r['setting']==setting),'normalized_mention':sum(mention(r) for r in rows if r['setting']==setting)} for setting in ['no_retrieval','gold','tfidf_retrieval']}
obj={'status':'COMPLETED_SINGLE_AI_ASSISTED_SEMANTIC_REVIEW','reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer_independence':'A differentagentfromgeneratorimplementationandpre-evaluationquestionrepair; reviewedprovidedoutputsandgoldsource; notindependenthumanreview or externalreplication.','raw_generations_sha256':hashlib.sha256(raw_path.read_bytes()).hexdigest(),'new_model_inference_performed_by_reviewer':False,'prompt_or_alias_changes_after_outputs':False,'scope':'All30goldand30TF-IDFnormalresponsesreadagainstsourceandfrozenquestion/answers. No-retrievalsummariesbelowareautomatictextproxiesonly, notafullsemanticreview. Normalreviewchecksanswertruthrelativetogoldsource, notwhetherallclaimsareentailedbytheactualretrievedfivepassages.','rubric':{'correct':'Requestedinformationisfullyidentifiedinthesource; harmlessparaphraseormultiplevalidexamplesallowed; noincorrectextraassertion.','partial':'Incompleteofficialname/dateorcorrectcorewithunsupported/incorrectextraexplanation; excludedfromfullcorrectcount.','incorrect':'Answerconflictswithrequestedsourcefact.','abstention':'Noanswergiven; distinguishfromincorrectassertion.','invalid':'Unusableoutput; noneobserved.'},'semantic_counts':counts,'semantic_counts_scope':'Counts use passage-conditioned interpretation; strict_source_scope_counts separately exclude theQuranwordingambiguity.','strict_source_scope_counts':{'gold':{'correct':23,'partial':2,'abstention':3,'incorrect':1,'source_scope_uncertain':1},'tfidf_retrieval':{'correct':22,'partial':3,'abstention':4,'source_scope_uncertain':1}},'automatic_proxy_counts':proxy,'engineering_gate':{'suggested_threshold_correct':24,'suggested_denominator':30,'gold_passage_conditioned_correct_excluding_partial':24,'partial_not_counted':2,'strict_unambiguous_gold_correct':23,'passage_conditioned_gold_adequate':24,'unconditional_pass':False,'decision':'BORDERLINE_DIAGNOSTIC_NOT_UNCONDITIONAL_PASS','interpretation':'Strictunambiguousadequacyis23/30;24/30requiresacceptingtheQuranparchmentboundasapassage-conditionedanswer. The24/30thresholdwasonlyasuggestedengineeringsanityexample,notapreregisteredstatisticaltestorareason toretunethequestions. No unconditionalpass. E1canbeperformedasboundedcomparisonwithpre-frozensource-valid85subsetandactualcleanutilitylimits,notasaqualifieddeploymentclaim.','scope_sensitivity':'Onecounteditem(Quran)correctlyrepeatstheannotatedparchmentdatebutretainsmanuscript-versus-writingambiguity. Ifrequiringunambiguouscurrent-worldtaskvalidityfor everycounteditem, only23/30remainclearlysupported; reportthissensitivityanddo nottreatthethresholdasastatisticalguarantee.','next_action':'Donotdropfailedquestionsorretuneprompt/aliasesfromtheseoutputs. Keepall30; usepre-frozensource-validtestmask andscope-specificsemanticreportinginE1.'},'records':reviews}
obj['reviewer_independence']='Review kept separate from generation implementation and source-question repair. This is a single review, not an independent panel or external replication.'
obj['scope']='Read all 30 gold and 30 TF-IDF normal responses against the source and frozen questions/answers. No-retrieval summaries are automatic text proxies only. Normal review checks answers relative to the gold source, not entailment by every actual retrieved passage.'
obj['semantic_counts_scope']='Passage-conditioned interpretation. Strict source-scope counts separately exclude the Quran question ambiguity.'
obj['engineering_gate']['interpretation']='Strict, unambiguous adequacy is 23/30. The 24/30 result accepts the Quran parchment bound as a passage-conditioned answer. The suggested engineering threshold is not a statistical test or a reason to retune questions. There is no unconditional pass. E1 can remain a bounded comparison with the frozen source-valid subset and actual clean utility limiting its claims.'
obj['engineering_gate']['scope_sensitivity']='One counted Quran answer repeats the annotated parchment date, but manuscript writing need not share that date. Excluding this ambiguity leaves 23/30. Report both counts; the threshold gives no statistical guarantee.'
obj['engineering_gate']['next_action']='Keep all 30 questions and frozen prompts/aliases. Do not tune them for this threshold. Apply the pre-evaluation source-valid mask and report actual clean utility in E1.'
(OUT/'Q_semantic_review.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
lines=['# 新开发Q：单次语义检查','', '性质：单个单次审核，未进行真人双评、外部复现或新模型推理。审阅全部30条gold与30条TF-IDF正常检索回答，并对照源文、已冻结题目及答案；未据输出修改提示或答案别名。','', '## 结论','', '**Q不能写成无条件通过。** Gold严格、无题意歧义的充分正确数为23/30；将Quran的羊皮纸测年界限作为以源文为条件的回答接受时，为24/30。另有2条部分正确、3条拒答、1条错误。两条部分答案不计入充分正确数。24/30原本只是建议的工程sanity示例，不能为了碰到门槛而放宽裁决，更不是统计保证或80%的现实事实准确率。','', '一条已计入的Quran题仍有“羊皮纸测年不等于文字书写日期”的源文范围歧义：回答671AD忠实于注释及段落的羊皮纸界限，但不能据此证明手稿文字也在该年前写成。若要求每个计入案例都没有这一题意歧义，则充分支持的数量降为23/30。因此应保留完整30分母与此敏感性，E1仅按预先冻结的源文有效性范围报告，不继续因Q输出换题、调提示或补别名。','', '| 条件 | 充分正确 | 部分 | 拒答 | 错误 |','|---|---:|---:|---:|---:|','| Gold证据（源文条件解释） | 24/30 | 2 | 3 | 1 |','| TF-IDF正常检索 | 23/30 | 3 | 4 | 0 |','', '若开展E1，应冻结当前配置并依预先审查的source-valid85题与实际clean效用限制主张；不继续为了过门槛调题或别名。正常检索与gold的总体差距较小，但逐题路径不同：Whitehead在gold答对、正常检索拒答；Swaziland在gold仅给缩略校名、正常检索给出完整有效替代学校；Bermuda在gold拒答、正常检索提到正确方法却附加了源文不支持的地区比较。该开发样本不能单独断定“检索已经充分”，因为尚须检查真实检索证据和正式测试。','', '## 字符串分数与语义审核的差别','', '| 条件 | 规范化整句匹配 | 规范化参考提及 |','|---|---:|---:|']
for k,name in [('no_retrieval','无检索'),('gold','Gold'),('tfidf_retrieval','TF-IDF正常检索')]:lines.append(f'| {name} | {proxy[k]["normalized_exact"]}/30 | {proxy[k]["normalized_mention"]}/30 |')
lines+=['', '上述是本审核器明确规范化规则下的文本代理，不能拿它代替语义准确率；无检索只列代理分数，未给其完整语义排行榜。','', '- Gold中多岛列表、Nicaraguans、P-700Granitoffensivemissiles、Milošević死亡陈述均与完整reference不同但语义足够。','- NationalCyber-Abwehrzentrum遗漏/混合官方扩写，SwazChristianUniversity截短正式校名，保守归部分正确。未新增这两个别名。','- TF-IDF的Bermuda回答以Geneticstudies开头，但附加WestandSouthAfrica对比，源文实际对比的是WestIndies与UnitedStates。只看reference提及会错当充分正确。','- TF-IDF的1757仅给年，未给完整事件日期，保守归部分；没有看到输出后再增加1757别名。','', '## 逐题Gold裁决','', '| 序号 | QID | 回答 | 裁决 | 理由 |','|---|---|---|---|---|']
for r in reviews:
 if r['setting']=='gold':lines.append(f'| {r["index_1based"]} | {r["qid"]} | {r["response"].replace(chr(10)," ").replace("|","/")} | {r["judgment"]} | {r["reason"]} |')
lines+=['', '逐题完整字段与TF-IDF裁决见`Q_semantic_review.json`。本审核不改变原始生成、原始代理计分或冻结数据。','']
(OUT/'Q_Semantic_Results.md').write_text('\n'.join(lines))
print(json.dumps({'semantic_counts':counts,'automatic_proxies':proxy,'gold_gate':obj['engineering_gate']},ensure_ascii=False))
