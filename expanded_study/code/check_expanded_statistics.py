"""Independently recompute all classification/paired intervals from saved scores.

This script loads no detector and executes no inference. The portable stdlib
verifier separately validates complete score binding, counts and tie-aware ranks.
"""
from pathlib import Path
import argparse,collections,hashlib,json,math
import numpy as np
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
parser.add_argument('--externalroot',type=Path,required=True,help='Pinned passive source folder containing InjecAgent and AgentDojo JSONL files')
parser.add_argument('--receipt',type=Path,help='Optional receipt output; omitted means print only')
args=parser.parse_args();BASE=args.root.resolve();ROOT=BASE/'results'
def read(name):return json.loads((ROOT/name).read_text())
def rows(path):return [json.loads(l)for l in Path(path).open()if l.strip()]
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def cohorts(row):return ['all']+[k+':'+str(row.get(k,'unspecified'))for k in ['family_id','template_id','placement','encoding_mode','language_mode','objective','threat_type']]
threshold=read('thresholds_frozen.json');pointkey={'new_normal_1pct':'threshold_1pct','new_normal_5pct':'threshold_5pct','previous_external_5pct':'previous_threshold'}
events=rows(ROOT/'case_predictions_complete.jsonl');documents=rows(ROOT/'document_predictions.jsonl');hosts=rows(BASE/'data/hosts.jsonl');cache={(r['model'],r['text_sha256']):r['score']for r in rows(ROOT/'unique_document_scores.jsonl')}
ordinary=[{'label':0,'article_id':r['article_id'],'scores':{m:cache[m,hashlib.sha256(r['context'].encode()).hexdigest()]for m in threshold}}for r in hosts if r['split']=='test']
records={};indexes=collections.defaultdict(list)
for level,rr in [('insertion_set',events),('local_document',[r for r in documents if r['local_label']is not None]),('ordinary_context',ordinary)]:
 records[level]=rr
 for index,r in enumerate(rr):
  for cohort in (['all']if level=='ordinary_context'else cohorts(r)):indexes[level,cohort].append(index)
selection_cache={}
def interval(groups,values,draws):
 bins=collections.defaultdict(lambda:[0,0])
 for group,value in zip(groups,values):bins[group][0]+=int(value);bins[group][1]+=1
 ordered=sorted(bins);n=len(ordered);key=(n,draws)
 if key not in selection_cache:selection_cache[key]=np.random.default_rng(20261022).integers(0,n,size=(draws,n))
 selected=selection_cache[key];sums=np.array([bins[g][0]for g in ordered],dtype=np.float64);counts=np.array([bins[g][1]for g in ordered],dtype=np.float64)
 estimates=sums[selected].sum(axis=1)/counts[selected].sum(axis=1)
 return {'point':float(np.mean(values)),'ci':np.quantile(estimates,[.025,.975]).tolist(),'groups':n}
def compare(actual,saved,groupkey='article_groups',cikey='ci95_article_percentile'):
 assert abs(actual['point']-saved['point'])<=1e-12,(actual,saved)
 assert np.allclose(actual['ci'],saved[cikey],rtol=0,atol=1e-12),(actual,saved)
 assert actual['groups']==saved[groupkey],(actual,saved)
checks=0
for summary in read('classification_summary.json'):
 level=summary['level'];rr=[records[level][i]for i in indexes[level,summary['cohort']]];labelkey='local_label'if level=='local_document'else'label';model=summary['model'];cut=threshold[model][pointkey[summary['operating_point']]]
 assert len(rr)==summary['n']and len({r['article_id']for r in rr})==summary['articles']
 for label,metric in [(1,'recall_uncertainty'),(0,'fpr_uncertainty')]:
  subset=[r for r in rr if r[labelkey]==label]
  if not subset:assert metric not in summary;continue
  saved=summary[metric];actual=interval([r['article_id']for r in subset],[r['scores'][model]>cut for r in subset],saved['draws']);compare(actual,saved);checks+=1
pairedchecks=0
for saved in read('classification_paired_differences.json'):
 label=1 if saved['metric']=='recall'else 0;rr=[events[i]for i in indexes['insertion_set',saved['cohort']]if events[i]['label']==label];key=pointkey[saved['operating_point']]
 delta=[int(r['scores']['LinearSVC']>threshold['LinearSVC'][key])-int(r['scores']['LR']>threshold['LR'][key])for r in rr]
 actual=interval([r['article_id']for r in rr],delta,saved['draws']);assert len(rr)==saved['n'];compare(actual,saved);pairedchecks+=1
# Independently reconstruct external task-component grouping by graph traversal.
source=args.externalroot.resolve()
external=rows(source/'injecagent_base_contexts.jsonl')+rows(source/'agentdojo_clean_tool_outputs_unique.jsonl');rawmap={r['id']:r for r in external};predictions=rows(ROOT/'external_predictions.jsonl');graph=collections.defaultdict(set)
for r in external:
 if r['dataset'].startswith('AgentDojo'):
  groups=r.get('all_source_groups')or[r['source_group']]
  for group in groups:graph[group].update(groups)
components={}
for start in sorted(graph):
 if start in components:continue
 todo=[start];seen=set()
 while todo:
  node=todo.pop()
  if node in seen:continue
  seen.add(node);todo.extend(graph[node]-seen)
 canonical=min(seen)
 for node in seen:components[node]=canonical
extindexes=collections.defaultdict(list)
for p in predictions:
 raw=rawmap[p['id']];expected=components[(raw.get('all_source_groups')or[raw['source_group']])[0]]if raw['dataset'].startswith('AgentDojo')else raw.get('payload_parent')or raw['source_group'];assert p['cluster_id']==expected
 assert p['text_sha256']==hashlib.sha256(raw['text'].encode()).hexdigest()
 for cohort in [p['dataset'],p['dataset']+'/family:'+p['family']]:extindexes[cohort].append(p)
externalchecks=0
for saved in read('external_summary.json'):
 rr=extindexes[saved['cohort']];model=saved['model'];cut=threshold[model][pointkey[saved['operating_point']]]
 assert len(rr)==saved['n']and len({r['cluster_id']for r in rr})==saved['clusters']
 assert len({r['payload_parent']for r in rr if r.get('payload_parent')})==saved['payload_parent_groups']
 assert len({r['source_group']for r in rr})==saved['user_task_parent_groups']
 for label,metric in [(1,'recall_uncertainty'),(0,'fpr_uncertainty')]:
  subset=[r for r in rr if r['label']==label]
  if not subset:continue
  state=saved[metric];actual=interval([r['cluster_id']for r in subset],[r['scores'][model]>cut for r in subset],state['draws']);compare(actual,state,'cluster_groups','ci95_cluster_percentile');externalchecks+=1
 if'alternative_user_task_group_recall'in saved:
  state=saved['alternative_user_task_group_recall'];actual=interval([r['source_group']for r in rr],[r['scores'][model]>cut for r in rr],state['draws']);compare(actual,state,'user_task_groups','ci95_user_task_percentile');externalchecks+=1
receipt={'status':'PASS','classification_summary_rows':len(read('classification_summary.json')),'classification_article_bootstrap_intervals_recomputed':checks,'paired_classifier_difference_intervals_recomputed':pairedchecks,'external_parent_or_component_intervals_recomputed':externalchecks,'external_prediction_cluster_labels_verified':len(predictions),'AgentDojo_connected_task_components':len(set(components.values())),'source_event_file':'case_predictions_complete.jsonl','source_event_sha256':sha(ROOT/'case_predictions_complete.jsonl'),'source_summary_sha256':sha(ROOT/'classification_summary.json'),'model_loads':0,'model_predictions':0,'detector_fits':0,'scope':'Independent article and passive-source grouped bootstrap recomputation from saved frozen scores; construction-conditional descriptive intervals, no agent or generator attack success.'}
if args.receipt:args.receipt.write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
