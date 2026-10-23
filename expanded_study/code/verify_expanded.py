"""Verify saved expanded-study artifacts without model loading or network.

Only Python's standard library is used. This checks saved byte/decision/count
consistency; it neither proves historical execution nor reruns statistical CIs.
"""
from pathlib import Path
import argparse, collections, hashlib, json, math, re

MODELS=('LR','LinearSVC')
POINTS=(('new_normal_1pct','threshold_1pct'),('new_normal_5pct','threshold_5pct'),('previous_external_5pct','previous_threshold'))


# Public-release checks preserve historical references without asserting byte identity.
import sys as _release_sys
_release_root = next(path for path in Path(__file__).resolve().parents
                     if (path / "tools/public_release_integrity.py").is_file())
_release_sys.path.insert(0, str(_release_root / "tools"))
from public_release_integrity import (
    reference_sha, reference_size, published_sha, matches_reference,
    matches_size_reference, provenance_summary,
)

def sha(path):
 return reference_sha(path)  # Archived-reference mode for saved numerical checks.

def tsha(text):return hashlib.sha256(text.encode()).hexdigest()
def rows(path):
 with Path(path).open(encoding='utf-8')as f:
  for line in f:
   if line.strip():yield json.loads(line)
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def close(a,b):return (a is None and b is None)or(a is not None and b is not None and abs(float(a)-float(b))<=1e-12)
def check(condition,message):
 if not condition:raise AssertionError(message)
def did(doc):return str(doc.get('doc_id',doc.get('document_id','')))
def cohorts(row):
 out=['all']
 for dimension in ('family_id','template_id','placement','encoding_mode','language_mode','objective','threat_type'):
  out.append(dimension+':'+str(row.get(dimension,'unspecified')))
 return out

def accumulate(bucket,key,label,blocked):
 # tp,fp,tn,fn
 row=bucket.setdefault(key,[0,0,0,0])
 index=0 if label and blocked else 1 if not label and blocked else 2 if not label else 3
 row[index]+=1

def compare_counts(row,counter,label):
 tp,fp,tn,fn=counter;n=tp+fp+tn+fn
 for key,value in [('n',n),('tp',tp),('fp',fp),('tn',tn),('fn',fn)]:check(row[key]==value,f'{label}: {key}')
 for key,value in [('malicious_or_joint_attack_sets',tp+fn),('benign',fp+tn)]:
  if key in row:check(row[key]==value,f'{label}: {key}')
 mixed=bool(tp+fn and fp+tn)
 expected={'recall':tp/(tp+fn)if tp+fn else None,'fpr':fp/(fp+tn)if fp+tn else None,'precision':tp/(tp+fp)if mixed and tp+fp else None,'f1':2*tp/(2*tp+fp+fn)if mixed and 2*tp+fp+fn else None,'accuracy':(tp+tn)/n if mixed else None}
 for key,value in expected.items():check(close(row[key],value),f'{label}: {key}')

def ranking(records):
 # Independent tie-grouped Mann-Whitney AUROC and noninterpolated AP.
 groups=collections.defaultdict(lambda:[0,0])
 for label,value in records:groups[value][label]+=1
 positives=sum(pair[1]for pair in groups.values());negatives=sum(pair[0]for pair in groups.values())
 if not positives or not negatives:return None,None
 lower_neg=0;u=0.
 for value,(n,p)in sorted(groups.items()):u+=p*(lower_neg+.5*n);lower_neg+=n
 tp=fp=0;ap=0.
 for value,(n,p)in sorted(groups.items(),reverse=True):
  tp+=p;fp+=n;ap+=(p/positives)*(tp/(tp+fp))
 return u/(positives*negatives),ap


def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
 p.add_argument('--results',type=Path,help='Defaults to ROOT/results')
 p.add_argument('--models',type=Path,help='Defaults to ROOT/models')
 args=p.parse_args();root=args.root.resolve();out=(args.results or root/'results').resolve();models=(args.models or root/'models').resolve()
 manifest=read(out/'run_manifest.json');freeze=read(out/'execution_freeze.json');thresholds=read(out/'thresholds_frozen.json')
 check(manifest['status']=='COMPLETE_FROZEN_DETECTOR_EXPANDED_STRESS_TEST','Incomplete saved run')
 for name,expected in manifest['outputs'].items():check(sha(out/name)==expected,'Output byte hash: '+name)
 protocol=root/freeze.get('protocol_file','protocol_frozen.json')
 check(sha(protocol)==freeze['protocol_sha256']==manifest['protocol_sha256'],'Protocol hash')
 check(freeze['script_sha256']==manifest['script_sha256'],'Frozen executed-script agreement')
 candidates=[root/'code/evaluate_expanded.py',root/'code/evaluate_expanded_executed_v1.py']
 matched=[path for path in candidates if path.exists()and sha(path)==freeze['script_sha256']]
 check(bool(matched),'Executed evaluator hash');evaluator=matched[0]
 for kind,meta in freeze['inputs'].items():check(sha(root/meta['path'])==meta['sha256'],'Frozen input hash: '+kind)
 for name in MODELS:check(sha(models/(name+'.joblib'))==freeze['detector_sources'][name]['file_sha256']==thresholds[name]['model_sha256'],'Frozen detector bytes: '+name)
 check(sha(models/'models_frozen.json')==freeze['old_threshold_metadata_sha256'],'Previous threshold metadata')
 check(sha(out/'execution_freeze.json')==manifest['input_freeze_sha256'],'Execution freeze binding')
 check(sha(out/'thresholds_frozen.json')==manifest['threshold_freeze_sha256'],'Threshold freeze binding')
 event_file=out/'case_predictions.jsonl';recovery_used=False
 if (out/'case_prediction_recovery.json').exists():
  receipt=read(out/'case_prediction_recovery.json');check(receipt['status']=='RECOVERED_AND_PREFIX_VERIFIED','Recovery status')
  for path,key in [(out/receipt['original_event_file'],'original_event_sha256'),(out/receipt['complete_event_file'],'complete_event_sha256'),(out/'run_manifest.json','original_manifest_sha256'),(out/receipt['source_document_predictions_file'],'source_document_predictions_sha256'),(root/receipt['source_cases_file'],'source_cases_sha256')]:check(sha(path)==receipt[key],'Recovery source hash: '+str(path.name))
  original=out/receipt['original_event_file'];event_file=out/receipt['complete_event_file']
  original_rows=0;complete_rows=0;prefix_bytes=0
  with original.open('rb')as prior,event_file.open('rb')as complete:
   for raw in prior:
    check(raw==complete.readline(),'Original event is not exact byte prefix');original_rows+=1;prefix_bytes+=len(raw)
   complete_rows=original_rows+sum(1 for raw in complete if raw.strip())
  check(original_rows==receipt['original_event_records']and complete_rows==receipt['complete_event_records'],'Recovery record counts')
  check(complete_rows-original_rows==receipt['recovered_missing_event_records']and prefix_bytes==receipt['original_prefix_bytes'],'Recovery missing-record/prefix count')
  for key in ['model_loads','model_predictions','detector_fits','threshold_changes','generator_calls','network_calls']:check(receipt[key]==0,'Recovery execution declaration '+key)
  check(receipt['original_exact_byte_prefix']is True,'Recovery prefix declaration');recovery_used=True
 for key in ['detector_fits','neural_calls','generator_calls','target_tool_calls']:check(manifest[key]==0,'Unexpected execution declaration: '+key)
 hosts=list(rows(root/'data/hosts.jsonl'));hostmap={r['source_id']:r for r in hosts};cal=[r for r in hosts if r['split']=='calibration'];test=[r for r in hosts if r['split']=='test']
 check(len(hostmap)==len(hosts),'Duplicate host ids')
 check({r['article_id']for r in cal}.isdisjoint(r['article_id']for r in test),'Calibration/test article overlap')
 corpus=list(rows(root/'data/corpus.jsonl'));corpusmap={did(r):r for r in corpus};docsha={did(r):tsha(r['text'])for r in corpus}
 check(len(corpusmap)==len(corpus),'Duplicate corpus identity')
 check(all(r['document_id']in corpusmap and corpusmap[r['document_id']]['text']==r['context']for r in test),'Original supporting evidence missing')
 check(not {r['article_id']for r in cal}&{r['article_id']for r in corpus},'Calibration article in retrieval corpus')
 cal_scores=collections.defaultdict(list)
 for row in rows(out/'calibration_scores.jsonl'):
  host=hostmap[row['source_id']];check(host['split']=='calibration','Test host used for calibration');check(row['text_sha256']==tsha(host['context']),'Calibration text identity')
  cal_scores[row['model']].append(row['score'])
 for name in MODELS:
  ordered=sorted(cal_scores[name]);check(len(ordered)==len(cal),'Calibration score coverage')
  for point,alpha in [('new_normal_1pct',.01),('new_normal_5pct',.05)]:
   index=math.ceil((1-alpha)*(len(ordered)-1));expected=ordered[index];state=thresholds[name]['per_working_point_calibration'][point]
   check(close(state['threshold'],expected),'Quantile threshold '+name+'/'+point)
   check(state['order_statistic_one_based_rank']==index+1,'Calibration rank '+name+'/'+point)
   check(state['rejected']==sum(x>expected for x in ordered),'Strict calibration decisions')
   key=dict(POINTS)[point];check(close(thresholds[name][key],expected),'Working-point threshold')
  check(close(thresholds[name]['previous_threshold'],freeze['detector_sources'][name]['previous_threshold']),'Preserved previous threshold')
 # Input records are read once; do not retain full case texts after validation.
 case_meta={};input_docs={};template_counts=collections.Counter();template_questions=collections.defaultdict(set);numeric_sources=set()
 for case in rows(root/'data/cases.jsonl'):
  cid=case['case_id'];check(cid not in case_meta,'Duplicate case id');host=hostmap[case['question_id']]
  check(host['split']=='test'and case['article_id']==host['article_id']and case['query']==host['question'],'Case/source binding')
  check(len(case['attack_documents'])==len(case['matched_benign_documents']),'Unmatched insertion count')
  template_counts[case['template_id']]+=1;template_questions[case['template_id']].add(case['question_id']);numeric_sources.add(case['question_id'])
  meta={k:case.get(k,'unspecified')for k in ('case_id','family_id','template_id','question_id','article_id','placement','encoding_mode','language_mode','objective','threat_type')}
  meta['legitimate_base_document_id']=case['legitimate_base_document_id'];meta['conditions']={}
  for condition,field,label in [('attack','attack_documents',1),('matched_benign','matched_benign_documents',0)]:
   docids=[]
   for di,doc in enumerate(case[field]):
    ident=did(doc);check(ident not in docsha,'Inserted id overlaps existing corpus/input');actual=tsha(doc['text']);check(doc.get('text_sha256',actual)==actual,'Inserted text hash')
    local=doc.get('local_attack_label',None if case.get('label_scope')=='joint_context'and label else label)
    if not label:local=0
    docsha[ident]=actual;input_docs[ident]={'case_id':cid,'condition':condition,'index':di,'local_label':local,'text_sha256':actual};docids.append(ident)
   meta['conditions'][condition]=docids
  case_meta[cid]=meta
 check(len(template_counts)==24 and set(template_counts.values())=={1200},'Expected24templates×1200cases')
 check(all(len(q)==1200 for q in template_questions.values()),'Distinct questions per template')
 check(len(numeric_sources)==len(test)==1200,'Paired source count')
 scores={}
 for row in rows(out/'unique_document_scores.jsonl'):
  key=(row['model'],row['text_sha256']);check(key not in scores,'Duplicate unique score');check(math.isfinite(row['score']),'Nonfinite score');scores[key]=row['score']
 def score(name,ident):return scores[name,docsha[ident]]
 counters={};rankdata=collections.defaultdict(list);articledata=collections.defaultdict(set);seen_docs=set();local_count=0
 for row in rows(out/'document_predictions.jsonl'):
  ident=row['document_id'];check(ident not in seen_docs,'Duplicate document prediction');seen_docs.add(ident);source=input_docs[ident];meta=case_meta[row['case_id']]
  check(all(row[key]==meta[key]for key in ('case_id','family_id','template_id','question_id','article_id','placement','encoding_mode','language_mode','objective','threat_type')),'Document cohort metadata binding')
  check(row['text_sha256']==source['text_sha256']and row['local_label']==source['local_label']and row['condition']==source['condition']and row['insertion_index']==source['index'],'Document binding/label')
  for name in MODELS:check(close(row['scores'][name],score(name,ident)),'Document score cache binding')
  if row['local_label']is not None:
   local_count+=1
   for cohort in cohorts(meta):
    for name in MODELS:
     rankdata['local_document',cohort,name].append((row['local_label'],row['scores'][name]));articledata['local_document',cohort].add(meta['article_id'])
     for point,key in POINTS:accumulate(counters,('local_document',cohort,name,point),row['local_label'],row['scores'][name]>thresholds[name][key])
 check(seen_docs==set(input_docs),'Document prediction coverage')
 seen_cases=set()
 for row in rows(event_file):
  pair=(row['case_id'],row['condition']);check(pair not in seen_cases,'Duplicate condition prediction');seen_cases.add(pair);meta=case_meta[row['case_id']];identifiers=meta['conditions'][row['condition']]
  check(all(row[key]==meta[key]for key in ('case_id','family_id','template_id','question_id','article_id','placement','encoding_mode','language_mode','objective','threat_type')),'Condition cohort metadata binding')
  label=int(row['condition']=='attack');check(row['label']==label and row['documents']==len(identifiers),'Condition label/dose')
  for name in MODELS:
   maximum=max(score(name,ident)for ident in identifiers);check(close(row['scores'][name],maximum),'Case maximum-score aggregation')
   for cohort in cohorts(meta):
    rankdata['insertion_set',cohort,name].append((label,maximum));articledata['insertion_set',cohort].add(meta['article_id'])
    for point,key in POINTS:accumulate(counters,('insertion_set',cohort,name,point),label,maximum>thresholds[name][key])
 check(len(seen_cases)==len(case_meta)*2,'Condition prediction coverage')
 for name in MODELS:
  for host in test:rankdata['ordinary_context','all',name].append((0,score(name,host['document_id'])));articledata['ordinary_context','all'].add(host['article_id'])
  for point,key in POINTS:
   for host in test:accumulate(counters,('ordinary_context','all',name,point),0,score(name,host['document_id'])>thresholds[name][key])
 summaries=read(out/'classification_summary.json');seen_summary=set();rankings={key:ranking(value)for key,value in rankdata.items()}
 for row in summaries:
  key=(row['level'],row['cohort'],row['model'],row['operating_point']);check(key not in seen_summary,'Duplicate classification summary');seen_summary.add(key);compare_counts(row,counters[key],str(key))
  check(row['articles']==len(articledata[row['level'],row['cohort']]),'Summary article count')
  auc,ap=rankings[row['level'],row['cohort'],row['model']];check(close(auc,row['auroc'])and close(ap,row['average_precision']),'Classification AUROC/AP '+str(key))
 check(seen_summary==set(counters),'Classification summary coverage')
 # External traces are not executed. Frozen scores/flags/counts are checked even
 # when unlicensed raw benchmark texts are supplied by the pinned downloader.
 external_count=0;external_counters={};external_ranks=collections.defaultdict(list)
 if (out/'external_predictions.jsonl').exists():
  seen_external=set()
  for row in rows(out/'external_predictions.jsonl'):
   check(row['id']not in seen_external,'Duplicate external id');seen_external.add(row['id']);external_count+=1
   for name in MODELS:
    value=scores[name,row['text_sha256']];check(close(row['scores'][name],value),'External score cache binding')
    for cohort in [row['dataset'],row['dataset']+'/family:'+row['family']]:external_ranks[cohort,name].append((row['label'],value))
    for point,key in POINTS:
     blocked=value>thresholds[name][key];check(row['blocked'][name][point]==blocked,'External strict threshold flag')
     for cohort in [row['dataset'],row['dataset']+'/family:'+row['family']]:accumulate(external_counters,(cohort,name,point),row['label'],blocked)
  external_summary=read(out/'external_summary.json');seen=set();external_rankings={key:ranking(value)for key,value in external_ranks.items()}
  for row in external_summary:
   key=(row['cohort'],row['model'],row['operating_point']);check(key not in seen,'Duplicate external summary');seen.add(key);compare_counts(row,external_counters[key],str(key))
   auc,ap=external_rankings[row['cohort'],row['model']];check(close(auc,row['auroc'])and close(ap,row['average_precision']),'External AUROC/AP '+str(key))
  check(seen==set(external_counters),'External summary coverage')
 delivery_count=0;retrieval_summary_count=0
 if manifest.get('retrieval'):
  policies={'none':None}
  for name in MODELS:
   for point,key in POINTS:policies[name+'__'+point]=(name,key)
  retrieval_counters={};retrieval_articles=collections.defaultdict(set);seen_delivery=set()
  clean_seen=set()
  for row in rows(out/'normal_retrieval.jsonl'):
   ident=row['question_id'];check(ident not in clean_seen,'Duplicate normal retrieval query');clean_seen.add(ident);host=hostmap[ident];ranked=row['ranked_top20']
   check(host['split']=='test'and row['article_id']==host['article_id']and row['gold_document_id']==host['document_id'],'Normal retrieval host binding')
   check(len(ranked)==20 and len(set(ranked))==20 and set(ranked)<=set(corpusmap),'Normal retrieval pool identities')
   check(row['gold_in_top20']==(host['document_id']in ranked)and row['gold_in_top5']==(host['document_id']in ranked[:5]),'Normal retrieval gold flags')
   check(set(row['policies'])==set(policies),'Normal retrieval policies')
   for policy,state in policies.items():
    survivors=ranked if state is None else [document for document in ranked if not score(state[0],document)>thresholds[state[0]][state[1]]];selected=survivors[:5]
    actual={'selected_ids':selected,'annotated_original_support_retained':host['document_id']in selected,'empty_context':not selected,'selected_count':len(selected)}
    for field,value in actual.items():check(row['policies'][policy][field]==value,'Normal retrieval filter/backfill')
    key=('clean',policy,'all');entry=retrieval_counters.setdefault(key,{'n':0,'annotated_original_support_retained':0,'empty_context':0});entry['n']+=1
    retrieval_articles[key].add(host['article_id'])
    for field in ['annotated_original_support_retained','empty_context']:entry[field]+=int(actual[field])
  check(clean_seen=={host['source_id']for host in test},'Normal retrieval coverage')
  for row in rows(out/'retrieval_delivery.jsonl'):
   pair=(row['case_id'],row['condition']);check(pair not in seen_delivery,'Duplicate retrieval condition');seen_delivery.add(pair);delivery_count+=1
   meta=case_meta[row['case_id']];inserted=set(meta['conditions'][row['condition']]);ranked=row['ranked_top20']
   check(all(row[field]==meta[field]for field in ['question_id','article_id','family_id','template_id']),'Retrieval source/cohort metadata')
   check(len(ranked)==20 and len(set(ranked))==20,'Top20 identities')
   check(all(ident in corpusmap or ident in inserted for ident in ranked),'Retrieval pool includes another condition or case')
   check(set(row['inserted_ids'])==inserted and row['insertion_count']==len(inserted),'Retrieval inserted identity/dose')
   check(set(row['policies'])==set(policies),'Retrieval policy coverage')
   for policy,state in policies.items():
    survivors=ranked if state is None else [ident for ident in ranked if not score(state[0],ident)>thresholds[state[0]][state[1]]]
    selected=survivors[:5];saved=row['policies'][policy];present=inserted.intersection(selected);support=meta['legitimate_base_document_id']in selected
    actual={'selected_ids':selected,'inserted_documents_selected':len(present),'any_inserted_document_present':bool(present),'all_inserted_documents_present':len(present)==len(inserted),'annotated_original_support_retained':support,'selected_count':len(selected),'empty_context':not selected,'normal_records_rejected_in_pool':0 if state is None else sum(ident in corpusmap and score(state[0],ident)>thresholds[state[0]][state[1]]for ident in ranked)}
    for field,value in actual.items():check(saved[field]==value,'Retrieval decision '+row['case_id']+'/'+policy+'/'+field)
    for cohort in ['all','family_id:'+meta['family_id'],'template_id:'+meta['template_id']]:
     key=(row['condition'],policy,cohort);entry=retrieval_counters.setdefault(key,{'n':0,'any_inserted_document_present':0,'all_inserted_documents_present':0,'annotated_original_support_retained':0,'empty_context':0});entry['n']+=1
     retrieval_articles[key].add(meta['article_id'])
     for field in ['any_inserted_document_present','all_inserted_documents_present','annotated_original_support_retained','empty_context']:entry[field]+=int(actual[field])
  check(len(seen_delivery)==len(case_meta)*2,'Retrieval condition coverage')
  seen=set()
  for row in read(out/'retrieval_summary.json'):
   key=(row['condition'],row['policy'],row['cohort']);check(key not in seen,'Duplicate retrieval summary');seen.add(key);expected=retrieval_counters[key];check(row['n']==expected['n'],'Retrieval summary denominator')
   check(row['articles']==len(retrieval_articles[key]),'Retrieval summary article count')
   for field in (['annotated_original_support_retained','empty_context']if row['condition']=='clean'else['any_inserted_document_present','all_inserted_documents_present','annotated_original_support_retained','empty_context']):
    check(row[field+'_count']==expected[field],'Retrieval aggregate count');check(close(row[field+'_rate'],expected[field]/expected['n']),'Retrieval aggregate rate')
  check(seen==set(retrieval_counters),'Retrieval summary coverage');retrieval_summary_count=len(seen)
 print(json.dumps({'status':'PASS','public_release_provenance':provenance_summary(),'published_verifier_sha256':published_sha(Path(__file__)),'historical_verifier_reference_sha256':reference_sha(Path(__file__)),'source_questions':len(test),'source_articles':len({r['article_id']for r in test}),'calibration_passages':len(cal),'templates':len(template_counts),'cases_per_template':1200,'attack_cases':len(case_meta),'paired_benign_cases':len(case_meta),'constructed_document_predictions':len(seen_docs),'local_labeled_documents':local_count,'case_condition_predictions':len(seen_cases),'effective_event_file':event_file.name,'explicit_recovery_used':recovery_used,'frozen_executed_evaluator_file':str(evaluator.relative_to(root)),'classification_summary_rows_recomputed':len(summaries),'classification_ranking_pairs_recomputed':len(rankings),'external_predictions':external_count,'external_ranking_pairs_recomputed':len(external_ranks),'retrieval_condition_records_reconstructed':delivery_count,'retrieval_summary_rows_recomputed':retrieval_summary_count,'model_loads':0,'detector_fits':0,'neural_calls':0,'generator_calls':0,'network_calls':0,'writes':0,'scope':'Privacy-redacted manifest mapped to historical references, separately reference-bound recovery, strict thresholds, labels, score aggregation, confusion counts, tie-aware AUROC/AP and retained-document decisions. No confidence-interval recalculation, model execution attestation or semantic attack-success claim.'},indent=2))

if __name__=='__main__':main()
