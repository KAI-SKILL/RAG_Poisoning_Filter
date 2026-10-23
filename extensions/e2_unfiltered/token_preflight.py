"""Hash-check weights and tokenize extension inputs without model inference."""
from pathlib import Path
import argparse,collections,hashlib,json,platform,statistics,sys,time
HERE=Path(__file__).resolve().parent
def default_project():
 for p in HERE.parents:
  if (p/'revised_experiment/prompts.py').is_file():return p
 raise ValueError('Pass --project for the project root')

def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def chat(prompt):return '<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\n'+prompt+'<|im_end|>\n<|im_start|>assistant\n'
def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--project',type=Path,default=default_project())
 parser.add_argument('--model',type=Path,required=True,help='Official hash-verified Qwen GGUF model; not bundled')
 parser.add_argument('--runtime-dir',type=Path,help='Optional directory containing an external installed llama_cpp package')
 parser.add_argument('--requests',type=Path,default=HERE/'requests.jsonl')
 parser.add_argument('--request-manifest',type=Path,default=HERE/'request_manifest.json')
 parser.add_argument('--output',type=Path,default=HERE/'token_preflight.json')
 args=parser.parse_args();ROOT=args.project.resolve()
 if args.runtime_dir:sys.path.insert(0,str(args.runtime_dir.resolve()))
 import llama_cpp
 request_manifest=json.loads(args.request_manifest.read_text());cfg=request_manifest['frozen_generation_config']
 assert llama_cpp.__version__==cfg['llama_cpp_python']
 assert platform.python_version()==cfg['python_version'] and platform.system()==cfg['platform_system'] and platform.machine()==cfg['machine']
 model=args.model.resolve()
 start=time.monotonic();actual=sha(model);assert actual==cfg['weights_sha256']
 model_hash_seconds=time.monotonic()-start
 # vocab_only skips neural forward passes; it only loads tokenizer metadata.
 llm=llama_cpp.Llama(model_path=str(model),vocab_only=True,n_ctx=4096,n_gpu_layers=0,verbose=False)
 rows=[json.loads(l)for l in args.requests.read_text().splitlines()if l.strip()]
 tokens=[]
 for r in rows:
  n=len(llm.tokenize(chat(r['prompt']).encode(),add_bos=False,special=True))
  assert n+48<=4096
  tokens.append({'qid':r['qid'],'setting':r['setting'],'chat_prompt_sha256':hashlib.sha256(chat(r['prompt']).encode()).hexdigest(),'input_tokens':n})
 llm.close()
 existing=[json.loads(l)for l in (ROOT/'output/revised_experiment/generation/raw_generations.jsonl').read_text().splitlines()if l.strip()]
 qids=set(request_manifest['e2_qids']);prior=[r for r in existing if r['qid']in qids and r['gate']=='none'and r['setting']in ['clean','counterfactual_1']]
 assert len(prior)==50
 unique={r['chat_prompt_sha256']:r for r in prior};assert len(unique)==50
 times=[r['seconds']for r in unique.values()];oldtoken=[r['usage']['prompt_tokens']for r in unique.values()]
 config={**cfg,'runner_sha256':sha(ROOT/'revised_experiment/gguf_generate.py'),'python_version':platform.python_version(),'platform_system':platform.system(),'machine':platform.machine()}
 stable=lambda x:json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
 confighash=hashlib.sha256(stable(config).encode()).hexdigest();assert confighash==request_manifest['frozen_generation_config_sha256']
 out={'status':'PASSED_TOKENIZATION_ONLY_NO_GENERATION','model_inference_executed':False,'vocab_only':True,'weights_sha256':actual,'model_hash_check_seconds':model_hash_seconds,'python_version':platform.python_version(),'llama_cpp_python':llama_cpp.__version__,'generation_config_would_match_frozen_sha256':confighash,'requests':125,'unique_prompts':125,'existing_prompt_cache_hits':0,'context_length':4096,'max_new_tokens':48,'min_input_tokens':min(t['input_tokens']for t in tokens),'max_input_tokens':max(t['input_tokens']for t in tokens),'mean_input_tokens':statistics.mean(t['input_tokens']for t in tokens),'all_prompts_fit_without_truncation':True,'prior_matched_none_baselines':{'unique_prompts':50,'mean_seconds':statistics.mean(times),'median_seconds':statistics.median(times),'min_seconds':min(times),'max_seconds':max(times),'mean_prompt_tokens':statistics.mean(oldtoken)},'rough_seconds_at_prior_matched_mean':125*statistics.mean(times),'runtime_estimate_scope':'Approximation from prior same25questions none-clean/CF1 unique executions on the same recorded CPU environment; not a new measurement or promise. New prompt lengths and shared-host load can change time.','per_request_tokens':tokens,'token_preflight_code_sha256':sha(Path(__file__)), 'request_file_sha256':sha(args.requests), 'request_manifest_sha256':sha(args.request_manifest), 'runtime_library_sha256':{p.name:sha(p)for p in sorted((Path(llama_cpp.__file__).resolve().parent/'lib').glob('*.so'))}}
 args.output.parent.mkdir(parents=True,exist_ok=True)
 args.output.write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps({k:v for k,v in out.items()if k not in ['per_request_tokens','runtime_library_sha256']},indent=2))
if __name__=='__main__':main()
