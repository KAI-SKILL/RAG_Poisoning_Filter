"""Fit on old70, calibrate on new normal100, then freeze and select contexts."""
from pathlib import Path
import argparse,collections,hashlib,json,time,sys
import numpy as np
import joblib
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from old_reanalysis.detectors import archived_training_rows,freeze_detectors,apply_detectors,fit_summary
from prompts import prompt

def rows(p):return [json.loads(l)for l in Path(p).read_text().splitlines()if l.strip()]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,a):Path(p).write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
def dump_rows(p,a):Path(p).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n'for r in a))
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--features',type=Path,required=True);p.add_argument('--pools',type=Path,required=True);p.add_argument('--old-split',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
 allrows=rows(a.features);poolrows=rows(a.pools);project=HERE.parent;split=json.loads(a.old_split.read_text());start=time.monotonic()
 train=archived_training_rows(project,split['train_qids'])
 original_calibration=[r for r in allrows if r['split']=='calibration']
 assert all(r['setting']=='clean' and r['label']==0 for r in original_calibration),'Calibration must contain only clean normal pools before clean->none API mapping'
 calibration=[{**r,'setting':'none'}for r in original_calibration];test=[r for r in allrows if r['split']=='test']
 assert len(calibration)==2000 and len({r['qid']for r in calibration})==100
 assert len({r['qid']for r in test})==100 and len(test)==8500
 assert {r['source_group']for r in calibration}.isdisjoint(r['source_group']for r in test)
 assert len({(r['qid'],r['setting'],r['index'])for r in allrows})==len(allrows),'Duplicate candidate rows'
 states=freeze_detectors(train,calibration,test)
 guard_scores=np.array([r['features']['guard']for r in calibration]);guard_thresholds={point:float(np.quantile(guard_scores,1-alpha,method='higher'))for point,alpha in [('1pct',.01),('5pct',.05)]}
 assert all(float(np.mean(guard_scores>guard_thresholds[point]))<=alpha+1e-12 for point,alpha in [('1pct',.01),('5pct',.05)])
 write(a.output/'fit_frozen.json',{'status':'FROZEN_TRAIN_AND_CALIBRATION_ONLY','training_qids':split['train_qids'],'training_rows':len(train),'training_features_origin':'unchanged original neural archives; new linear fits','calibration_qids':sorted({r['qid']for r in calibration}),'calibration_rows':2000,'models':fit_summary(states),'guard_only_thresholds':guard_thresholds,'guard_only_calibration_scores':guard_scores.tolist(),'features_sha256':sha(a.features),'old_split_sha256':sha(a.old_split),'code_sha256':sha(__file__)})
 joblib.dump(states,a.output/'frozen_detectors.joblib')
 params={}
 for m,s in states.items():
  if s['columns'] is not None:
   sc=s['model'].steps[0][1];lr=s['model'].steps[-1][1]
   params[m]={'columns':s['columns'],'mean':sc.mean_.tolist(),'scale':sc.scale_.tolist(),'coef':lr.coef_[0].tolist(),'intercept':float(lr.intercept_[0]),'thresholds':s['thresholds']}
 write(a.output/'linear_parameters.json',params)
 sparse=states['tfidf_lr']['model'];union=sparse.named_steps['features'];sparse_lr=sparse.named_steps['lr'];branches=[];offset=0
 for name,vectorizer in union.transformer_list:
  size=len(vectorizer.vocabulary_)
  branches.append({'name':name,'offset':offset,'features':size,'vocabulary':{term:int(index)for term,index in vectorizer.vocabulary_.items()},'idf':vectorizer.idf_.tolist(),'analyzer':vectorizer.analyzer,'ngram_range':list(vectorizer.ngram_range),'strip_accents':vectorizer.strip_accents,'lowercase':vectorizer.lowercase,'sublinear_tf':vectorizer.sublinear_tf,'norm':vectorizer.norm,'token_pattern':vectorizer.token_pattern,'binary':vectorizer.binary,'use_idf':vectorizer.use_idf})
  offset+=size
 assert offset==len(sparse_lr.coef_[0])
 write(a.output/'tfidf_parameters.json',{'status':'JSON_EXPORT_OF_THIS_FITTED_SPARSE_MODEL_NO_REFIT','branches':branches,'coef':sparse_lr.coef_[0].tolist(),'intercept':float(sparse_lr.intercept_[0]),'thresholds':states['tfidf_lr']['thresholds'],'feature_union_weights':None,'feature_union_normalization':'Each vectorizer L2-normalizes its own branch; no further union normalization.','input_view':'passage text only'})
 prediction={}
 detection=[]
 for point in ['1pct','5pct']:
  pr=apply_detectors(test,states,point)
  for r,q in zip(test,pr):
   q['risk']['guard_only']=r['features']['guard'];q['blocked']['guard_only']=r['features']['guard']>guard_thresholds[point]
   prediction[(r['qid'],r['setting'],r['index'],point)]=q
  methods=['ctx','no_guard','fused','tfidf_lr','guard_only']
  for subset in ['all100','source_valid85']:
   for setting in sorted({r['setting']for r in test}):
    rr=[r for r in test if r['setting']==setting and(subset=='all100'or r['source_supported'])]
    for m in methods:
     bad=[r for r in rr if r['label']];good=[r for r in rr if not r['label']]
     tp=sum(prediction[r['qid'],r['setting'],r['index'],point]['blocked'][m]for r in bad);fp=sum(prediction[r['qid'],r['setting'],r['index'],point]['blocked'][m]for r in good)
     detection.append({'point':point,'subset':subset,'setting':setting,'method':m,'questions':len({r['qid']for r in rr}),'malicious_candidates':len(bad),'benign_candidates':len(good),'tp':tp,'fp':fp,'recall':tp/len(bad)if bad else None,'fpr':fp/len(good)if good else None})
 write(a.output/'detection_summary.json',detection)
 predrows=[]
 for r in test:
  predrows.append({**{k:r[k]for k in ['qid','setting','index','id','label','family','text_hash','features']},'risk':prediction[r['qid'],r['setting'],r['index'],'1pct']['risk'],'blocked':{point:prediction[r['qid'],r['setting'],r['index'],point]['blocked']for point in ['1pct','5pct']}})
 dump_rows(a.output/'predictions.jsonl',predrows)
 requests=[];admission=[]
 bins=collections.defaultdict(list)
 for r in test:bins[r['qid'],r['setting']].append(r)
 for pool in poolrows:
  if pool['split']!='test':continue
  qid=pool['qid'];setting=pool['setting'];rr=sorted(bins[qid,setting],key=lambda r:r['index']);assert [r['id']for r in rr]==[d['id']for d in pool['pool']]
  methods=['ctx','no_guard','fused']if setting.startswith('benign_')or setting=='counterfactual_5'else ['none','ctx','no_guard','fused','tfidf_lr','guard_only']
  for m in methods:
   chosen=[d for i,d in enumerate(pool['pool'])if m=='none'or not prediction[qid,setting,i,'1pct']['blocked'][m]][:5]
   data={k:pool[k]for k in ['qid','question','split','source_group','title','source_title','answers','incorrect','source_supported','e2_selected']}
   row={**data,'setting':setting,'gate':m,'context_ids':[d['id']for d in chosen],'malicious_count':sum(d.get('label',0)for d in chosen),'gold_retained':any(d['id']==pool['gold_document_id']for d in chosen),'legitimate_support_retained':any(d.get('legitimate_support',False)for d in chosen),'empty_context':not chosen,'prompt':prompt(pool['question'],chosen),'working_point':'1pct'}
   requests.append(row);admission.append({k:v for k,v in row.items()if k not in ['prompt','answers','question']})
 assert len(requests)==2175 and len({(r['qid'],r['setting'],r['gate'])for r in requests})==2175
 dump_rows(a.output/'context_requests.jsonl',requests);dump_rows(a.output/'admission.jsonl',admission)
 write(a.output/'selection_manifest.json',{'status':'COMPLETE_FROZEN_SELECTION_NOT_GENERATION','requested_rows':2175,'E1_rows':1800,'E2_additional_rows':375,'unique_prompts':len({r['prompt']for r in requests}),'queries':100,'working_point':'1pct','fit_selection_seconds':time.monotonic()-start,'pool_features_sha256':sha(a.pools),'features_sha256':sha(a.features),'fit_metadata_sha256':sha(a.output/'fit_frozen.json'),'tfidf_parameters_sha256':sha(a.output/'tfidf_parameters.json'),'requests_sha256':sha(a.output/'context_requests.jsonl'),'predictions_sha256':sha(a.output/'predictions.jsonl'),'baseline_note':'guard_only is the same public component, not a reproduction of a full external defense.','new_model_inference':'No neural inference in this script; only preceding cache/feature manifests establish neural execution.'})
 print(json.dumps(json.loads((a.output/'selection_manifest.json').read_text())))
if __name__=='__main__':main()
