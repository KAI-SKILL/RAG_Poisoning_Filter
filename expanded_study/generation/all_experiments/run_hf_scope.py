"""Run frozen Q/E1/E2/E3 inputs with the existing native BF16 HF engine.

--plan uses Python's standard library only and never loads/downloads a model.
Each (scope, model) needs a separate node-local output directory. This adapter
never changes an input source, source protocol, metric implementation, or the
original hf_gpu/run_hf_grid.py. The adapter and original engine hashes are bound
into input preparation, derived protocol, actual response config, and scoring.
"""
from __future__ import annotations
import argparse,contextlib,copy,hashlib,importlib.util,io,json,os,re,sqlite3,sys
from pathlib import Path

PROJECT_ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
SCOPES=('Q','E1','E2','E3')
MODEL_KEYS=('qwen3_8b','llama31_8b')
REGISTRY_SCHEMA='Group9-all-experiments-v1'
REQUIRED_REQUEST_FIELDS={'request_order','request_id','prompt_sha256','case_id','question_id','article_id','family_id','template_id','condition','policy','objective','reference_answers_json','requested_output','metadata_json'}

def stable(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def textsha(value):return hashlib.sha256(value.encode('utf-8')).hexdigest()
def digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb')as stream:
  for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def require(condition,message):
 if not condition:raise ValueError(message)
def readonly(path):return sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro&immutable=1',uri=True)
def checked_relative(root,value,label):
 require(isinstance(value,str)and value,label+' is missing from registry')
 relative=Path(value)
 require(not relative.is_absolute()and '..'not in relative.parts,label+' must be relative to project root')
 path=(root/relative).resolve()
 require(root==path or root in path.parents,label+' escapes project root')
 require(path.is_file(),label+' does not exist: '+str(path))
 return path

def load_engine(project_root=PROJECT_ROOT):
 path=Path(project_root).resolve()/'generation/hf_gpu/run_hf_grid.py'
 require(path.is_file(),'Missing original HF engine: '+str(path))
 name='group9_scope_original_hf_'+textsha(str(path))[:16]
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 return module

def normalized_groups(groups):
 if isinstance(groups,dict):
  require(bool(groups)and all(isinstance(policies,dict)and bool(policies)for policies in groups.values()),'Malformed nested condition-policy coverage')
  groups=[{'condition':condition,'policy':policy,'rows':n}for condition,policies in groups.items()for policy,n in policies.items()]
 require(isinstance(groups,list)and bool(groups),'Registry condition_policy_counts must be a nonempty list')
 result=[];seen=set()
 for row in groups:
  require(isinstance(row,dict)and set(row)=={'condition','policy','rows'},'Malformed registry condition-policy coverage')
  condition,policy,n=row['condition'],row['policy'],row['rows']
  require(condition in ('clean','attack','matched_benign')and isinstance(policy,str)and policy,'Invalid condition/policy coverage label')
  require(isinstance(n,int)and not isinstance(n,bool)and n>0,'Coverage row count must be a positive integer')
  key=(condition,policy);require(key not in seen,'Duplicate registry condition-policy coverage');seen.add(key)
  result.append({'condition':condition,'policy':policy,'rows':n})
 return sorted(result,key=lambda row:(row['condition'],row['policy']))

class ScopeContext:
 """Registry-bound source selection. No model, CUDA, tokenizer, or network use."""
 def __init__(self,args,project_root=PROJECT_ROOT,engine=None):
  self.a=args;self.root=Path(project_root).resolve();self.engine=engine or load_engine(self.root)
  require(args.scope in SCOPES,'--scope must be Q, E1, E2, or E3')
  require(args.model_key in MODEL_KEYS,'Only the two registered native BF16 8B models are supported')
  self.scope=args.scope
  self.registry_path=Path(args.registry or self.root/'generation/all_experiments/experiment_registry.json').resolve()
  self.registry=read(self.registry_path);self.registry_sha256=digest(self.registry_path)
  require(self.registry.get('schema')==REGISTRY_SCHEMA,'Unexpected experiment registry schema')
  require(isinstance(self.registry.get('scopes'),dict)and set(self.registry['scopes'])==set(SCOPES),'Registry must explicitly cover Q, E1, E2, and E3')
  self.entry=copy.deepcopy(self.registry['scopes'][self.scope]);require(isinstance(self.entry,dict),'Invalid scope registry entry')
  required_models=self.entry.get('required_models',self.registry.get('required_models'))
  require(isinstance(required_models,list)and len(required_models)==len(set(required_models))and set(MODEL_KEYS)<=set(required_models),'Registry required_models must explicitly include both native 8B model keys')
  require(args.model_key in required_models,'Model is not required for this scope')
  self.inputs=checked_relative(self.root,self.entry.get('inputs_file'),'inputs_file')
  self.protocol=checked_relative(self.root,self.entry.get('protocol_file'),'protocol_file')
  for field in ('inputs_sha256','protocol_sha256'):
   require(isinstance(self.entry.get(field),str)and re.fullmatch('[0-9a-f]{64}',self.entry[field])is not None,'Registry '+field+' must be a SHA256')
  require(args.source_inputs is None or Path(args.source_inputs).resolve()==self.inputs,'--source-inputs differs from the selected registry scope')
  require(args.source_protocol is None or Path(args.source_protocol).resolve()==self.protocol,'--source-protocol differs from the selected registry scope')
  args.source_inputs=self.inputs;args.source_protocol=self.protocol
  args.scorer=Path(args.scorer or self.root/'code/generation/score_generations.py').resolve()
  require(args.output is not None,'--output is required; use a separate node-local directory per scope and model')
  args.output=Path(args.output).resolve()
  require(args.output!=self.root and args.output not in self.inputs.parents and args.output not in self.protocol.parents,'Output directory cannot contain the frozen source inputs or protocol')
  args.batch_size=int(args.batch_size);require(args.batch_size>0,'Batch size must be positive')
  registered=copy.deepcopy(read(self.root/'generation/hf_gpu/model_registry.json')[args.model_key])
  require(args.revision is None or args.revision.lower()==registered['revision'].lower(),'Revision must match the pinned original HF model registry; prepare a separately registered experiment for a changed model')
  self.spec=self.engine.resolve(args)
  require(self.spec==registered,'Actual resolved model differs from the original pinned model registry')
  self.source_protocol=self.engine.checked_source_protocol(args)
  self.binding={'scope':self.scope,'registry_schema':REGISTRY_SCHEMA,'registry_sha256':self.registry_sha256,'registry_scope_entry_sha256':textsha(stable(self.entry)),'adapter_entrypoint_sha256':digest(__file__),'original_hf_entrypoint_sha256':digest(self.root/'generation/hf_gpu/run_hf_grid.py'),'model_registry_sha256':digest(self.root/'generation/hf_gpu/model_registry.json'),'source_inputs_sha256':self.entry['inputs_sha256'],'source_protocol_sha256':self.entry['protocol_sha256'],'metric_source_sha256':digest(args.scorer),'identity_note':'Adapter provenance; no source protocol or model text is changed.'}
  self._summary=None
  self.check_frozen();self.source_summary(self.inputs)
  # Original prepare_native calls this module-level function. This explicit
  # per-module adaptation removes only the original E3-only policy assumption.
  self.engine.source_summary=self.source_summary
 def check_frozen(self):
  require(digest(self.registry_path)==self.registry_sha256,'Experiment registry changed during the operation')
  require(digest(self.inputs)==self.entry['inputs_sha256'],'Selected source input SHA differs from registry')
  require(digest(self.protocol)==self.entry['protocol_sha256'],'Selected source protocol SHA differs from registry')
  require(digest(self.root/'generation/hf_gpu/run_hf_grid.py')==self.binding['original_hf_entrypoint_sha256'],'Original HF engine changed during operation')
  require(digest(self.root/'generation/hf_gpu/model_registry.json')==self.binding['model_registry_sha256'],'Original HF model registry changed during operation')
  require(digest(__file__)==self.binding['adapter_entrypoint_sha256'],'Scope adapter changed during operation')
  require(digest(self.a.scorer)==self.binding['metric_source_sha256'],'Frozen metric source changed during operation')
  require(self.source_protocol['inputs_sqlite_sha256']==self.entry['inputs_sha256'],'Source protocol/input identity mismatch')
  require(self.source_protocol['scorer_sha256']==self.binding['metric_source_sha256'],'Source protocol/metric identity mismatch')
  if 'experiment_scope'in self.source_protocol:require(self.source_protocol['experiment_scope']==self.scope,'Source protocol explicitly names another scope')
  if 'scope'in self.source_protocol:require(str(self.source_protocol['scope']).upper()==self.scope,'Source protocol explicitly names another scope')
 def source_summary(self,path):
  require(Path(path).resolve()==self.inputs,'Original engine requested an input outside selected scope')
  self.check_frozen()
  if self._summary is not None:return copy.deepcopy(self._summary)
  expected_policies=self.entry.get('policies')
  require(isinstance(expected_policies,list)and bool(expected_policies)and len(set(expected_policies))==len(expected_policies)and all(isinstance(p,str)and p for p in expected_policies),'Registry policies must be a unique nonempty list')
  expected_groups=normalized_groups(self.entry.get('condition_policy_counts'))
  db=readonly(path)
  try:
   require(REQUIRED_REQUEST_FIELDS<={row[1]for row in db.execute('PRAGMA table_info(requests)')},'Source request schema is incomplete')
   requested=db.execute('SELECT count(*) FROM requests').fetchone()[0];unique=db.execute('SELECT count(*) FROM prompts').fetchone()[0]
   policies=[row[0]for row in db.execute('SELECT DISTINCT policy FROM requests ORDER BY policy')]
   groups=[{'condition':c,'policy':p,'rows':n}for c,p,n in db.execute('SELECT condition,policy,count(*) FROM requests GROUP BY condition,policy ORDER BY condition,policy')]
   require(db.execute('SELECT count(*) FROM requests WHERE prompt_sha256 NOT IN(SELECT prompt_sha256 FROM prompts)').fetchone()[0]==0,'Broken source request mapping')
   require(db.execute('SELECT count(*) FROM prompts WHERE prompt_sha256 NOT IN(SELECT prompt_sha256 FROM requests)').fetchone()[0]==0,'Orphan source prompts outside request grid')
   require(db.execute('SELECT count(*) FROM(SELECT request_id FROM requests GROUP BY request_id HAVING count(*)<>1)').fetchone()[0]==0,'Duplicate source request IDs')
  finally:db.close()
  require(isinstance(self.entry.get('requested_rows'),int)and requested==self.entry['requested_rows'],'Source request count differs from registered scope')
  require(isinstance(self.entry.get('source_unique_prompts'),int)and unique==self.entry['source_unique_prompts'],'Source unique prompt count differs from registered scope')
  require(set(policies)==set(expected_policies),'Source policies differ from registered scope')
  require(groups==expected_groups,'Source condition-policy coverage differs from registered scope')
  p=self.source_protocol
  require(p['requested_rows']==requested and p['unique_prompts']==unique and set(p['policies'])==set(policies),'Frozen source protocol row/policy coverage differs from selected source')
  if 'condition_policy_counts'in p:require(normalized_groups(p['condition_policy_counts'])==groups,'Source protocol condition-policy coverage differs')
  self._summary={'requested_rows':requested,'source_unique_prompts':unique,'policies':policies,'condition_policy_counts':groups,'source_inputs_sha256':self.entry['inputs_sha256'],'experiment_scope':self.scope,'scope_adapter_binding':self.binding}
  return copy.deepcopy(self._summary)
 def bind_backend(self,backend):
  # prepare_native already freezes tokenizer_identity. Add a clearly labeled
  # adapter-provenance field, retaining the actual tokenizer properties.
  require('scope_adapter_binding'not in backend.tokenizer_identity,'Backend was already scope-bound')
  backend.tokenizer_identity={**backend.tokenizer_identity,'scope_adapter_binding':copy.deepcopy(self.binding)}
  return backend
 def prepare(self,backend):
  native=self.engine.prepare_native(self.inputs,self.a.output,backend,self.spec)
  self.validate_native(native)
  return native
 def validate_native(self,native):
  require(native['requested_rows']==self.entry['requested_rows']and native['source_unique_prompts']==self.entry['source_unique_prompts'],'Native preparation lost source scope coverage')
  require(native['source_inputs_sha256']==self.entry['inputs_sha256'],'Native inputs refer to another source scope')
  identity=native['preparation_identity']
  require(identity['producer_sha256']==self.binding['original_hf_entrypoint_sha256'],'Native preparation used another HF producer')
  require(identity['tokenizer']['scope_adapter_binding']==self.binding,'Native input preparation adapter identity differs')
  require(identity['model']==self.spec,'Native input preparation model identity differs')
  require(normalized_groups(native['condition_policy_counts'])==normalized_groups(self.entry['condition_policy_counts']),'Native preparation condition-policy coverage differs')
 def derived(self,native):
  self.validate_native(native)
  path=self.engine.derived_protocol(self.a,native)
  p=read(path)
  require(p['renderer_change']['tokenizer']['scope_adapter_binding']==self.binding,'Derived protocol lacks adapter/scope identity')
  record={'status':'SCOPE_BOUND_HF_NATIVE_FOLLOWUP','experiment_scope':self.scope,'scope_adapter_binding':self.binding,'source_protocol_unchanged':True,'metric_functions_unchanged':True,'native_inputs_sha256':native['native_inputs_sha256'],'derived_protocol_sha256':digest(path),'actual_entrypoint':'generation/all_experiments/run_hf_scope.py','derived_protocol_producer':'generation/hf_gpu/run_hf_grid.py::derived_protocol','metrics_entrypoint':'original frozen metric.analyze through original HF score()'}
  sidecar=self.a.output/'scope_adapter_binding.json'
  if sidecar.exists():require(read(sidecar)==record,'Saved scope/protocol binding differs')
  else:self.engine.atomic(sidecar,record)
  return path
 def config(self,backend,native,protocol):
  return {'engine':'transformers_native_cuda_bf16','experiment_scope':self.scope,'model_key':self.a.model_key,'input_sqlite_sha256':native['native_inputs_sha256'],'source_inputs_sqlite_sha256':native['source_inputs_sha256'],'scoring_protocol_sha256':digest(protocol),'source_metrics_protocol_sha256':digest(self.protocol),'runner_sha256':self.binding['original_hf_entrypoint_sha256'],'scope_adapter_binding':copy.deepcopy(self.binding),'backend':backend.identity,'batch_size':self.a.batch_size,'context_tokens':self.engine.CONTEXT,'max_new_tokens':self.engine.MAX_NEW,'seed':12,'schedule':'lexicalquestionthenminimumrequestorder','latency_scope':'Per-rowelapsed_secondsisamortizedbatchcost,notindividualrequestlatency'}
 def plan(self):
  return {'status':'PLAN_ONLY_NO_MODEL_OR_NETWORK','experiment_scope':self.scope,'model_key':self.a.model_key,'model':self.spec,'source':self.source_summary(self.inputs),'source_protocol_sha256':self.entry['protocol_sha256'],'scope_adapter_binding':self.binding,'batch_size':self.a.batch_size,'dtype':'bfloat16','context_tokens':self.engine.CONTEXT,'max_new_tokens':self.engine.MAX_NEW,'native_token_preflight':'Every full prompt is rendered and measured using this model tokenizer before any generation; overflow is rejected without truncation.','source_inputs_or_protocol_changed':False,'actual_gpu_inference':False}
 def run(self,backend=None):
  self.check_frozen();filesystem=self.engine.local_filesystem(self.a.output)
  backend=self.bind_backend(backend or self.engine.HFBackend(self.a,self.spec))
  native=self.prepare(backend);protocol=self.derived(native);backend.load()
  require(backend.identity['tokenizer']['scope_adapter_binding']==self.binding,'Loaded backend omitted adapter provenance')
  config=self.config(backend,native,protocol)
  self.engine.atomic(self.a.output/'runtime_observations.json',{'created_utc':self.engine.now(),'output_filesystem':filesystem,'experiment_scope':self.scope,'scope_adapter_binding':self.binding,'GPU_execution_validation':'Backend is loaded only by --run; fixture backends remain explicitly marked in saved backend implementation.'})
  result=self.engine.run_engine(self.a.output/'native_inputs.sqlite',self.a.output,backend,config,self.a.batch_size)
  self.check_frozen();return result
 def score(self):
  self.check_frozen();native=read(self.a.output/'input_manifest.json');self.validate_native(native)
  protocol=self.derived(native)
  manifest=read(self.a.output/'run_manifest.json');config=manifest['config']
  require(config.get('experiment_scope')==self.scope and config.get('scope_adapter_binding')==self.binding,'Actual run configuration belongs to another scope or adapter revision')
  require(config['runner_sha256']==self.binding['original_hf_entrypoint_sha256'],'Actual run used another HF engine entrypoint')
  require(config['backend']['tokenizer']['scope_adapter_binding']==self.binding,'Actual backend scope identity differs')
  # The original score rechecks the logical response snapshot, actual metadata,
  # model identity, full coverage, source metric/protocol fingerprints and all
  # closed scoring output hashes. No synthetic response or alternate metric is
  # introduced by this adapter.
  self.engine.score(self.a)
  destination=self.a.score_output or self.a.output/('partial_scoring'if self.a.partial else'scoring')
  score_name='partial_scoring_manifest.json'if self.a.partial else'scoring_manifest.json'
  scored=read(destination/score_name)
  record={'status':'PARTIAL_SCOPE_SCORING_DIAGNOSTIC'if self.a.partial else'COMPLETE_SCOPE_GENERATION_SCORING','experiment_scope':self.scope,'model_key':self.a.model_key,'scope_adapter_binding':self.binding,'derived_protocol_sha256':digest(protocol),'scoring_manifest_sha256':digest(destination/score_name),'actual_unique_response_records':scored['actual_unique_response_records'],'scored_request_rows':scored['scored_request_rows'],'expected_request_rows':self.entry['requested_rows'],'response_config_sha256':scored['response_config_sha256'],'response_snapshot_sha256':scored['response_snapshot_sha256'],'metric_source_unchanged':True,'independent_gpu_execution_attestation':False}
  path=self.a.output/('partial_scope_scoring_manifest.json'if self.a.partial else'scope_scoring_manifest.json')
  if path.exists():require(read(path)==record,'Existing scope scoring receipt differs')
  else:self.engine.atomic(path,record)
  return record

def parser():
 p=argparse.ArgumentParser(description=__doc__);actions=p.add_mutually_exclusive_group()
 for action in ('plan','run','score','self-test'):actions.add_argument('--'+action,action='store_true')
 p.add_argument('--scope',choices=SCOPES);p.add_argument('--model-key',choices=MODEL_KEYS);p.add_argument('--registry',type=Path);p.add_argument('--revision');p.add_argument('--source-inputs',type=Path);p.add_argument('--source-protocol',type=Path);p.add_argument('--scorer',type=Path);p.add_argument('--output',type=Path);p.add_argument('--cache-dir',type=Path);p.add_argument('--device',default='cuda:0');p.add_argument('--batch-size',type=int,default=8);p.add_argument('--score-output',type=Path);p.add_argument('--partial',action='store_true')
 return p

def main(argv=None):
 a=parser().parse_args(argv)
 if a.self_test:
  path=HERE/'test_hf_scope.py';spec=importlib.util.spec_from_file_location('group9_scope_adapter_tests',path);test=importlib.util.module_from_spec(spec);spec.loader.exec_module(test)
  with contextlib.redirect_stdout(io.StringIO()):result=test.run_checks()
  print(json.dumps(result,indent=2));return
 context=ScopeContext(a)
 if a.score:result=context.score()
 elif a.run:result={k:v for k,v in context.run().items()if k!='config'}
 else:result=context.plan()
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()
