"""Check fresh pinned embeddings against supplied retrieval-score records.

Read-only numerical audit; no uploaded code/model is executed.
"""
from pathlib import Path
import json,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'output/improved_experiment';CACHE=BASE/'cache';OUT=ROOT/'improvement_audit/fresh_retrieval_anchor_audit.json'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
texts=json.loads((CACHE/'contriever_texts.json').read_text());idx={s:i for i,s in enumerate(texts)};a=np.load(CACHE/'contriever.npy',mmap_mode='r');assert len(texts)==a.shape[0]and a.shape[1]==768
progress=json.loads((CACHE/'contriever_progress.json').read_text());assert progress['done']==len(texts)
clean=json.loads((ROOT/'improved_experiment/inputs/clean_target_candidates.json').read_text());attacks=json.loads((ROOT/'improved_experiment/inputs/attacks_main.json').read_text());record={(r['qid'],r['doc_id']):r for r in[json.loads(x)for x in(BASE/'retrieval_anchor_rows.jsonl').read_text().splitlines()]}
results={}
def stats(ds):
 x=np.array(ds);assert max(x)<1e-3
 return {'n':len(x),'mean_abs_difference':float(x.mean()),'max_abs_difference':float(x.max()),'within_predeclared_1e_3_anchor_tolerance':True}
d=[]
for q in clean:
 qe=a[idx[attacks[q]['question']]]
 for p in clean[q]['docs'][:20]:
  score=float(a[idx[(p.get('title','')+' '+p['text']).strip()]]@qe);r=record[q,p['id']];assert r['stored']==p['score']and r['recomputed']==score;d.append(abs(score-p['score']))
results['clean_title_plus_text']=stats(d)
for name in['data','data_single']:
 d=[]
 for p in(ROOT/'new_reference'/name/'nq/retrieved').glob('*.jsonl'):
  for r in[json.loads(x)for x in p.read_text().splitlines()]:
   qe=a[idx[r['question']]]
   for p in r['pool']:
    if p['is_adv']:d.append(abs(float(a[idx[p['text']]]@qe)-p['score']))
 results[name+'_supplied_adversarial_scores']=stats(d)
metadata={'scope':'Fresh pinned Contriever cache independently checked against supplied stored clean and attack scores; does not authenticate supplied generation model.','cache_shape':list(a.shape),'cache_config':json.loads((CACHE/'contriever_config.json').read_text()),'model_manifest_sha256':h(ROOT/'improved_experiment/models/contriever/model_manifest.json'),'anchor_rows_sha256':h(BASE/'retrieval_anchor_rows.jsonl'),'results':results}
OUT.write_text(json.dumps(metadata,indent=2));print(json.dumps(results,indent=2))
