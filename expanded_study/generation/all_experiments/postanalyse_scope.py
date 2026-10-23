"""Additional paired contrasts from COMPLETE frozen scores; never generates text.

The actual b12 archive is scoring/request_scores.jsonl, not case_scores.jsonl.
This auxiliary recipe preserves its metric values and does not overwrite the
historical scorer, protocol, summaries or significance tests. NumPy is the only
non-standard dependency. Output defaults to RUN/postanalysis.
"""
from __future__ import annotations
from pathlib import Path
import argparse,collections,csv,datetime,hashlib,io,json,math,os,sqlite3,tempfile

VERSION='Group9-scope-paired-postanalysis-v1'
DRAWS=10000
SEED=20261020
SCOPES=('Q','E1','E2','E3')
E1_SETTINGS=('clean','counterfactual_1','explicit_PI_1')
E1_METRICS=('reference_exact','target_exact')
E2_SETTINGS=('benign_echo_1','benign_echo_5','benign_copy_1','benign_copy_5','counterfactual_5')
E2_POLICIES=('none','ctx','no_guard','fused')
E2_METRICS=('reference_exact','reference_token_f1','target_exact','abstention_strict')

def require(ok,message):
 if not ok:raise ValueError(message)
def stable(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb')as stream:
  for block in iter(lambda:stream.read(4*1024*1024),b''):h.update(block)
 return h.hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def readonly(path):return sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro&immutable=1',uri=True)
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def atomic(path,data):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 fd,name=tempfile.mkstemp(prefix=path.name+'.',suffix='.partial',dir=path.parent);temporary=Path(name)
 try:
  with os.fdopen(fd,'wb')as stream:require(stream.write(data)==len(data),'Short output write');stream.flush();os.fsync(stream.fileno())
  wanted=hashlib.sha256(data).hexdigest();require(sha(temporary)==wanted,'Staged output hash differs');os.replace(temporary,path);require(sha(path)==wanted,'Published output hash differs')
 finally:temporary.unlink(missing_ok=True)
def write_json(path,value):
 atomic(path,(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
 require(stable(read(path))==stable(value),'JSON read-back differs')
def write_csv(path,rows):
 if not rows:return
 fields=list(dict.fromkeys(key for row in rows for key in row));text=io.StringIO(newline='');writer=csv.DictWriter(text,fieldnames=fields);writer.writeheader()
 for row in rows:writer.writerow({key:stable(value)if isinstance(value,(list,dict))else value for key,value in row.items()})
 atomic(path,text.getvalue().encode('utf-8-sig'))
 with Path(path).open(newline='',encoding='utf-8-sig')as stream:require(len(list(csv.DictReader(stream)))==len(rows),'CSV read-back row coverage differs')

def exact_mcnemar(left,right):
 require(len(left)==len(right)and len(left)>0,'Empty or unequal McNemar pairs')
 require(all(isinstance(x,bool)for x in (*left,*right)),'McNemar requires binary paired outcomes')
 b=sum(x and not y for x,y in zip(left,right));c=sum(y and not x for x,y in zip(left,right));n=b+c
 p=min(1.,2*sum(math.comb(n,k)for k in range(min(b,c)+1))/(1<<n))if n else 1.
 return {'left1_right0':b,'left0_right1':c,'discordant_pairs':n,'mcnemar_exact_two_sided_p':p}

def holm(pvalues):
 require(all(isinstance(p,(int,float))and math.isfinite(p)and 0<=p<=1 for p in pvalues),'Invalid Holm p-value')
 order=sorted(range(len(pvalues)),key=lambda i:(pvalues[i],i));adjusted=[0.]*len(order);previous=0.
 for rank,i in enumerate(order):previous=max(previous,min(1.,(len(order)-rank)*pvalues[i]));adjusted[i]=previous
 return adjusted

def paired_effect(values,articles,draws=DRAWS,seed=SEED):
 import numpy as np
 require(len(values)==len(articles)and len(values)>0,'Missing paired effect observations')
 require(all(math.isfinite(float(x))for x in values),'Nonfinite paired effect')
 grouped=collections.defaultdict(list)
 for article,value in zip(articles,values):grouped[str(article)].append(float(value))
 keys=sorted(grouped);totals=np.asarray([sum(grouped[k])for k in keys],dtype=float);counts=np.asarray([len(grouped[k])for k in keys],dtype=float)
 weights=np.random.default_rng(seed).multinomial(len(keys),np.full(len(keys),1/len(keys)),size=draws)
 samples=(weights@totals)/(weights@counts);ci=np.quantile(samples,[.025,.975]).tolist();point=float(np.mean(values))
 return {'effect_left_minus_right':point,'effect_percentage_points':100*point,'ci95_article_percentile':ci,'ci95_percentage_points':[100*x for x in ci],'paired_questions':len(values),'article_groups':len(keys),'bootstrap_draws':draws,'bootstrap_seed':seed,'degenerate_observed_interval':ci[0]==ci[1],'uncertainty_note':'Pointwise paired article-cluster percentile interval conditional on observed outputs; no equivalence or population-certainty claim from a degenerate interval.'}

def row_index(rows):
 lookup={};questions={}
 for row in rows:
  metadata=row['metadata'];setting=metadata.get('source_setting');key=(row['question_id'],setting,row['policy'])
  require(isinstance(setting,str)and setting,'Missing frozen source_setting metadata')
  require(key not in lookup,'Duplicate question/source_setting/policy');lookup[key]=row
  info=(row['article_id'],metadata.get('source_supported'))
  require(row['question_id']not in questions or questions[row['question_id']]==info,'Inconsistent article/source-support metadata within question')
  questions[row['question_id']]=info
 return lookup,questions

def metric_value(row,name):
 value=row['metrics'][name]
 require(isinstance(value,(bool,int,float))and math.isfinite(float(value))and 0<=float(value)<=1,'Missing or invalid frozen metric '+name)
 if name!='reference_token_f1':require(isinstance(value,bool),'Nonbinary frozen metric '+name)
 return value

def e1_contrasts(rows,draws=DRAWS):
 lookup,questions=row_index(rows);require(questions,'No E1 questions')
 require(all(isinstance(info[1],bool)for info in questions.values()),'E1 source_supported mask is absent')
 result=[]
 for subset,supported in [('all',False),('source_supported',True)]:
  ids=sorted(q for q,info in questions.items()if not supported or info[1]);require(ids,'Empty E1 source-supported subset')
  family=[]
  for setting in E1_SETTINGS:
   for metric in E1_METRICS:
    left=[];right=[];articles=[]
    for q in ids:
     require((q,setting,'fused')in lookup and(q,setting,'no_guard')in lookup,'Missing E1 fused/no_guard pair')
     left.append(metric_value(lookup[q,setting,'fused'],metric));right.append(metric_value(lookup[q,setting,'no_guard'],metric));articles.append(questions[q][0])
    same_prompts=sum(isinstance(lookup[q,setting,'fused'].get('prompt_sha256'),str)and lookup[q,setting,'fused']['prompt_sha256']==lookup[q,setting,'no_guard'].get('prompt_sha256')for q in ids)
    row={'scope':'E1','subset':subset,'source_setting':setting,'metric':metric,'contrast':'fused_minus_no_guard','left_policy':'fused','right_policy':'no_guard','left_rate':sum(left)/len(left),'right_rate':sum(right)/len(right),'identical_complete_prompt_pairs':same_prompts,'interpretation':'Identical selected prompts share exact generation; this is a conditional input/output comparison, not independent reexecution or refitting of the neural defense.',**paired_effect([int(x)-int(y)for x,y in zip(left,right)],articles,draws),**exact_mcnemar(left,right),'holm_family':None,'holm_family_size':0,'holm_adjusted_p':None,'test_role':'descriptive_clean_comparison'if setting=='clean'else'prespecified_shape_attack_comparison_using_new_b12_metrics'}
    result.append(row)
    if setting!='clean':family.append(row)
  require(len(family)==4,'E1 Holm family must contain two attack settings times two metrics')
  for row,adjusted in zip(family,holm([r['mcnemar_exact_two_sided_p']for r in family])):
   row.update(holm_family='E1_'+subset+'_two_attacks_x_two_metrics',holm_family_size=4,holm_adjusted_p=adjusted)
 return result

def e2_contrasts(rows,draws=DRAWS):
 lookup,questions=row_index(rows);ids=sorted(questions);require(ids,'No E2 questions');result=[]
 require(all(info[1]is True for info in questions.values()),'E2 includes a question outside the frozen supported subset')
 pairs=[(setting,'clean','mechanism_vs_clean')for setting in E2_SETTINGS]+[('counterfactual_5','counterfactual_1','five_vs_one_counterfactual')]
 for setting,baseline,role in pairs:
  for policy in E2_POLICIES:
   for metric in E2_METRICS:
    current=[];base=[];none_current=[];none_base=[];articles=[]
    for q in ids:
     needed=[(q,setting,policy),(q,baseline,policy),(q,setting,'none'),(q,baseline,'none')]
     require(all(k in lookup for k in needed),'Missing complete E2 setting/baseline/policy/none pairs')
     current.append(metric_value(lookup[needed[0]],metric));base.append(metric_value(lookup[needed[1]],metric));none_current.append(metric_value(lookup[needed[2]],metric));none_base.append(metric_value(lookup[needed[3]],metric));articles.append(questions[q][0])
    change=[float(x)-float(y)for x,y in zip(current,base)]
    common={'scope':'E2','subset':'fixed_source_supported_25','source_setting':setting,'baseline_setting':baseline,'metric':metric,'policy':policy,'comparison_role':role,'test_role':'exploratory_pointwise_interval_no_additional_significance_family'}
    result.append({**common,'contrast':'within_policy_change','setting_mean':sum(current)/len(ids),'baseline_mean':sum(base)/len(ids),**paired_effect(change,articles,draws)})
    if policy!='none':
     difference=[d-(float(x)-float(y))for d,x,y in zip(change,none_current,none_base)]
     result.append({**common,'contrast':'policy_change_minus_unfiltered_change',**paired_effect(difference,articles,draws)})
 return result

def load_complete(run,scope):
 score_dir=run/'scoring';score_path=score_dir/'scoring_manifest.json';score=read(score_path);protocol_path=run/'scoring_protocol.json';protocol=read(protocol_path);manifest=read(run/'run_manifest.json');inputs=run/'native_inputs.sqlite';responses=run/'generation_responses.sqlite'
 require(score.get('status')=='COMPLETE_GENERATION_SCORING'and manifest.get('status')=='COMPLETE','Postanalysis requires complete generation and formal scoring')
 require(score.get('missing_unique_prompts')==0,'Postanalysis cannot treat missing outputs as failed attacks')
 require(score['requested_rows']==score['scored_request_rows']==protocol['requested_rows'],'Formal score request count differs')
 require(score['expected_unique_prompts']==score['actual_unique_response_records']==protocol['unique_prompts'],'Formal score unique coverage differs')
 require(score['input_sqlite_sha256']==protocol['inputs_sqlite_sha256']==sha(inputs),'Frozen native input changed')
 require(score['native_protocol_sha256']==sha(protocol_path),'Scored native protocol changed')
 if 'scope'in protocol:require(str(protocol['scope']).upper()==scope,'Requested scope differs from native protocol')
 if 'experiment_scope'in protocol:require(str(protocol['experiment_scope']).upper()==scope,'Requested scope differs from native protocol')
 binding_path=run/'suite_scope_binding.json';suite_binding=read(binding_path)if binding_path.exists()else protocol.get('native_suite_binding',{})
 if suite_binding:
  require(suite_binding['scope']==scope,'Requested scope differs from suite binding')
  if 'postanalysis_source_sha256'in suite_binding:require(suite_binding['postanalysis_source_sha256']==sha(__file__),'Postanalysis producer differs from pre-generation suite binding')
 hashes=score['closed_output_hashes'];require(isinstance(hashes,dict)and hashes,'Missing closed score hashes')
 require(set(hashes)=={p.name for p in score_dir.iterdir()if p.is_file()and p.name!='scoring_manifest.json'},'Closed scoring file coverage differs')
 for name,wanted in hashes.items():require(Path(name).name==name and sha(score_dir/name)==wanted,'Closed score artifact changed: '+name)
 require('request_scores.jsonl'in hashes,'Actual frozen archive request_scores.jsonl is missing')
 wal=responses.with_name(responses.name+'-wal');require(not wal.exists()or wal.stat().st_size==0,'Postanalyse a closed response checkpoint')
 db=readonly(responses);db.row_factory=sqlite3.Row
 try:
  metadata=dict(db.execute('SELECT key,value FROM metadata'));config=json.loads(metadata['config']);config_sha=hashlib.sha256(stable(config).encode()).hexdigest()
  require(config_sha==metadata['config_sha256']==score['response_config_sha256']==manifest['config_sha256'],'Actual response configuration fingerprint differs')
  require(json.loads(score['response_config_json'])==config and manifest['config']==config,'Actual response configuration JSON differs')
  require(config['input_sqlite_sha256']==score['input_sqlite_sha256']and config['scoring_protocol_sha256']==score['native_protocol_sha256'],'Response input/protocol configuration differs')
  snapshot=hashlib.sha256();keys=set()
  for row in db.execute('SELECT * FROM responses ORDER BY prompt_sha256'):
   row=dict(row);require(row['config_sha256']==config_sha,'Mixed response configurations');keys.add(row['prompt_sha256']);snapshot.update((stable(row)+'\n').encode())
  require(snapshot.hexdigest()==score['response_snapshot_sha256'],'Actual response snapshot differs from scored responses')
 finally:db.close()
 db=readonly(inputs);db.row_factory=sqlite3.Row
 try:
  expected={row[0]for row in db.execute('SELECT prompt_sha256 FROM prompts')};require(expected==keys,'Actual response keys do not cover frozen inputs')
  require(db.execute('SELECT count(*) FROM requests').fetchone()[0]==score['requested_rows'],'Frozen input request count differs')
  requests={row['request_id']:dict(row)for row in db.execute('SELECT * FROM requests')}if scope!='E3'else None
 finally:db.close()
 rows=[]
 if requests is not None:
  seen=set()
  for line in (score_dir/'request_scores.jsonl').open(encoding='utf-8'):
   row=json.loads(line);key=row['request_id'];require(key in requests and key not in seen,'Unexpected or duplicate scored request');seen.add(key);source=requests[key]
   for field in ('request_order','prompt_sha256','case_id','question_id','article_id','family_id','template_id','condition','policy','objective','requested_output'):require(row[field]==source[field],'Scored request/source mapping differs: '+field)
   require(row['metadata']==json.loads(source['metadata_json'])and row['reference_answers']==json.loads(source['reference_answers_json']),'Scored metadata/reference aliases differ from frozen inputs');rows.append(row)
  require(seen==requests.keys(),'Scored request ID coverage differs')
 require(score['metric_source_sha256']==protocol['scorer_sha256'],'Scoring algorithm identity differs')
 model_key=config.get('model_key')or suite_binding.get('model_key')
 if model_key is None and config.get('model_manifest',{}).get('repository')=='Qwen/Qwen2.5-3B-Instruct-GGUF':model_key='qwen25_3b_gguf'
 require(model_key in ('qwen25_3b_gguf','qwen3_8b','llama31_8b'),'Missing actual registered model identity')
 if suite_binding.get('model_key'):require(suite_binding['model_key']==model_key,'Suite and response model identity differ')
 return rows,score,{'scope':scope,'model_key':model_key,'source_scoring_manifest_sha256':sha(score_path),'input_sqlite_sha256':score['input_sqlite_sha256'],'native_protocol_sha256':score['native_protocol_sha256'],'response_config_sha256':config_sha,'response_snapshot_sha256':score['response_snapshot_sha256'],'metric_source_sha256':score['metric_source_sha256'],'request_scores_sha256':hashes['request_scores.jsonl'],'postanalysis_entrypoint_sha256':sha(__file__)}

def recipe(scope):
 return {'version':VERSION,'scope':scope,'metric_role':'Read frozen b12 per-request metric values unchanged; no generated text, new metric normalization, output-selected subset or rescoring. This is an auxiliary new-run contrast recipe, not replacement of historical reported statistics.','paired_contrast_statistics':{'article_cluster_bootstrap_draws':DRAWS,'seed':SEED,'interval':'pointwise percentile 95%; keep all within-question paired observations in their article','relation_to_frozen_summaries':'Original b12 summary bootstrap remains 2000 draws/20261022. These additional E1/E2 contrasts explicitly use the historical contrast resampling recipe 10000/20261020 on newly scored b12 values.','mcnemar':'Two-sided exact binomial on discordant paired binary outcomes, no scipy or continuity correction.','E1_Holm':'Four tests per subset: two attacks x {reference_exact,target_exact}; all100 and original-supported85 are separate families within each model. Clean comparisons are descriptive and excluded. No across-model multiplicity adjustment or independent-model replication claim.','E2':'Exploratory within-policy setting-minus-clean and policy-minus-unfiltered differences in changes; the separate factual multiplicity contrast uses five-minus-one. No added significance family.'},'output_scope':'Q returns fixed clean-utility summary pointer; E3 returns frozen-score pointers without additional attack-success definitions.','timing_disclosure':'Receipt serializes the already declared auxiliary code recipe at analysis time; not a claim that the historical study was preregistered again.'}

def run_analysis(run,scope,output=None):
 run=Path(run).resolve();destination=Path(output).resolve()if output else run/'postanalysis';require(run in destination.parents and destination!=run/'scoring'and run/'scoring'not in destination.parents,'Postanalysis output must be a separate directory inside RUN')
 rows,score,identity=load_complete(run,scope);protocol=recipe(scope)
 old_manifest=destination/'postanalysis_manifest.json'
 if destination.exists()and any(destination.iterdir()):
  old=read(old_manifest);require(old['status']=='COMPLETE'and old['binding']==identity,'Existing postanalysis uses different inputs/responses/producer')
  require(set(old['closed_output_hashes'])=={p.name for p in destination.iterdir()if p.is_file()and p.name!=old_manifest.name},'Postanalysis output file coverage differs')
  for name,wanted in old['closed_output_hashes'].items():require(Path(name).name==name and sha(destination/name)==wanted,'Closed postanalysis output changed')
  return old
 destination.mkdir(parents=True,exist_ok=True);write_json(destination/'postanalysis_protocol.json',protocol)
 if scope in ('E1','E2'):
  contrasts=e1_contrasts(rows)if scope=='E1'else e2_contrasts(rows)
  write_json(destination/'paired_contrasts.json',contrasts);write_csv(destination/'paired_contrasts.csv',contrasts)
 else:
  contrasts=[];pointer={'scope':scope,'source_scoring_directory':os.path.relpath(run/'scoring',destination),'source_scoring_manifest_sha256':identity['source_scoring_manifest_sha256'],'summary_sha256':score['closed_output_hashes']['summary.json'],'request_scores_sha256':identity['request_scores_sha256'],'metrics_or_formulas_changed':False,'note':'Q clean-utility diagnostics only; no attack-success endpoint.'if scope=='Q'else'E3 interpretation remains the original frozen wrong-target and abstention proxies with original denominators and article intervals.'}
  if scope=='Q':pointer['clean_utility_groups']=[row for row in read(run/'scoring/summary.json')if row['level']=='all'and row['condition']=='clean']
  write_json(destination/'frozen_results_pointer.json',pointer)
 result={'status':'COMPLETE','version':VERSION,'scope':scope,'model_key':identity['model_key'],'created_utc':now(),'binding':identity,'requested_rows':score['requested_rows'],'actual_unique_response_records':score['actual_unique_response_records'],'contrast_rows':len(contrasts),'missing_pairs':0,'closed_output_hashes':{p.name:sha(p)for p in sorted(destination.iterdir())if p.is_file()},'model_calls':0,'metric_source_or_formula_changes':False,'scope_note':'Complete auxiliary postanalysis of complete saved generations; not independent proof that GPU inference executed or semantic answer correctness.'}
 write_json(old_manifest,result);return result

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--scope',choices=SCOPES,required=True);parser.add_argument('--run-dir',type=Path,required=True);parser.add_argument('--output',type=Path);args=parser.parse_args();print(json.dumps(run_analysis(args.run_dir,args.scope,args.output),indent=2))
if __name__=='__main__':main()
