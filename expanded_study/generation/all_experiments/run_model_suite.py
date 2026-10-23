"""Run the registered Q/E1/E2/E3 grids only inside a UoA Slurm allocation.

Default mode is a light plan. This file never authenticates SSH or submits jobs.
Each scope keeps independent prompts, configuration, responses and scoring.
"""
from pathlib import Path
import argparse,datetime,hashlib,importlib.util,json,os,shutil,signal,sqlite3,subprocess,sys

HERE=Path(__file__).resolve().parent
MODELS=('qwen25_3b_gguf','qwen3_8b','llama31_8b')
SCOPES=('Q','E1','E2','E3')
ACTIVE=None
PAUSE=False

def read(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def stable(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def require(ok,message):
 if not ok:raise ValueError(message)
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);temp=p.with_suffix(p.suffix+'.partial')
 with temp.open('w')as f:f.write(json.dumps(x,indent=2,ensure_ascii=False)+'\n');f.flush();os.fsync(f.fileno())
 temp.replace(p)
def load(p,name):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def link_exact(source,target):
 source=Path(source).resolve();target=Path(target);target.parent.mkdir(parents=True,exist_ok=True)
 if target.exists():require(sha(target)==sha(source),'Existing immutable input differs: '+str(target));return
 target.symlink_to(source)
def pause(signum,frame):
 global PAUSE
 PAUSE=True
 if ACTIVE is not None:(ACTIVE/'pause_requested').touch()
 print(stable({'status':'PAUSE_REQUESTED','signal':signum,'active_output':str(ACTIVE)if ACTIVE else None}),flush=True)
def call(argv,log=None):
 if PAUSE:raise InterruptedError('Pause requested before next setup/generation step')
 if log:
  with Path(log).open('a')as f:r=subprocess.run([str(x)for x in argv],stdout=f,stderr=subprocess.STDOUT)
 else:r=subprocess.run([str(x)for x in argv])
 require(r.returncode==0,'Command failed (exit '+str(r.returncode)+'): '+Path(str(argv[0])).name)

def validate_scope(root,registry,scope):
 r=registry['scopes'][scope];inputs=root/r['inputs_file'];protocol=root/r['protocol_file']
 require(sha(inputs)==r['inputs_sha256']and sha(protocol)==r['protocol_sha256'],'Registered input/protocol bytes differ: '+scope)
 p=read(protocol);require(p['inputs_sqlite_sha256']==r['inputs_sha256'],'Scope protocol uses different input')
 return r,inputs,protocol

def native_score(root,out):
 core=load(root/'generation/hf_gpu/run_hf_grid.py','suite_safe_readers');metric=load(root/'code/generation/score_generations.py','suite_frozen_metrics')
 protocol=read(out/'scoring_protocol.json');inputs=out/'native_inputs.sqlite';manifest=read(out/'run_manifest.json')
 require(manifest['status']=='COMPLETE','Unfinished generation cannot be formally scored')
 require(sha(inputs)==protocol['inputs_sqlite_sha256'],'Native input fingerprint differs')
 require(sha(root/'code/generation/score_generations.py')==protocol['scorer_sha256'],'Frozen metric source differs')
 requests,keys=core.scoring_inputs(inputs);responses,snapshot,metadata=core.scoring_responses(out/'generation_responses.sqlite');config=json.loads(metadata['config'])
 require(hashlib.sha256(stable(config).encode()).hexdigest()==metadata['config_sha256']==manifest['config_sha256'],'Response configuration fingerprint mismatch')
 require(config['input_sqlite_sha256']==sha(inputs)and config['scoring_protocol_sha256']==sha(out/'scoring_protocol.json'),'Actual generator used different input/protocol')
 require(set(responses)==keys,'Incomplete or unexpected generated prompt keys')
 dest=out/'scoring';receipt=dest/'scoring_manifest.json'
 if receipt.exists():
  old=read(receipt);require(old['response_snapshot_sha256']==snapshot and old['response_config_sha256']==metadata['config_sha256'],'Existing scoring is stale')
  for name,digest in old['closed_output_hashes'].items():require(sha(dest/name)==digest,'Existing scoring file changed')
  return
 require(not dest.exists()or not any(dest.iterdir()),'Incomplete scoring output exists; retain it and select a fresh score directory')
 result=metric.analyze(requests,responses,dest,False)
 result.update(scoring_version=protocol['scoring_version'],created_utc=now(),native_protocol_sha256=sha(out/'scoring_protocol.json'),metric_source_sha256=sha(root/'code/generation/score_generations.py'),entrypoint_sha256=sha(__file__),input_sqlite_sha256=sha(inputs),response_snapshot_sha256=snapshot,response_config_sha256=metadata['config_sha256'],response_config_json=metadata['config'],closed_output_hashes={p.name:sha(p)for p in sorted(dest.iterdir())if p.is_file()},execution_scope='Registered native Q4 scope; fresh actual responses, no inherited answer reuse; frozen metric functions with explicitly declared scope protocol.')
 metric.write_json(receipt,result)

def setup_native(root,runtime):
 require((3,11)<=sys.version_info[:2]<(3,13),'Use Python 3.11 or 3.12, selected through GROUP9_PYTHON if needed')
 env=runtime/'native_env';py=env/'bin/python'
 if not py.exists():call([sys.executable,'-m','venv',env])
 call([py,'-m','pip','install','numpy==2.3.5'])
 build=runtime/'native_cuda';models=runtime/'qwen25_3b_gguf'
 call([py,root/'generation/runtime/build_native_server.py','--cuda','--cuda-architectures','80;90','--workdir',build,'--jobs','2'])
 call([py,root/'generation/runtime/download_model.py','--model-dir',models])
 return py,build,models

def native_run(a,entry,inputs,source_protocol,out,runtime,binding):
 require(not any(x in str(out)for x in '#?'),'Native llama.cpp branch currently requires paths without # or ?')
 gpu=load(HERE/'launch_native_gpu.py','suite_gpu_device').get_gpu_identity()
 binding={**binding,'actual_gpu_evidence':gpu}
 py,build,models=setup_native(a.project_root,runtime)
 layout=runtime/'native_layouts'/binding['model_key']/binding['scope'];folder=layout/'generation/input'
 link_exact(inputs,out/'native_inputs.sqlite');link_exact(inputs,folder/'generation_inputs.sqlite')
 for field,name in [('tokens_file','token_counts.sqlite'),('token_receipt_file','token_counts.json')]:
  require(field in entry,'Missing actual pinned GGUF token preflight: '+field)
  source=a.project_root/entry[field];require(sha(source)==entry[field.replace('_file','_sha256')],'Token preflight bytes differ')
  link_exact(source,folder/name)
 protocol={**read(source_protocol),'native_suite_binding':binding,'runtime_scope_note':'New registered per-scope Q4 run. Original source protocol remains unchanged.'}
 p=out/'scoring_protocol.json'
 if p.exists():require(read(p)==protocol,'Changed native runtime scope protocol')
 else:save(p,protocol)
 link_exact(p,layout/'generation/scoring_protocol_frozen.json')
 save(out/'input_manifest.json',{'status':'REGISTERED_NATIVE_INPUTS_NO_GENERATION_YET','source_inputs_sha256':sha(inputs),'native_inputs_sha256':sha(inputs),'native_unique_prompts':entry['source_unique_prompts'],'requested_rows':entry['requested_rows'],'suite_binding':binding})
 call([py,HERE/'launch_native_gpu.py','--root',layout,'--project-root',a.project_root,'--server',build/'build/bin/llama-server','--model',models/'qwen2.5-3b-instruct-q4_k_m.gguf','--build-manifest',build/'build_receipt.json','--batch-size',str(a.batch_size),'--threads',str(a.threads),'--gpu-layers','99','--output',out],out/'job_console.log')
 return py

def recover_unfinished_preparation(out,resume):
 """Keep interrupted tokenizer preparation; rebuild only before any response DB."""
 target=out/'native_inputs.sqlite';receipt=out/'input_manifest.json'
 artifacts=[p for p in out.glob('native_inputs.sqlite.partial*')if p.is_file()]
 if target.exists()!=receipt.exists():artifacts.extend(p for p in (target,receipt)if p.exists())
 if not artifacts:return
 require(resume,'Interrupted input preparation requires --resume')
 require(not(out/'generation_responses.sqlite').exists(),'Do not rebuild inputs after response storage exists; retain this branch for inspection')
 folder=out/'interrupted_preparation'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');folder.mkdir(parents=True)
 for path in artifacts:path.rename(folder/path.name)
 save(folder/'recovery_receipt.json',{'status':'UNFINISHED_PREPARATION_RETAINED_BEFORE_REBUILD','created_utc':now(),'generation_response_database_existed':False,'files':{p.name:sha(p)for p in folder.iterdir()if p.is_file()}})

def main():
 global ACTIVE
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project-root',type=Path,default=HERE.parents[1]);p.add_argument('--model-key',choices=MODELS,required=True);p.add_argument('--scopes',nargs='+',choices=SCOPES,default=list(SCOPES));p.add_argument('--run',action='store_true');p.add_argument('--plan',action='store_true');p.add_argument('--resume',action='store_true');p.add_argument('--batch-size',type=int,default=8);p.add_argument('--threads',type=int,default=4);a=p.parse_args();a.project_root=a.project_root.resolve()
 registry_path=a.project_root/'generation/all_experiments/experiment_registry.json';registry=read(registry_path)
 require(set(a.scopes)<=set(registry['scopes']),'Requested scope not registered')
 if not a.run:
  print(json.dumps({'status':'PLAN_ONLY_NO_MODELS_NETWORK_OR_SUBMISSION','model':a.model_key,'scopes':[{scope:registry['scopes'][scope]['requested_rows']}for scope in a.scopes],'all_required_scopes':list(SCOPES),'all_models':list(MODELS),'actual_gpu_execution':False},indent=2));return
 visible=os.environ.get('CUDA_VISIBLE_DEVICES','')
 require(os.environ.get('SLURM_JOB_ID')and visible and visible.strip().lower()not in {'-1','none','nodevfiles','void'},'Use a Slurm job with an allocated GPU; never run compute from an SSH shell')
 require(a.batch_size>0 and a.threads>0,'Invalid batch or thread count')
 upi=os.environ.get('USER','');require(upi and '/'not in upi,'Missing cluster user identity')
 data=(Path('/data')/upi).resolve();require(a.project_root.is_relative_to(data),'Store the project and all runtime files under /data/<UPI>/')
 runtime=a.project_root/'runtime_all';runtime.mkdir(exist_ok=True)
 # WAL checkpoints require actual known local storage. Never remove this check
 # to run the same WAL protocol on NFS/Lustre; an approved local /data mount is needed.
 load(a.project_root/'generation/hf_gpu/run_hf_grid.py','suite_fs_guard').local_filesystem(a.project_root/'generation/all_runs')
 for key,folder in [('TMPDIR','tmp'),('HF_HOME','hf_home'),('HF_HUB_CACHE','hf_cache'),('PIP_CACHE_DIR','pip_cache'),('XDG_CACHE_HOME','xdg_cache'),('TORCH_HOME','torch_cache')]:
  path=runtime/folder;path.mkdir(exist_ok=True);os.environ[key]=str(path)
 proxy='http://squid.auckland.ac.nz:3128'
 for key in ['HTTP_PROXY','HTTPS_PROXY','http_proxy','https_proxy']:os.environ.setdefault(key,proxy)
 os.environ['NO_PROXY']='localhost,127.0.0.1,::1';os.environ['no_proxy']=os.environ['NO_PROXY'];os.environ['HF_HUB_DISABLE_XET']='1'
 os.environ['CUDA_VISIBLE_DEVICES']=os.environ['CUDA_VISIBLE_DEVICES'].split(',')[0]
 for sig in [signal.SIGUSR1,signal.SIGTERM,signal.SIGINT]:signal.signal(sig,pause)
 post_sha=sha(HERE/'postanalyse_scope.py')
 require(registry['postanalysis_source_sha256']==post_sha,'Registered auxiliary contrast recipe changed')
 suite_binding={'model_key':a.model_key,'registry_sha256':sha(registry_path),'suite_entrypoint_sha256':sha(__file__),'postanalysis_source_sha256':post_sha,'batch_size':a.batch_size,'threads':a.threads}
 state={'status':'RUNNING','started_utc':now(),'model_key':a.model_key,'required_scopes':a.scopes,'scope_states':{},'suite_binding':suite_binding,'generator_results_inherited':False}
 modelroot=a.project_root/'generation/all_runs'/a.model_key;modelroot.mkdir(parents=True,exist_ok=True)
 save(modelroot/'suite_manifest.json',state)
 exporter=load(HERE/'export_scope_results.py','suite_exporter')
 py=None
 try:
  if a.model_key!='qwen25_3b_gguf':
   env=a.project_root/'runtime_hf_env';os.environ['GROUP9_HF_ENV']=str(env);os.environ['GROUP9_PROJECT_ROOT']=str(a.project_root)
   call(['bash',a.project_root/'generation/hf_gpu/setup_hf_env.sh']);py=env/'bin/python'
  for scope in a.scopes:
   if PAUSE:raise InterruptedError('Paused before next scope')
   entry,inputs,protocol=validate_scope(a.project_root,registry,scope);out=modelroot/scope;out.mkdir(exist_ok=True);ACTIVE=out
   binding={**suite_binding,'scope':scope,'inputs_sha256':entry['inputs_sha256'],'source_protocol_sha256':entry['protocol_sha256']}
   marker=out/'suite_scope_binding.json'
   if marker.exists():require(read(marker)==binding,'Changed suite configuration; use a separate run branch')
   else:save(marker,binding)
   if (out/'generation_responses.sqlite').exists():require(a.resume,'Existing responses require --resume; do not silently repeat or mix runs')
   if (out/'pause_requested').exists():
    require(a.resume,'Paused output requires --resume');(out/'pause_requested').unlink()
   exported=a.project_root/'generation/all_results'/a.model_key/scope
   if a.model_key=='qwen25_3b_gguf':py=native_run(a,entry,inputs,protocol,out,runtime,binding)
   else:
    recover_unfinished_preparation(out,a.resume)
    adapter=a.project_root/'generation/all_experiments/run_hf_scope.py'
    args=[py,adapter,'--scope',scope,'--registry',registry_path,'--model-key',a.model_key,'--output',out,'--cache-dir',runtime/'hf_cache','--batch-size',str(a.batch_size)]
    call(args+['--run'],out/'job_console.log')
   # Preserve generation before potentially long scoring and packaging work.
   first=exporter.export(out,exported);m=read(out/'run_manifest.json')
   if m['status']!='COMPLETE':
    state['scope_states'][scope]={'status':m['status'],'responses':first['actual_unique_responses']};state['status']='INCOMPLETE';break
   if a.model_key=='qwen25_3b_gguf':call([py,HERE/'score_native_scope.py','--project-root',a.project_root,'--output',out],out/'scoring_console.log')
   else:call(args+['--score'],out/'scoring_console.log')
   call([py,HERE/'postanalyse_scope.py','--scope',scope,'--run-dir',out,'--output',out/'postanalysis'],out/'postanalysis_console.log')
   final=exporter.export(out,exported);require(final['full_asr_ready'],'Closed result export failed complete-result verification')
   state['scope_states'][scope]={'status':'COMPLETE','responses':final['actual_unique_responses'],'archive':final['archive']};save(modelroot/'suite_manifest.json',state)
  else:state['status']='COMPLETE'
 except BaseException as error:
  state.update(status='INCOMPLETE_ERROR',error_type=type(error).__name__,error=str(error))
  if ACTIVE and ACTIVE.exists():
   try:exporter.export(ACTIVE,a.project_root/'generation/all_results'/a.model_key/ACTIVE.name)
   except Exception as export_error:state['export_error']=str(export_error)
 finally:
  state['finished_or_paused_utc']=now();save(modelroot/'suite_manifest.json',state)
  print(json.dumps(state,indent=2))
 if state['status']!='COMPLETE':raise SystemExit(3)

if __name__=='__main__':main()
