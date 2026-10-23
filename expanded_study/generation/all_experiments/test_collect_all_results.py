"""Offline missing/corrupt/full twelve-slot fixtures. No actual GPU or model."""
from pathlib import Path
import contextlib,copy,hashlib,importlib.util,io,json,shutil,sqlite3,tempfile
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[1]
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
collector=load(HERE/'collect_all_results.py','collector_under_test');helper=load(HERE/'test_hf_scope.py','scope_mock_helper')
def save(path,value):Path(path).parent.mkdir(parents=True,exist_ok=True);Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def read(path):return json.loads(Path(path).read_text())
def sha(path):return collector.Digests()(path)
def fixture_root(folder):
 f=helper.Fixture(folder);root=f.root
 for name in ['run_hf_scope.py','run_model_suite.py','postanalyse_scope.py','launch_native_gpu.py','collect_all_results.py','export_scope_results.py']:
  shutil.copy2(HERE/name,root/'generation/all_experiments'/name)
 for name in ['export_hf_results.py']:shutil.copy2(PROJECT/'generation/hf_gpu'/name,root/'generation/hf_gpu'/name)
 (root/'generation/runtime').mkdir();(root/'code/generation').mkdir(exist_ok=True)
 for name in ['model_manifest.json','source_identity.json']:shutil.copy2(PROJECT/'generation/runtime'/name,root/'generation/runtime'/name)
 shutil.copy2(PROJECT/'code/generation/run_native_generation.py',root/'code/generation/run_native_generation.py')
 f.registry['required_models']=list(collector.MODELS);f.registry['metric_source_sha256']=sha(root/'code/generation/score_generations.py');f.registry['postanalysis_source_sha256']=sha(root/'generation/all_experiments/postanalyse_scope.py')
 for scope,entry in f.registry['scopes'].items():
  entry['required_models']=list(collector.MODELS);source=root/entry['inputs_file'];db=sqlite3.connect(source);keys=[row[0]for row in db.execute('SELECT prompt_sha256 FROM prompts')];db.close();tokens=source.with_name('token_counts.sqlite');db=sqlite3.connect(tokens);db.execute('CREATE TABLE tokens(prompt_sha256 TEXT PRIMARY KEY,prompt_tokens INTEGER NOT NULL)');db.executemany('INSERT INTO tokens VALUES(?,?)',[(key,100)for key in keys]);db.commit();db.close();receipt=tokens.with_suffix('.json');save(receipt,{'status':'PASS_ALL_FULL_PROMPTS_FIT','fixture_only':'MOCK_TOKEN_COUNTS_NOT_GGUF_EXECUTION','input_sqlite_sha256':entry['inputs_sha256'],'token_file_sha256':sha(tokens),'model_sha256':'626b4a6678b86442240e33df819e00132d3ba7dddfe1cdc4fbb18e0a9615c62d'})
  entry.update(tokens_file=str(tokens.relative_to(root)),tokens_sha256=sha(tokens),token_receipt_file=str(receipt.relative_to(root)),token_receipt_sha256=sha(receipt))
 save(f.registry_path,f.registry);return f

def marker(f,model,scope):
 e=f.registry['scopes'][scope]
 return {'model_key':model,'scope':scope,'registry_sha256':sha(f.registry_path),'suite_entrypoint_sha256':sha(f.root/'generation/all_experiments/run_model_suite.py'),'postanalysis_source_sha256':f.registry['postanalysis_source_sha256'],'batch_size':2,'threads':4,'inputs_sha256':e['inputs_sha256'],'source_protocol_sha256':e['protocol_sha256']}
def post(f,out,model,scope):
 score=read(out/'scoring/scoring_manifest.json');p=out/'postanalysis';p.mkdir();save(p/'mock_closed_pointer.json',{'fixture_only':True,'scoring_manifest_sha256':sha(out/'scoring/scoring_manifest.json')})
 binding={'scope':scope,'model_key':model,'source_scoring_manifest_sha256':sha(out/'scoring/scoring_manifest.json'),'input_sqlite_sha256':sha(out/'native_inputs.sqlite'),'native_protocol_sha256':sha(out/'scoring_protocol.json'),'response_config_sha256':score['response_config_sha256'],'response_snapshot_sha256':score['response_snapshot_sha256'],'metric_source_sha256':f.registry['metric_source_sha256'],'request_scores_sha256':sha(out/'scoring/request_scores.jsonl'),'postanalysis_entrypoint_sha256':f.registry['postanalysis_source_sha256']}
 save(p/'postanalysis_manifest.json',{'status':'COMPLETE','scope':scope,'model_key':model,'fixture_only':'MOCK_RECEIPT_NOT_AN_ACTUAL_POSTANALYSIS_RUN','binding':binding,'requested_rows':score['requested_rows'],'actual_unique_response_records':score['actual_unique_response_records'],'contrast_rows':0,'missing_pairs':0,'model_calls':0,'closed_output_hashes':{'mock_closed_pointer.json':sha(p/'mock_closed_pointer.json')}})

def native(f,scope,out):
 out.mkdir(parents=True);entry=f.registry['scopes'][scope];source=f.root/entry['inputs_file'];shutil.copy2(source,out/'native_inputs.sqlite');m=marker(f,'qwen25_3b_gguf',scope);save(out/'suite_scope_binding.json',m)
 gpu=load(f.root/'generation/all_experiments/launch_native_gpu.py','mock_cuda_proof');identity={'status':'ACTUAL_CUDA_DEVICE_VERIFIED','gpu_name':'MOCK NVIDIA A100','memory_total_mib':80000,'compute_capability':'8.0','driver_version':'MOCK_DRIVER'};fixed=gpu.binding(identity)
 protocol={**read(f.root/entry['protocol_file']),'native_suite_binding':{**m,'actual_gpu_evidence':identity}};save(out/'scoring_protocol.json',protocol)
 save(out/'input_manifest.json',{'native_inputs_sha256':sha(out/'native_inputs.sqlite'),'native_unique_prompts':entry['source_unique_prompts'],'requested_rows':entry['requested_rows'],'source_inputs_sha256':entry['inputs_sha256']})
 launch={'server_argv':['/MOCK/llama-server','-m','/MOCK/qwen2.5-3b-instruct-q4_k_m.gguf','-ngl','99'],'launcher_sha256':sha(f.root/'generation/all_experiments/launch_native_gpu.py'),'native_server_sha256':'b'*64,'transport':'MOCK loopback; actual_cuda_binding_sha256='+fixed['sha256'],'actual_gpu_identity':identity,'native_gpu_verification':gpu.VERIFICATION_CONFIG,'actual_cuda_binding_sha256':fixed['sha256']};save(out/'server_launch.json',launch)
 config={'input_sqlite_sha256':sha(out/'native_inputs.sqlite'),'scoring_protocol_sha256':sha(out/'scoring_protocol.json'),'model_manifest':read(f.root/'generation/runtime/model_manifest.json'),'runner_sha256':sha(f.root/'code/generation/run_native_generation.py'),'token_preflight_sha256':entry['token_receipt_sha256'],'generation_parameters':{'n_predict':48,'temperature':0.0,'top_k':0,'top_p':1.0,'min_p':0.0,'repeat_penalty':1.0,'seed':12,'stop':['<|im_end|>','<|endoftext|>'],'stream':False,'cache_prompt':False,'return_tokens':True},'server_launch_identity':{k:launch[k]for k in ['server_argv','launcher_sha256','native_server_sha256','transport']},'server_build_identity':{'backend':'CUDA','vendor_llama_cpp_commit':read(f.root/'generation/runtime/source_identity.json')['vendor_llama_cpp_commit'],'archive_sha256':read(f.root/'generation/runtime/source_identity.json')['archive_sha256'],'artifacts':[{'path':'build/bin/llama-server','sha256':'b'*64}]},'fixture_only':'MOCK_NO_GPU_OR_MODEL'}
 config['server_launch_identity']['server_argv']=['llama-server','-m','qwen2.5-3b-instruct-q4_k_m.gguf','-ngl','99'];fingerprint=collector.textsha(collector.stable(config));src=sqlite3.connect(source);items=src.execute('SELECT prompt_sha256,chat_prompt,prompt FROM prompts ORDER BY first_request_order').fetchall();src.close()
 raw=[{'prompt':chat,'content':'2003'if'CLEAN'in user else'2010','tokens_evaluated':100,'tokens_predicted':2,'truncated':False,'stop_type':'eos','index':i}for i,(key,chat,user)in enumerate(items)]
 db=sqlite3.connect(out/'generation_responses.sqlite');db.execute('CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT)');db.executemany('INSERT INTO metadata VALUES(?,?)',[('config',collector.stable(config)),('config_sha256',fingerprint)])
 db.execute('CREATE TABLE attempts(attempt_id INTEGER PRIMARY KEY,batch_id INTEGER,prompt_count INTEGER,returned_count INTEGER,prompt_keys_json TEXT,started_utc TEXT,finished_utc TEXT,status TEXT,raw_json TEXT,error TEXT)');db.execute('INSERT INTO attempts VALUES(?,?,?,?,?,?,?,?,?,?)',(1,0,len(items),len(items),collector.stable([item[0]for item in items]),'2026-10-22T00:00:01+00:00','2026-10-22T00:00:20+00:00','COMMITTED',collector.stable(raw),None))
 db.execute('CREATE TABLE responses(prompt_sha256 TEXT PRIMARY KEY,response TEXT,finish_reason TEXT,prompt_tokens INTEGER,completion_tokens INTEGER,elapsed_seconds REAL,raw_json TEXT,executed_utc TEXT,batch_id INTEGER,config_sha256 TEXT)')
 for item,result in zip(items,raw):db.execute('INSERT INTO responses VALUES(?,?,?,?,?,?,?,?,?,?)',(item[0],result['content'],'stop',100,2,1.,collector.stable(result),'2026-10-22T00:00:10+00:00',0,fingerprint))
 db.commit();db.close();save(out/'run_manifest.json',{'status':'COMPLETE','config':config,'config_sha256':fingerprint,'completed_unique_prompts':len(items),'requested_rows':entry['requested_rows'],'generator_inference_executed':True,'cumulative_batch_attempts':1,'cumulative_known_returned_responses':len(items),'cumulative_unknown_outcome_requested_prompts':0})
 text='ggml_cuda_init: found 1 CUDA devices\nDevice 0: '+identity['gpu_name']+', compute capability 8.0\nusing device CUDA0 ('+identity['gpu_name']+')\noffloaded 29/29 layers to GPU\n';data=text.encode();proof,excerpt=gpu.verify_new_log(data,identity);sessiondir=out/'native_gpu_sessions/MOCK_SESSION_1';sessiondir.mkdir(parents=True);(out/'native_server.log').write_bytes(data);(sessiondir/'startup_log.txt').write_bytes(data);(sessiondir/'cuda_excerpt.txt').write_text(excerpt)
 session={**proof,'session_id':'MOCK_SESSION_1','slurm_job_id':'MOCK_SLURM_JOB','log_file':'native_server.log','log_start_offset':0,'log_end_offset':len(data),'startup_log_file':'native_gpu_sessions/MOCK_SESSION_1/startup_log.txt','startup_log_sha256':sha(sessiondir/'startup_log.txt'),'excerpt_file':'native_gpu_sessions/MOCK_SESSION_1/cuda_excerpt.txt','excerpt_sha256':sha(sessiondir/'cuda_excerpt.txt'),'actual_cuda_binding_sha256':fixed['sha256'],'generation_started':True,'generator_returncode':0,'verified_utc':'2026-10-22T00:00:00+00:00','generator_finished_utc':'2026-10-22T00:01:00+00:00'};save(sessiondir/'session.json',session)
 save(out/'actual_gpu_evidence.json',{'schema_version':gpu.SCHEMA,'identity':identity,'verification_config':gpu.VERIFICATION_CONFIG,'observations':[{'fixture_only':True}]});save(out/'native_gpu_execution.json',{'schema_version':gpu.SCHEMA,'status':'ACTUAL_CUDA_FULL_OFFLOAD_VERIFIED','identity':identity,'verification_config':gpu.VERIFICATION_CONFIG,'sessions':[session]})
 suite=load(f.root/'generation/all_experiments/run_model_suite.py','mock_suite_metrics');suite.native_score(f.root,out);post(f,out,'qwen25_3b_gguf',scope)

def refresh_export(directory):
 files=[{'path':p.relative_to(directory).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)}for p in sorted(directory.rglob('*'))if p.is_file()and p.name!='export_files.json'];save(directory/'export_files.json',files)

def run_checks():
 checks=[]
 with tempfile.TemporaryDirectory(prefix='collector-MOCK-only-')as folder:
  f=fixture_root(folder);results=f.root/'generation/all_results';missing=collector.collect(f.root,allow_mock=True);assert missing['status']=='MOCK_INCOMPLETE'and missing['complete_slots']==0 and len(missing['slots'])==12
  checks.append('no_result_slots_produces_explicit_incomplete_twelve_slot_inventory')
  exporter=load(f.root/'generation/hf_gpu/export_hf_results.py','mock_base_export');runs=f.root/'generation/all_runs'
  for model in collector.MODELS:
   for scope in collector.SCOPES:
    out=runs/model/scope
    if model=='qwen25_3b_gguf':native(f,scope,out)
    else:
     context=f.context(scope,model=model,output=out);backend=f.backend(context);context.run(backend);context.score();save(out/'suite_scope_binding.json',marker(f,model,scope));post(f,out,model,scope)
    exported=exporter.export(out,results/model/scope);assert exported['full_asr_ready']is True
  full=collector.collect(f.root,allow_mock=True)
  assert full['status']=='MOCK_ALL_COMPLETE',[(slot['model_key'],slot['scope'],slot['issues'])for slot in full['slots']if slot['status']!='COMPLETE']
  assert full['complete_slots']==12 and full['full_project_generation_and_analysis_ready']is False and full['validation_mode']=='MOCK_FIXTURE_VALIDATION_NO_GPU_EXECUTION'
  checks.append('all_twelve_mock_slots_cover_actual_fixture_keys_raw_attempts_scoring_postanalysis_and_device_records')
  inspector=collector.Inspector(f.root,allow_mock=True);hfslot=results/'qwen3_8b/E1';nativefile=hfslot/'native_inputs.sqlite';saved_native=nativefile.read_bytes();protocol=read(hfslot/'scoring_protocol.json');input_receipt=read(hfslot/'input_manifest.json')
  db=sqlite3.connect(nativefile);db.execute('UPDATE requests SET request_order=request_order+100000');db.commit();db.close();changed_protocol={**protocol,'inputs_sqlite_sha256':sha(nativefile)};changed_receipt={**input_receipt,'native_inputs_sha256':sha(nativefile)}
  try:inspector.validate_inputs(hfslot,'qwen3_8b','E1',changed_protocol,changed_receipt)
  except ValueError as error:assert'request order keys'in str(error)
  else:raise AssertionError('Zero metadata join was accepted')
  nativefile.write_bytes(saved_native);db=sqlite3.connect(nativefile);key=db.execute('SELECT min(source_prompt_sha256) FROM source_prompt_map').fetchone()[0];db.execute('UPDATE source_prompt_map SET source_prompt_sha256=? WHERE source_prompt_sha256=?',('f'*64,key));db.commit();db.close();changed_protocol={**protocol,'inputs_sqlite_sha256':sha(nativefile)};changed_receipt={**input_receipt,'native_inputs_sha256':sha(nativefile)}
  try:inspector.validate_inputs(hfslot,'qwen3_8b','E1',changed_protocol,changed_receipt)
  except ValueError as error:assert'source keys'in str(error)
  else:raise AssertionError('Orphan source prompt map was accepted')
  nativefile.write_bytes(saved_native)
  checks.append('equal_row_counts_cannot_hide_missing_source_request_or_prompt_map_keys')
  nativeslot=results/'qwen25_3b_gguf/Q';responsefile=nativeslot/'generation_responses.sqlite';saved_response=responsefile.read_bytes();db=sqlite3.connect(responsefile);db.execute("UPDATE responses SET finish_reason='length'");db.commit();db.close();native_inputs=inspector.validate_inputs(nativeslot,'qwen25_3b_gguf','Q',read(nativeslot/'scoring_protocol.json'),read(nativeslot/'input_manifest.json'));token_db=sqlite3.connect(f.root/f.registry['scopes']['Q']['tokens_file']);native_inputs['gguf_token_map']=dict(token_db.execute('SELECT * FROM tokens'));token_db.close()
  try:inspector.actual_responses(nativeslot,'qwen25_3b_gguf',native_inputs,read(nativeslot/'run_manifest.json')['config_sha256'])
  except ValueError as error:assert'finish reason'in str(error)
  else:raise AssertionError('Raw/native finish mismatch was accepted')
  responsefile.write_bytes(saved_response)
  checks.append('native_finish_reason_must_match_raw_generator_termination')
  production=collector.collect(f.root);assert production['status']=='INCOMPLETE'and production['complete_slots']<12
  checks.append('mock_native_hf_backends_cannot_make_production_all_complete')
  slot=results/'qwen3_8b/E1';scores=slot/'scoring/request_scores.jsonl';original=scores.read_bytes();scores.write_bytes(original+b'CORRUPT\n');corrupt=collector.collect(f.root,allow_mock=True);assert corrupt['status']=='MOCK_INCOMPLETE'and next(s for s in corrupt['slots']if s['directory']==str(slot))['status']=='INVALID_CLOSED_EXPORT';scores.write_bytes(original)
  checks.append('corrupt_closed_scoring_file_is_rejected')
  # Even if an attacker refreshes superficial inventories, request/source and
  # frozen formula recomputation prevent invented actual results.
  rows=[json.loads(line)for line in scores.read_text().splitlines()];rows[0]['metrics']['reference_exact']=not rows[0]['metrics']['reference_exact'];scores.write_text(''.join(collector.stable(row)+'\n'for row in rows));sm=slot/'scoring/scoring_manifest.json';saved_sm=sm.read_bytes();value=read(sm);value['closed_output_hashes']['request_scores.jsonl']=sha(scores);save(sm,value);postmanifest=slot/'postanalysis/postanalysis_manifest.json';saved_pm=postmanifest.read_bytes();value=read(postmanifest);value['binding']['source_scoring_manifest_sha256']=sha(sm);value['binding']['request_scores_sha256']=sha(scores);save(postmanifest,value);refresh_export(slot);changed=collector.collect(f.root,allow_mock=True);bad=next(s for s in changed['slots']if s['directory']==str(slot));assert bad['status']=='INCOMPLETE_OR_INVALID_RESULT'and'actual request metric differs'in bad['issues'][0],bad
  scores.write_bytes(original);sm.write_bytes(saved_sm);postmanifest.write_bytes(saved_pm);refresh_export(slot)
  checks.append('rehashed_fabricated_request_metric_fails_actual_response_metric_recomputation')
  postpath=slot/'postanalysis';saved_post=postpath.with_name('postanalysis_saved');postpath.rename(saved_post);refresh_export(slot);absent=collector.collect(f.root,allow_mock=True);assert absent['status']=='MOCK_INCOMPLETE';saved_post.rename(postpath);refresh_export(slot)
  observed=next(s for s in absent['slots']if s['directory']==str(slot));assert observed['observed_unique_response_records']>0 and observed['observed_missing_native_unique_prompts']==0 and observed['response_identity_and_metrics_complete']is False
  checks.append('missing_postanalysis_prevents_complete_while_inventory_retains_actual_saved_record_counts')
  # Thin exporter stage callback is tested directly, without GPU or copying any
  # real input database: no postanalysis must create an INCOMPLETE filename.
  wrapper=load(f.root/'generation/all_experiments/export_scope_results.py','strong_wrapper_test');source=runs/'qwen3_8b/E1';shutil.rmtree(source/'postanalysis');checkpoint=wrapper.export(source,f.root/'strong_exports/qwen3_8b/E1',f.root);assert checkpoint['full_asr_ready']is False and'INCOMPLETE_Checkpoint'in checkpoint['archive']
  checks.append('strong_export_callback_never_names_a_missing_postanalysis_scope_complete')
  dest=f.root/'collected_mock';collector.save_inventory(full,dest);receipt=collector.package(full,dest);assert'INCOMPLETE_Checkpoints'in receipt['archive_file']and receipt['full_project_generation_and_analysis_ready']is False
  checks.append('mock_validation_inventory_and_package_keep_incomplete_names_and_no_gpu_claim')
 return {'status':'PASS','tests':checks,'fixture_slots':12,'real_model_loads':0,'real_gpu_inference':0,'network_calls':0,'fixture_result_status':'MOCK_ALL_COMPLETE_IS_NOT_ALL_COMPLETE','collector_sha256':sha(HERE/'collect_all_results.py'),'wrapper_sha256':sha(HERE/'export_scope_results.py'),'temporary_mock_fixtures_removed':True}

if __name__=='__main__':
 with contextlib.redirect_stdout(io.StringIO()):result=run_checks()
 print(json.dumps(result,indent=2))
