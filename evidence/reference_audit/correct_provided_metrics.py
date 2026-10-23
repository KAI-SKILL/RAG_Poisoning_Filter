"""Independent reanalysis of supplied logs; does not execute archive code or any model."""
from pathlib import Path
import json,re,collections,csv,hashlib,math
import numpy as np
from scipy.stats import binomtest
ROOT=Path(__file__).resolve().parents[2];SRC=ROOT/'new_reference';OUT=Path(__file__).resolve().parent
def readl(p):return[json.loads(x)for x in p.read_text().splitlines()if x.strip()]
def norm(x):return re.sub(r'\s+',' ',str(x)).strip().lower().rstrip('.')
def hit(a,s):return norm(a)in norm(s)
def bounded(a,s):return bool(re.search(r'(?<!\w)'+re.escape(norm(a))+r'(?!\w)',norm(s)))
def exact(a,s):return norm(a)==norm(s)
def wilson(k,n):
 if not n:return(None,None)
 z=1.95996398454;p=k/n;den=1+z*z/n;m=(p+z*z/(2*n))/den;r=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
 return(max(0,m-r),min(1,m+r))
def writecsv(name,rows):
 with(OUT/name).open('w',newline='')as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
D={}
for folder in(SRC/'results'/'nq').glob('*_hf'):
 defense=folder.name.removesuffix('_hf')
 for p in folder.glob('*.jsonl'):D[defense,p.stem]={r['qid']:r for r in readl(p)}
metrics=[];cis=[]
for(defense,setting),rs in sorted(D.items()):
 clean=D[defense,'none'];qids=sorted(rs);n=len(qids);r={'provenance':'supplied_HF_tagged_logs_unverified_model','defense':defense,'setting':setting,'n':n}
 for method,fn in [('legacy',hit),('bounded',bounded),('exact',exact)]:
  attack=sum(fn(rs[q]['incorrect'],rs[q]['response'])for q in qids);base=sum(fn(clean[q]['incorrect'],clean[q]['response'])for q in qids);correct=sum(fn(rs[q]['correct'],rs[q]['response'])for q in qids);new=sum(fn(rs[q]['incorrect'],rs[q]['response'])and not fn(clean[q]['incorrect'],clean[q]['response'])for q in qids);resolved=sum(not fn(rs[q]['incorrect'],rs[q]['response'])and fn(clean[q]['incorrect'],clean[q]['response'])for q in qids)
  r.update({f'{method}_target_hits':attack,f'{method}_clean_target_hits':base,f'{method}_new_target_hits':new,f'{method}_resolved_target_hits':resolved,f'{method}_paired_net_target_change':new-resolved,f'{method}_correct_hits':correct,f'{method}_new_target_rate_of_previously_target_free':new/(n-base)if n>base else None})
  for metric,k in [('target_hit',attack),('correct_hit',correct),('new_target_hit',new)]:
   lo,hi=wilson(k,n);cis.append({'provenance':'supplied_unverified_model','defense':defense,'setting':setting,'match_rule':method,'metric':metric,'k':k,'n':n,'fraction':k/n,'wilson95_low':lo,'wilson95_high':hi,'interpretation':'descriptive fraction of selected100questions; no population/adaptive robustness claim'})
 r.update({'groups_with_attack_context':sum(x['n_adv_ctx']>0 for x in rs.values()),'adversarial_contexts_total':sum(x['n_adv_ctx']for x in rs.values()),'clean_contexts_total':sum(x['n_clean_ctx']for x in rs.values())})
 metrics.append(r)
writecsv('provided_corrected_metrics.csv',metrics);writecsv('provided_metric_intervals.csv',cis)
# Pairwise exact McNemar; retain full precision and apply Holm across comparisons in each match-rule/metric family.
mc=[]
for rule,fn in [('legacy',hit),('bounded',bounded),('exact',exact)]:
 for b in ['none','trust_rule','trust_guard','trust_ctx','oracle']:
  a='trust_fused'
  for setting in sorted({s for d,s in D}):
   aa=D[a,setting];bb=D[b,setting];label='correct'if setting=='none'else'incorrect';metric='correct_hit'if setting=='none'else'target_hit';qs=sorted(set(aa)&set(bb));ao=sum(fn(aa[q][label],aa[q]['response'])and not fn(bb[q][label],bb[q]['response'])for q in qs);bo=sum(fn(bb[q][label],bb[q]['response'])and not fn(aa[q][label],aa[q]['response'])for q in qs);p=binomtest(ao,ao+bo,.5).pvalue if ao+bo else 1.
   mc.append({'provenance':'supplied_unverified_model','match_rule':rule,'metric':metric,'setting':setting,'defense_a':a,'defense_b':b,'n_pairs':len(qs),'a_only':ao,'b_only':bo,'two_sided_exact_p':p,'holm_adjusted_p':None,'holm_family':'match_rule+metric across allsettings and reference defenses'})
for rule in ['legacy','bounded','exact']:
 for metric in ['correct_hit','target_hit']:
  inds=[i for i,r in enumerate(mc)if r['match_rule']==rule and r['metric']==metric];order=sorted(inds,key=lambda i:mc[i]['two_sided_exact_p']);running=0
  for rank,i in enumerate(order):running=max(running,min(1.,(len(order)-rank)*mc[i]['two_sided_exact_p']));mc[i]['holm_adjusted_p']=running
writecsv('provided_paired_statistics.csv',mc)
# Duplicate prompts and inconsistent responses, fully retained for forensic reproducibility.
prompts=collections.defaultdict(list)
for(d,s),rs in D.items():
 for q,r in rs.items():prompts[r['prompt']].append({'defense':d,'setting':s,'qid':q,'response':r['response']})
conflicts=[{'prompt_sha256':hashlib.sha256(p.encode()).hexdigest(),'prompt':p,'occurrences':rows}for p,rows in prompts.items()if len({r['response']for r in rows})>1]
(OUT/'provided_prompt_conflicts.json').write_text(json.dumps(conflicts,indent=2,ensure_ascii=False))
# Reconstruct step6 fold assignment independently. Evaluate IDs, exact texts, and normalized question overlap.
T=json.loads((SRC/'data'/'nq'/'targets.json').read_text());qids=sorted(T);np.random.default_rng(12).shuffle(qids);fold={q:i%5 for i,q in enumerate(qids)};maps={q:{'all_doc_ids':set(),'clean_doc_ids':set(),'all_texts':set(),'clean_texts':set()}for q in qids}
for p in(SRC/'data'/'nq'/'retrieved').glob('*.jsonl'):
 for r in readl(p):
  for d in r['pool']:
   m=maps[r['qid']];m['all_doc_ids'].add(d['doc_id']);m['all_texts'].add(d['text'])
   if not d['is_adv']:m['clean_doc_ids'].add(d['doc_id']);m['clean_texts'].add(d['text'])
foldrows=[]
for f in range(5):
 test=[q for q in qids if fold[q]==f];val=[q for q in qids if fold[q]==(f+1)%5];train=[q for q in qids if fold[q]not in[f,(f+1)%5]];row={'test_fold':f,'n_train_qids':len(train),'n_val_qids':len(val),'n_test_qids':len(test),'train_test_qid_overlap':len(set(train)&set(test)),'train_test_normalized_question_overlap':len({norm(T[q]['question'])for q in train}&{norm(T[q]['question'])for q in test})}
 for feature in ['all_doc_ids','clean_doc_ids','all_texts','clean_texts']:
  a=set().union(*(maps[q][feature]for q in train));b=set().union(*(maps[q][feature]for q in test));over=a&b;row['train_test_overlap_'+feature]=len(over)
  if feature.endswith('doc_ids'):row['overlapping_'+feature]='|'.join(sorted(over))
  row['test_qids_affected_'+feature]=sum(bool(maps[q][feature]&a)for q in test)
 foldrows.append(row)
writecsv('provided_fold_document_overlap.csv',foldrows)
print('Created corrected metrics, Wilson intervals, exact paired statistics, conflict detail, fold document overlap.')
for r in foldrows:print(r)
for r in mc:
 if r['match_rule']=='bounded'and r['defense_b']=='trust_ctx'and r['setting']in['poison','stealth']:print('FUSEDvsCTX',r)
