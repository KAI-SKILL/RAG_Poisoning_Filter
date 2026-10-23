"""Read-only validation of the twelve closed Q/E1/E2/E3 model result slots.

No model, network, submission, or inherited CPU output is used. Process/Slurm
status never establishes completion. Missing or corrupt slots produce an
INCOMPLETE inventory. Only exact actual response coverage, bound model/device
identity, frozen scoring and closed postanalysis can establish ALL_COMPLETE.
"""
from __future__ import annotations
import argparse,csv,datetime,hashlib,importlib.util,io,json,math,os,re,sqlite3,tempfile,zipfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
PROJECT_ROOT=HERE.parents[1]
MODELS=('qwen25_3b_gguf','qwen3_8b','llama31_8b')
SCOPES=('Q','E1','E2','E3')
SCHEMA='Group9-all-experiments-v1'
HEX=re.compile(r'^[0-9a-f]{64}$')

def stable(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def textsha(value):return hashlib.sha256(value.encode()).hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def require(condition,message):
 if not condition:raise ValueError(message)
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
def readonly(path):return sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro&immutable=1',uri=True)
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def timestamp(value):
 require(isinstance(value,str),'Missing execution timestamp');result=datetime.datetime.fromisoformat(value)
 require(result.tzinfo is not None,'Execution timestamp lacks timezone');return result

def local_path(root,name):
 require(isinstance(name,str)and name and not Path(name).is_absolute()and '..'not in Path(name).parts,'Unsafe relative artifact path')
 path=(Path(root)/name).resolve();require(Path(root).resolve()in path.parents,'Artifact path escapes its root')
 return path

class Digests:
 """Reuse a file hash only while its inode, size, ctime and mtime stay fixed."""
 def __init__(self):self.cache={}
 def __call__(self,path):
  path=Path(path);require(path.is_file(),'Missing file: '+str(path));s=path.stat();identity=(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
  if path in self.cache and self.cache[path][0]==identity:return self.cache[path][1]
  h=hashlib.sha256()
  with path.open('rb')as stream:
   for block in iter(lambda:stream.read(4*1024*1024),b''):h.update(block)
  after=path.stat();require(identity==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns),'File changed while hashing: '+str(path))
  value=h.hexdigest();self.cache[path]=(identity,value);return value

def groups(value):
 if isinstance(value,dict):value=[{'condition':condition,'policy':policy,'rows':n}for condition,policies in value.items()for policy,n in policies.items()]
 require(isinstance(value,list)and bool(value),'Missing condition-policy coverage')
 normalized=[];seen=set()
 for row in value:
  require(isinstance(row,dict)and set(row)=={'condition','policy','rows'},'Invalid condition-policy coverage')
  key=(row['condition'],row['policy']);require(key not in seen,'Duplicate condition-policy coverage');seen.add(key)
  require(key[0]in ('clean','attack','matched_benign')and isinstance(key[1],str)and isinstance(row['rows'],int)and row['rows']>0,'Invalid condition-policy coverage value')
  normalized.append(row)
 return sorted(normalized,key=lambda row:(row['condition'],row['policy']))

def closed_hashes(directory,manifest_name,hashes,digest):
 require(isinstance(hashes,dict)and bool(hashes),'No closed output fingerprints')
 wanted=set()
 for name,value in hashes.items():
  require(Path(name).name==name and HEX.fullmatch(value)is not None,'Unsafe or malformed closed output fingerprint')
  path=local_path(directory,name);require(digest(path)==value,'Closed output fingerprint differs: '+name);wanted.add(name)
 actual={p.relative_to(directory).as_posix()for p in Path(directory).rglob('*')if p.is_file()and p.name!=manifest_name}
 require(actual==wanted,'Closed output file coverage differs')

def observed_closed_records(directory):
 """Count saved records without promoting a partial export to a full result."""
 directory=Path(directory);response=directory/'generation_responses.sqlite';inputs=directory/'native_inputs.sqlite'
 result={'observed_unique_response_records':0,'observed_expected_native_unique_prompts':None,'observed_missing_native_unique_prompts':None,'observed_request_rows_with_response':0,'observed_response_config_sha256':None,'response_identity_and_metrics_complete':False}
 keys=set()
 if response.is_file():
  db=readonly(response)
  try:
   require(db.execute('PRAGMA integrity_check').fetchone()[0]=='ok','Observed response database integrity failed')
   metadata=dict(db.execute('SELECT key,value FROM metadata'));require(textsha(stable(json.loads(metadata['config'])))==metadata['config_sha256'],'Observed response configuration hash differs')
   for key,fingerprint in db.execute('SELECT prompt_sha256,config_sha256 FROM responses'):
    require(key not in keys and fingerprint==metadata['config_sha256'],'Observed response key/configuration differs');keys.add(key)
   result.update(observed_unique_response_records=len(keys),observed_response_config_sha256=metadata['config_sha256'])
  finally:db.close()
 if inputs.is_file():
  db=readonly(inputs)
  try:
   expected={r[0]for r in db.execute('SELECT prompt_sha256 FROM prompts')};require(keys<=expected,'Observed responses contain keys outside native inputs')
   if response.is_file():
    db.execute('ATTACH DATABASE ? AS actual',(response.resolve().as_uri()+'?mode=ro&immutable=1',));mapped=db.execute('SELECT count(*) FROM requests r JOIN actual.responses a USING(prompt_sha256)').fetchone()[0]
   else:mapped=0
   result.update(observed_expected_native_unique_prompts=len(expected),observed_missing_native_unique_prompts=len(expected-keys),observed_request_rows_with_response=mapped)
  finally:db.close()
 return result

class Inspector:
 def __init__(self,root,registry_path=None,allow_mock=False):
  self.root=Path(root).resolve();self.digest=Digests();self.allow_mock=bool(allow_mock)
  self.registry_path=Path(registry_path or self.root/'generation/all_experiments/experiment_registry.json').resolve();self.registry=read(self.registry_path);self.registry_sha256=self.digest(self.registry_path)
  require(self.registry.get('schema')==SCHEMA and set(self.registry['scopes'])==set(SCOPES),'Wrong complete-experiment registry')
  require(set(self.registry['required_models'])==set(MODELS),'Registry does not require all three model families')
  self.metric_path=self.root/'code/generation/score_generations.py';self.metric_sha256=self.digest(self.metric_path)
  require(self.registry['metric_source_sha256']==self.metric_sha256,'Registry frozen metric source differs')
  self.post_path=self.root/'generation/all_experiments/postanalyse_scope.py';self.post_sha256=self.digest(self.post_path)
  require(self.registry['postanalysis_source_sha256']==self.post_sha256,'Registry postanalysis source differs')
  self.metric=load(self.metric_path,'collector_frozen_metric_'+self.metric_sha256[:12])
  self.hf_models=read(self.root/'generation/hf_gpu/model_registry.json');self.source={}
  for scope,entry in self.registry['scopes'].items():
   require(set(entry.get('required_models',self.registry['required_models']))==set(MODELS),'Scope omits a required model')
   inputs=local_path(self.root,entry['inputs_file']);protocol=local_path(self.root,entry['protocol_file']);p=read(protocol)
   require(self.digest(inputs)==entry['inputs_sha256']and self.digest(protocol)==entry['protocol_sha256'],'Registered source bytes differ: '+scope)
   require(protocol.with_suffix('.sha256').read_text().split()[0]==entry['protocol_sha256'],'Source protocol checksum differs: '+scope)
   require(p['inputs_sqlite_sha256']==entry['inputs_sha256']and p['scorer_sha256']==self.metric_sha256,'Source protocol identity differs: '+scope)
   require(p['requested_rows']==entry['requested_rows']and p['unique_prompts']==entry['source_unique_prompts']and set(p['policies'])==set(entry['policies']),'Source protocol coverage differs: '+scope)
   if 'scope'in p:require(str(p['scope']).upper()==scope,'Source protocol scope differs')
   if 'condition_policy_counts'in p:require(groups(p['condition_policy_counts'])==groups(entry['condition_policy_counts']),'Source protocol condition-policy coverage differs')
   self.source[scope]=(entry,inputs,protocol,p)
 def export_inventory(self,directory):
  directory=Path(directory);manifest=directory/'export_files.json';record=read(manifest);require(isinstance(record,list)and bool(record),'Missing closed export file inventory')
  before=self.digest(manifest);paths={}
  for row in record:
   require(set(row)=={'path','bytes','sha256'}and isinstance(row['bytes'],int)and row['bytes']>=0 and HEX.fullmatch(row['sha256'])is not None,'Malformed export file inventory row')
   name=row['path'];require(name not in paths and name!='export_files.json','Duplicate export artifact path')
   path=local_path(directory,name);require(not path.is_symlink(),'Closed export retains a symbolic link')
   require(path.is_file()and path.stat().st_size==row['bytes']and self.digest(path)==row['sha256'],'Closed export artifact differs: '+name);paths[name]=row
   require(not any(part.startswith('.')or part=='__pycache__'for part in Path(name).parts)and not name.endswith(('-wal','-shm','-journal','.partial','.pyc')),'Live or unfinished file in closed export')
  actual={p.relative_to(directory).as_posix()for p in directory.rglob('*')if p.is_file()and p.name!='export_files.json'}
  require(actual==set(paths),'Closed export inventory misses or adds files')
  require(self.digest(manifest)==before,'Export file inventory changed during validation')
  return {'manifest_sha256':before,'file_count':len(paths),'files':paths}
 def scope_marker(self,directory,model,scope):
  entry,inputs,protocol,p=self.source[scope];marker=read(directory/'suite_scope_binding.json')
  required={'model_key':model,'scope':scope,'registry_sha256':self.registry_sha256,'inputs_sha256':entry['inputs_sha256'],'source_protocol_sha256':entry['protocol_sha256'],'suite_entrypoint_sha256':self.digest(self.root/'generation/all_experiments/run_model_suite.py')}
  for key,value in required.items():require(marker.get(key)==value,'Suite scope/model/source binding differs: '+key)
  if 'postanalysis_source_sha256'in marker:require(marker['postanalysis_source_sha256']==self.post_sha256,'Suite postanalysis source differs')
  return marker
 def hf_binding(self,model,scope):
  entry,_,_,_=self.source[scope]
  return {'scope':scope,'registry_schema':SCHEMA,'registry_sha256':self.registry_sha256,'registry_scope_entry_sha256':textsha(stable(entry)),'adapter_entrypoint_sha256':self.digest(self.root/'generation/all_experiments/run_hf_scope.py'),'original_hf_entrypoint_sha256':self.digest(self.root/'generation/hf_gpu/run_hf_grid.py'),'model_registry_sha256':self.digest(self.root/'generation/hf_gpu/model_registry.json'),'source_inputs_sha256':entry['inputs_sha256'],'source_protocol_sha256':entry['protocol_sha256'],'metric_source_sha256':self.metric_sha256,'identity_note':'Adapter provenance; no source protocol or model text is changed.'}
 def native_gpu(self,directory,config,protocol,marker):
  gpu=load(self.root/'generation/all_experiments/launch_native_gpu.py','collector_cuda_proof')
  evidence=read(directory/'actual_gpu_evidence.json');execution=read(directory/'native_gpu_execution.json');launch=read(directory/'server_launch.json');identity=evidence['identity']
  require(identity.get('status')=='ACTUAL_CUDA_DEVICE_VERIFIED'and isinstance(identity.get('gpu_name'),str)and identity['gpu_name']and isinstance(identity.get('memory_total_mib'),int)and identity['memory_total_mib']>0,'Missing actual allocated CUDA identity')
  require(evidence['schema_version']==gpu.SCHEMA and execution['schema_version']==gpu.SCHEMA and evidence['verification_config']==execution['verification_config']==gpu.VERIFICATION_CONFIG,'GPU evidence verification configuration differs')
  require(execution['identity']==identity and protocol['native_suite_binding']['actual_gpu_evidence']==identity,'Actual device is not bound into runtime scoring protocol')
  fixed=gpu.binding(identity)
  require(launch['actual_gpu_identity']==identity and launch['native_gpu_verification']==gpu.VERIFICATION_CONFIG and launch['actual_cuda_binding_sha256']==fixed['sha256'],'Native launch CUDA identity differs')
  require(launch['launcher_sha256']==self.digest(self.root/'generation/all_experiments/launch_native_gpu.py'),'Native CUDA launcher source differs')
  require(config['server_launch_identity']['launcher_sha256']==launch['launcher_sha256']and config['server_launch_identity']['transport']==launch['transport']and('actual_cuda_binding_sha256='+fixed['sha256'])in launch['transport'],'Actual response configuration did not bind CUDA proof')
  argv=launch['server_argv'];require('-ngl'in argv and argv[argv.index('-ngl')+1]=='99','Native launch does not request full GPU offload')
  normalized=list(argv);normalized[0]=Path(normalized[0]).name
  if '-m'in normalized:normalized[normalized.index('-m')+1]=Path(normalized[normalized.index('-m')+1]).name
  require(config['server_launch_identity']['server_argv']==normalized,'Actual launch arguments differ from response configuration')
  require(config['server_build_identity']['backend']=='CUDA','Recorded native build is not CUDA')
  source=read(self.root/'generation/runtime/source_identity.json')
  require(config['server_build_identity']['vendor_llama_cpp_commit']==source['vendor_llama_cpp_commit']and config['server_build_identity']['archive_sha256']==source['archive_sha256'],'Native runtime source revision differs')
  artifacts=config['server_build_identity']['artifacts'];require(any(Path(a.get('path',a.get('file',''))).name=='llama-server'and a['sha256']==launch['native_server_sha256']for a in artifacts),'Native server binary identity differs from build artifacts')
  require(config['server_launch_identity']['native_server_sha256']==launch['native_server_sha256'],'Actual server binary identity differs')
  intervals=[];sessions=execution.get('sessions');require(isinstance(sessions,list)and sessions,'No actual native server sessions')
  previous_end=-1
  for session in sessions:
   if not session.get('generation_started'):continue
   require(session['status']=='ACTUAL_CUDA_FULL_OFFLOAD_VERIFIED'and session['actual_cuda_binding_sha256']==fixed['sha256'],'Generated responses came from an unverified CUDA session')
   require(session.get('slurm_job_id')and session.get('all_model_layers_offloaded')is True and session['offloaded_layers']==session['total_layers']>0,'GPU session has no complete positive layer offload')
   start,end=session['log_start_offset'],session['log_end_offset'];require(isinstance(start,int)and isinstance(end,int)and end>start>=0 and start>=previous_end,'Overlapping or invalid same-session log offsets');previous_end=end
   startup=local_path(directory,session['startup_log_file']);excerpt=local_path(directory,session['excerpt_file']);log=local_path(directory,session['log_file'])
   require(self.digest(startup)==session['startup_log_sha256']and self.digest(excerpt)==session['excerpt_sha256'],'GPU log proof bytes differ')
   data=startup.read_bytes();require(len(data)==end-start,'GPU startup log offsets disagree with recorded bytes')
   with log.open('rb')as stream:stream.seek(start);require(stream.read(end-start)==data,'GPU proof does not come from the recorded same-session server bytes')
   proof,expected=gpu.verify_new_log(data,identity);require(excerpt.read_bytes()==expected.encode(),'GPU excerpt does not match independently parsed startup proof')
   for field in ('offloaded_layers','total_layers','all_model_layers_offloaded'):require(session[field]==proof[field],'GPU parsed proof differs: '+field)
   detailed=local_path(directory,'native_gpu_sessions/'+session['session_id']+'/session.json');require(read(detailed)==session,'GPU session ledger and detailed receipt differ')
   require(isinstance(session.get('generator_returncode'),int),'GPU session has no finished generator accounting')
   intervals.append((timestamp(session['verified_utc']),timestamp(session['generator_finished_utc'])))
  require(intervals,'No verified CUDA session actually started generation')
  return intervals
 def validate_inputs(self,directory,model,scope,protocol,native):
  entry,source,_,_=self.source[scope];path=directory/'native_inputs.sqlite';require(self.digest(path)==protocol['inputs_sqlite_sha256']==native['native_inputs_sha256'],'Native input bytes differ')
  db=readonly(path);db.row_factory=sqlite3.Row
  try:
   require(db.execute('PRAGMA integrity_check').fetchone()[0]=='ok','Native input integrity failed')
   columns=[r[1]for r in db.execute('PRAGMA table_info(requests)')];require(columns and all(re.fullmatch('[a-z_][a-z0-9_]*',c)for c in columns),'Unsafe native request column')
   requested=db.execute('SELECT count(*) FROM requests').fetchone()[0];keys=set()
   for prompt_row in db.execute('SELECT * FROM prompts'):
    prompt_row=dict(prompt_row);key,chat,user=prompt_row['prompt_sha256'],prompt_row['chat_prompt'],prompt_row['prompt']
    require(isinstance(chat,str)and textsha(chat)==key and key not in keys,'Full native prompt/hash coverage differs');keys.add(key)
    require(isinstance(user,str)and user.encode()in chat.encode(),'Native full prompt does not preserve its exact user body')
    if model!='qwen25_3b_gguf':require(prompt_row['user_body_sha256']==textsha(user),'Native user body fingerprint differs from actual bytes')
   actual_groups=[{'condition':c,'policy':p,'rows':n}for c,p,n in db.execute('SELECT condition,policy,count(*) FROM requests GROUP BY condition,policy ORDER BY condition,policy')]
   require(requested==entry['requested_rows']and actual_groups==groups(entry['condition_policy_counts']),'Native request scope coverage differs')
   require({r[0]for r in db.execute('SELECT DISTINCT prompt_sha256 FROM requests')}==keys,'Native full-prompt/request coverage differs')
   db.execute('ATTACH DATABASE ? AS original',(source.resolve().as_uri()+'?mode=ro&immutable=1',))
   original_columns=[r[1]for r in db.execute('PRAGMA original.table_info(requests)')];require(columns==original_columns,'Native source request schema changed')
   require(db.execute('SELECT request_order FROM requests EXCEPT SELECT request_order FROM original.requests').fetchone()is None and db.execute('SELECT request_order FROM original.requests EXCEPT SELECT request_order FROM requests').fetchone()is None,'Native/source request order keys do not exactly cover each other')
   compared=[c for c in columns if c!='prompt_sha256'];difference=' OR '.join('n.'+c+' IS NOT s.'+c for c in compared)
   require(db.execute('SELECT count(*) FROM requests n JOIN original.requests s USING(request_order) WHERE '+difference).fetchone()[0]==0,'Native request metadata differs from registered source')
   require(db.execute('SELECT count(*) FROM original.requests').fetchone()[0]==requested,'Source/native request counts differ')
   if model=='qwen25_3b_gguf':require(self.digest(path)==entry['inputs_sha256'],'Native GGUF branch changed the original ChatML input bytes')
   else:
    require(db.execute('SELECT count(*) FROM source_prompt_map').fetchone()[0]==entry['source_unique_prompts'],'Native source prompt map coverage differs')
    require(db.execute('SELECT source_prompt_sha256 FROM source_prompt_map EXCEPT SELECT prompt_sha256 FROM original.prompts').fetchone()is None and db.execute('SELECT prompt_sha256 FROM original.prompts EXCEPT SELECT source_prompt_sha256 FROM source_prompt_map').fetchone()is None,'Native source prompt map source keys do not exactly cover original prompts')
    require(db.execute('SELECT native_prompt_sha256 FROM source_prompt_map EXCEPT SELECT prompt_sha256 FROM prompts').fetchone()is None and db.execute('SELECT prompt_sha256 FROM prompts EXCEPT SELECT native_prompt_sha256 FROM source_prompt_map').fetchone()is None,'Native source prompt map native keys do not exactly cover native prompts')
    require(db.execute('SELECT count(*) FROM original.prompts s JOIN source_prompt_map m ON m.source_prompt_sha256=s.prompt_sha256 JOIN prompts n ON n.prompt_sha256=m.native_prompt_sha256 WHERE s.prompt IS NOT n.prompt').fetchone()[0]==0,'Native renderer changed original user bodies')
    require(db.execute('SELECT count(*) FROM source_prompt_map m JOIN prompts n ON n.prompt_sha256=m.native_prompt_sha256 WHERE m.user_body_sha256 IS NOT n.user_body_sha256').fetchone()[0]==0,'Native source map user-body fingerprint differs')
    require(db.execute('SELECT count(*) FROM original.requests s JOIN requests n USING(request_order) JOIN source_prompt_map m ON m.source_prompt_sha256=s.prompt_sha256 WHERE n.prompt_sha256 IS NOT m.native_prompt_sha256').fetchone()[0]==0,'Native request prompt mapping differs from source map')
   require(protocol['requested_rows']==requested and protocol['unique_prompts']==len(keys),'Derived protocol grid coverage differs')
  finally:db.close()
  return {'requested_rows':requested,'keys':keys,'unique_prompts':len(keys),'path':path}
 def actual_responses(self,directory,model,inputs,config_hash):
  path=directory/'generation_responses.sqlite';db=readonly(path);db.row_factory=sqlite3.Row;native=readonly(inputs['path']);native.row_factory=sqlite3.Row
  try:
   require(db.execute('PRAGMA integrity_check').fetchone()[0]=='ok','Response database integrity failed')
   metadata=dict(db.execute('SELECT key,value FROM metadata'));config=json.loads(metadata['config'])
   require(textsha(stable(config))==metadata['config_sha256']==config_hash,'Actual response metadata configuration hash differs')
   committed={};attempts=known=unknown=errors=0
   has_batch='batch_id'in {row[1]for row in db.execute('PRAGMA table_info(attempts)')}
   for record in db.execute('SELECT * FROM attempts ORDER BY attempt_id'):
    row=dict(record);attempts+=1;prompt_keys=json.loads(row['prompt_keys_json']);require(isinstance(prompt_keys,list)and len(prompt_keys)==row['prompt_count']and len(set(prompt_keys))==len(prompt_keys),'Attempt ledger prompt count differs')
    if row['returned_count']is None:unknown+=row['prompt_count']
    else:
     require(isinstance(row['returned_count'],int)and row['returned_count']>=0,'Invalid actual returned sequence count');known+=row['returned_count']
     raw=json.loads(row['raw_json']);raw=raw if isinstance(raw,list)else[raw];require(len(raw)==row['returned_count'],'Attempt raw return count differs')
    if row['status']=='ERROR_UNKNOWN':errors+=1
    if row['status']=='COMMITTED':
     require(row['returned_count']==row['prompt_count'],'Committed attempt is missing returned sequences')
     actual_keys=[]
     for raw_row in raw:
      key=textsha(raw_row['prompt'])if model=='qwen25_3b_gguf'else raw_row['prompt_sha256'];actual_keys.append(key)
      require(key not in committed,'A full prompt has multiple committed executions in one slot')
      committed[key]=(row['batch_id']if has_batch else row['attempt_id'],textsha(stable(raw_row)))
     require(actual_keys==prompt_keys,'Committed raw prompt order differs from submitted ledger')
   rows=set();snapshot=hashlib.sha256();executed=[]
   for record in db.execute('SELECT * FROM responses ORDER BY prompt_sha256'):
    row=dict(record);key=row['prompt_sha256'];require(key not in rows and row['config_sha256']==config_hash,'Actual response key/configuration differs');rows.add(key)
    require(isinstance(row['response'],str)and row['finish_reason']in ('stop','length'),'Invalid response text/termination')
    require(all(isinstance(row[k],int)and row[k]>=0 for k in ('prompt_tokens','completion_tokens'))and row['completion_tokens']<=48,'Invalid measured actual token counts')
    require(isinstance(row['elapsed_seconds'],(int,float))and math.isfinite(row['elapsed_seconds'])and row['elapsed_seconds']>=0,'Invalid measured elapsed time')
    raw=json.loads(row['raw_json']);require((row['batch_id'],textsha(stable(raw)))==committed.get(key),'Actual response is not backed by its committed raw attempt')
    prompt=native.execute('SELECT * FROM prompts WHERE prompt_sha256=?',(key,)).fetchone();require(prompt is not None,'Actual response has an unregistered full prompt');prompt=dict(prompt)
    if model=='qwen25_3b_gguf':
     require(raw.get('prompt')==prompt['chat_prompt']and raw.get('content','').strip()==row['response']and not raw.get('truncated',False),'Native returned full prompt/content differs')
     require(row['finish_reason']==('length'if raw.get('stopped_limit')or raw.get('stop_type')=='limit'else'stop'),'Native stored finish reason differs from actual raw termination')
     timing=raw.get('timings',{});measured_prompt=raw.get('tokens_evaluated',timing.get('prompt_n'));measured_completion=raw.get('tokens_predicted',timing.get('predicted_n'))
     require(measured_prompt==row['prompt_tokens']and measured_completion==row['completion_tokens']and abs(row['prompt_tokens']-inputs['gguf_token_map'][key])<=1,'Native actual measured tokens differ from raw return or pinned preflight')
    else:
     require(raw['prompt_sha256']==key and raw['input_body_sha256']==prompt['user_body_sha256'],'HF raw response prompt/body identity differs')
     for field in ('response','finish_reason','prompt_tokens','completion_tokens'):require(raw[field]==row[field],'HF raw/actual response field differs: '+field)
     require(row['prompt_tokens']==prompt['prompt_tokens'],'HF actual tokens differ from native preflight')
     if not self.allow_mock:require(isinstance(raw.get('output_token_ids'),list)and len(raw['output_token_ids'])==row['completion_tokens'],'HF raw actual output token IDs are missing')
    executed.append(timestamp(row['executed_utc']));snapshot.update((stable(row)+'\n').encode())
   require(rows==inputs['keys'],'Actual unique response keys do not exactly cover full native prompts')
   require(set(committed)==rows,'Committed raw attempts and actual response keys differ')
  finally:db.close();native.close()
  return {'count':len(rows),'response_snapshot_sha256':snapshot.hexdigest(),'config':config,'config_sha256':config_hash,'metadata':metadata,'executed_times':executed,'attempts':attempts,'known_returned':known,'unknown_requested':unknown,'errors':errors}
 def score_rows(self,directory,inputs,model):
  native=readonly(inputs['path']);native.row_factory=sqlite3.Row;db=readonly(directory/'generation_responses.sqlite');db.row_factory=sqlite3.Row;seen=set();clean={}
  try:
   for request in native.execute("SELECT question_id,policy,prompt_sha256 FROM requests WHERE condition='clean'"):
    response=db.execute('SELECT response,finish_reason,completion_tokens FROM responses WHERE prompt_sha256=?',(request['prompt_sha256'],)).fetchone();require(response is not None,'Missing clean generation')
    key=(request['question_id'],request['policy']);require(key not in clean,'Duplicate same-policy clean request');clean[key]=dict(response)
   with (directory/'scoring/request_scores.jsonl').open(encoding='utf-8')as stream:
    for line in stream:
     require(line.endswith('\n'),'Unterminated scored request record');row=json.loads(line);key=row['request_id'];require(key not in seen,'Duplicate scored request ID');seen.add(key)
     request=native.execute('SELECT * FROM requests WHERE request_id=?',(key,)).fetchone();require(request is not None,'Scored request is outside registered native grid');request=dict(request)
     for field in ('request_id','request_order','prompt_sha256','case_id','question_id','article_id','family_id','template_id','condition','policy','objective','requested_output'):require(row[field]==request[field],'Scored request/source field differs: '+field)
     require(row['reference_answers']==json.loads(request['reference_answers_json'])and row['metadata']==json.loads(request['metadata_json']),'Scored request aliases/metadata differ')
     response=db.execute('SELECT response,finish_reason,prompt_tokens,completion_tokens FROM responses WHERE prompt_sha256=?',(request['prompt_sha256'],)).fetchone()
     for field in ('response','finish_reason','prompt_tokens','completion_tokens'):require(row[field]==response[field],'Scored response/actual field differs: '+field)
     expected={**row,'metrics':self.metric.score_response(row['response'],row['reference_answers'],row['requested_output'],row['finish_reason'],row['completion_tokens'])}
     if row['condition']=='clean':expected['metrics'].update({name:None for name in self.metric.CASE_METRICS})
     else:self.metric.enrich_case(expected,clean.get((row['question_id'],row['policy'])))
     require(set(row['metrics'])==set(expected['metrics']),'Scored request metric coverage differs')
     for field,value in expected['metrics'].items():
      actual=row['metrics'][field]
      if isinstance(value,float):require(isinstance(actual,(int,float))and math.isclose(actual,value,rel_tol=1e-12,abs_tol=1e-12),'Recomputed actual request metric differs: '+field)
      else:require(actual==value,'Recomputed actual request metric differs: '+field)
   require(len(seen)==inputs['requested_rows'],'Scored request ID coverage differs from full grid')
  finally:native.close();db.close()
  return len(seen)
 def validate_payload(self,directory,model,scope):
  directory=Path(directory).resolve();entry,source,source_protocol,original=self.source[scope];marker=self.scope_marker(directory,model,scope)
  for p in directory.rglob('*'):
   if p.is_file()and p.name.endswith(('-wal','-shm','-journal','.partial')):raise ValueError('Result payload retains a live or unfinished file')
  protocol=read(directory/'scoring_protocol.json');native=read(directory/'input_manifest.json');manifest=read(directory/'run_manifest.json')
  require(protocol['scorer_sha256']==self.metric_sha256 and protocol['scoring_version']==original['scoring_version'],'Actual scoring metric definition differs')
  inputs=self.validate_inputs(directory,model,scope,protocol,native)
  config=manifest['config'];config_hash=textsha(stable(config));require(config_hash==manifest['config_sha256'],'Run configuration fingerprint differs')
  require(config['input_sqlite_sha256']==self.digest(inputs['path'])and config['scoring_protocol_sha256']==self.digest(directory/'scoring_protocol.json'),'Generation input/protocol fingerprint differs')
  if model=='qwen25_3b_gguf':
   binding=protocol['native_suite_binding']
   for field,value in marker.items():require(binding.get(field)==value,'Native runtime scope binding differs: '+field)
   require(config['model_manifest']==read(self.root/'generation/runtime/model_manifest.json'),'Actual GGUF model/quantization differs from the pinned original model')
   require(config['runner_sha256']==self.digest(self.root/'code/generation/run_native_generation.py'),'Actual native response writer source differs')
   require(config['token_preflight_sha256']==entry['token_receipt_sha256'],'Actual native token preflight differs')
   token_file=local_path(self.root,entry['tokens_file']);token_receipt=local_path(self.root,entry['token_receipt_file'])
   require(self.digest(token_file)==entry['tokens_sha256']and self.digest(token_receipt)==entry['token_receipt_sha256'],'Pinned native token preflight files changed')
   token_db=readonly(token_file)
   try:inputs['gguf_token_map']=dict(token_db.execute('SELECT prompt_sha256,prompt_tokens FROM tokens'))
   finally:token_db.close()
   require(set(inputs['gguf_token_map'])==inputs['keys']and all(isinstance(n,int)and n>0 and n+48<=4096 for n in inputs['gguf_token_map'].values()),'Pinned native tokenizer coverage/length differs')
   require(config['generation_parameters']=={'n_predict':48,'temperature':0.0,'top_k':0,'top_p':1.0,'min_p':0.0,'repeat_penalty':1.0,'seed':12,'stop':['<|im_end|>','<|endoftext|>'],'stream':False,'cache_prompt':False,'return_tokens':True},'Actual native decoding parameters differ from the frozen experiment')
   intervals=self.native_gpu(directory,config,protocol,marker)
  else:
   expected=self.hf_binding(model,scope);require(config.get('experiment_scope')==scope and config.get('scope_adapter_binding')==expected,'Actual HF model scope/adapter binding differs')
   require(native['preparation_identity']['tokenizer']['scope_adapter_binding']==expected and protocol['renderer_change']['tokenizer']['scope_adapter_binding']==expected,'Native preparation/derived protocol scope binding differs')
   require(config['runner_sha256']==expected['original_hf_entrypoint_sha256']and config['source_metrics_protocol_sha256']==entry['protocol_sha256'],'Actual HF engine/source protocol identity differs')
   backend=config['backend'];require(backend['model']==self.hf_models[model]==native['preparation_identity']['model'],'Actual HF model key/revision differs')
   require(config['context_tokens']==4096 and config['max_new_tokens']==48 and config['seed']==12 and config['batch_size']>0,'Actual HF generation budget or seed differs')
   require(backend['tokenizer']['scope_adapter_binding']==expected,'Actual HF tokenizer lacks scope binding')
   if not self.allow_mock:
    require(backend['implementation']=='transformers_native_cuda_bf16','Actual HF backend is not native CUDA BF16')
    environment=backend['environment'];require(environment.get('dtype')=='bfloat16'and environment.get('cuda')and environment.get('gpu_name')and isinstance(environment.get('gpu_total_memory'),int)and environment['gpu_total_memory']>0,'No actual CUDA BF16 device evidence')
    require(backend.get('model_parameter_count',0)>0 and isinstance(backend.get('snapshot_artifacts'),list)and any(a['file'].endswith('.safetensors')and HEX.fullmatch(a['sha256'])and a['bytes']>0 for a in backend['snapshot_artifacts']),'No actual pinned safetensors model artifact identity')
   require((directory/'scoring_protocol.json').with_suffix('.sha256').read_text().split()[0]==self.digest(directory/'scoring_protocol.json'),'Derived HF protocol checksum differs')
  actual=self.actual_responses(directory,model,inputs,config_hash)
  require(actual['config']==config,'Actual stored response configuration differs from run manifest')
  require(manifest['status']=='COMPLETE'and manifest['completed_unique_prompts']==actual['count']==inputs['unique_prompts']and manifest['requested_rows']==inputs['requested_rows'],'Run manifest is not consistent with full actual output coverage')
  require(manifest.get('generator_inference_executed')is True,'Run has no recorded actual inference')
  if model=='qwen25_3b_gguf':
   require(all(any(start<=executed<=end for start,end in intervals)for executed in actual['executed_times']),'Actual native response timestamp falls outside every verified CUDA generation session')
  for field,value in [('cumulative_batch_attempts',actual['attempts']),('cumulative_unknown_outcome_requested_prompts',actual['unknown_requested'])]:require(manifest[field]==value,'Run attempt ledger accounting differs: '+field)
  known='cumulative_known_returned_responses'if model=='qwen25_3b_gguf'else'cumulative_known_returned_sequences';require(manifest[known]==actual['known_returned'],'Actual returned sequence accounting differs')
  scoring_path=directory/'scoring/scoring_manifest.json';score=read(scoring_path)
  expected={'status':'COMPLETE_GENERATION_SCORING','response_config_sha256':config_hash,'response_snapshot_sha256':actual['response_snapshot_sha256'],'input_sqlite_sha256':self.digest(inputs['path']),'native_protocol_sha256':self.digest(directory/'scoring_protocol.json'),'metric_source_sha256':self.metric_sha256,'requested_rows':inputs['requested_rows'],'scored_request_rows':inputs['requested_rows'],'missing_unique_prompts':0,'expected_unique_prompts':inputs['unique_prompts'],'actual_unique_response_records':actual['count'],'scoring_version':original['scoring_version']}
  for field,value in expected.items():require(score.get(field)==value,'Formal scoring identity/coverage differs: '+field)
  require(json.loads(score['response_config_json'])==config,'Formal scoring configuration JSON differs')
  if model!='qwen25_3b_gguf':require(score['model_key']==model and score['model_identity']==self.hf_models[model],'Formal scoring model identity differs')
  closed_hashes(directory/'scoring','scoring_manifest.json',score['closed_output_hashes'],self.digest)
  row_count=self.score_rows(directory,inputs,model)
  post=read(directory/'postanalysis/postanalysis_manifest.json');require(post['status']=='COMPLETE'and post['scope']==scope and post['requested_rows']==inputs['requested_rows']and post['actual_unique_response_records']==actual['count'],'Postanalysis scope/status/coverage differs')
  require(post['missing_pairs']==0 and post['model_calls']==0,'Postanalysis has unresolved required comparisons or model calls')
  expected_post={'source_scoring_manifest_sha256':self.digest(scoring_path),'input_sqlite_sha256':self.digest(inputs['path']),'native_protocol_sha256':self.digest(directory/'scoring_protocol.json'),'response_config_sha256':config_hash,'response_snapshot_sha256':actual['response_snapshot_sha256'],'metric_source_sha256':self.metric_sha256,'request_scores_sha256':self.digest(directory/'scoring/request_scores.jsonl'),'postanalysis_entrypoint_sha256':self.post_sha256,'model_key':model}
  for field,value in expected_post.items():require(post['binding'].get(field)==value,'Postanalysis source/result binding differs: '+field)
  closed_hashes(directory/'postanalysis','postanalysis_manifest.json',post['closed_output_hashes'],self.digest)
  require(self.digest(self.registry_path)==self.registry_sha256,'Registry changed during collection')
  return {'status':'COMPLETE','model_key':model,'scope':scope,'actual_unique_responses':actual['count'],'expected_native_unique_prompts':inputs['unique_prompts'],'mapped_request_rows':inputs['requested_rows'],'scored_request_rows_recomputed':row_count,'config_sha256':config_hash,'response_snapshot_sha256':actual['response_snapshot_sha256'],'native_inputs_sha256':self.digest(inputs['path']),'native_protocol_sha256':self.digest(directory/'scoring_protocol.json'),'scoring_manifest_sha256':self.digest(scoring_path),'postanalysis_manifest_sha256':self.digest(directory/'postanalysis/postanalysis_manifest.json'),'unknown_outcome_requested_prompts':actual['unknown_requested'],'point_metric_check':'Every scored request source mapping, actual response, base metric and clean-paired case metric recomputed. Aggregate/bootstrap files verified by closed fingerprints; intervals not independently resampled.','gpu_execution_evidence':'RECORDED_ACTUAL_DEVICE_AND_BOUND_RUN_CONFIG_NOT_INDEPENDENT_REMOTE_ATTESTATION'}
 def validate_slot(self,directory,model,scope):
  inventory=self.export_inventory(directory)
  result=self.validate_payload(directory,model,scope);receipt=read(Path(directory)/'export_receipt.json')
  require(receipt['status']=='COMPLETE_GENERATION_AND_SCORING'and receipt['full_asr_ready']is True,'Export is not formally complete')
  require(receipt['actual_unique_responses']==result['actual_unique_responses']and receipt['expected_unique_prompts']==result['expected_native_unique_prompts']and receipt['config_sha256']==result['config_sha256'],'Export receipt counts/configuration differ')
  require(self.digest(Path(directory)/'export_files.json')==inventory['manifest_sha256'],'Closed export changed during validation')
  return {**result,'export_inventory_sha256':inventory['manifest_sha256'],'export_files':inventory['file_count']}

def collect(root,results_root=None,registry_path=None,allow_mock=False):
 root=Path(root).resolve();results_root=Path(results_root or root/'generation/all_results').resolve();slots=[];issues=[]
 try:inspector=Inspector(root,registry_path,allow_mock)
 except Exception as error:inspector=None;issues.append(type(error).__name__+': '+str(error))
 for model in MODELS:
  for scope in SCOPES:
   directory=results_root/model/scope;entry=inspector.registry['scopes'][scope]if inspector else{}
   slot={'model_key':model,'scope':scope,'directory':str(directory),'status':'MISSING','actual_unique_responses':0,'mapped_request_rows':entry.get('requested_rows'),'expected_source_unique_prompts':entry.get('source_unique_prompts'),'issues':[],'export_inventory_verified':False}
   if not directory.is_dir():slot['issues']=['No closed result directory; plan or scheduler status is not generated data.']
   elif inspector is None:slot.update(status='UNVERIFIABLE_REGISTRY',actual_unique_responses=None,issues=list(issues))
   else:
    try:inspector.export_inventory(directory);slot['export_inventory_verified']=True;slot.update(observed_closed_records(directory))
    except Exception as error:slot.update(status='INVALID_CLOSED_EXPORT',actual_unique_responses=None,issues=[type(error).__name__+': '+str(error)])
    else:
     try:slot.update(inspector.validate_slot(directory,model,scope));slot['response_identity_and_metrics_complete']=True
     except Exception as error:
      slot.update(status='INCOMPLETE_OR_INVALID_RESULT',actual_unique_responses=slot.get('observed_unique_response_records'),issues=[type(error).__name__+': '+str(error)])
   slots.append(slot)
 complete=sum(s['status']=='COMPLETE'for s in slots);status='ALL_COMPLETE'if complete==12 and not issues else'INCOMPLETE'
 if allow_mock:status='MOCK_ALL_COMPLETE'if status=='ALL_COMPLETE'else'MOCK_INCOMPLETE'
 return {'status':status,'created_utc':now(),'collector_sha256':Digests()(__file__),'registry_sha256':inspector.registry_sha256 if inspector else None,'required_slots':12,'complete_slots':complete,'missing_or_unverified_slots':12-complete,'registry_issues':issues,'model_keys':list(MODELS),'scopes':list(SCOPES),'slots':slots,'full_project_generation_and_analysis_ready':status=='ALL_COMPLETE','existing_cpu_results_inherited':False,'model_calls':0,'network_calls':0,'validation_mode':'MOCK_FIXTURE_VALIDATION_NO_GPU_EXECUTION'if allow_mock else'ACTUAL_SAVED_ARTIFACT_CONSISTENCY','execution_attestation_note':'Checks saved device/configuration evidence and raw outputs; does not independently attest another computer or claim that a job exit status is an experiment result.'}

def atomic(path,data):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix(path.suffix+'.partial')
 with tmp.open('wb')as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
 tmp.replace(path)
def save_inventory(result,destination):
 destination=Path(destination);destination.mkdir(parents=True,exist_ok=True);atomic(destination/'collection_inventory.json',(json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode())
 output=io.StringIO();fields=['model_key','scope','status','actual_unique_responses','expected_source_unique_prompts','expected_native_unique_prompts','mapped_request_rows','observed_unique_response_records','observed_expected_native_unique_prompts','observed_missing_native_unique_prompts','observed_request_rows_with_response','response_identity_and_metrics_complete','export_inventory_verified','issues'];writer=csv.DictWriter(output,fieldnames=fields);writer.writeheader()
 for slot in result['slots']:writer.writerow({field:json.dumps(slot.get(field),ensure_ascii=False)if field=='issues'else slot.get(field)for field in fields})
 atomic(destination/'collection_inventory.csv',output.getvalue().encode('utf-8-sig'))
def package(result,destination):
 destination=Path(destination).resolve();name='Group9_All_Experiments_COMPLETE_Results.zip'if result['status']=='ALL_COMPLETE'else'Group9_All_Experiments_INCOMPLETE_Checkpoints.zip';archive=destination/name;temporary=archive.with_suffix('.zip.partial');digest=Digests();included=[]
 with zipfile.ZipFile(temporary,'w',zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True)as output:
  for filename in ['collection_inventory.json','collection_inventory.csv']:output.write(destination/filename,arcname='all_collected/'+filename)
  for slot in result['slots']:
   if not slot['export_inventory_verified']:continue
   directory=Path(slot['directory']);before=digest(directory/'export_files.json');rows=read(directory/'export_files.json')
   for row in rows:
    path=local_path(directory,row['path']);require(digest(path)==row['sha256'],'Closed export changed before packaging')
    output.write(path,arcname='all_results/'+slot['model_key']+'/'+slot['scope']+'/'+row['path'])
   require(digest(directory/'export_files.json')==before,'Closed export inventory changed before packaging')
   output.write(directory/'export_files.json',arcname='all_results/'+slot['model_key']+'/'+slot['scope']+'/export_files.json');included.append(slot['model_key']+'/'+slot['scope'])
 with zipfile.ZipFile(temporary)as output:require(output.testzip()is None,'Collection ZIP CRC failed')
 temporary.replace(archive);receipt={'status':'PACKAGE_CLOSED_RESULTS'if result['status']=='ALL_COMPLETE'else'PACKAGE_INCOMPLETE_CHECKPOINTS','archive_file':name,'archive_bytes':archive.stat().st_size,'archive_sha256':digest(archive),'inventory_sha256':digest(destination/'collection_inventory.json'),'included_closed_slots':included,'full_project_generation_and_analysis_ready':result['status']=='ALL_COMPLETE','model_calls':0};atomic(destination/'collection_package_receipt.json',(json.dumps(receipt,indent=2)+'\n').encode());return receipt

def main(argv=None):
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--project-root',type=Path,default=PROJECT_ROOT);parser.add_argument('--results-root',type=Path);parser.add_argument('--registry',type=Path);parser.add_argument('--output',type=Path);parser.add_argument('--package',action='store_true');parser.add_argument('--allow-incomplete-exit-zero',action='store_true');args=parser.parse_args(argv)
 result=collect(args.project_root,args.results_root,args.registry);destination=args.output or args.project_root/'generation/all_collected';save_inventory(result,destination)
 response={'status':result['status'],'complete_slots':result['complete_slots'],'required_slots':12,'inventory':str(Path(destination)/'collection_inventory.json'),'actual_model_calls':0}
 if args.package:response['package']=package(result,destination)
 print(json.dumps(response,indent=2));return 0 if result['status']=='ALL_COMPLETE'or args.allow_incomplete_exit_zero else 3
if __name__=='__main__':raise SystemExit(main())
