"""Tokenize every frozen full prompt; perform no language-model generation."""
from pathlib import Path
import argparse,hashlib,json,sqlite3,time,os

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--input',type=Path,required=True);p.add_argument('--model',type=Path,required=True)
 p.add_argument('--output',type=Path,required=True);p.add_argument('--context',type=int,default=4096)
 p.add_argument('--max-new-tokens',type=int,default=48);a=p.parse_args()
 import llama_cpp
 if a.output.exists():raise SystemExit('Refusing overwrite of token preflight; use a new output')
 a.output.parent.mkdir(parents=True,exist_ok=True);temporary=a.output.with_suffix(a.output.suffix+'.partial')
 if temporary.exists():temporary.unlink()
 source=sqlite3.connect('file:'+str(a.input.resolve())+'?mode=ro',uri=True)
 target=sqlite3.connect(temporary);target.execute('CREATE TABLE tokens(prompt_sha256 TEXT PRIMARY KEY,prompt_tokens INTEGER NOT NULL)')
 start=time.monotonic();llm=llama_cpp.Llama(model_path=str(a.model),vocab_only=True,n_ctx=a.context,n_gpu_layers=0,verbose=False)
 counts=[];bad=[]
 for i,(key,chat)in enumerate(source.execute('SELECT prompt_sha256,chat_prompt FROM prompts ORDER BY first_request_order'),1):
  assert hashlib.sha256(chat.encode()).hexdigest()==key
  n=len(llm.tokenize(chat.encode(),add_bos=False,special=True));counts.append(n)
  target.execute('INSERT INTO tokens VALUES(?,?)',(key,n))
  if n+a.max_new_tokens>a.context:bad.append({'prompt_sha256':key,'tokens':n})
  if i%2000==0:target.commit();print(json.dumps({'tokenized':i,'elapsed_seconds':round(time.monotonic()-start,2),'maximum':max(counts)}),flush=True)
 expected=source.execute('SELECT count(*) FROM prompts').fetchone()[0];assert len(counts)==expected
 target.commit();assert target.execute('PRAGMA integrity_check').fetchone()[0]=='ok';target.close();temporary.replace(a.output)
 ordered=sorted(counts)
 receipt={'status':'PASS_ALL_FULL_PROMPTS_FIT'if not bad else 'FAIL_OVERFLOW','input_sqlite_sha256':sha(a.input),'token_file_sha256':sha(a.output),'tokenizer_runtime':'llama-cpp-python '+llama_cpp.__version__,'producer_sha256':sha(__file__),'model_sha256':sha(a.model),'unique_prompts':expected,'context_tokens':a.context,'maximum_new_tokens':a.max_new_tokens,'input_tokens_min':min(counts),'input_tokens_median':ordered[len(ordered)//2],'input_tokens_p95':ordered[int(.95*(len(ordered)-1))],'input_tokens_max':max(counts),'overflow_count':len(bad),'overflow_prompts':bad,'add_bos':False,'parse_special':True,'generation_calls':0,'elapsed_seconds':time.monotonic()-start,'truncation_permitted':False}
 a.output.with_suffix('.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
 if bad:raise SystemExit(1)
if __name__=='__main__':main()
