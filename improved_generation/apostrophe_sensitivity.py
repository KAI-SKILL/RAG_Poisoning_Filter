"""Post-run measurement sensitivity only; frozen scorer and model output unchanged.

Join apostrophes occurring inside words before applying the frozen string rules.
This prevents possessive Ocean's from creating a standalone reference letter S.
"""
from pathlib import Path
import csv,hashlib,json,re
from scoring import exact_match,bounded_mention
HERE=Path(__file__).resolve().parent;OUT=HERE/'output'
def joined(s):return re.sub(r"(?<=\w)['’](?=\w)",'',str(s))
rows=[json.loads(x) for x in (OUT/'raw_generations.jsonl').read_text().splitlines()]
changes=[];summary=[]
for r in rows:
 new={k:fn(joined(r[a]),joined(r['response'])) for k,a,fn in [('correct_exact','correct',exact_match),('target_exact','incorrect',exact_match),('correct_mention','correct',bounded_mention),('target_mention','incorrect',bounded_mention)]}
 new['both_mentioned']=new['correct_mention'] and new['target_mention']
 changed=[k for k in new if r[k]!=new[k]]
 if changed:changes.append({k:r[k] for k in ['qid','gate','setting','correct','incorrect','response']}|{'changed_fields':changed,'old':{k:r[k] for k in changed},'apostrophe_aware':{k:new[k] for k in changed}})
 r['_apostrophe_aware']=new
for gate in ['none','rule','guard','ctx','fused','oracle','aug_fused']:
 for setting in ['none','poison','ignore','stealth']:
  sel=[r for r in rows if r['gate']==gate and r['setting']==setting]
  summary.append({'gate':gate,'setting':setting,**{k+'_original':sum(r[k] for r in sel) for k in ['correct_exact','target_exact','correct_mention','target_mention','both_mentioned']},**{k+'_apostrophe_aware':sum(r['_apostrophe_aware'][k] for r in sel) for k in ['correct_exact','target_exact','correct_mention','target_mention','both_mentioned']}})
metadata={'status':'post-run sensitivity; original frozen outputs/statistics retained','reason':'within-word apostrophe should not manufacture a standalone single-letter answer token','normalization_change':"remove an apostrophe only when surrounded by word characters, then apply frozen score rules; no model/threshold/prompt change",'n_changed_condition_rows':len(changes),'affected_qids':sorted({r['qid'] for r in changes}),'raw_sha256':hashlib.sha256((OUT/'raw_generations.jsonl').read_bytes()).hexdigest()}
(OUT/'apostrophe_sensitivity.json').write_text(json.dumps({'metadata':metadata,'changes':changes,'condition_summary':summary},indent=2))
with (OUT/'apostrophe_sensitivity.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=summary[0]);w.writeheader();w.writerows(summary)
print(json.dumps(metadata,indent=2))
for r in summary:
 if any(r[k+'_original']!=r[k+'_apostrophe_aware'] for k in ['correct_exact','target_exact','correct_mention','target_mention','both_mentioned']):print(r)
