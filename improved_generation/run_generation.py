"""Exploratory real-NQ generation follow-up; fresh frozen gates required.

Never imports uploaded scripts. Expects 2,800 prepared context rows with qid,
setting, gate, question, correct, incorrect, prompt, and selected context metadata.
"""
from pathlib import Path
import argparse,collections,csv,datetime,hashlib,json,os,platform,time
os.environ.setdefault('HF_HUB_OFFLINE','1')
os.environ.setdefault('TRANSFORMERS_OFFLINE','1')
os.environ.setdefault('HF_HUB_DISABLE_TELEMETRY','1')
import numpy as np
import torch,transformers
from qwen_cpu import PinnedQwen
from scoring import score

HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
GATES=['none','rule','guard','ctx','fused','oracle','aug_fused'];SETTINGS=['none','poison','ignore','stealth']

def sha(data):return hashlib.sha256(data).hexdigest()
def stable(obj):return json.dumps(obj,sort_keys=True,ensure_ascii=False,separators=(',',':'))
def wilson(k,n):
 if not n:return [None,None]
 z=1.95996398454;p=k/n;den=1+z*z/n;mid=(p+z*z/(2*n))/den;rad=z*((p*(1-p)/n+z*z/(4*n*n))**.5)/den
 return [mid-rad,mid+rad]
def paired_ci(v):
 a=np.asarray(v,dtype=float);rng=np.random.default_rng(12)
 return np.quantile(rng.choice(a,size=(10000,len(a)),replace=True).mean(1),[.025,.975]).tolist()

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--input',type=Path,required=True);ap.add_argument('--output',type=Path,default=HERE/'output');args=ap.parse_args()
 args.output.mkdir(parents=True,exist_ok=True)
 rows=[json.loads(x) for x in args.input.read_text().splitlines() if x.strip()]
 targets_path=HERE/'inputs'/'targets.json';targets=json.loads(targets_path.read_text())
 assert len(targets)==100 and len(rows)==2800
 assert len({(r['qid'],r['gate'],r['setting']) for r in rows})==2800
 assert {r['qid'] for r in rows}==set(targets)
 assert {r['gate'] for r in rows}==set(GATES) and {r['setting'] for r in rows}==set(SETTINGS)
 for r in rows:
  assert r['correct']==targets[r['qid']]['correct'] and r['incorrect']==targets[r['qid']]['incorrect']
  assert r['question']==targets[r['qid']]['question']
  assert r['prompt'].startswith('You are a helpful assistant, below is a query from a user and some relevant contexts.')
  assert r['prompt'].endswith('\n\nQuery: '+r['question']+' \n\nAnswer:')
 rows.sort(key=lambda r:(int(r['qid'].removeprefix('test')),GATES.index(r['gate']),SETTINGS.index(r['setting'])))
 protocol_path=HERE/'protocol.json';protocol=json.loads(protocol_path.read_text())
 assert protocol['gates']==GATES and protocol['settings']==SETTINGS and protocol['n_requested_rows']==len(rows)
 assert sha(targets_path.read_bytes())==protocol['targets_sha256']
 model_manifest=HERE/'model_manifest.json';manifest=json.loads(model_manifest.read_text())
 assert manifest['repository']==protocol['model'] and manifest['revision']==protocol['revision']
 model_dir=HERE/'models'/'Qwen2.5-0.5B-Instruct'
 for f in manifest['files']:
  p=model_dir/f['file'];assert p.stat().st_size==f['bytes'] and sha(p.read_bytes())==f['sha256']
 model=PinnedQwen(threads=4,max_new_tokens=64)
 effective_config=model.model.generation_config.to_dict();effective_config.update(max_new_tokens=64,do_sample=False,pad_token_id=model.tokenizer.pad_token_id)
 config={'study_status':'exploratory follow-up after inspection of supplied outputs; no main-case prompt tuning','model':manifest['repository'],'revision':manifest['revision'],'model_manifest_sha256':sha(model_manifest.read_bytes()),'parameter_count':model.parameter_count,'dtype':'float32','device':'cpu','torch_version':torch.__version__,'transformers_version':transformers.__version__,'python_version':platform.python_version(),'threads':4,'inter_op_threads':1,'batch_size':4,'batch_order':'deduplicate chat prompt, then sort by unpadded token length and chat SHA256; fixed batches of4','decoding':effective_config,'system_message':'You are a helpful assistant.','max_new_tokens':64,'max_input_tokens':'no truncation; refuse input+64 beyond model max_position_embeddings','model_max_positions':model.max_positions,'seed':12,'protocol_sha256':sha(protocol_path.read_bytes()),'runner_code_sha256':sha(Path(__file__).read_bytes()),'scoring_code_sha256':sha((HERE/'scoring.py').read_bytes()),'model_code_sha256':sha((HERE/'qwen_cpu.py').read_bytes())}
 unique={}
 for r in rows:
  chat=model.render(r['prompt']);key=sha(chat.encode());r['chat_prompt_sha256']=key;r['prompt_sha256']=sha(r['prompt'].encode())
  if key not in unique:
   n=len(model.tokenizer.encode(chat,add_special_tokens=True,truncation=False));assert n+64<=model.max_positions
   unique[key]={'prompt':r['prompt'],'input_tokens':n}
 keys=sorted(unique,key=lambda k:(unique[k]['input_tokens'],k))
 all_chunks=[keys[i:i+4] for i in range(0,len(keys),4)]
 batch_for_key={k:sha(stable(chunk).encode()) for chunk in all_chunks for k in chunk}
 config.update(input_sha256=sha(args.input.read_bytes()),fixed_batch_assignment_sha256=sha(stable(all_chunks).encode()))
 config_sha=sha(stable(config).encode())
 metadata={'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'config':config,'config_sha256':config_sha,'input_file':str(args.input),'input_sha256':sha(args.input.read_bytes()),'targets_file_sha256':sha(targets_path.read_bytes()),'n_requested_rows':len(rows),'n_qids':100,'qids':sorted(targets,key=lambda s:int(s.removeprefix('test'))),'n_unique_prompts':len(unique),'batch_benchmark_sha256':sha((HERE/'batch_benchmark.json').read_bytes()),'hardware':{'platform':platform.platform(),'logical_cpu_count':os.cpu_count()}}
 (args.output/'run_manifest.json').write_text(json.dumps(metadata,indent=2))
 cache_path=args.output/'responses_cache.jsonl';cache={}
 if cache_path.exists():
  for line in cache_path.read_text().splitlines():
   if not line.strip():continue
   r=json.loads(line);assert r['config_sha256']==config_sha,'Refusing stale model/decoder/scorer cache.'
   assert sha(r['chat_prompt'].encode())==r['chat_prompt_sha256']
   k=r['chat_prompt_sha256'];assert k in unique and r['batch_id']==batch_for_key[k]
   if k in cache:
    for field in ['response','config_sha256','batch_id','chat_prompt','input_tokens','generated_tokens','truncated','hit_generation_cap']:
     assert cache[k][field]==r[field],'Conflicting duplicate cache record.'
   else:cache[k]=r
 pending_chunks=[chunk for chunk in all_chunks if any(k not in cache for k in chunk)]
 pending=[k for k in keys if k not in cache];start=time.perf_counter();executed=0
 with cache_path.open('a') as f:
  for batch_index,chunk in enumerate(pending_chunks):
   batch=model.generate_batch([unique[k]['prompt'] for k in chunk]);executed+=len(chunk)
   for k,answer in zip(chunk,batch):
    assert sha(answer['chat_prompt'].encode())==k and answer['input_tokens']==unique[k]['input_tokens']
    if k in cache:
     assert cache[k]['response']==answer['response'],'Same fixed batch produced different output on resume.'
     continue
    entry={'config_sha256':config_sha,'chat_prompt_sha256':k,'batch_id':sha(stable(chunk).encode()),**answer}
    cache[k]=entry;f.write(json.dumps(entry,ensure_ascii=False)+'\n')
   f.flush()
   print(f'{batch_index+1}/{len(pending_chunks)} fixed batches; {len(cache)}/{len(keys)} cached; elapsed {time.perf_counter()-start:.1f}s',flush=True)
 results=[]
 for r in rows:
  gen=cache[r['chat_prompt_sha256']]
  results.append({**r,**gen,**score(r['correct'],r['incorrect'],gen['response'])})
 (args.output/'raw_generations.jsonl').write_text('\n'.join(json.dumps(r,ensure_ascii=False) for r in results)+'\n')
 summary=[]
 for gate in GATES:
  clean={r['qid']:r for r in results if r['gate']==gate and r['setting']=='none'}
  for setting in SETTINGS:
   attacked={r['qid']:r for r in results if r['gate']==gate and r['setting']==setting};qids=metadata['qids'];n=len(qids)
   row={'gate':gate,'setting':setting,'n':n}
   for key in ['correct_exact','target_exact','correct_mention','target_mention','abstention','both_mentioned']:
    count=sum(attacked[q][key] for q in qids);row[key+'_count']=count;row[key+'_rate']=count/n
   c_nonhit=[q for q in qids if not clean[q]['target_mention']]
   row.update(clean_target_mention_count=sum(clean[q]['target_mention'] for q in qids),clean_nonhit_denominator=len(c_nonhit),new_target_count=sum(attacked[q]['target_mention'] for q in c_nonhit),new_target_rate=sum(attacked[q]['target_mention'] for q in c_nonhit)/len(c_nonhit) if c_nonhit else None,target_paired_difference=sum(int(attacked[q]['target_mention'])-int(clean[q]['target_mention']) for q in qids)/n,target_paired_bootstrap95=paired_ci([int(attacked[q]['target_mention'])-int(clean[q]['target_mention']) for q in qids]),correct_exact_paired_difference=sum(int(attacked[q]['correct_exact'])-int(clean[q]['correct_exact']) for q in qids)/n,target_mention_wilson95=wilson(row['target_mention_count'],n))
   summary.append(row)
 batch_times={cache[k]['batch_id']:cache[k]['batch_seconds'] for k in keys}
 metadata.update(n_recorded_batches=len(batch_times),recorded_inference_batch_seconds=sum(batch_times.values()),mean_allocated_seconds_per_unique_prompt=sum(batch_times.values())/len(keys),padded_input_tokens_max=max(cache[k]['padded_input_tokens'] for k in keys),completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),generation_wall_seconds=time.perf_counter()-start,n_new_executions=executed,n_new_unique_cache_entries=len(pending),n_cache_prompt_results=len(keys),n_truncated_rows=sum(r['truncated'] for r in results),n_generated_cap_rows=sum(r['hit_generation_cap'] for r in results),input_tokens_min=min(r['input_tokens'] for r in results),input_tokens_max=max(r['input_tokens'] for r in results),raw_generations_sha256=sha((args.output/'raw_generations.jsonl').read_bytes()))
 (args.output/'summary.json').write_text(json.dumps({'metadata':metadata,'results':summary},indent=2))
 with (args.output/'summary.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=summary[0]);w.writeheader();w.writerows(summary)
 print(json.dumps({'metadata':metadata,'results':summary},indent=2),flush=True)

if __name__=='__main__':main()
