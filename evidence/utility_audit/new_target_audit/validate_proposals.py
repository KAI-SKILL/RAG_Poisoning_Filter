from pathlib import Path
import json,hashlib,re
p=Path('revision_work/utility_audit/new_target_audit/target_proposals.json');x=json.loads(p.read_text());rs=[json.loads(s) for s in Path('revision_work/new_eval_data/test_records.jsonl').read_text().splitlines()];by={r['qid']:r for r in rs};checks=[]
for r in x['records']:
 s=by[r['qid']];text=s['gold_passage'].replace(s['correct'],r['proposed_incorrect']);applied=[]
 for e in r['extra_replacements_after_default']:
  n=text.count(e['from']);applied.append({'from':e['from'],'matches':n});text=text.replace(e['from'],e['to'])
 checks.append({'qid':r['qid'],'target':r['proposed_incorrect'],'target_occurs_after_replacement':r['proposed_incorrect'] in text,'reference_remains_after_replacement':s['correct'] in text,'extra_replacement_matches':applied,'proposed_counterfactual_text':text,'source_eligibility':r['valid_attack_eligibility']})
assert len(checks)==100
assert all(y['target_occurs_after_replacement'] for y in checks)
assert not any(y['reference_remains_after_replacement'] for y in checks)
assert all(v['matches']>=1 for y in checks for v in y['extra_replacement_matches'])
Path('revision_work/utility_audit/new_target_audit/counterfactual_integration_preview.json').write_text(json.dumps({'status':'PREVIEW_ONLY_NOT_FORMAL_DATASET','model_outputs_used':False,'proposals_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'checks':checks},ensure_ascii=False,indent=2)+'\n')
notes=['# 新100题错误目标独立审查','', '未读取任何模型输出。每题对照问题、原reference及源文中的答案关系，改用语义类型匹配的目标；不按攻击成功率筛选。原始100题分母保留，15题源文本身有问题不被升级为可靠语义攻击。','', '结果：100个候选目标均与参考答案/别名不同，且未直接出现在gold段落。85题可作明确标注的snapshot反事实；15题按源文审查withheld。所有数字型目标保留单位和基本格式，日期保持有效日期，人名/地名/学校/作品/机构分别对应原问题类型。','', '这次审核以归档源文关系为条件，不是100次独立现实世界事实核验。有些开放问题在现实中可有多个正确答案，因此后续应报告相对该源文的目标采纳，不直接宣称每个目标都是现实世界唯一错误答案。','', '额外一致性处理：LiquidTelecom单位换算；Noblegases语法；RichardRussell州名/代指；Czech数量比较词；GreatPlains两种英制/公制单位；Delhi人数与比较词。详见逐题extra_replacements_after_default。Digimon目标已避开包含原题名DigimonWorld的DigimonWorld2，采用另一游戏DigimonRumbleArena，避免机械制造双答案命中。','', 'Pegasys与Housemusic两题原ref即有冲突，不通过替换一个同类型target掩盖。宗教/历史政治题保留某来源/某群体说法的归因，不将其改写成无归因事实。','', '文件：target_proposals.json为逐题正式建议；counterfactual_integration_preview.json仅用于整合检查，不是已冻结正式数据集。每个额外替换均验证能在默认替换后匹配至少一次，100条预览均包含目标且不保留完整原reference。']
Path('revision_work/utility_audit/new_target_audit/Target_Audit_Notes.md').write_text('\n'.join(notes)+'\n')
print('100 integration previews checked; all companion replacements applied; references absent.')
