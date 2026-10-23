"""Checkpoint full frozen prompts through a pinned local llama.cpp server.

Exact full-prompt duplicates share one execution. Distinct prompts never share
answer records. Responses commit transactionally after every fixed batch.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,os,platform,sqlite3,time,urllib.request

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb')as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def stable(obj):return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def atomic(path,obj):
 tmp=path.with_suffix(path.suffix+'.partial')
 with tmp.open('w')as f:f.write(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
 tmp.replace(path)
def post(url,obj,timeout):
 req=urllib.request.Request(url,data=stable(obj).encode(),headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=timeout)as response:return json.load(response)
def ledger_totals(db):
 n,known,unknown,errors=db.execute("SELECT count(*),coalesce(sum(returned_count),0),coalesce(sum(CASE WHEN returned_count IS NULL THEN prompt_count ELSE 0 END),0),coalesce(sum(CASE WHEN status='ERROR_UNKNOWN' THEN 1 ELSE 0 END),0) FROM attempts").fetchone()
 return {'cumulative_batch_attempts':n,'cumulative_known_returned_responses':known,'cumulative_unknown_outcome_requested_prompts':unknown,'cumulative_http_errors':errors,'generator_inference_executed':True if known else None if unknown else False,'attempt_ledger_scope':'Every HTTP attempt is durable before dispatch; unknown outcomes are disclosed separately from unique committed prompts, never counted as zero inference.'}

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--input',type=Path,required=True);p.add_argument('--tokens',type=Path,required=True)
 p.add_argument('--output',type=Path,required=True);p.add_argument('--model-manifest',type=Path,required=True)
 p.add_argument('--server-build',type=Path,required=True);p.add_argument('--server-launch',type=Path,required=True);p.add_argument('--protocol',type=Path,required=True)
 p.add_argument('--server-url',default='http://127.0.0.1:18080');p.add_argument('--batch-size',type=int,default=8)
 p.add_argument('--timeout',type=float,default=1800);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
 inputs=sqlite3.connect('file:'+str(a.input.resolve())+'?mode=ro',uri=True)
 expected=inputs.execute('SELECT count(*) FROM prompts').fetchone()[0]
 requested=inputs.execute('SELECT count(*) FROM requests').fetchone()[0]
 token_receipt=json.loads(a.tokens.with_suffix('.json').read_text())
 assert token_receipt['status']=='PASS_ALL_FULL_PROMPTS_FIT' and token_receipt['input_sqlite_sha256']==sha(a.input)
 assert token_receipt['token_file_sha256']==sha(a.tokens)
 with urllib.request.urlopen(a.server_url+'/props',timeout=30)as response:props=json.load(response)
 parameters={'n_predict':48,'temperature':0.0,'top_k':0,'top_p':1.0,'min_p':0.0,'repeat_penalty':1.0,'seed':12,'stop':['<|im_end|>','<|endoftext|>'],'stream':False,'cache_prompt':False,'return_tokens':True}
 props.pop('is_sleeping',None)
 props.pop('model_path',None)
 props.pop('media_marker',None)  # Runtime-random multimodal marker; this is a text-only suite.
 build=json.loads(a.server_build.read_text())
 build_identity={'vendor_llama_cpp_commit':build.get('vendor_llama_cpp_commit',build.get('source_revision')),'archive_sha256':build.get('archive_sha256',build.get('source_archive_sha256')),'backend':build.get('mode','CPU'),'cuda_architectures':build.get('cuda_architectures'),'artifacts':build['artifacts']}
 launch=json.loads(a.server_launch.read_text())
 launch_argv=list(launch['server_argv'])
 launch_argv[0]=Path(launch_argv[0]).name
 if '-m'in launch_argv:launch_argv[launch_argv.index('-m')+1]=Path(launch_argv[launch_argv.index('-m')+1]).name
 launch_identity={'server_argv':launch_argv,'launcher_sha256':launch['launcher_sha256'],'native_server_sha256':launch['native_server_sha256'],'transport':launch['transport']}
 model_manifest=json.loads(a.model_manifest.read_text())
 assert token_receipt['model_sha256']==next(x['sha256'] for x in model_manifest['files'] if x['file'].endswith('.gguf')),'Model token preflight identity differs'
 config={'input_sqlite_sha256':sha(a.input),'token_preflight_sha256':sha(a.tokens.with_suffix('.json')),'model_manifest':model_manifest,'server_build_identity':build_identity,'server_launch_identity':launch_identity,'scoring_protocol_sha256':sha(a.protocol),'runner_sha256':sha(__file__),'generation_parameters':parameters,'batch_size':a.batch_size,'scheduling':'Question-sharded fixed order: lexical question_id, then minimum request_order; incomplete full prompts only on guarded resume. Native batch-dependent floating point behavior remains possible.','server_props':props,'python_version':platform.python_version(),'platform_system':platform.system(),'machine':platform.machine(),'expected_unique_prompts':expected,'requested_rows':requested}
 config_hash=hashlib.sha256(stable(config).encode()).hexdigest()
 database=a.output/'generation_responses.sqlite';db=sqlite3.connect(database)
 db.execute('PRAGMA journal_mode=WAL');db.execute('PRAGMA synchronous=FULL')
 db.execute('CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL)')
 db.execute('CREATE TABLE IF NOT EXISTS attempts(attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,batch_id INTEGER NOT NULL,prompt_count INTEGER NOT NULL,returned_count INTEGER,prompt_keys_json TEXT NOT NULL,started_utc TEXT NOT NULL,finished_utc TEXT,status TEXT NOT NULL,raw_json TEXT,error TEXT)')
 db.execute('CREATE TABLE IF NOT EXISTS responses(prompt_sha256 TEXT PRIMARY KEY,response TEXT NOT NULL,finish_reason TEXT NOT NULL,prompt_tokens INTEGER,completion_tokens INTEGER,elapsed_seconds REAL NOT NULL,raw_json TEXT NOT NULL,executed_utc TEXT NOT NULL,batch_id INTEGER NOT NULL,config_sha256 TEXT NOT NULL)')
 prior=db.execute('SELECT value FROM metadata WHERE key="config_sha256"').fetchone()
 if prior:assert prior[0]==config_hash,'Refusing resume under changed execution configuration'
 else:db.executemany('INSERT INTO metadata VALUES(?,?)',[('config_sha256',config_hash),('config',stable(config))]);db.commit()
 completed={r[0]for r in db.execute('SELECT prompt_sha256 FROM responses')}
 input_keys={r[0]for r in inputs.execute('SELECT prompt_sha256 FROM prompts')}
 assert completed<=input_keys
 tokens=sqlite3.connect('file:'+str(a.tokens.resolve())+'?mode=ro',uri=True)
 token_map=dict(tokens.execute('SELECT prompt_sha256,prompt_tokens FROM tokens'))
 start=time.monotonic();initial=len(completed);next_batch=db.execute('SELECT coalesce(max(batch_id),-1)+1 FROM responses').fetchone()[0]
 manifest={'status':'RUNNING','started_or_resumed_utc':now(),'config_sha256':config_hash,'config':config,'preexisting_exact_responses':initial,'completed_unique_prompts':initial,'expected_unique_prompts':expected,'requested_rows':requested,'new_successful_responses':0,'batch_http_attempts_this_session':0,'errors_this_session':0,'elapsed_this_session_seconds':0,'generator_inference_executed_this_session':False,'target_tool_calls':0,'runtime_observations_this_session':{'platform':platform.platform(),'server_build_receipt':build}}
 manifest.update(ledger_totals(db))
 atomic(a.output/'run_manifest.json',manifest)
 cursor=inputs.execute('SELECT p.prompt_sha256,p.chat_prompt FROM prompts p JOIN (SELECT prompt_sha256,min(question_id) AS q,min(request_order) AS n FROM requests GROUP BY prompt_sha256) r ON r.prompt_sha256=p.prompt_sha256 ORDER BY r.q,r.n')
 batch=[]
 def execute_batch(items,batch_id):
  for key,chat in items:
   assert hashlib.sha256(chat.encode()).hexdigest()==key
   assert token_map[key]+parameters['n_predict']<=token_receipt['context_tokens']
  body={**parameters,'prompt':[chat for _,chat in items]}
  attempt=db.execute('INSERT INTO attempts(batch_id,prompt_count,prompt_keys_json,started_utc,status) VALUES(?,?,?,?,?)',(batch_id,len(items),stable([key for key,_ in items]),now(),'SENT')).lastrowid;db.commit()
  manifest['batch_http_attempts_this_session']+=1;atomic(a.output/'run_manifest.json',manifest)
  t=time.monotonic()
  try:
   result=post(a.server_url+'/completion',body,a.timeout)
  except BaseException as error:
   db.execute('UPDATE attempts SET status=?,finished_utc=?,error=? WHERE attempt_id=?',('ERROR_UNKNOWN',now(),repr(error),attempt));db.commit();raise
  elapsed=time.monotonic()-t
  db.execute('UPDATE attempts SET status=?,finished_utc=?,returned_count=?,raw_json=? WHERE attempt_id=?',('RESPONSE_RECEIVED',now(),len(result)if isinstance(result,list)else 1,stable(result),attempt));db.commit()
  if isinstance(result,dict)and len(items)==1:result=[result]
  assert isinstance(result,list)and len(result)==len(items),'Incomplete response batch'
  for index,(item,raw)in enumerate(zip(items,result,strict=True)):
   key,chat=item
   assert isinstance(raw,dict)and isinstance(raw.get('content'),str),'Missing generated text'
   assert raw.get('prompt')==chat,'Returned full prompt differs from submitted prompt'
   assert not raw.get('truncated',False),'Generator truncated a prompt'
   if 'index'in raw:assert raw['index']==index,'Response order mismatch'
   finish='length'if raw.get('stopped_limit')or raw.get('stop_type')=='limit'else 'stop'
   timing=raw.get('timings',{})
   actual_prompt_tokens=raw.get('tokens_evaluated',timing.get('prompt_n'))
   completion_tokens=raw.get('tokens_predicted',timing.get('predicted_n'))
   assert isinstance(actual_prompt_tokens,int)and abs(actual_prompt_tokens-token_map[key])<=1,'Server/preflight tokenizer disagreement'
   assert isinstance(completion_tokens,int)and 0<=completion_tokens<=parameters['n_predict'],'Invalid completion token accounting'
   db.execute('INSERT INTO responses VALUES(?,?,?,?,?,?,?,?,?,?)',(key,raw['content'].strip(),finish,actual_prompt_tokens,completion_tokens,elapsed/len(items),stable(raw),now(),batch_id,config_hash))
  db.execute('UPDATE attempts SET status=? WHERE attempt_id=?',('COMMITTED',attempt));db.commit();completed.update(key for key,_ in items)
  manifest.update(ledger_totals(db))
  manifest.update(completed_unique_prompts=len(completed),new_successful_responses=len(completed)-initial,elapsed_this_session_seconds=time.monotonic()-start,generator_inference_executed_this_session=True,last_batch=batch_id,last_batch_seconds=elapsed,last_checkpoint_utc=now())
  atomic(a.output/'run_manifest.json',manifest)
  print(stable({'completed_unique_prompts':len(completed),'expected':expected,'last_batch_seconds':round(elapsed,3),'elapsed_session_seconds':round(time.monotonic()-start,3),'new_responses':len(completed)-initial}),flush=True)
 try:
  for key,chat in cursor:
   if (a.output/'pause_requested').exists():
    db.execute('PRAGMA wal_checkpoint(TRUNCATE)');db.close()
    manifest.update(status='PAUSED_BY_CONTROL_FILE',stopped_utc=now(),completed_unique_prompts=len(completed),elapsed_this_session_seconds=time.monotonic()-start)
    atomic(a.output/'run_manifest.json',manifest);print(stable({'paused':True,'completed_unique_prompts':len(completed)}),flush=True);return
   if key in completed:continue
   batch.append((key,chat))
   if len(batch)==a.batch_size:execute_batch(batch,next_batch);next_batch+=1;batch=[]
  if batch:execute_batch(batch,next_batch)
  actual={r[0]for r in db.execute('SELECT prompt_sha256 FROM responses')}
  assert actual==input_keys and len(actual)==expected
  assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
  manifest.update(ledger_totals(db))
  db.execute('PRAGMA wal_checkpoint(TRUNCATE)');db.close()
  manifest.update(status='COMPLETE',completed_utc=now(),response_database_sha256=sha(database),completed_unique_prompts=expected,elapsed_this_session_seconds=time.monotonic()-start)
  atomic(a.output/'run_manifest.json',manifest);print(stable({'complete':True,'unique_prompts':expected,'requested_rows':requested}),flush=True)
 except BaseException as error:
  db.rollback();manifest.update(ledger_totals(db));manifest['errors_this_session']+=1;db.execute('PRAGMA wal_checkpoint(TRUNCATE)');db.close()
  manifest.update(status='INCOMPLETE_ERROR',error_type=type(error).__name__,error=str(error),completed_unique_prompts=len(completed),elapsed_this_session_seconds=time.monotonic()-start,stopped_utc=now())
  atomic(a.output/'run_manifest.json',manifest);raise
if __name__=='__main__':main()
