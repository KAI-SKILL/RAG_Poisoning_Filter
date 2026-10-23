"""Pinned CPU GGUF generation with exact-prompt deduplication and guarded resume.

Install the optional requirements in this directory, then pass --model and
--input JSONL. This never overwrites the archived 0.5B execution.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,os,platform,time,sys
try:
 import resource
except ImportError:
 resource=None

def peak_rss_kib():
 if resource is None:return None
 x=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
 return int(x/1024) if sys.platform=="darwin" else int(x)

def sha(b):return hashlib.sha256(b).hexdigest()
def stable(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def render(prompt):return '<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\n'+prompt+'<|im_end|>\n<|im_start|>assistant\n'
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--model',type=Path,required=True);p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--threads',type=int,default=6);p.add_argument('--limit',type=int);a=p.parse_args()
 import llama_cpp
 a.output.mkdir(parents=True,exist_ok=True)
 manifest=json.loads((a.model.parent/'manifest.json').read_text())
 expected=next(x['sha256'] for x in manifest['files'] if x['file']==a.model.name)
 actual=hashlib.file_digest(a.model.open('rb'),'sha256').hexdigest();assert actual==expected,'GGUF bytes differ from immutable upstream hash'
 rows=[json.loads(l) for l in a.input.read_text().splitlines() if l.strip()]
 if a.limit:rows=rows[:a.limit]
 config={'model_repository':manifest['repository'],'revision':manifest['revision'],'weights_sha256':actual,'quantization':'Q4_K_M','llama_cpp_python':llama_cpp.__version__,'context_length':4096,'max_new_tokens':48,'threads':a.threads,'temperature':0.0,'top_k':0,'top_p':1.0,'repeat_penalty':1.0,'seed':12,'system_message':'You are a helpful assistant.','prompt_render':'Qwen ChatML explicit template','runner_sha256':sha(Path(__file__).read_bytes()),'python_version':platform.python_version(),'platform_system':platform.system(),'machine':platform.machine()}
 config_hash=sha(stable(config).encode());cache_path=a.output/'responses_cache.jsonl';cache={}
 if cache_path.exists():
  for l in cache_path.read_text().splitlines():
   r=json.loads(l);assert r['config_sha256']==config_hash,'Refusing stale resume configuration';assert sha(r['chat_prompt'].encode())==r['chat_prompt_sha256'];cache[r['chat_prompt_sha256']]=r
 unique={sha(render(r['prompt']).encode()):render(r['prompt']) for r in rows}
 start=time.monotonic();llm=llama_cpp.Llama(model_path=str(a.model),n_ctx=4096,n_threads=a.threads,n_threads_batch=a.threads,n_batch=512,n_ubatch=128,seed=12,verbose=False,n_gpu_layers=0)
 token_counts={key:len(llm.tokenize(chat.encode(),add_bos=False,special=True))for key,chat in unique.items()}
 assert all(n+48<=4096 for n in token_counts.values()),('Refuse truncation before any generation',max(token_counts.values()))
 metadata={'max_preflight_input_tokens':max(token_counts.values()),'all_prompts_fit_context':True,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'config':config,'config_sha256':config_hash,'input_sha256':sha(a.input.read_bytes()),'requested_rows':len(rows),'unique_prompts':len(unique),'cached_before_run':len(cache),'platform':platform.platform(),'logical_cpus':os.cpu_count(),'host_memory_limit_note':'Peak RSS is measured only when the platform resource API is available. This is not a measured Windows16GB deployment guarantee.'}
 (a.output/'run_manifest.json').write_text(json.dumps(metadata,indent=2))
 with cache_path.open('a') as f:
  for i,(key,chat) in enumerate(unique.items(),1):
   if key in cache:continue
   assert token_counts[key]+48<=4096
   t=time.monotonic();result=llm(chat,max_tokens=48,temperature=0,top_k=0,top_p=1.0,repeat_penalty=1.0,seed=12,stop=['<|im_end|>','<|endoftext|>'],echo=False)
   entry={'config_sha256':config_hash,'chat_prompt_sha256':key,'chat_prompt':chat,'response':result['choices'][0]['text'].strip(),'finish_reason':result['choices'][0]['finish_reason'],'usage':result['usage'],'seconds':time.monotonic()-t,'peak_rss_kib':peak_rss_kib(),'executed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'truncated':False}
   cache[key]=entry;f.write(json.dumps(entry,ensure_ascii=False)+'\n');f.flush()
   print(json.dumps({'completed':i,'unique_total':len(unique),'elapsed_s':round(time.monotonic()-start,2),'last_seconds':round(entry['seconds'],2),'qid':[r.get('qid') for r in rows if sha(render(r['prompt']).encode())==key][:1]}),flush=True)
 results=[{**r,**cache[sha(render(r['prompt']).encode())]} for r in rows]
 (a.output/'raw_generations.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in results))
 metadata.update(completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),elapsed_seconds=time.monotonic()-start,peak_rss_kib=peak_rss_kib(),completed_rows=len(results),completed_unique_prompts=len(unique))
 (a.output/'run_manifest.json').write_text(json.dumps(metadata,indent=2))
 print(json.dumps({'complete':True,'rows':len(results),'unique_prompts':len(unique),'elapsed_seconds':metadata['elapsed_seconds'],'peak_rss_kib':metadata['peak_rss_kib']}),flush=True)
if __name__=='__main__':main()
