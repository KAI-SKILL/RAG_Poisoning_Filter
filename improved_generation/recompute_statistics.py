"""Recompute planned paired statistics and transparent cost accounting; no LLM."""
from pathlib import Path
import argparse,collections,csv,hashlib,json,math
import numpy as np
HERE=Path(__file__).resolve().parent
GATES=['none','rule','guard','ctx','fused','oracle','aug_fused']
SETTINGS=['none','poison','ignore','stealth']

def exact_mcnemar(b,c):
 n=b+c
 return 1.0 if n==0 else min(1.0,2*sum(math.comb(n,k) for k in range(min(b,c)+1))/(2**n))
def bootstrap_ci(values):
 v=np.asarray(values,dtype=float);rng=np.random.default_rng(12)
 return np.quantile(rng.choice(v,size=(10000,len(v)),replace=True).mean(1),[.025,.975]).tolist()
def write_csv(path,rows):
 with path.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=HERE/'output');a=ap.parse_args()
 raw=a.output/'raw_generations.jsonl';rows=[json.loads(x) for x in raw.read_text().splitlines()]
 assert len(rows)==2800 and len({(r['qid'],r['gate'],r['setting']) for r in rows})==2800
 lookup={(r['gate'],r['setting'],r['qid']):r for r in rows};qids=sorted({r['qid'] for r in rows},key=lambda s:int(s.removeprefix('test')));assert len(qids)==100
 comparisons=[]
 for setting in SETTINGS[1:]:
  for gate in GATES[1:]:
   base=[lookup['none',setting,q] for q in qids];policy=[lookup[gate,setting,q] for q in qids]
   b=sum(x['target_mention'] and not y['target_mention'] for x,y in zip(base,policy));c=sum(not x['target_mention'] and y['target_mention'] for x,y in zip(base,policy))
   target=[int(x['target_mention'])-int(y['target_mention']) for x,y in zip(base,policy)]
   exact=[int(y['correct_exact'])-int(x['correct_exact']) for x,y in zip(base,policy)]
   mention=[int(y['correct_mention'])-int(x['correct_mention']) for x,y in zip(base,policy)]
   comparisons.append({'setting':setting,'policy':gate,'n_qids':100,'none_target_policy_not':b,'policy_target_none_not':c,'discordant_pairs':b+c,'mcnemar_exact_two_sided_p':exact_mcnemar(b,c),'target_reduction_none_minus_policy':float(np.mean(target)),'target_reduction_bootstrap95':bootstrap_ci(target),'reference_exact_change_policy_minus_none':float(np.mean(exact)),'reference_exact_change_bootstrap95':bootstrap_ci(exact),'reference_mention_change_policy_minus_none':float(np.mean(mention)),'reference_mention_change_bootstrap95':bootstrap_ci(mention)})
 assert len(comparisons)==18
 ordered=sorted(range(18),key=lambda i:comparisons[i]['mcnemar_exact_two_sided_p']);previous=0.
 for rank,i in enumerate(ordered):
  adjusted=min(1.,max(previous,(18-rank)*comparisons[i]['mcnemar_exact_two_sided_p']));previous=adjusted
  comparisons[i]['holm_adjusted_p']=adjusted;comparisons[i]['holm_reject_at_0_05']=adjusted<=.05
 primary=[]
 for setting in SETTINGS[1:]:
  base=[lookup['ctx',setting,q] for q in qids];policy=[lookup['fused',setting,q] for q in qids]
  b=sum(x['target_mention'] and not y['target_mention'] for x,y in zip(base,policy));c=sum(not x['target_mention'] and y['target_mention'] for x,y in zip(base,policy))
  target=[int(x['target_mention'])-int(y['target_mention']) for x,y in zip(base,policy)]
  exact=[int(y['correct_exact'])-int(x['correct_exact']) for x,y in zip(base,policy)]
  mention=[int(y['correct_mention'])-int(x['correct_mention']) for x,y in zip(base,policy)]
  primary.append({'setting':setting,'baseline':'ctx','policy':'fused','n_qids':100,'ctx_target_fused_not':b,'fused_target_ctx_not':c,'discordant_pairs':b+c,'mcnemar_exact_two_sided_p':exact_mcnemar(b,c),'target_reduction_ctx_minus_fused':float(np.mean(target)),'target_reduction_bootstrap95':bootstrap_ci(target),'reference_exact_change_fused_minus_ctx':float(np.mean(exact)),'reference_exact_change_bootstrap95':bootstrap_ci(exact),'reference_mention_change_fused_minus_ctx':float(np.mean(mention)),'reference_mention_change_bootstrap95':bootstrap_ci(mention)})
 previous=0.
 for rank,i in enumerate(sorted(range(3),key=lambda i:primary[i]['mcnemar_exact_two_sided_p'])):
  adjusted=min(1.,max(previous,(3-rank)*primary[i]['mcnemar_exact_two_sided_p']));previous=adjusted
  primary[i]['holm_adjusted_p']=adjusted;primary[i]['holm_reject_at_0_05']=adjusted<=.05
 # Every model prompt may serve multiple condition rows. Assigning first request
 # is an accounting convention, never a per-policy speed benchmark.
 owners={};conditions=collections.defaultdict(set);unique={}
 for r in rows:
  k=r['chat_prompt_sha256'];owners.setdefault(k,(r['gate'],r['setting']));conditions[k].add((r['gate'],r['setting']));unique[k]=r
 costs=[]
 for gate in GATES:
  for setting in SETTINGS:
   selected=[r for r in rows if r['gate']==gate and r['setting']==setting];keys={r['chat_prompt_sha256'] for r in selected};charged={k for k in keys if owners[k]==(gate,setting)}
   costs.append({'gate':gate,'setting':setting,'requested_rows':len(selected),'unique_prompt_results_used':len(keys),'shared_prompt_results_used':sum(len(conditions[k])>1 for k in keys),'global_prompt_executions_first_credited':len(charged),'allocated_inference_seconds_first_credited':sum(unique[k]['seconds'] for k in charged),'mean_allocated_inference_seconds_per_unique_result_used':float(np.mean([unique[k]['seconds'] for k in keys])),'input_tokens_min':min(r['input_tokens'] for r in selected),'input_tokens_max':max(r['input_tokens'] for r in selected),'generated_tokens_mean_including_eos':float(np.mean([r['generated_tokens'] for r in selected])),'at_generation_cap_rows':sum(r['at_generation_cap'] for r in selected),'stopped_by_cap_rows_without_eos':sum(r['hit_generation_cap'] for r in selected),'ended_with_eos_rows':sum(r['ended_with_eos'] for r in selected),'truncated_rows':sum(r['truncated'] for r in selected)})
 assert sum(r['global_prompt_executions_first_credited'] for r in costs)==len(unique)
 batch_times={r['batch_id']:r['batch_seconds'] for r in unique.values()}
 metadata={'analysis':'exploratory follow-up; statistics specified before main NQ generation','raw_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'analysis_code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'statistics_plan_amendment_sha256':hashlib.sha256((HERE/'statistics_plan_amendment.json').read_bytes()).hexdigest(),'bootstrap_replicates':10000,'bootstrap_seed':12,'bootstrap_unit':'whole qid, same resampling indices across policy and reference measures; conditional on this benchmark and model','mcnemar':'exact two-sided binomial conditional on discordant bounded-target-mention pairs','holm_family':'18 none-versus-policy target-mention tests; adjusted separately from the PRIMARY3 fused-versus-ctx tests across poison/ignore/stealth; no rounding before adjustment','n_unique_prompt_evaluations':len(unique),'n_unique_inference_batches':len(batch_times),'recorded_total_batch_inference_seconds':sum(batch_times.values()),'generated_cap_unique_prompts':sum(r['hit_generation_cap'] for r in unique.values()),'eos_unique_prompts':sum(r['ended_with_eos'] for r in unique.values()),'latency_accounting':'seconds per unique result is its measured batch time divided by batch size; first-request attribution partitions real global execution cost and is not a policy-specific latency estimate; reused results are not additional executions','reference_scope':'canonical historical single strings; exact/mention metrics do not establish semantic truth or current2026factuality'}
 (a.output/'policy_comparisons.json').write_text(json.dumps({'metadata':metadata,'results':comparisons},indent=2));write_csv(a.output/'policy_comparisons.csv',comparisons)
 (a.output/'primary_fused_vs_ctx.json').write_text(json.dumps({'metadata':metadata,'family':'PRIMARY3 fused versus ctx; separate Holm family','results':primary},indent=2));write_csv(a.output/'primary_fused_vs_ctx.csv',primary)
 (a.output/'condition_costs.json').write_text(json.dumps({'metadata':metadata,'results':costs},indent=2));write_csv(a.output/'condition_costs.csv',costs)
 summary_path=a.output/'summary.json';summary=json.loads(summary_path.read_text());summary.update(primary_fused_vs_ctx=primary,policy_comparisons=comparisons,condition_costs=costs,analysis_metadata=metadata);summary_path.write_text(json.dumps(summary,indent=2))
 print(json.dumps(metadata,indent=2))

if __name__=='__main__':main()
