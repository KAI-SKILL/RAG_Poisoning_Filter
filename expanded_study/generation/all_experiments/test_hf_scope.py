"""Offline adapter fixtures. No model weights, CUDA, or network are used."""
from __future__ import annotations
import argparse,builtins,contextlib,copy,hashlib,importlib.util,io,json,shutil,sqlite3,tempfile
from pathlib import Path
from unittest import mock

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('group9_scope_under_test',HERE/'run_hf_scope.py');adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)

def read(path):return json.loads(Path(path).read_text())
def save(path,value):Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def fails(fn,phrase):
 try:fn()
 except ValueError as exc:
  assert phrase in str(exc),(phrase,str(exc));return
 raise AssertionError('Expected rejection: '+phrase)

class Tokenizer:
 def __init__(self,family):self.family=family;self.calls=[]
 def apply_chat_template(self,messages,**kwargs):self.calls.append(kwargs);return self.family+' MOCK NATIVE '+messages[0]['content']+'\n'+messages[1]['content']+'\nASSISTANT'
 def __call__(self,text,**kwargs):return {'input_ids':list(range(len(text.split())+10))}

class Backend:
 def __init__(self,model):self.spec=copy.deepcopy(model);self.tokenizer=Tokenizer(model['family']);self.tokenizer_identity={'fixture_native_family':model['family']};self.calls=0
 def load(self):self.identity={'implementation':'MOCK_SCOPE_ONLY_NO_MODEL_NO_GPU','model':self.spec,'tokenizer':copy.deepcopy(self.tokenizer_identity),'environment':{'status':'MOCK_ONLY'}}
 def generate(self,items):
  self.calls+=1
  return [{'prompt_sha256':row['prompt_sha256'],'response':'2003'if'CLEAN'in row['prompt']else'2010','finish_reason':'stop','prompt_tokens':row['prompt_tokens'],'completion_tokens':2,'input_body_sha256':row['user_body_sha256']}for row in items]

class Fixture:
 def __init__(self,folder):
  self.root=Path(folder);(self.root/'generation/hf_gpu').mkdir(parents=True);(self.root/'code/generation').mkdir(parents=True)
  for name in ('run_hf_grid.py','model_registry.json'):shutil.copy2(PROJECT/'generation/hf_gpu'/name,self.root/'generation/hf_gpu'/name)
  shutil.copy2(PROJECT/'code/generation/score_generations.py',self.root/'code/generation/score_generations.py')
  self.registry_path=self.root/'generation/all_experiments/experiment_registry.json';self.registry_path.parent.mkdir()
  self.registry={'schema':adapter.REGISTRY_SCHEMA,'required_models':list(adapter.MODEL_KEYS),'scopes':{}}
  self.model_registry=read(self.root/'generation/hf_gpu/model_registry.json')
  policies={'Q':['none','gold_evidence','tfidf_retrieval'],'E1':['none','ctx','no_guard','fused','tfidf_lr','guard_only'],'E2':['none','ctx','no_guard','fused'],'E3':['none','LR__new_normal_1pct','LinearSVC__new_normal_1pct']}
  for scope in adapter.SCOPES:
   directory=self.registry_path.parent/'inputs'/scope.lower();directory.mkdir(parents=True);source=directory/'generation_inputs.sqlite';db=sqlite3.connect(source)
   db.execute('CREATE TABLE prompts(prompt_sha256 TEXT PRIMARY KEY,chat_prompt TEXT,prompt TEXT,char_count INTEGER,first_request_order INTEGER)')
   db.execute('CREATE TABLE requests(request_order INTEGER PRIMARY KEY,request_id TEXT UNIQUE,prompt_sha256 TEXT REFERENCES prompts(prompt_sha256),case_id TEXT,question_id TEXT,article_id TEXT,family_id TEXT,template_id TEXT,condition TEXT,policy TEXT,objective TEXT,reference_answer TEXT,reference_answers_json TEXT,requested_output TEXT,selected_ids_json TEXT,metadata_json TEXT)')
   conditions=['clean']if scope=='Q'else['clean','attack']if scope=='E1'else['clean','attack','matched_benign'];order=0
   for question in range(2):
    for condition in conditions:
     user=('CLEAN'if condition=='clean'else condition.upper())+' '+scope+' question '+str(question)+'\nExact body: "quotes".\nAnswer:';chat='ORIGINAL_CHATML '+user;key=adapter.textsha(chat);first=order+1
     db.execute('INSERT INTO prompts VALUES(?,?,?,?,?)',(key,chat,user,len(chat),first))
     for policy in policies[scope]:
      order+=1;case=scope+'::q'+str(question)+'::attack'if condition!='clean'else scope+'::clean::q'+str(question)
      objective='none'if condition=='clean'else'target_answer'
      db.execute('INSERT INTO requests VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(order,scope+'::request'+str(order),key,case,'q'+str(question),'article'+str(question),None if condition=='clean'else'fixture',None if condition=='clean'else'fixture__v1',condition,policy,objective,'2003','["2003"]','2010','[]',json.dumps({'source_scope':scope,'encoding_mode':'plain_en','placement':'end','language_mode':'en'})))
   db.commit();groups=[{'condition':c,'policy':p,'rows':n}for c,p,n in db.execute('SELECT condition,policy,count(*) FROM requests GROUP BY condition,policy ORDER BY condition,policy')];unique=db.execute('SELECT count(*) FROM prompts').fetchone()[0];db.close()
   nested={}
   for group in groups:nested.setdefault(group['condition'],{})[group['policy']]=group['rows']
   frozen=read(PROJECT/'generation/scoring_protocol_frozen.json');frozen.update(status='MOCK_SCOPE_PROTOCOL_NO_GPU_OUTPUTS',experiment_scope=scope,scope=scope.lower(),inputs_sqlite_sha256=adapter.digest(source),requested_rows=order,unique_prompts=unique,policies=policies[scope],condition_policy_counts=nested)
   protocol=directory/'scoring_protocol.json';save(protocol,frozen);protocol.with_suffix('.sha256').write_text(adapter.digest(protocol)+'  scoring_protocol.json\n')
   self.registry['scopes'][scope]={'inputs_file':str(source.relative_to(self.root)),'inputs_sha256':adapter.digest(source),'protocol_file':str(protocol.relative_to(self.root)),'protocol_sha256':adapter.digest(protocol),'requested_rows':order,'source_unique_prompts':unique,'policies':policies[scope],'condition_policy_counts':groups}
  save(self.registry_path,self.registry)
 def args(self,scope,output=None,model='qwen3_8b',**changes):
  values={'scope':scope,'model_key':model,'registry':self.registry_path,'revision':None,'source_inputs':None,'source_protocol':None,'scorer':None,'output':output or self.root/'runs'/scope/model,'cache_dir':None,'device':'cuda:0','batch_size':2,'score_output':None,'partial':False}
  values.update(changes);return argparse.Namespace(**values)
 def context(self,scope,**kwargs):return adapter.ScopeContext(self.args(scope,**kwargs),project_root=self.root)
 def backend(self,context):return Backend(context.spec)


def run_checks():
 checks=[]
 with tempfile.TemporaryDirectory(prefix='group9 scope mock #?-')as folder:
  fixture=Fixture(folder);baseline={scope:entry['inputs_sha256']for scope,entry in fixture.registry['scopes'].items()};original_engine_sha=adapter.digest(PROJECT/'generation/hf_gpu/run_hf_grid.py')
  imported=[];real_import=builtins.__import__
  def guarded_import(name,*args,**kwargs):
   if name.split('.')[0]in {'torch','transformers','accelerate','huggingface_hub','numpy'}:raise AssertionError('Plan imported non-stdlib/model dependency: '+name)
   imported.append(name);return real_import(name,*args,**kwargs)
  with mock.patch.object(builtins,'__import__',guarded_import):
   for scope in adapter.SCOPES:
    context=fixture.context(scope);plan=context.plan();assert plan['status']=='PLAN_ONLY_NO_MODEL_OR_NETWORK'and plan['source']['requested_rows']==fixture.registry['scopes'][scope]['requested_rows']
  checks.append('all_four_scope_plans_use_only_stdlib_and_no_model_or_network')
  states={};contexts={};backends={}
  for scope in adapter.SCOPES:
   context=fixture.context(scope);backend=fixture.backend(context)
   with contextlib.redirect_stdout(io.StringIO()):state=context.run(backend)
   assert state['status']=='COMPLETE'and state['completed_unique_prompts']==fixture.registry['scopes'][scope]['source_unique_prompts']
   native=read(context.a.output/'input_manifest.json');binding=context.binding
   assert native['preparation_identity']['tokenizer']['scope_adapter_binding']==binding
   assert state['config']['scope_adapter_binding']==binding and state['config']['backend']['tokenizer']['scope_adapter_binding']==binding
   assert read(context.a.output/'scoring_protocol.json')['renderer_change']['tokenizer']['scope_adapter_binding']==binding
   assert binding['adapter_entrypoint_sha256']==adapter.digest(HERE/'run_hf_scope.py')and binding['original_hf_entrypoint_sha256']==original_engine_sha
   assert all(call.get('enable_thinking')is False for call in backend.tokenizer.calls)
   with contextlib.redirect_stdout(io.StringIO()):scored=context.score()
   assert scored['status']=='COMPLETE_SCOPE_GENERATION_SCORING'and scored['scored_request_rows']==fixture.registry['scopes'][scope]['requested_rows']
   states[scope]=state;contexts[scope]=context;backends[scope]=backend
  checks.append('q_clean_only_and_e1_e2_e3_different_policies_and_conditions_run_and_score_without_gpu')
  checks.append('adapter_engine_registry_scope_identities_bound_in_inputs_protocol_backend_and_responses')
  checks.append('native_bodies_exactly_preserved_and_qwen_thinking_disabled')
  first=contexts['E1'];before_score=adapter.digest(first.a.output/'scoring/scoring_manifest.json');resumed=fixture.context('E1');resume_backend=fixture.backend(resumed)
  with contextlib.redirect_stdout(io.StringIO()):state=resumed.run(resume_backend);resumed.score()
  assert resume_backend.calls==0 and state['generator_inference_executed']is True and state['generator_inference_executed_this_session']is False
  assert adapter.digest(first.a.output/'scoring/scoring_manifest.json')==before_score
  checks.append('same_scope_resume_makes_zero_duplicate_generations_and_scores_idempotently')
  other=fixture.context('E2',output=first.a.output);other_backend=other.bind_backend(fixture.backend(other))
  fails(lambda:other.prepare(other_backend),'stale or changed native inputs')
  checks.append('e1_checkpoint_cannot_be_reused_as_e2_native_inputs')
  changed=copy.deepcopy(states['E1']['config']);changed['scope_adapter_binding']['adapter_entrypoint_sha256']='0'*64
  fails(lambda:first.engine.run_engine(first.a.output/'native_inputs.sqlite',first.a.output,backends['E1'],changed,2),'changed model/input/runtime/precision/batch')
  checks.append('changed_adapter_logic_fingerprint_rejects_response_resume_before_model_call')
  manifest_path=first.a.output/'run_manifest.json';saved_manifest=manifest_path.read_bytes();value=read(manifest_path);value['config']['experiment_scope']='E2';save(manifest_path,value)
  fails(first.score,'another scope or adapter revision');manifest_path.write_bytes(saved_manifest)
  checks.append('score_rejects_wrong_actual_run_scope_before_metric_analysis')
  native_manifest_path=first.a.output/'input_manifest.json';saved_native=native_manifest_path.read_bytes();value=read(native_manifest_path);value['preparation_identity']['tokenizer']['scope_adapter_binding']['adapter_entrypoint_sha256']='0'*64;save(native_manifest_path,value)
  fails(first.score,'input preparation adapter identity');native_manifest_path.write_bytes(saved_native)
  checks.append('score_rejects_native_input_adapter_provenance_change')
  saved_registry=fixture.registry_path.read_bytes();value=read(fixture.registry_path);value['scopes']['E1']['condition_policy_counts'][0]['rows']+=1;save(fixture.registry_path,value)
  fails(lambda:fixture.context('E1'),'condition-policy coverage');fixture.registry_path.write_bytes(saved_registry)
  checks.append('registered_coverage_mismatch_is_rejected')
  protocol=first.protocol;saved_protocol=protocol.read_bytes();sidecar=protocol.with_suffix('.sha256');saved_sidecar=sidecar.read_bytes();value=read(protocol);value['scope']='e2';save(protocol,value);sidecar.write_text(adapter.digest(protocol)+'  scoring_protocol.json\n');value=read(fixture.registry_path);value['scopes']['E1']['protocol_sha256']=adapter.digest(protocol);save(fixture.registry_path,value)
  fails(lambda:fixture.context('E1'),'Source protocol explicitly names another scope');protocol.write_bytes(saved_protocol);sidecar.write_bytes(saved_sidecar);fixture.registry_path.write_bytes(saved_registry)
  checks.append('explicit_source_protocol_scope_mismatch_is_rejected_even_when_hashes_are_registered')
  source=first.inputs;saved_source=source.read_bytes();source.write_bytes(saved_source+b'MOCK_CHANGED_BYTES')
  fails(lambda:fixture.context('E1'),'source input SHA');source.write_bytes(saved_source)
  checks.append('source_input_byte_change_is_rejected')
  fails(lambda:fixture.context('E1',source_inputs=contexts['E2'].inputs),'--source-inputs differs')
  fails(lambda:fixture.context('E1',revision='0'*40),'pinned original HF model registry')
  try:
   with contextlib.redirect_stderr(io.StringIO()):adapter.parser().parse_args(['--scope','E1','--model-key','qwen25_3b_bf16'])
  except SystemExit:pass
  else:raise AssertionError('Unsupported third native model accepted')
  checks.append('cli_source_override_changed_revision_and_unrequested_3b_bf16_are_rejected')
  fixture_engine=fixture.root/'generation/hf_gpu/run_hf_grid.py';saved_engine=fixture_engine.read_bytes();fixture_engine.write_bytes(saved_engine+b'\n# MOCK changed engine\n')
  changed_context=fixture.context('E1');fails(changed_context.score,'another HF producer');fixture_engine.write_bytes(saved_engine)
  checks.append('original_hf_engine_logic_change_is_bound_and_rejected_for_saved_native_inputs')
  q=contexts['Q'];response=q.a.output/'generation_responses.sqlite';db=sqlite3.connect(response);db.execute('DELETE FROM responses WHERE prompt_sha256=(SELECT min(prompt_sha256) FROM responses)');db.commit();db.close()
  full=fixture.context('Q',score_output=q.a.output/'fresh_incomplete_full_scoring')
  fails(full.score,'Incomplete actual generations')
  partial=fixture.context('Q',partial=True,score_output=q.a.output/'partial_scoring')
  with contextlib.redirect_stdout(io.StringIO()):p=partial.score()
  assert p['status']=='PARTIAL_SCOPE_SCORING_DIAGNOSTIC'and p['actual_unique_response_records']==1 and p['scored_request_rows']==3
  assert read(q.a.output/'partial_scoring/partial_scoring_manifest.json')['missing_unique_prompts']==1
  checks.append('actual_response_snapshot_blocks_false_full_completion_and_partial_keeps_missing_explicit')
  for scope,entry in fixture.registry['scopes'].items():assert adapter.digest(fixture.root/entry['inputs_file'])==baseline[scope]
  assert adapter.digest(PROJECT/'generation/hf_gpu/run_hf_grid.py')==original_engine_sha
  checks.append('original_production_hf_engine_and_all_fixture_frozen_sources_remain_byte_unchanged')
 return {'status':'PASS','checks':checks,'real_model_loads':0,'real_gpu_inference':0,'network_calls':0,'scope_count':len(adapter.SCOPES),'fixture_backend':'MOCK_SCOPE_ONLY_NO_MODEL_NO_GPU','temporary_fixtures_removed':True,'adapter_sha256':adapter.digest(HERE/'run_hf_scope.py'),'test_sha256':adapter.digest(__file__),'original_hf_entrypoint_sha256':original_engine_sha,'actual_cluster_execution':'NOT_EXECUTED_ON_THIS_HOST'}

if __name__=='__main__':
 with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):result=run_checks()
 print(json.dumps(result,indent=2))
