"""Native BF16 HF evaluation. --plan and --self-test never load/download models.

Run each model in its own node-local output directory. Existing HF permissions
are used for gated weights; credentials are never requested, stored or printed.
The original 3B inputs/scorer/protocol remain unchanged. Native chat rendering
gets a new input database and a separately bound protocol using frozen metrics.
"""
from __future__ import annotations
from pathlib import Path
import argparse,collections,contextlib,datetime,hashlib,importlib.util,importlib.metadata,io,json,os,platform,re,sqlite3,sys,tempfile,time

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
SYSTEM='You are a helpful assistant.'
DATE='22 Oct 2026'
POLICIES=('none','LR__new_normal_1pct','LinearSVC__new_normal_1pct')
MAX_NEW=48
CONTEXT=4096

def stable(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb')as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
def textsha(x):return hashlib.sha256(x.encode('utf-8')).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def require(ok,message):
 if not ok:raise ValueError(message)
def atomic(path,obj):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix(path.suffix+'.partial')
 with tmp.open('w',encoding='utf-8')as f:f.write(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
 tmp.replace(path)
def readonly(path):return sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True)
def load_module(path,name):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def local_filesystem(path):
 mountinfo=Path('/proc/self/mountinfo');require(mountinfo.exists(),'Cannot establish node-local filesystem; Linux mountinfo is required')
 chosen=None;resolved=Path(path).resolve()
 for line in mountinfo.read_text().splitlines():
  left,right=line.split(' - ',1);point=left.split()[4]
  point=re.sub(r'\\([0-7]{3})',lambda m:chr(int(m[1],8)),point);mount=Path(point)
  if resolved==mount or mount in resolved.parents:
   if chosen is None or len(point)>chosen[0]:chosen=(len(point),right.split()[0])
 require(chosen is not None,'Cannot identify output filesystem')
 require(chosen[1]in {'ext2','ext3','ext4','xfs','btrfs','tmpfs','ramfs','overlay','zfs','bcachefs'},'SQLite WAL output must use known node-local storage; detected '+chosen[1])
 return {'status':'KNOWN_LOCAL_FILESYSTEM','filesystem_type':chosen[1]}

def checked_source_protocol(a):
 value=read(a.source_protocol);receipt=a.source_protocol.with_suffix('.sha256')
 require(receipt.is_file()and receipt.read_text().split()[0]==digest(a.source_protocol),'Source scoring protocol SHA receipt differs')
 require(value['scorer_sha256']==digest(a.scorer),'Frozen scoring algorithm source changed')
 return value

def resolve(a):
 require(a.model_key is not None,'--model-key is required')
 spec=dict(read(HERE/'model_registry.json')[a.model_key]);spec['revision']=a.revision or spec['revision']
 require(re.fullmatch(r'[0-9a-fA-F]{40}',spec['revision'])is not None,'Use a complete immutable 40-hex HF revision')
 spec['revision']=spec['revision'].lower()
 require(a.batch_size>0,'Batch size must be positive')
 require(a.output is not None,'--output must be a separate node-local directory for this model')
 return spec

def source_summary(path):
 db=readonly(path)
 count=db.execute('SELECT count(*) FROM requests').fetchone()[0];unique=db.execute('SELECT count(*) FROM prompts').fetchone()[0]
 policies=[r[0]for r in db.execute('SELECT DISTINCT policy FROM requests ORDER BY policy')]
 require(set(policies)==set(POLICIES),'Unexpected source policies')
 require(db.execute('SELECT count(*) FROM requests WHERE prompt_sha256 NOT IN (SELECT prompt_sha256 FROM prompts)').fetchone()[0]==0,'Broken source request mapping')
 groups=[{'condition':c,'policy':p,'rows':n}for c,p,n in db.execute('SELECT condition,policy,count(*) FROM requests GROUP BY condition,policy ORDER BY condition,policy')]
 db.close();return {'requested_rows':count,'source_unique_prompts':unique,'policies':policies,'condition_policy_counts':groups,'source_inputs_sha256':digest(path)}

def render(tokenizer,spec,user):
 kwargs={'date_string':DATE}
 if spec['family']=='qwen3':kwargs['enable_thinking']=False
 chat=tokenizer.apply_chat_template([{'role':'system','content':SYSTEM},{'role':'user','content':user}],tokenize=False,add_generation_prompt=True,**kwargs)
 require(isinstance(chat,str)and user.encode('utf-8')in chat.encode('utf-8'),'Native template changed the user body')
 ids=tokenizer(chat,add_special_tokens=False,truncation=False,return_attention_mask=False)['input_ids']
 require(isinstance(ids,list)and all(isinstance(t,int)for t in ids),'Unexpected tokenizer output')
 require(0<len(ids)and len(ids)+MAX_NEW<=CONTEXT,'Token overflow: refuse truncation ('+str(len(ids))+')')
 return chat,len(ids)

def prepare_native(source,out,backend,spec):
 out.mkdir(parents=True,exist_ok=True);target=out/'native_inputs.sqlite';receipt=out/'input_manifest.json'
 summary=source_summary(source);identity={'model':spec,'tokenizer':backend.tokenizer_identity,'template_date':DATE,'context_tokens':CONTEXT,'maximum_new_tokens':MAX_NEW,'source_inputs_sha256':summary['source_inputs_sha256'],'producer_sha256':digest(__file__)}
 if target.exists()or receipt.exists():
  saved=read(receipt);require(saved['preparation_identity']==identity and saved['native_inputs_sha256']==digest(target),'Refuse stale or changed native inputs');return saved
 stage=out/'native_inputs.sqlite.partial';require(not stage.exists(),'Incomplete preparation exists; use a fresh output directory')
 src=readonly(source);db=sqlite3.connect(stage,uri=True);db.execute('PRAGMA foreign_keys=ON');db.execute('PRAGMA synchronous=FULL')
 db.execute('CREATE TABLE prompts(prompt_sha256 TEXT PRIMARY KEY,chat_prompt TEXT NOT NULL,prompt TEXT NOT NULL,prompt_tokens INTEGER NOT NULL,first_request_order INTEGER NOT NULL,user_body_sha256 TEXT NOT NULL)')
 db.execute('CREATE TABLE source_prompt_map(source_prompt_sha256 TEXT PRIMARY KEY,native_prompt_sha256 TEXT NOT NULL REFERENCES prompts(prompt_sha256),user_body_sha256 TEXT NOT NULL)')
 minimum=None;maximum=0;source_prompts=0
 try:
  with db:
   for old,user,first in src.execute('SELECT prompt_sha256,prompt,first_request_order FROM prompts ORDER BY first_request_order'):
    chat,n=render(backend.tokenizer,spec,user);key=textsha(chat);bodyhash=textsha(user)
    inserted=db.execute('INSERT OR IGNORE INTO prompts VALUES(?,?,?,?,?,?)',(key,chat,user,n,first,bodyhash)).rowcount
    if not inserted:require(db.execute('SELECT chat_prompt,prompt FROM prompts WHERE prompt_sha256=?',(key,)).fetchone()==(chat,user),'Native hash collision or body loss')
    db.execute('INSERT INTO source_prompt_map VALUES(?,?,?)',(old,key,bodyhash));source_prompts+=1
    minimum=n if minimum is None else min(minimum,n);maximum=max(maximum,n)
   sql=src.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='requests'").fetchone()[0];db.execute(sql)
   columns=[r[1]for r in src.execute('PRAGMA table_info(requests)')];require('prompt_sha256'in columns,'Missing source prompt key')
   require(all(re.fullmatch(r'[a-z_][a-z0-9_]*',c)for c in columns),'Unexpected source column name')
   db.execute('ATTACH DATABASE ? AS original',(source.resolve().as_uri()+'?mode=ro',))
   selected=['m.native_prompt_sha256'if c=='prompt_sha256'else 'r.'+c for c in columns]
   db.execute('INSERT INTO requests('+','.join(columns)+') SELECT '+','.join(selected)+' FROM original.requests r JOIN source_prompt_map m ON m.source_prompt_sha256=r.prompt_sha256')
   require(db.execute('SELECT count(*) FROM requests').fetchone()[0]==summary['requested_rows'],'Request rows lost')
   other=[c for c in columns if c!='prompt_sha256']
   differences=' OR '.join('t.'+c+' IS NOT r.'+c for c in other)
   require(db.execute('SELECT count(*) FROM requests t JOIN original.requests r USING(request_order) WHERE '+differences).fetchone()[0]==0,'Source request metadata changed')
   db.execute('CREATE INDEX requests_prompt_index ON requests(prompt_sha256)');db.execute('CREATE INDEX requests_question_index ON requests(question_id,request_order)')
  require(db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'and not db.execute('PRAGMA foreign_key_check').fetchall(),'Native SQLite integrity failure')
  unique=db.execute('SELECT count(*) FROM prompts').fetchone()[0]
  require(source_prompts==summary['source_unique_prompts'],'Missing source prompt bodies')
  for key,chat,user,n,first,bodyhash in db.execute('SELECT * FROM prompts'):
   require(textsha(chat)==key and textsha(user)==bodyhash and user in chat,'Native text/hash mismatch')
  db.close();src.close();require(digest(source)==summary['source_inputs_sha256'],'Source input changed during preparation');stage.replace(target)
 except BaseException:
  db.close();src.close();raise
 report={**summary,'status':'NATIVE_INPUTS_PREPARED_NO_GENERATION','native_inputs_sha256':digest(target),'native_unique_prompts':unique,'input_tokens_min':minimum,'input_tokens_max':maximum,'all_prompts_fit':True,'all_user_bodies_byte_preserved':True,'request_fields_changed':['prompt_sha256'],'preparation_identity':identity,'created_utc':now()}
 atomic(receipt,report);return report

def derived_protocol(a,native):
 original=checked_source_protocol(a)
 require(original['inputs_sqlite_sha256']==native['source_inputs_sha256'],'Source protocol/input mismatch')
 protocol={**original,'source_metrics_created_utc':original.get('created_utc'),'created_utc':read(a.output/'scoring_protocol.json')['created_utc']if(a.output/'scoring_protocol.json').exists()else now(),'status':'HF_NATIVE_RENDERING_FOLLOWUP_FROZEN_BEFORE_THIS_RUN','source_metrics_protocol_sha256':digest(a.source_protocol),'source_inputs_sqlite_sha256':native['source_inputs_sha256'],'inputs_sqlite_file':'native_inputs.sqlite','inputs_sqlite_sha256':native['native_inputs_sha256'],'requested_rows':native['requested_rows'],'unique_prompts':native['native_unique_prompts'],'renderer_change':native['preparation_identity'],'scoring_entrypoint':'run_hf_grid.py --score using original frozen scorer functions; original fixed-input CLI is not rewritten','model_execution_note':'Per-model native BF16 follow-up. Preparation or self-tests do not establish actual GPU execution.'}
 path=a.output/'scoring_protocol.json'
 for condition,field in [('clean','clean_question_policy_rows'),('attack','attack_rows'),('matched_benign','matched_benign_rows')]:protocol[field]=sum(g['rows']for g in native['condition_policy_counts']if g['condition']==condition)
 if path.exists():require(read(path)==protocol,'Derived scoring protocol changed')
 else:atomic(path,protocol)
 checksum=path.with_suffix('.sha256');expected=digest(path)
 if checksum.exists():require(checksum.read_text().split()[0]==expected,'Derived protocol SHA receipt differs')
 else:checksum.write_text(expected+'  '+path.name+'\n')
 return path

class HFBackend:
 def __init__(self,a,spec):
  os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG',':4096:8');os.environ.setdefault('TOKENIZERS_PARALLELISM','false')
  import torch,transformers,accelerate
  from huggingface_hub import snapshot_download
  require(torch.cuda.is_available(),'--run requires an actual CUDA GPU; no CPU fallback')
  self.torch=torch;self.transformers=transformers;self.a=a;self.spec=spec;self.device=torch.device(a.device)
  require(self.device.type=='cuda'and torch.cuda.is_bf16_supported(),'Native BF16 CUDA support is required')
  torch.cuda.set_device(self.device);torch.manual_seed(12);torch.cuda.manual_seed_all(12)
  torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False;torch.use_deterministic_algorithms(True)
  self.snapshot=Path(snapshot_download(spec['model_id'],revision=spec['revision'],cache_dir=str(a.cache_dir)if a.cache_dir else None,allow_patterns=['*.json','*.safetensors','*.jinja','tokenizer.model','LICENSE*','README.md']))
  require(self.snapshot.name==spec['revision'],'Downloaded snapshot revision differs')
  self.artifacts=[{'file':str(p.relative_to(self.snapshot)),'sha256':digest(p),'bytes':p.stat().st_size}for p in sorted(self.snapshot.rglob('*'))if p.is_file()and p.suffix in ('.json','.safetensors','.jinja','.model')]
  require(any(r['file'].endswith('.safetensors')for r in self.artifacts),'No safetensors weights found')
  self.tokenizer=transformers.AutoTokenizer.from_pretrained(self.snapshot,trust_remote_code=False,local_files_only=True)
  self.tokenizer.padding_side='left'
  if self.tokenizer.pad_token_id is None:self.tokenizer.pad_token=self.tokenizer.eos_token
  require(self.tokenizer.pad_token_id is not None,'No valid padding token')
  template=self.tokenizer.get_chat_template()
  self.tokenizer_identity={'model_id':spec['model_id'],'revision':spec['revision'],'class':type(self.tokenizer).__name__,'native_template':template,'native_template_sha256':textsha(template),'backend_tokenizer_sha256':textsha(self.tokenizer.backend_tokenizer.to_str()),'special_token_ids':list(self.tokenizer.all_special_ids),'pad_token_id':self.tokenizer.pad_token_id,'eos_token_id':self.tokenizer.eos_token_id,'padding_side':'left','date_string':DATE,'enable_thinking':False if spec['family']=='qwen3'else None,'trust_remote_code':False}
  props=torch.cuda.get_device_properties(self.device)
  self.environment={'python':platform.python_version(),'system':platform.system(),'machine':platform.machine(),'torch':torch.__version__,'transformers':transformers.__version__,'accelerate':accelerate.__version__,'tokenizers':importlib.metadata.version('tokenizers'),'jinja2':importlib.metadata.version('jinja2'),'huggingface_hub':importlib.metadata.version('huggingface-hub'),'safetensors':importlib.metadata.version('safetensors'),'numpy':importlib.metadata.version('numpy'),'cuda':torch.version.cuda,'cudnn':torch.backends.cudnn.version(),'gpu_name':props.name,'compute_capability':[props.major,props.minor],'gpu_total_memory':props.total_memory,'dtype':'bfloat16','attention':'sdpa','tf32':False,'deterministic_algorithms':True,'cublas_workspace_config':os.environ['CUBLAS_WORKSPACE_CONFIG']}
  self.model=None
 def load(self):
  t=self.torch;self.model=self.transformers.AutoModelForCausalLM.from_pretrained(self.snapshot,trust_remote_code=False,local_files_only=True,torch_dtype=t.bfloat16,device_map={'':str(self.device)},low_cpu_mem_usage=True,attn_implementation='sdpa').eval()
  require(str(next(self.model.parameters()).dtype)=='torch.bfloat16','Actual model dtype differs')
  require(all(p.device.type=='cuda'for p in self.model.parameters()),'Model was offloaded outside CUDA')
  eos=self.model.generation_config.eos_token_id;self.eos=list(eos)if isinstance(eos,list)else [eos]
  if self.tokenizer.eos_token_id is not None:self.eos.append(self.tokenizer.eos_token_id)
  if self.spec['family']=='llama31'and '<|eot_id|>'in self.tokenizer.get_vocab():self.eos.append(self.tokenizer.convert_tokens_to_ids('<|eot_id|>'))
  self.eos=sorted({x for x in self.eos if isinstance(x,int)})
  require(bool(self.eos),'No EOS termination IDs')
  self.generation={'do_sample':False,'num_beams':1,'max_new_tokens':MAX_NEW,'repetition_penalty':1.0,'use_cache':True,'eos_token_id':self.eos,'pad_token_id':self.tokenizer.pad_token_id,'bos_token_id':self.tokenizer.bos_token_id}
  self.generation_config=self.transformers.GenerationConfig(**self.generation)
  self.identity={'implementation':'transformers_native_cuda_bf16','model':self.spec,'snapshot_artifacts':self.artifacts,'model_class':type(self.model).__name__,'model_parameter_count':self.model.num_parameters(),'tokenizer':self.tokenizer_identity,'environment':self.environment,'generation':self.generation}
 def generate(self,items):
  t=self.torch;batch=self.tokenizer([r['chat_prompt']for r in items],padding=True,return_tensors='pt',add_special_tokens=False,truncation=False)
  actual=batch['attention_mask'].sum(dim=1).tolist();require(actual==[r['prompt_tokens']for r in items],'GPU input/token preflight disagreement')
  width=batch['input_ids'].shape[1];require(width+MAX_NEW<=CONTEXT,'Padded batch overflow; no truncation allowed')
  batch={k:v.to(self.device)for k,v in batch.items()}
  with t.inference_mode():generated=self.model.generate(**batch,generation_config=self.generation_config)
  t.cuda.synchronize(self.device);tails=generated[:,width:].tolist();returned=[]
  for item,ids in zip(items,tails,strict=True):
   end=next((i for i,x in enumerate(ids)if x in self.eos),None)
   completion=ids[:end+1]if end is not None else ids
   require(end is not None or len(completion)==MAX_NEW,'Unexpected generation termination')
   returned.append({'prompt_sha256':item['prompt_sha256'],'response':self.tokenizer.decode(completion[:-1]if end is not None else completion,skip_special_tokens=False,clean_up_tokenization_spaces=False).strip(),'finish_reason':'stop'if end is not None else'length','prompt_tokens':item['prompt_tokens'],'completion_tokens':len(completion),'output_token_ids':completion,'input_body_sha256':item['user_body_sha256']})
  return returned

def totals(db):
 attempts,known,unknown,errors=db.execute("SELECT count(*),coalesce(sum(returned_count),0),coalesce(sum(CASE WHEN returned_count IS NULL THEN prompt_count ELSE 0 END),0),coalesce(sum(CASE WHEN status='ERROR_UNKNOWN' THEN 1 ELSE 0 END),0) FROM attempts").fetchone()
 return {'cumulative_batch_attempts':attempts,'cumulative_known_returned_sequences':known,'cumulative_unknown_outcome_requested_prompts':unknown,'cumulative_errors':errors,'generator_inference_executed':True if known else None if unknown else False}

def run_engine(inputs,out,backend,config,batch_size):
 config_hash=textsha(stable(config));source=readonly(inputs);source.row_factory=sqlite3.Row
 keys={r[0]for r in source.execute('SELECT prompt_sha256 FROM prompts')};path=out/'generation_responses.sqlite';db=sqlite3.connect(path)
 db.execute('PRAGMA journal_mode=WAL');db.execute('PRAGMA synchronous=FULL')
 db.execute('CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL)')
 db.execute('CREATE TABLE IF NOT EXISTS attempts(attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,prompt_count INTEGER NOT NULL,returned_count INTEGER,prompt_keys_json TEXT NOT NULL,started_utc TEXT NOT NULL,finished_utc TEXT,status TEXT NOT NULL,raw_json TEXT,error TEXT)')
 db.execute('CREATE TABLE IF NOT EXISTS responses(prompt_sha256 TEXT PRIMARY KEY,response TEXT NOT NULL,finish_reason TEXT NOT NULL,prompt_tokens INTEGER NOT NULL,completion_tokens INTEGER NOT NULL,elapsed_seconds REAL NOT NULL,raw_json TEXT NOT NULL,executed_utc TEXT NOT NULL,batch_id INTEGER NOT NULL,config_sha256 TEXT NOT NULL)')
 prior=db.execute("SELECT value FROM metadata WHERE key='config_sha256'").fetchone()
 if prior:require(prior[0]==config_hash,'Refuse changed model/input/runtime/precision/batch configuration on resume')
 else:db.executemany('INSERT INTO metadata VALUES(?,?)',[('config_sha256',config_hash),('config',stable(config))]);db.commit()
 completed={r[0]for r in db.execute('SELECT prompt_sha256 FROM responses')};require(completed<=keys,'Unexpected saved response key')
 manifest={'status':'RUNNING','started_or_resumed_utc':now(),'config':config,'config_sha256':config_hash,'expected_unique_prompts':len(keys),'requested_rows':source.execute('SELECT count(*) FROM requests').fetchone()[0],'completed_unique_prompts':len(completed),'generator_inference_executed_this_session':False,'errors_this_session':0,'new_successful_responses':0,'target_tool_calls':0}
 initial=len(completed);started=time.monotonic()
 def save(status):
  manifest.update(totals(db));manifest.update(status=status,completed_unique_prompts=len(completed),new_successful_responses=len(completed)-initial,elapsed_this_session_seconds=time.monotonic()-started,checkpoint_utc=now());atomic(out/'run_manifest.json',manifest)
 def execute(items):
  attempt=db.execute('INSERT INTO attempts(prompt_count,prompt_keys_json,started_utc,status)VALUES(?,?,?,?)',(len(items),stable([x['prompt_sha256']for x in items]),now(),'SENT')).lastrowid;db.commit();save('RUNNING')
  start=time.monotonic()
  try:returned=backend.generate(items)
  except BaseException as error:db.execute('UPDATE attempts SET status=?,finished_utc=?,error=? WHERE attempt_id=?',('ERROR_UNKNOWN',now(),repr(error),attempt));db.commit();raise
  elapsed=time.monotonic()-start
  db.execute('UPDATE attempts SET returned_count=?,finished_utc=?,status=?,raw_json=? WHERE attempt_id=?',(len(returned),now(),'RESPONSE_RECEIVED',stable(returned),attempt));db.commit()
  require(len(returned)==len(items),'Missing returned generation rows')
  for item,row in zip(items,returned,strict=True):
   require(row['prompt_sha256']==item['prompt_sha256']and row['input_body_sha256']==item['user_body_sha256'],'Returned prompt/body identity mismatch')
   require(isinstance(row['response'],str)and row['finish_reason']in ('stop','length'),'Malformed generation record')
   require(row['prompt_tokens']==item['prompt_tokens']and isinstance(row['completion_tokens'],int)and 0<=row['completion_tokens']<=MAX_NEW,'Invalid measured token count')
   db.execute('INSERT INTO responses VALUES(?,?,?,?,?,?,?,?,?,?)',(row['prompt_sha256'],row['response'],row['finish_reason'],row['prompt_tokens'],row['completion_tokens'],elapsed/len(items),stable(row),now(),attempt,config_hash))
  db.execute('UPDATE attempts SET status=? WHERE attempt_id=?',('COMMITTED',attempt));db.commit();completed.update(x['prompt_sha256']for x in items);manifest['generator_inference_executed_this_session']=True;save('RUNNING')
  print(stable({'completed_unique_prompts':len(completed),'expected':len(keys),'batch_seconds':round(elapsed,3),'status':'RUNNING'}),flush=True)
 status='RUNNING';save(status)
 try:
  cursor=source.execute('SELECT p.* FROM prompts p JOIN(SELECT prompt_sha256,min(question_id)q,min(request_order)n FROM requests GROUP BY prompt_sha256)r USING(prompt_sha256) ORDER BY r.q,r.n');batch=[]
  for row in cursor:
   if (out/'pause_requested').exists():status='PAUSED_BY_CONTROL_FILE';break
   if row['prompt_sha256']in completed:continue
   batch.append(dict(row))
   if len(batch)==batch_size:execute(batch);batch=[]
  else:
   if (out/'pause_requested').exists():status='PAUSED_BY_CONTROL_FILE'
   else:
    if batch:execute(batch)
    require(completed==keys,'Missing outputs cannot be declared complete');status='PAUSED_BY_CONTROL_FILE'if(out/'pause_requested').exists()else'COMPLETE'
  save(status)
 except BaseException as error:
  db.rollback();manifest['errors_this_session']+=1;manifest.update(error_type=type(error).__name__,error=str(error));save('INCOMPLETE_ERROR');raise
 finally:
  db.execute('PRAGMA wal_checkpoint(TRUNCATE)');db.close();source.close()
 if status=='COMPLETE':manifest['response_database_sha256']=digest(path);atomic(out/'run_manifest.json',manifest)
 return manifest

def scoring_inputs(path):
 db=readonly(path);db.row_factory=sqlite3.Row
 required={'request_order','request_id','prompt_sha256','case_id','question_id','article_id','family_id','template_id','condition','policy','objective','reference_answers_json','requested_output','metadata_json'}
 require(required<={r[1]for r in db.execute('PRAGMA table_info(requests)')},'Missing native scoring request fields')
 requests=[dict(r)for r in db.execute('SELECT * FROM requests ORDER BY request_order')];keys=set()
 for key,chat in db.execute('SELECT prompt_sha256,chat_prompt FROM prompts'):
  require(textsha(chat)==key,'Scoring prompt text/hash mismatch');keys.add(key)
 db.close();return requests,keys

def scoring_responses(path):
 # Identical logical snapshot definition to the frozen scorer, with safe URI
 # parsing here so filenames containing # or ? cannot address another database.
 db=readonly(path);db.row_factory=sqlite3.Row;db.execute('BEGIN');rows={};snapshot=hashlib.sha256();configs=set();metadata=dict(db.execute('SELECT key,value FROM metadata'))
 for result in db.execute('SELECT * FROM responses ORDER BY prompt_sha256'):
  row=dict(result);key=row['prompt_sha256'];require(key not in rows,'Duplicate response key')
  require(isinstance(row['response'],str)and row['finish_reason']in ('stop','length'),'Invalid response text/finish reason')
  require(all(isinstance(row[k],int)and row[k]>=0 for k in ('prompt_tokens','completion_tokens')),'Invalid measured token count')
  require(isinstance(row.get('config_sha256'),str)and row['config_sha256'],'Missing response configuration fingerprint')
  configs.add(row['config_sha256']);rows[key]=row;snapshot.update((stable(row)+'\n').encode())
 require(len(configs)<=1 and(not configs or configs=={metadata.get('config_sha256')}),'Mixed response/metadata configurations')
 db.commit();db.close();return rows,snapshot.hexdigest(),metadata

def score(a):
 spec=resolve(a);checked_source_protocol(a)
 path=a.output/'native_inputs.sqlite';protocol=a.output/'scoring_protocol.json';native=read(a.output/'input_manifest.json');p=read(protocol)
 require(protocol.with_suffix('.sha256').read_text().split()[0]==digest(protocol),'Derived scoring protocol SHA receipt differs')
 require(p['inputs_sqlite_sha256']==digest(path)==native['native_inputs_sha256'],'Native scoring input changed')
 require(p['scorer_sha256']==digest(a.scorer)and p['source_metrics_protocol_sha256']==digest(a.source_protocol),'Frozen metric source/protocol changed')
 manifest=read(a.output/'run_manifest.json')
 require(a.partial or manifest['status']=='COMPLETE','Incomplete execution requires --partial; missing outputs are not failures')
 wal=a.output/'generation_responses.sqlite-wal';require(not wal.exists()or wal.stat().st_size==0,'Score a closed checkpoint, not an active WAL')
 metric=load_module(a.scorer,'group9_frozen_metrics');requests,keys=scoring_inputs(path);responses,snapshot,metadata=scoring_responses(a.output/'generation_responses.sqlite');config=json.loads(metadata['config'])
 require(textsha(stable(config))==metadata['config_sha256']==manifest['config_sha256']and config==manifest['config'],'Response configuration fingerprint mismatch')
 require(config['input_sqlite_sha256']==digest(path)and config['scoring_protocol_sha256']==digest(protocol),'Generation used different inputs/protocol')
 require(config['model_key']==a.model_key and config['backend']['model']==spec==native['preparation_identity']['model'],'CLI model label/revision differs from actual saved model identity')
 require(len(requests)==p['requested_rows']and len(keys)==p['unique_prompts']and {x['prompt_sha256']for x in requests}==keys,'Incomplete native request grid')
 destination=a.score_output or a.output/('partial_scoring'if a.partial else'scoring');name='partial_scoring_manifest.json'if a.partial else'scoring_manifest.json'
 def validate(saved):
  require(saved['response_config_sha256']==metadata['config_sha256']and saved['response_snapshot_sha256']==snapshot and saved['native_protocol_sha256']==digest(protocol)and saved['input_sqlite_sha256']==digest(path),'Existing scoring manifest uses different responses or inputs')
  require(saved['model_key']==a.model_key and saved['model_identity']==spec and saved['metric_source_sha256']==digest(a.scorer),'Existing scoring model/metric identity differs')
  expected=saved['closed_output_hashes'];require(set(expected)=={f.name for f in destination.iterdir()if f.is_file()and f.name!=name},'Scoring output file coverage changed')
  for filename,wanted in expected.items():require(Path(filename).name==filename and digest(destination/filename)==wanted,'Closed scoring artifact hash differs: '+filename)
 if destination.exists()and any(destination.iterdir()):
  saved=read(destination/name);validate(saved);print(json.dumps({'status':'EXISTING_SCORING_VERIFIED','model_key':a.model_key,'manifest':name},indent=2));return
 result=metric.analyze(requests,responses,destination,a.partial)
 result.update(scoring_version=p['scoring_version'],created_utc=now(),native_protocol_sha256=digest(protocol),source_metrics_protocol_sha256=digest(a.source_protocol),metric_source_sha256=digest(a.scorer),entrypoint_sha256=digest(__file__),input_sqlite_sha256=digest(path),response_snapshot_sha256=snapshot,response_config_sha256=metadata['config_sha256'],response_config_json=metadata['config'],model_key=a.model_key,model_identity=spec,execution_backend=config['backend']['implementation'],execution_scope='Score saved per-model native responses using original frozen metric functions. Artifact consistency is not independent GPU execution attestation.',closed_output_hashes={f.name:digest(f)for f in sorted(destination.iterdir())if f.is_file()})
 metric.write_json(destination/name,result);validate(read(destination/name));print(json.dumps(result,indent=2))

def self_test():
 class Tokenizer:
  def __init__(self,family,overflow=False):self.family=family;self.overflow=overflow;self.calls=[]
  def apply_chat_template(self,messages,**kwargs):self.calls.append(kwargs);return self.family+' NATIVE '+messages[0]['content']+'\n'+messages[1]['content']+'\nASSISTANT'
  def __call__(self,text,**kwargs):return {'input_ids':list(range(5000 if self.overflow else len(text.split())+10))}
 class Backend:
  def __init__(self,family='qwen3'):self.tokenizer=Tokenizer(family);self.tokenizer_identity={'fixture':family};self.calls=0;self.fail=False;self.bad=False
  def generate(self,items):
   self.calls+=1
   if self.fail:raise RuntimeError('MOCK_UNKNOWN_ONLY')
   return [{'prompt_sha256':'BAD'if self.bad else r['prompt_sha256'],'response':'MOCK','finish_reason':'stop','prompt_tokens':r['prompt_tokens'],'completion_tokens':2,'input_body_sha256':r['user_body_sha256']}for r in items]
 checks=[]
 with tempfile.TemporaryDirectory(prefix='hf-grid mock-#?-')as folder:
  base=Path(folder);source=base/'source.sqlite';db=sqlite3.connect(source)
  db.execute('CREATE TABLE prompts(prompt_sha256 TEXT PRIMARY KEY,chat_prompt TEXT,prompt TEXT,first_request_order INTEGER)');db.execute('CREATE TABLE requests(request_order INTEGER PRIMARY KEY,request_id TEXT UNIQUE,prompt_sha256 TEXT REFERENCES prompts(prompt_sha256),case_id TEXT,question_id TEXT,article_id TEXT,family_id TEXT,template_id TEXT,condition TEXT,policy TEXT,objective TEXT,reference_answer TEXT,reference_answers_json TEXT,requested_output TEXT,selected_ids_json TEXT,metadata_json TEXT)')
  for i in range(2):
   user='Body '+str(i)+'\nExact punctuation: "quoted".\nAnswer:';old=textsha('OLD_CHATML'+user);db.execute('INSERT INTO prompts VALUES(?,?,?,?)',(old,'OLD_CHATML'+user,user,i+1))
   for j,policy in enumerate(POLICIES):db.execute('INSERT INTO requests VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(i*3+j+1,'r'+str(i)+policy,old,'clean--q'+str(i),'q'+str(i),'a'+str(i),None,None,'clean',policy,'none','2003','["2003"]','2010','[]','{}'))
  db.commit();db.close();sourcehash=digest(source);backend=Backend();spec=read(HERE/'model_registry.json')['qwen3_8b']
  prepared=prepare_native(source,base/'model',backend,spec);inputs=base/'model/native_inputs.sqlite';require(prepared['requested_rows']==6 and prepared['native_unique_prompts']==2,'Fixture mapping counts');require(digest(source)==sourcehash,'Source mutated');require(all(c.get('enable_thinking')is False and c['date_string']==DATE for c in backend.tokenizer.calls),'Thinking/date not hardfixed');checks.append('native_user_bodies_all_mapping_preserved_and_qwen_thinking_off')
  llama=Backend('llama31');chat,n=render(llama.tokenizer,{'family':'llama31'},'Body');require(chat.startswith('llama31')and'enable_thinking'not in llama.tokenizer.calls[0],'Llama reused Qwen template');checks.append('llama_native_template_separate')
  try:render(Tokenizer('qwen3',True),spec,'Body');raise AssertionError('Overflow accepted')
  except ValueError:checks.append('overflow_rejected_without_truncation')
  fixture_protocol=base/'mock_source_protocol.json';frozen=read(ROOT/'generation/scoring_protocol_frozen.json');frozen['inputs_sqlite_sha256']=sourcehash;atomic(fixture_protocol,frozen);fixture_protocol.with_suffix('.sha256').write_text(digest(fixture_protocol)+'  mock_source_protocol.json\n')
  scoring_args=argparse.Namespace(output=base/'model',source_protocol=fixture_protocol,scorer=ROOT/'code/generation/score_generations.py',model_key='qwen3_8b',revision=None,batch_size=2,partial=False,score_output=None)
  bound_protocol=derived_protocol(scoring_args,prepared)
  config={'model_key':'qwen3_8b','backend':{'model':spec,'implementation':'MOCK_ONLY_NOT_GPU'},'input_sqlite_sha256':digest(inputs),'scoring_protocol_sha256':digest(bound_protocol),'runner_sha256':digest(__file__),'identity':'MOCK_NOT_REAL_MODEL'}
  out=base/'model';run_engine(inputs,out,backend,config,2);require(backend.calls==1,'Dedup did not reduce calls');again=run_engine(inputs,out,backend,config,2);require(backend.calls==1 and again['cumulative_known_returned_sequences']==2 and again['generator_inference_executed']is True and again['generator_inference_executed_this_session']is False,'Resume accounting');checks.append('complete_unique_dedup_and_guarded_zero_call_resume')
  score(scoring_args);first_score=digest(out/'scoring/scoring_manifest.json');score(scoring_args);require(digest(out/'scoring/scoring_manifest.json')==first_score,'Idempotent scoring rewrote outputs');checks.append('original_frozen_metric_functions_native_protocol_and_idempotent_closed_hashes')
  try:run_engine(inputs,out,backend,{**config,'identity':'CHANGED'},2);raise AssertionError('Changed identity accepted')
  except ValueError:checks.append('changed_model_runtime_identity_rejected')
  failed=base/'failed';failed.mkdir();bad=Backend();bad.fail=True
  try:run_engine(inputs,failed,bad,config,2);raise AssertionError('Unknown failure accepted')
  except RuntimeError:pass
  db=readonly(failed/'generation_responses.sqlite');require(db.execute('SELECT status FROM attempts').fetchall()==[('ERROR_UNKNOWN',)],'Attempt lost');db.close();bad.fail=False;resumed=run_engine(inputs,failed,bad,config,2);require(resumed['cumulative_batch_attempts']==2 and resumed['cumulative_unknown_outcome_requested_prompts']==2 and resumed['cumulative_known_returned_sequences']==2,'Retry totals lost');checks.append('sent_unknown_failure_durable_and_resume_totals')
  rejected=base/'rejected';rejected.mkdir();bad=Backend();bad.bad=True
  try:run_engine(inputs,rejected,bad,config,2);raise AssertionError('Bad identity accepted')
  except ValueError:pass
  db=readonly(rejected/'generation_responses.sqlite');require(db.execute('SELECT count(*) FROM responses').fetchone()[0]==0,'Bad batch committed');db.close();checks.append('returned_identity_mismatch_rejected_before_commit')
  paused=base/'paused';paused.mkdir();(paused/'pause_requested').touch();b=Backend();state=run_engine(inputs,paused,b,config,2);require(state['status']=='PAUSED_BY_CONTROL_FILE'and b.calls==0,'Pause generated or completed');checks.append('pause_control_never_false_complete')
 return {'status':'PASS','checks':checks,'mock_generation_batches':True,'real_model_loads':0,'real_gpu_inference':0,'network_calls':0,'temporary_fixtures_removed':True,'runner_sha256':digest(__file__),'actual_gpu_validation':'NOT_EXECUTED_ON_THIS_HOST'}

def main():
 p=argparse.ArgumentParser(description=__doc__);actions=p.add_mutually_exclusive_group()
 for action in ('plan','run','score','self-test'):actions.add_argument('--'+action,action='store_true')
 p.add_argument('--model-key',choices=('qwen3_8b','llama31_8b'));p.add_argument('--revision');p.add_argument('--source-inputs',type=Path,default=ROOT/'generation/input/generation_inputs.sqlite');p.add_argument('--output',type=Path);p.add_argument('--cache-dir',type=Path);p.add_argument('--device',default='cuda:0');p.add_argument('--batch-size',type=int,default=8);p.add_argument('--scorer',type=Path,default=ROOT/'code/generation/score_generations.py');p.add_argument('--source-protocol',type=Path,default=ROOT/'generation/scoring_protocol_frozen.json');p.add_argument('--score-output',type=Path);p.add_argument('--partial',action='store_true');a=p.parse_args()
 if a.self_test:
  with contextlib.redirect_stdout(io.StringIO()):result=self_test()
  print(json.dumps(result,indent=2));return
 spec=resolve(a);a.output=a.output.resolve()
 if a.score:score(a);return
 if not a.run:
  print(json.dumps({'status':'PLAN_ONLY_NO_MODEL_OR_NETWORK','model':spec,'source':source_summary(a.source_inputs),'batch_size':a.batch_size,'dtype':'bfloat16','context_tokens':CONTEXT,'max_new_tokens':MAX_NEW,'system_message':SYSTEM,'template_date':DATE,'native_token_preflight':'Required for every model; not inferred from oldGGUFtokens','original_inputs_changed':False,'gated_access':'Existing authorizedHFsessiononly; no credential logging','actual_gpu_inference':False},indent=2));return
 filesystem=local_filesystem(a.output)
 backend=HFBackend(a,spec);native=prepare_native(a.source_inputs,a.output,backend,spec);protocol=derived_protocol(a,native);backend.load()
 config={'engine':'transformers_native_cuda_bf16','model_key':a.model_key,'input_sqlite_sha256':native['native_inputs_sha256'],'source_inputs_sqlite_sha256':native['source_inputs_sha256'],'scoring_protocol_sha256':digest(protocol),'source_metrics_protocol_sha256':digest(a.source_protocol),'runner_sha256':digest(__file__),'backend':backend.identity,'batch_size':a.batch_size,'context_tokens':CONTEXT,'max_new_tokens':MAX_NEW,'seed':12,'schedule':'lexicalquestionthenminimumrequestorder','latency_scope':'Per-rowelapsed_secondsisamortizedbatchcost,notindividualrequestlatency'}
 atomic(a.output/'runtime_observations.json',{'created_utc':now(),'output_filesystem':filesystem,'GPU_execution_validation':'GPU backend loaded only by this actual --run invocation'})
 state=run_engine(a.output/'native_inputs.sqlite',a.output,backend,config,a.batch_size);print(json.dumps({k:v for k,v in state.items()if k!='config'},indent=2))
if __name__=='__main__':main()
