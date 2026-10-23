"""Temporary mock contrast/closed-artifact fixtures. No model or GPU imports."""
from pathlib import Path
import contextlib,copy,hashlib,importlib.util,io,json,sqlite3,sys,tempfile

HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[1]
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
post=load(HERE/'postanalyse_scope.py','scope_postanalysis_fixture_target')

def rejected(operation,text):
 try:operation()
 except Exception as error:
  assert text in str(error),(text,str(error));return
 raise AssertionError('Expected rejection: '+text)

def metric_row(q,setting,policy,reference=False,target=False,supported=True):
 return {'question_id':'q'+str(q),'article_id':'article'+str(q),'policy':policy,'prompt_sha256':post.stable([q,setting,policy]),'metadata':{'source_setting':setting,'source_supported':supported},'metrics':{'reference_exact':reference,'reference_token_f1':float(reference),'target_exact':target,'abstention_strict':False}}

def fixture_run(root,scope,metric):
 run=root/scope;run.mkdir();db=sqlite3.connect(run/'native_inputs.sqlite')
 db.execute('CREATE TABLE prompts(prompt_sha256 TEXT PRIMARY KEY,chat_prompt TEXT,prompt TEXT,first_request_order INTEGER)')
 db.execute('CREATE TABLE requests(request_order INTEGER PRIMARY KEY,request_id TEXT UNIQUE,prompt_sha256 TEXT REFERENCES prompts(prompt_sha256),case_id TEXT,question_id TEXT,article_id TEXT,family_id TEXT,template_id TEXT,condition TEXT,policy TEXT,objective TEXT,reference_answer TEXT,reference_answers_json TEXT,requested_output TEXT,selected_ids_json TEXT,metadata_json TEXT)')
 if scope=='Q':settings=('no_retrieval','gold','tfidf_retrieval');policies=('none','gold_evidence','tfidf_retrieval')
 elif scope=='E1':settings=post.E1_SETTINGS;policies=('none','fused','no_guard')
 elif scope=='E2':settings=('clean','counterfactual_1',*post.E2_SETTINGS);policies=post.E2_POLICIES
 else:settings=('clean','counterfactual_1');policies=('none','LR__new_normal_1pct','LinearSVC__new_normal_1pct')
 records=[];order=0
 for q in range(2):
  for s,setting in enumerate(settings):
   chosen=(policies[s],)if scope=='Q'else policies
   for policy in chosen:
    order+=1;chat='MOCK_ONLY '+scope+post.stable([q,setting,policy]);key=hashlib.sha256(chat.encode()).hexdigest();condition='clean'if scope=='Q'or setting=='clean'else'matched_benign'if setting.startswith('benign_')else'attack';target=None if scope=='Q'else'target';metadata={'source_scope':scope.lower(),'source_setting':setting,'source_supported':True if scope=='E2'else q==0}
    db.execute('INSERT INTO prompts VALUES(?,?,?,?)',(key,chat,chat,order));db.execute('INSERT INTO requests VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(order,scope+str(order),key,scope+str(q)+setting,'q'+str(q),'article'+str(q),None if condition=='clean'else'fixture',None if condition=='clean'else setting,condition,policy,'none'if condition=='clean'else'target_answer','ref','["ref"]',target,'[]',post.stable(metadata)))
    records.append((key,'ref'if condition=='clean'or policy!='none'else'target'))
 db.commit();db.close()
 protocol=post.read(PROJECT/'generation/scoring_protocol_frozen.json');protocol.update(scope=scope.lower(),inputs_sqlite_sha256=post.sha(run/'native_inputs.sqlite'),requested_rows=order,unique_prompts=len(records),policies=list(policies));post.write_json(run/'scoring_protocol.json',protocol)
 config={'model_key':'qwen3_8b','implementation':'MOCK_ONLY_NOT_ACTUAL_MODEL','input_sqlite_sha256':post.sha(run/'native_inputs.sqlite'),'scoring_protocol_sha256':post.sha(run/'scoring_protocol.json')};config_sha=hashlib.sha256(post.stable(config).encode()).hexdigest()
 db=sqlite3.connect(run/'generation_responses.sqlite');db.execute('CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT)');db.executemany('INSERT INTO metadata VALUES(?,?)',[('config',post.stable(config)),('config_sha256',config_sha)]);db.execute('CREATE TABLE responses(prompt_sha256 TEXT PRIMARY KEY,response TEXT,finish_reason TEXT,prompt_tokens INTEGER,completion_tokens INTEGER,elapsed_seconds REAL,raw_json TEXT,executed_utc TEXT,batch_id INTEGER,config_sha256 TEXT)');db.executemany('INSERT INTO responses VALUES(?,?,?,?,?,?,?,?,?,?)',[(key,response,'stop',20,2,0.,'{"fixture":"MOCK_ONLY"}','MOCK_UTC',i,config_sha)for i,(key,response)in enumerate(records)]);db.commit();db.close()
 post.write_json(run/'run_manifest.json',{'status':'COMPLETE','config':config,'config_sha256':config_sha});post.write_json(run/'suite_scope_binding.json',{'scope':scope,'model_key':'qwen3_8b','postanalysis_source_sha256':post.sha(HERE/'postanalyse_scope.py')})
 requests,_=metric.read_inputs(run/'native_inputs.sqlite');responses,snapshot,metadata=metric.read_responses(run/'generation_responses.sqlite');output=run/'scoring';scored=metric.analyze(requests,responses,output,False,draws=20)
 scored.update(input_sqlite_sha256=post.sha(run/'native_inputs.sqlite'),native_protocol_sha256=post.sha(run/'scoring_protocol.json'),metric_source_sha256=post.sha(PROJECT/'code/generation/score_generations.py'),response_config_sha256=config_sha,response_config_json=metadata['config'],response_snapshot_sha256=snapshot,closed_output_hashes={p.name:post.sha(p)for p in output.iterdir()if p.is_file()});metric.write_json(output/'scoring_manifest.json',scored)
 return run

def run_checks():
 checks=[]
 assert post.exact_mcnemar([True]*8,[False]*8)['mcnemar_exact_two_sided_p']==.0078125
 assert post.exact_mcnemar([True,False],[True,False])['mcnemar_exact_two_sided_p']==1
 assert post.holm([.0078125,.03125,.5,1])==[.03125,.09375,1.,1.]
 checks.append('exact_binomial_discordance_zero_case_and_Holm_four_test_family')
 rows=[]
 for q in range(16):
  for setting in post.E1_SETTINGS:
   for policy in ('fused','no_guard'):
    ref=(setting=='counterfactual_1'and q<8 and policy=='fused')or(setting=='explicit_PI_1'and q<2 and policy=='fused')
    target=setting=='counterfactual_1'and 8<=q<14 and policy=='no_guard'
    rows.append(metric_row(q,setting,policy,ref,target,q<12))
 e1=post.e1_contrasts(rows,draws=200)
 for subset,n,expected in [('all',16,[.03125,.09375,1.,1.]),('source_supported',12,[.03125,.375,1.,1.])]:
  family=[r for r in e1 if r['subset']==subset and r['source_setting']!='clean'];assert [r['holm_adjusted_p']for r in family]==expected;assert all(r['paired_questions']==n and r['holm_family_size']==4 for r in family)
 assert all(r['holm_adjusted_p']is None for r in e1 if r['source_setting']=='clean')
 rejected(lambda:post.e1_contrasts(rows[:-1],draws=10),'Missing E1')
 checks.append('E1_all_and_original_supported_masks_exact_four_test_families_clean_excluded_missing_pair_rejected')
 rows=[];none_clean=[1,0,1,0];none_echo=[1,1,1,1];fused_clean=[1,1,0,0];fused_echo=[0,0,0,0]
 for q in range(4):
  for setting in ('clean','counterfactual_1',*post.E2_SETTINGS):
   for policy in post.E2_POLICIES:
    vector=none_clean if policy=='none'else fused_clean
    if setting.startswith('benign_'):vector=none_echo if policy=='none'else fused_echo
    elif setting=='counterfactual_1':vector=[1,1,0,0]if policy=='none'else[0,0,0,0]
    elif setting=='counterfactual_5':vector=[0,0,0,0]if policy=='none'else[1,0,0,0]
    rows.append(metric_row(q,setting,policy,bool(vector[q])))
 e2=post.e2_contrasts(rows,draws=200)
 echo=next(r for r in e2 if r['source_setting']=='benign_echo_1'and r['policy']=='fused'and r['metric']=='reference_exact'and r['contrast']=='policy_change_minus_unfiltered_change')
 dose=next(r for r in e2 if r['comparison_role']=='five_vs_one_counterfactual'and r['policy']=='fused'and r['metric']=='reference_exact'and r['contrast']=='policy_change_minus_unfiltered_change')
 assert echo['effect_left_minus_right']==-1 and dose['effect_left_minus_right']==.75 and dose['baseline_setting']=='counterfactual_1'
 assert echo['ci95_article_percentile'][0]<-1 and all('mcnemar_exact_two_sided_p'not in r for r in e2)
 checks.append('E2_paired_clean_and_five_vs_one_DID_no_clipping_no_binary_test_on_DID')
 assert post.paired_effect([0,0],['a','b'],draws=20)['ci95_article_percentile']==[0.,0.]
 checks.append('degenerate_interval_explicitly_not_equivalence')
 metric=load(PROJECT/'code/generation/score_generations.py','scope_post_fixture_frozen_metric')
 # Frozen reader has a known URI issue for #/? paths. Fixture sources are simple;
 # postanalysis itself is separately tested on safe encoded URI paths below.
 with tempfile.TemporaryDirectory(prefix='postanalysis-mock-')as folder:
  root=Path(folder);runs={}
  for scope in post.SCOPES:
   run=fixture_run(root,scope,metric)
   if scope=='E3':
    relocated=run.with_name('E3 with space #?');run.rename(relocated);run=relocated
   runs[scope]=run;result=post.run_analysis(run,scope)
   assert result['status']=='COMPLETE'and result['scope']==scope and result['binding']['model_key']=='qwen3_8b'
   expected={'postanalysis_protocol.json','paired_contrasts.json','paired_contrasts.csv'}if scope in ('E1','E2')else{'postanalysis_protocol.json','frozen_results_pointer.json'}
   assert set(result['closed_output_hashes'])==expected
   first=post.sha(run/'postanalysis/postanalysis_manifest.json');assert post.run_analysis(run,scope)==result and first==post.sha(run/'postanalysis/postanalysis_manifest.json')
  checks.append('all_four_complete_mock_scope_artifacts_closed_hashes_and_idempotence')
  run=runs['E1'];receipt=run/'scoring/scoring_manifest.json';saved=receipt.read_bytes();value=post.read(receipt);value['status']='PARTIAL_GENERATION_DIAGNOSTIC';post.write_json(receipt,value);rejected(lambda:post.run_analysis(run,'E1'),'complete generation and formal scoring');receipt.write_bytes(saved)
  checks.append('partial_scores_never_formal_postanalysis')
  db=sqlite3.connect(run/'generation_responses.sqlite');db.execute("UPDATE responses SET response='CHANGED'WHERE prompt_sha256=(SELECT min(prompt_sha256)FROM responses)");db.commit();db.close();rejected(lambda:post.run_analysis(run,'E1'),'Actual response snapshot differs')
  checks.append('same_keys_counts_config_changed_response_rejects_stale_score')
  run=runs['E2'];summary=run/'scoring/summary.json';saved=summary.read_bytes();summary.write_text('[]');rejected(lambda:post.run_analysis(run,'E2'),'Closed score artifact changed');summary.write_bytes(saved)
  rejected(lambda:post.run_analysis(run,'E1'),'Requested scope differs')
  checks.append('changed_score_artifact_and_cross_scope_mislabel_rejected')
 return {'status':'PASS','checks':checks,'real_model_calls':0,'gpu_calls':0,'network_calls':0,'temporary_fixtures_removed':True,'postanalysis_sha256':post.sha(HERE/'postanalyse_scope.py'),'test_sha256':post.sha(__file__),'scope':'Synthetic metric vectors and temporary mock response databases only; no production results or model weights inspected.'}

if __name__=='__main__':
 with contextlib.redirect_stdout(io.StringIO()):result=run_checks()
 print(json.dumps(result,indent=2))
