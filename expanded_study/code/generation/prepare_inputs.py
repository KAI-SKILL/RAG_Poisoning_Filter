"""Prepare every expanded 3B generation request with exact-prompt deduplication.

This script performs no tokenization, inference, model loading or network calls.
Source scoring and retrieval decisions remain unchanged. All request rows are
preserved even where identical complete ChatML prompts share one generation.
"""
from __future__ import annotations
from pathlib import Path
import argparse, ast, collections, datetime, hashlib, importlib.util, json, os, sqlite3, time

POLICIES=('none','LR__new_normal_1pct','LinearSVC__new_normal_1pct')
SOURCE_FILES=(
 'data/hosts.jsonl','data/corpus.jsonl','data/cases.jsonl',
 'results/retrieval_delivery.jsonl','results/normal_retrieval.jsonl',
 'results/thresholds_frozen.json','results/execution_freeze.json',
 'prior_study/original_project/revised_experiment/prompts.py',
 'prior_study/original_project/revised_experiment/gguf_generate.py',
)

def sha(path:Path)->str:
 h=hashlib.sha256()
 with path.open('rb')as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()

def stable(obj):return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def rows(path):
 with path.open(encoding='utf-8')as f:
  for n,line in enumerate(f,1):
   if not line.strip():raise ValueError(f'Blank row {n}: {path}')
   yield json.loads(line)

def require(condition,message):
 if not condition:raise ValueError(message)

def producer_functions(root):
 prompt_path=root/'prior_study/original_project/revised_experiment/prompts.py'
 spec=importlib.util.spec_from_file_location('frozen_project_prompts',prompt_path)
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 generator_path=root/'prior_study/original_project/revised_experiment/gguf_generate.py'
 tree=ast.parse(generator_path.read_text(encoding='utf-8'))
 render=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='render')
 namespace={};exec(compile(ast.Module(body=[render],type_ignores=[]),str(generator_path),'exec'),namespace)
 # Assert expected immutable surface while executing the original local functions.
 reference='<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\nCHECK<|im_end|>\n<|im_start|>assistant\n'
 require(namespace['render']('CHECK')==reference,'Unexpected original ChatML renderer')
 return mod.prompt,namespace['render'],hashlib.sha256(ast.dump(render,include_attributes=False).encode()).hexdigest()

SCHEMA='''
CREATE TABLE prompts (
 prompt_sha256 TEXT PRIMARY KEY NOT NULL,
 chat_prompt TEXT NOT NULL,
 prompt TEXT NOT NULL,
 char_count INTEGER NOT NULL,
 first_request_order INTEGER NOT NULL
) WITHOUT ROWID;
CREATE TABLE requests (
 request_order INTEGER PRIMARY KEY,
 request_id TEXT UNIQUE NOT NULL,
 prompt_sha256 TEXT NOT NULL REFERENCES prompts(prompt_sha256),
 case_id TEXT NOT NULL,
 question_id TEXT NOT NULL,
 article_id TEXT NOT NULL,
 family_id TEXT,
 template_id TEXT,
 condition TEXT NOT NULL CHECK(condition IN ('clean','attack','matched_benign')),
 policy TEXT NOT NULL,
 objective TEXT NOT NULL,
 reference_answer TEXT NOT NULL,
 reference_answers_json TEXT NOT NULL,
 requested_output TEXT,
 selected_ids_json TEXT NOT NULL,
 metadata_json TEXT NOT NULL,
 UNIQUE(case_id,condition,policy)
);
CREATE TABLE preparation_metadata (
 key TEXT PRIMARY KEY NOT NULL,
 value_json TEXT NOT NULL
) WITHOUT ROWID;
'''

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
 p.add_argument('--output-dir',type=Path,help='Defaults to ROOT/generation/input; must not contain prior outputs')
 a=p.parse_args();root=a.root.resolve();out=(a.output_dir or root/'generation/input').resolve();out.mkdir(parents=True,exist_ok=True)
 dbpath=out/'generation_inputs.sqlite';partial=out/'generation_inputs.sqlite.partial';manifestpath=out/'input_manifest.json'
 require(not any(x.exists()for x in (dbpath,partial,manifestpath)),'Refusing to overwrite existing preparation artifacts')
 start=time.monotonic();source_hashes={rel:sha(root/rel)for rel in SOURCE_FILES}
 prompt,render,render_ast_hash=producer_functions(root)
 hosts={};calibration_ids=set()
 for host in rows(root/'data/hosts.jsonl'):
  sid=host['source_id'];require(sid not in hosts and sid not in calibration_ids,'Duplicate host ID')
  if host['split']=='test':hosts[sid]=host
  elif host['split']=='calibration':calibration_ids.add(sid)
  else:raise ValueError('Unexpected host role')
 require(len(hosts)==1200 and len(calibration_ids)==1200,'Unexpected host role sizes')
 corpus={}
 for doc in rows(root/'data/corpus.jsonl'):
  did=doc['document_id'];require(did not in corpus and doc['split']=='test','Invalid corpus doc')
  corpus[did]=doc
 require(len(corpus)==4982,'Unexpected corpus size')
 con=sqlite3.connect(partial)
 con.execute('PRAGMA journal_mode=DELETE');con.execute('PRAGMA synchronous=FULL');con.execute('PRAGMA foreign_keys=ON');con.executescript(SCHEMA)
 request_order=0;duplicates=0;counts=collections.Counter();objective_counts=collections.Counter();templates=collections.Counter();source_questions=set();case_ids=set();clean_questions=set()
 insert_request='INSERT INTO requests VALUES ('+','.join('?'for _ in range(16))+')'

 def add(case,condition,policy,selected_ids,lookup,decision,host):
  nonlocal request_order,duplicates
  require(policy in POLICIES,'Policy outside frozen primary comparison')
  require(len(selected_ids)==len(set(selected_ids))<=5,'Invalid delivery identities')
  documents=[lookup[x]if x in lookup else corpus[x]for x in selected_ids]
  text=prompt(host['question'],documents);chat=render(text);key=hashlib.sha256(chat.encode('utf-8')).hexdigest()
  request_order+=1
  cursor=con.execute('INSERT OR IGNORE INTO prompts VALUES (?,?,?,?,?)',(key,chat,text,len(chat),request_order))
  if cursor.rowcount==0:
   duplicates+=1;stored=con.execute('SELECT chat_prompt FROM prompts WHERE prompt_sha256=?',(key,)).fetchone()[0]
   require(stored==chat,'Hash collision or inconsistent prompt deduplication')
  clean=condition=='clean';case_id=('clean--'+host['source_id'])if clean else case['case_id']
  request_id=case_id+'::'+condition+'::'+policy
  metadata={'selected_document_text_sha256':[hashlib.sha256(d['text'].encode()).hexdigest()for d in documents],
   'selected_document_titles':[d.get('title','')for d in documents],
   'gold_document_id':host['document_id'],'host_numeric_target':host['target'],
   'source_article_id':host['article_id'],'delivery_decision':decision,
   'construction_scope':'controlled_numeric_answer_source_substitution_and_instruction_suite',
   'clean_response_target_note':'Clean numeric target is host.target; abstention objectives must be evaluated against each attack case objective, never inferred from this numeric target.'}
  if not clean:
   metadata.update({k:case[k]for k in ('placement','encoding_mode','language_mode','threat_type','label_scope','dose','construction_status')})
  objective='none'if clean else case['objective']
  reference=host['answer']if clean else case['reference_answer']
  require(reference==host['answer'],'Case reference differs from source host')
  con.execute(insert_request,(request_order,request_id,key,case_id,host['source_id'],host['article_id'],None if clean else case['family_id'],None if clean else case['template_id'],condition,policy,objective,reference,stable(host['answers']),host['target']if clean else case['requested_output'],stable(selected_ids),stable(metadata)))
  counts[(condition,policy)]+=1;objective_counts[(condition,objective,policy)]+=1
  source_questions.add(host['source_id'])

 with con:
  # Preserve source file ordering; all clean baselines run before attacks.
  for record in rows(root/'results/normal_retrieval.jsonl'):
   qid=record['question_id'];require(qid in hosts and qid not in clean_questions,'Duplicate/missing clean question')
   clean_questions.add(qid);host=hosts[qid]
   require(record['article_id']==host['article_id']and record['gold_document_id']==host['document_id'],'Clean source identity mismatch')
   for policy in POLICIES:
    decision=record['policies'][policy]
    add(None,'clean',policy,decision['selected_ids'],{},decision,host)
  require(clean_questions==set(hosts),'Incomplete clean baselines')
  delivery=iter(rows(root/'results/retrieval_delivery.jsonl'))
  for case in rows(root/'data/cases.jsonl'):
   cid=case['case_id'];qid=case['question_id'];require(cid not in case_ids and qid in hosts,'Duplicate case or missing test host')
   case_ids.add(cid);host=hosts[qid];require(case['query']==host['question']and case['article_id']==host['article_id'],'Case source identity mismatch')
   templates[case['template_id']]+=1
   for condition,key in [('attack','attack_documents'),('matched_benign','matched_benign_documents')]:
    try:record=next(delivery)
    except StopIteration:raise ValueError('Retrieval archive shorter than case grid')from None
    require(record['case_id']==cid and record['condition']==condition and record['question_id']==qid,'Retrieval/case order or identity mismatch')
    require(record['article_id']==host['article_id']and record['template_id']==case['template_id'],'Retrieval article/template mismatch')
    lookup={d['doc_id']:d for d in case[key]}
    require(len(lookup)==len(case[key])and not(set(lookup)&set(corpus)),'Inserted identities collide')
    require(set(record['inserted_ids'])==set(lookup),'Inserted document identity mismatch')
    for policy in POLICIES:
     decision=record['policies'][policy]
     require(set(decision['selected_ids']).issubset(set(corpus)|set(lookup)),'Foreign condition document delivered')
     add(case,condition,policy,decision['selected_ids'],lookup,decision,host)
   if len(case_ids)%1200==0:print(stable({'prepared_cases':len(case_ids),'requested_rows':request_order,'elapsed_seconds':round(time.monotonic()-start,2)}),flush=True)
  require(next(delivery,None)is None,'Retrieval archive longer than case grid')
  require(len(case_ids)==28800 and len(templates)==24 and set(templates.values())=={1200},'Case/template coverage mismatch')
  require(request_order==176400 and source_questions==set(hosts),'Requested grid coverage mismatch')
  require(all(counts[(condition,policy)]==n for condition,n in [('clean',1200),('attack',28800),('matched_benign',28800)]for policy in POLICIES),'Condition-policy denominator mismatch')
  con.executescript('CREATE INDEX requests_prompt_index ON requests(prompt_sha256); CREATE INDEX requests_cohort_index ON requests(condition,policy,template_id); CREATE INDEX requests_question_index ON requests(question_id,condition,policy);')
  metadata={'schema_version':1,'status':'COMPLETE_INPUT_PREPARATION_NO_MODEL_EXECUTION','policies':POLICIES,
   'requested_rows':request_order,'cases':len(case_ids),'test_questions':len(hosts),'test_articles':len({h['article_id']for h in hosts.values()}),
   'calibration_passages_excluded':len(calibration_ids),'template_counts':dict(sorted(templates.items())),
   'input_source_hashes':source_hashes,'producer_sha256':sha(Path(__file__).resolve()),
   'chatml_render_function_ast_sha256':render_ast_hash,'prompt_semantics':'Exact original prior_study prompts.prompt and gguf_generate.render functions; selected document IDs are metadata only.',
   'model_calls':0,'tokenizer_calls':0,'network_calls':0,'no_token_fit_claim':'Every unique prompt still requires real generator-tokenizer preflight before any production generation.',
   'deduplication':'SHA-256 of exact complete ChatML UTF-8. Full strings checked equal whenever key reused. No response cache or output is read.',
   'clean_target_scope':'host.target is numeric bookkeeping only; per-attack abstention objectives must compare same clean response using that attack case objective.'}
  for k,v in metadata.items():con.execute('INSERT INTO preparation_metadata VALUES (?,?)',(k,stable(v)))
 con.commit()
 require(con.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite integrity failure')
 require(not con.execute('PRAGMA foreign_key_check').fetchall(),'SQLite foreign key failure')
 readback_rows=con.execute('SELECT COUNT(*) FROM requests').fetchone()[0];unique=con.execute('SELECT COUNT(*) FROM prompts').fetchone()[0]
 require(readback_rows==176400 and unique==56373 and duplicates==120027,'Unexpected independently computed exact prompt budget')
 require(con.execute('SELECT MIN(request_order),MAX(request_order) FROM requests').fetchone()==(1,176400),'Request ordinal coverage mismatch')
 stored_counts={(c,p):n for c,p,n in con.execute('SELECT condition,policy,COUNT(*) FROM requests GROUP BY condition,policy')}
 require(stored_counts==dict(counts),'Readback count mismatch')
 # Rehash stored full prompt bytes independently, without loading all strings.
 for key,chat,text,char_count,first_order in con.execute('SELECT * FROM prompts'):
  require(hashlib.sha256(chat.encode()).hexdigest()==key and len(chat)==char_count and render(text)==chat,'Stored full-prompt identity mismatch')
 require(all(sha(root/rel)==expected for rel,expected in source_hashes.items()),'Source bytes changed during preparation')
 con.close()
 with partial.open('rb')as f:os.fsync(f.fileno())
 partial.replace(dbpath)
 report={**metadata,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sqlite_file':'generation/input/generation_inputs.sqlite','sqlite_bytes':dbpath.stat().st_size,'sqlite_sha256':sha(dbpath),'unique_chat_prompts':unique,'exact_prompt_reused_request_rows':duplicates,
  'condition_policy_counts':[{'condition':c,'policy':p,'rows':n}for(c,p),n in sorted(counts.items())],
  'objective_condition_policy_counts':[{'condition':c,'objective':o,'policy':p,'rows':n}for(c,o,p),n in sorted(objective_counts.items())],
  'validation':{'sqlite_integrity_check':'ok','foreign_key_check_errors':0,'all_full_prompt_hashes_recomputed':unique,'request_id_and_case_condition_policy_unique_constraints':True,'all_inputs_rehashed_after_build':True,'all_source_test_questions_present':True,'no_calibration_questions_requested':True},
  'elapsed_seconds':time.monotonic()-start}
 tmp=manifestpath.with_suffix('.json.partial');tmp.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');tmp.replace(manifestpath)
 print(stable({k:report[k]for k in ('status','requested_rows','unique_chat_prompts','sqlite_bytes','sqlite_sha256','elapsed_seconds')}),flush=True)

if __name__=='__main__':main()
