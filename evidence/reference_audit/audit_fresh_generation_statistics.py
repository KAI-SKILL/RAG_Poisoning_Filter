"""Read-only independent paired-statistics/cost audit, no generator execution."""
from pathlib import Path
import json,hashlib,collections,sys
import numpy as np
from scipy.stats import binomtest
ROOT=Path(__file__).resolve().parents[1]
BASE=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'improved_generation/output'
def read(p):return json.loads(p.read_text())
rows=[json.loads(l)for l in(BASE/'raw_generations.jsonl').read_text().splitlines()if l.strip()]
lookup={(r['gate'],r['setting'],r['qid']):r for r in rows}
qids=sorted({r['qid']for r in rows},key=lambda s:int(s.removeprefix('test')))
assert len(rows)==2800 and len(lookup)==2800 and len(qids)==100
idx=np.random.default_rng(12).integers(0,100,(10000,100))
def close(a,b,label):assert np.allclose(a,b,rtol=0,atol=1e-11),(label,a,b)
def ci(v):return np.quantile(np.asarray(v,dtype=float)[idx].mean(axis=1),[.025,.975])
def audit_family(filename,basegate,bcname,cbname,delta_suffix,utility_suffix):
 d=read(BASE/filename);out=[]
 for r in d['results']:
  setting=r['setting'];gate=r['policy'];x=[lookup[basegate,setting,q]for q in qids];y=[lookup[gate,setting,q]for q in qids]
  b=sum(a['target_mention']and not c['target_mention']for a,c in zip(x,y));c=sum(not a['target_mention']and z['target_mention']for a,z in zip(x,y));p=binomtest(b,b+c,.5).pvalue if b+c else 1.
  assert r[bcname]==b and r[cbname]==c and r['discordant_pairs']==b+c and r['n_qids']==100
  close(r['mcnemar_exact_two_sided_p'],p,(filename,setting,gate,'p'))
  for score,delta_key,ci_key in [('target_mention','target_reduction_'+delta_suffix,'target_reduction_bootstrap95'),('correct_exact','reference_exact_change_'+utility_suffix,'reference_exact_change_bootstrap95'),('correct_mention','reference_mention_change_'+utility_suffix,'reference_mention_change_bootstrap95')]:
   v=np.array([int(a[score])-int(z[score])for a,z in zip(x,y)])*(1 if score=='target_mention'else-1)
   close(r[delta_key],v.mean(),(filename,setting,gate,delta_key));close(r[ci_key],ci(v),(filename,setting,gate,ci_key))
  out.append((r,p))
 order=sorted(range(len(out)),key=lambda i:out[i][1]);prev=0.
 for rank,i in enumerate(order):
  r,p=out[i];adj=min(1.,max(prev,(len(out)-rank)*p));prev=adj;close(r['holm_adjusted_p'],adj,(filename,'holm'));assert r['holm_reject_at_0_05']==(adj<=.05)
 assert d['metadata']['raw_sha256']==hashlib.sha256((BASE/'raw_generations.jsonl').read_bytes()).hexdigest()
 return [{'setting':r['setting'],'policy':r['policy'],'b':r[bcname],'c':r[cbname],'p':p,'holm':r['holm_adjusted_p']}for r,p in out]
primary=audit_family('primary_fused_vs_ctx.json','ctx','ctx_target_fused_not','fused_target_ctx_not','ctx_minus_fused','fused_minus_ctx')
secondary=audit_family('policy_comparisons.json','none','none_target_policy_not','policy_target_none_not','none_minus_policy','policy_minus_none')
assert len(primary)==3 and len(secondary)==18
costs=read(BASE/'condition_costs.json');uni={};conditions=collections.defaultdict(set);owner={}
for r in rows:
 k=r['chat_prompt_sha256'];uni[k]=r;conditions[k].add((r['gate'],r['setting']));owner.setdefault(k,(r['gate'],r['setting']))
assert len(uni)==668
for c in costs['results']:
 pair=c['gate'],c['setting'];sel=[r for r in rows if(r['gate'],r['setting'])==pair];keys={r['chat_prompt_sha256']for r in sel};charged=[k for k in keys if owner[k]==pair]
 counts={'requested_rows':len(sel),'unique_prompt_results_used':len(keys),'shared_prompt_results_used':sum(len(conditions[k])>1 for k in keys),'global_prompt_executions_first_credited':len(charged),'input_tokens_min':min(r['input_tokens']for r in sel),'input_tokens_max':max(r['input_tokens']for r in sel),'at_generation_cap_rows':sum(r['at_generation_cap']for r in sel),'stopped_by_cap_rows_without_eos':sum(r['hit_generation_cap']for r in sel),'ended_with_eos_rows':sum(r['ended_with_eos']for r in sel),'truncated_rows':sum(r['truncated']for r in sel)}
 for k,v in counts.items():assert c[k]==v,(pair,k,c[k],v)
 close(c['allocated_inference_seconds_first_credited'],sum(uni[k]['seconds']for k in charged),(pair,'seconds'));close(c['mean_allocated_inference_seconds_per_unique_result_used'],np.mean([uni[k]['seconds']for k in keys]),(pair,'meanseconds'));close(c['generated_tokens_mean_including_eos'],np.mean([r['generated_tokens']for r in sel]),(pair,'tokens'))
batches={r['batch_id']:r['batch_seconds']for r in uni.values()};assert len(batches)==167
close(sum(c['allocated_inference_seconds_first_credited']for c in costs['results']),sum(batches.values()),'costpartition');assert sum(c['global_prompt_executions_first_credited']for c in costs['results'])==668
result={'status':'passed','input_directory':str(BASE),'primary3':primary,'secondary18':secondary,'cost_conditions':len(costs['results']),'unique_prompts':len(uni),'unique_batches':len(batches),'total_batch_seconds':sum(batches.values()),'cap_unique_prompts':sum(r['hit_generation_cap']for r in uni.values()),'cap_requested_rows':sum(r['hit_generation_cap']for r in rows),'interpretation':'No primary Holm rejection; lower target mentions relative to no filtering do not imply fusion superiority over context or semantic answer accuracy.'}
name='fresh_generation_statistics_independent_audit.json'if BASE.name=='output'else BASE.name+'_statistics_independent_audit.json'
(ROOT/'improvement_audit'/name).write_text(json.dumps(result,indent=2));print('PASS',name,len(primary),len(secondary),len(costs['results']))
