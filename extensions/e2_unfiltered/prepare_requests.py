"""Freeze matched unfiltered E2 requests without fitting or generating answers."""
from pathlib import Path
import argparse,collections,datetime,hashlib,importlib.util,json
HERE=Path(__file__).resolve().parent
def default_project():
 for p in HERE.parents:
  if (p/'revised_experiment/prompts.py').is_file():return p
 return HERE.parent/'Group9_Project'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def rows(path):return [json.loads(l)for l in path.read_text().splitlines()if l.strip()]
def stable(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def chat(prompt):return '<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\n'+prompt+'<|im_end|>\n<|im_start|>assistant\n'
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--project',type=Path,default=default_project(),help='Project root containing revised_experiment and output archives')
 parser.add_argument('--output',type=Path,default=HERE,help='Directory for requests and their frozen manifest')
 args=parser.parse_args();ROOT=args.project.resolve();OUT=args.output.resolve();OUT.mkdir(parents=True,exist_ok=True)
 pools_path=ROOT/'output/revised_experiment/fresh_features/pools_with_features.jsonl'
 existing_path=ROOT/'output/revised_experiment/selection/context_requests.jsonl'
 predictions_path=ROOT/'output/revised_experiment/selection/predictions.jsonl'
 cache_path=ROOT/'output/revised_experiment/generation/responses_cache.jsonl'
 pools=rows(pools_path);existing=rows(existing_path);predictions=rows(predictions_path);cache=rows(cache_path)
 prompts=load('frozen_prompts',ROOT/'revised_experiment/prompts.py')
 runner=load('frozen_runner',ROOT/'revised_experiment/gguf_generate.py')
 assert runner.render('test')==chat('test')
 settings=['benign_echo_1','benign_echo_5','benign_copy_1','benign_copy_5','counterfactual_5']
 selected=[p for p in pools if p['split']=='test'and p['setting']in settings]
 assert len(selected)==125
 qids=sorted({p['qid']for p in selected});assert len(qids)==25
 assert all(p['source_supported'] and p['e2_selected'] and len(p['pool'])==20 for p in selected)
 assert collections.Counter(p['setting']for p in selected)==dict.fromkeys(settings,25)
 pi={(r['qid'],r['setting'],r['index']):r for r in predictions}
 old={(r['qid'],r['setting'],r['gate']):r for r in existing}
 cache_keys={c['chat_prompt_sha256']:c for c in cache};assert len(cache_keys)==432
 run=json.loads((ROOT/'output/revised_experiment/generation/run_manifest.json').read_text())
 assert len({c['config_sha256']for c in cache})==1 and next(iter(cache_keys.values()))['config_sha256']==run['config_sha256']
 for c in cache:
  assert hashlib.sha256(c['chat_prompt'].encode()).hexdigest()==c['chat_prompt_sha256']
 out=[];reconstructed=0
 data_fields=['qid','question','split','source_group','title','source_title','answers','incorrect','source_supported','e2_selected']
 for pool in selected:
  qid,s=pool['qid'],pool['setting']
  # Independently reconstruct every retained filtered E2 request before adding
  # none. This binds our pool order, title handling and support metadata to the
  # actual executed input rather than only checking denominators.
  for m in ['ctx','no_guard','fused']:
   chosen=[d for i,d in enumerate(pool['pool'])if not pi[qid,s,i]['blocked']['1pct'][m]][:5]
   previous=old[qid,s,m]
   assert previous['context_ids']==[d['id']for d in chosen]
   assert previous['prompt']==prompts.prompt(pool['question'],chosen)
   assert previous['gold_retained']==any(d['id']==pool['gold_document_id']for d in chosen)
   assert previous['legitimate_support_retained']==any(d.get('legitimate_support',False)for d in chosen)
   assert previous['malicious_count']==sum(d.get('label',0)for d in chosen)
   assert all(previous[k]==pool[k]for k in data_fields)
   reconstructed+=1
  chosen=pool['pool'][:5]
  row={**{k:pool[k]for k in data_fields},'setting':s,'gate':'none','context_ids':[d['id']for d in chosen],
       'malicious_count':sum(d.get('label',0)for d in chosen),'gold_retained':any(d['id']==pool['gold_document_id']for d in chosen),
       'legitimate_support_retained':any(d.get('legitimate_support',False)for d in chosen),'empty_context':not chosen,
       'prompt':prompts.prompt(pool['question'],chosen),'working_point':'1pct'}
  assert (qid,s,'none')not in old
  out.append(row)
 # Match unchanged E1 clean and CF1 rows for all policies, retaining original
 # answers/references/targets. Baselines remain reused, not new execution rows.
 baseline_keys=[(qid,s,m)for qid in qids for s in ['clean','counterfactual_1']for m in ['none','ctx','no_guard','fused']]
 assert all(k in old for k in baseline_keys)
 for row in out:
  base=old[row['qid'],'clean','none']
  assert all(row[k]==base[k]for k in data_fields)
 keys={hashlib.sha256(chat(r['prompt']).encode()).hexdigest()for r in out}
 hits=keys&set(cache_keys);new=keys-set(cache_keys)
 before_qids={r['qid']for r in existing if r['e2_selected']};assert before_qids==set(qids)
 request_path=OUT/'requests.jsonl';request_path.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n'for r in out))
 (OUT/'baseline_keys.json').write_text(json.dumps([list(k)for k in baseline_keys],indent=2)+'\n')
 manifest={'status':'FROZEN_REQUESTS_NO_INFERENCE','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'role':'Post-hoc matched unfiltered E2 extension after original results; not original prespecified primary family',
    'conditions':settings,'requested_rows':len(out),'questions':len(qids),'unique_extension_chat_prompts':len(keys),
    'unique_cache_hits_among_extension_prompts':len(hits),'genuinely_new_unique_prompts_required':len(new),
    'all_cache_ancestor_entries':len(cache),'reused_e1_baseline_rows':len(baseline_keys),
    'existing_filtered_e2_rows_reconstructed_exactly':reconstructed,'model_inference_executed':False,
    'inputs_sha256':{str(p.relative_to(ROOT)):sha(p)for p in [pools_path,existing_path,predictions_path,cache_path,ROOT/'revised_experiment/prompts.py',ROOT/'revised_experiment/gguf_generate.py',ROOT/'revised_experiment/evaluate_new.py',ROOT/'revised_experiment/data/test_source_quality_audit.json']},
    'frozen_generation_config':run['config'],'frozen_generation_config_sha256':run['config_sha256'],
    'request_builder_sha256':sha(Path(__file__)), 'requests_sha256':sha(request_path),'new_unique_chat_prompt_sha256':sorted(new),'inherited_requested_prompt_sha256':sorted(hits),
    'e2_qids':qids,'grouping':'One question per article; same25qids preserved for each paired contrast'}
 (OUT/'request_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print(json.dumps({k:v for k,v in manifest.items()if k not in ['new_unique_chat_prompt_sha256','inherited_requested_prompt_sha256','e2_qids','inputs_sha256','frozen_generation_config']},indent=2))
if __name__=='__main__':main()
