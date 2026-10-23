from pathlib import Path
import json,collections,hashlib
ROOT=Path('current/package/Group9_Project');OUT=Path('revision_work/utility_audit')
a=json.loads((OUT/'q_development30_materials.json').read_text());s=json.loads((OUT/'frozen_old100_split.json').read_text());screen=json.loads((OUT/'old100_evidence_screen.json').read_text())
rows=[json.loads(x) for x in (ROOT/'improved_generation/output/corrected/raw_generations.jsonl').read_text().splitlines()]
clean=[x for x in rows if x['gate']=='none' and x['setting']=='none']
labels={'missing_support':'缺少支持','supported':'支持充分','label_conflict':'标签冲突','insufficient_support':'支持不足','needs_question_qualification':'须限定题意','underspecified_question':'题意缺条件','temporal_conflict':'时间冲突','answer_type_mismatch':'答案类型不符'}
lines=['# Q前置检查：正常问答与证据有效性','',
'状态：旧数据的原30题有效性门槛未通过。未下载或运行新模型，未改动原项目输入、输出和评分。',
'', '## 已冻结的分割','',
f'旧100题按共享docID、规范化完整段落或相同Wikipedia题名并组，共{s["group_count"]}个来源联通组。组大小最大5题，使用固定哈希顺序和接近30的subset-sum选择，得到70训练/30开发。冻结发生在任何新模型输出之前，未按可回答性或模型结果选题。',
'', '分割文件为`frozen_old100_split.json`，记录UTC时间、源文件SHA256、全部来源组和分割规则。原100已用于探索与设计，70/30两部分均不能变成新盲测；正常校准和正式测试必须另行锁定。',
'', '## 30题逐条核查的结果','',
f'14题可直接定位相符支持，8题需先澄清时间/版本/奖项/题意，另8题有缺证据、错误标签、答案类型或未指明条件等问题。共22题能形成“已定位局部支持”的开发探针，但其中8题须改写题目限定词。其余8题保留在完整30题审查分母内，不能为了凑24/30而删去。',
'', '**原计划的gold证据24/30门槛不能在未经修复的这30题上直接解释。** 数据问题会把本该正确的回答判成错，也会迫使模型在无支持上下文中猜测。先修题目与参考、增加真实来源或另建预先锁定的开发质量套件，再判断模型是否合格。',
'', '下表的rank是旧clean20候选中的原顺序，未按新模型输出选择；“支持充分”只说明该归档段落/题名支持开发题目，不等于我们已核实所有现实世界事实在2026年仍成立。',
'', '| QID | 原问题 | 状态 | 局部支持rank | 处理 |','|---|---|---|---|---|']
for r in a['records']:
 note=r['audit_note'].replace('|','/')
 lines.append(f'| {r["qid"]} | {r["question_original"]} | {labels[r["audit_status"]]} | {r["support_rank_in_clean20"] or "—"} | {note} |')
lines += ['', '## 会影响结论的具体错误','',
'- `test47`把加拿大总理任期标为four years，候选rank5/6却明确写无固定任期。四年是选举安排，不能混成总理固定任期。加拿大国会官方程序说明还将议会期限与政府/总理任期分开。',
'- `test312`将“超过一半骨头在哪里”标为axial skeleton。NIH/NCI SEER给出成人通常206块骨头，axial80、appendicular126；axial不是多数。不能继续使用该标签计算事实准确率。',
'- `test412`把clock faces上的IIII当错误目标，但Seiko官方博物馆记录它是常见表盘写法。目标字符串出现不能自动视作攻击造成的事实错误。',
'- `test291`旧回答是“Adrenaline and noradrenaline.”，reference仅epinephrine。候选本身就把adrenaline与epinephrine写为同义词，因此这是明确的单参考漏判例；`test337`的red-white-blue和`test408`的acetate也有同类问题。',
'- `test177`排名3段落的题名是Ariana Richards，正文只有Richards。旧生成提示不含题名，丢失了名字线索。新提示如加入题名必须冻结统一格式，并明确这是管线变化。',
'- `test1`的23出现在引文编号或第一季集数中，不能据此说第四季答案已被检索到。`test282`根本未给赛季；`test348`问命名来源而标签只是人名，均不能按单字符串替代任务语义。',
'', '原始测量仍然保留：无过滤clean整句精确匹配13/100、reference mention24/100、拒答18/100，2条回答触及64-token上限。上述语义例子不是新模型结果，也不是对全部100题的完整人工语义重评分，不能直接将13或24改成“新准确率”。',
'', '## 全100题的证据线索筛查','',
'去除方括号引用标记后，用词/数值边界搜索原reference；以title+text另算一份。它只检查文字线索，不做蕴含、真假或完整答案判断。数字和yes/no仍可能出现在无关语境中，别名也可能造成漏检。',
'', '| 筛查项 | 数量 |','|---|---:|',
f'| top5正文含原reference | {screen["summary"]["lexical_top5_text_presence"]}/100 |',
f'| top20正文含原reference | {screen["summary"]["lexical_top20_text_presence"]}/100 |',
f'| top20题名或正文含原reference | {screen["summary"]["title_or_text_presence"]}/100 |',
f'| 有需说明的时间/范围/标签/评分风险 | {screen["summary"]["manual_risk_flags"]}/100 |',
'', '这里的33项是风险提示数，不是33道已证实错题。其余题也不被自动认证为可靠真值。逐题信息见`old100_evidence_screen.json`。',
'', '| top5正文线索 | 旧reference mention=true | 旧reference mention=false |','|---|---:|---:|','| 有 | 23 | 34 |','| 无 | 1 | 42 |',
'', '该表说明正常效用弱同时涉及候选证据、模型利用证据与测量。不能仅凭模型规模将原因归于生成器，也不能把字符串线索当真正的检索可回答率。',
'', '## 给执行者的文件接口','',
'- `q_development30_materials.json`：完整30题、原题/标签、来源组、支持或缺失、风险、normal top5、原回答与旧指标。',
'- `q_local_support_probe22.json`：22条局部支持开发诊断，每题有no retrieval、gold local support、normal top5三条件；8条限定改题显式标记。只可报告n=22及相应开发范围。',
'- `scoring_failure_examples.json`：明确别名/格式漏判和需裁决的部分回答例子。',
'- `old100_evidence_screen.json`：100题线索筛查和33个风险记录。',
'', '建议执行者先冻结答案别名、判分rubric和提示格式，再看新输出；不要使用同一模型自己的回答决定哪些题有答案。真实gold应来自独立可信材料，模型生成一段包含reference的文字不能替代gold证据。',
'', '## 已核对的原始外部来源','',
'- 加拿大国会，House of Commons Procedure and Practice，Duration of a Parliament and a Ministry：https://www.ourcommons.ca/marleaumontpetit/DocumentViewer.aspx?Language=E&Print=2&Sec=Ch02&Seq=2',
'- NIH/NCI SEER，Divisions of the Skeleton：https://training.seer.cancer.gov/anatomy/skeletal/divisions/',
'- Seiko Museum，The Mystery of Numerical Notation on the Dial Plate：https://museum.seiko.co.jp/en/knowledge/trivia02/',
'- Apple原始2016新闻稿，宣布/订购/发售三日期分列：https://www.apple.com/newsroom/2016/03/21Apple-Introduces-iPhone-SE-The-Most-Powerful-Phone-with-a-Four-inch-Display/',
'', '以上使用的是原始机构/厂商材料；其他局部gold来自用户已提供的归档Wikipedia候选，逐段保留id、题名、正文和hash，未声称它们都是原始独立事实来源。','']
(OUT/'Q_Preflight_Analysis.md').write_text('\n'.join(lines))
# Verify all audit records resolve to exact unchanged archived evidence.
assert len(a['records'])==30 and set(x['qid'] for x in a['records'])==set(s['development_qids'])
assert len(set(s['train_qids'])&set(s['development_qids']))==0
c=json.loads((ROOT/'improved_experiment/inputs/clean_target_candidates.json').read_text())
for r in a['records']:
 if r['support_document']:
  assert c[r['qid']]['docs'][r['support_rank_in_clean20']-1]==r['support_document']
  assert hashlib.sha256(json.dumps(r['support_document'],ensure_ascii=False,sort_keys=True).encode()).hexdigest()==r['support_document_sha256']
for g in s['groups']:assert set(g['qids']).issubset(set(s[g['split']+'_qids'] if g['split']=='development' else s['train_qids']))
(OUT/'audit_validation.json').write_text(json.dumps({'status':'passed','split_training':70,'split_development':30,'source_groups':83,'support_exact_archived_documents':22,'all30_preserved':True,'new_inference_executed':False,'original_data_gate_passed':False,'limits':'Validation checks frozen split and exact evidence identity, not independent current-world factual certification of100answers.'},ensure_ascii=False,indent=2)+'\n')
print('analysis and validation ready')
