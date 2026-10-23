"""Construct paired contexts from detector artifacts without fitting anything.

Prerequisites (created by experiment/benchmark.py):
output/experiment/filtered_groups.jsonl, predictions.jsonl, results.json.

Clean retrieval features are recomputed after removing the sole attack passage;
all thresholds, text-only scores and fusion coefficients stay frozen.
"""
from pathlib import Path
import hashlib,json,math
import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'output'/'experiment';OUT=ROOT/'output'/'generation'
METHODS=['acceptall','keyword','lexical','retrieval','neural','combined']

def retrieval_scores(passages,question):
 v=HashingVectorizer(n_features=2**18,alternate_sign=False,ngram_range=(1,2),norm='l2',lowercase=True)
 x=v.transform([p['text'] for p in passages]);q=v.transform([question])
 qc=(x@q.T).toarray().ravel();pair=(x@x.T).toarray()
 peer=(pair.sum(1)-np.diag(pair))/(len(passages)-1)
 return 1-.5*qc-.5*peer

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 paths=[SOURCE/'filtered_groups.jsonl',SOURCE/'predictions.jsonl',SOURCE/'results.json']
 groups=[json.loads(x) for x in paths[0].read_text().splitlines()]
 preds={r['id']:r for r in (json.loads(x) for x in paths[1].read_text().splitlines())}
 config=json.loads(paths[2].read_text());thresholds=config['thresholds'];fusion=config['fusion']
 groups=[g for g in groups if g['split']=='test_joint']
 assert len(groups)==96,'Frozen protocol requires ALL96 joint-shift groups.'
 rows=[]
 for g in groups:
  attack=[p for p in g['passages'] if p['label']==1]
  assert len(attack)==1
  family=attack[0]['family'];topic=g['passages'][0]['topic']
  clean=[p for p in g['passages'] if not p['label']]
  clean_r=retrieval_scores(clean,g['question'])
  clean_retained={method:[] for method in METHODS}
  for j,p in enumerate(clean):
   score=dict(preds[p['id']]['scores']);score['retrieval']=float(clean_r[j])
   z=fusion['intercept']+fusion['weights'][0]*score['neural']+fusion['weights'][1]*score['retrieval']
   score['combined']=1/(1+math.exp(-z))
   for method in METHODS:
    if method=='acceptall':block=False
    else:
     threshold=thresholds[method]
     block=threshold is not None and score[method]>=threshold
    if not block:clean_retained[method].append(p['id'])
  for method in METHODS:
   for condition in ['clean','attacked']:
    if condition=='clean':ids=clean_retained[method]
    else:ids=[p['id'] for p in g['passages']] if method=='acceptall' else g['retained'][method]
    context='\n\n'.join(p['text'] for p in g['passages'] if p['id'] in ids)
    rows.append({'group_id':g['group_id'],'split':g['split'],'family':family,'topic':topic,'gate':method,'condition':condition,'query':g['question'],'gold_answer':g['gold_answer'],'attack_target':g['attack_target'],'retained_ids':ids,'retained_benign_count':sum(p['id'] in ids and p['label']==0 for p in g['passages']),'retained_attack_count':sum(p['id'] in ids and p['label']==1 for p in g['passages']),'retained_benign_evidence_count':sum(p['id'] in ids and p['answer_evidence'] for p in g['passages']),'context':context})
 (OUT/'evaluation_contexts.jsonl').write_text('\n'.join(json.dumps(r,ensure_ascii=False) for r in rows)+'\n')
 meta={'source_files':[{"path":str(p.relative_to(ROOT)),"sha256":hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths],'split':'test_joint','n_groups':len(groups),'n_rows':len(rows),'gates':METHODS,'clean_protocol':'remove sole malicious passage; retain benign quoted directives; independently recompute clean retrieval and fusion scores; retain frozen text-only scores, coefficients and thresholds','context_protocol':'preserve original candidate order; join accepted passage texts using a blank line; no labels or gold answers are inserted','thresholds':thresholds,'fusion':fusion}
 (OUT/'context_preparation.json').write_text(json.dumps(meta,indent=2))
 print(json.dumps({'n_groups':len(groups),'n_rows':len(rows),'gates':METHODS},indent=2))

if __name__=='__main__':main()
