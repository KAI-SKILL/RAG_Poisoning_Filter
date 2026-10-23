"""Independent whole-question bootstrap/exposure/NotInject arithmetic audit."""
from pathlib import Path
import json,collections
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'output/improved_experiment'
def read(p):return json.loads(Path(p).read_text())
def readl(p):return[json.loads(x)for x in Path(p).read_text().splitlines()if x.strip()]
def eq(a,b,name):assert np.allclose(a,b,rtol=0,atol=1e-12),(name,a,b)
bs=read(BASE/'bootstrap.json');pol=read(BASE/'policy_admission.json');methods=list(read(BASE/'protocol.json')['variants']);draws=np.random.default_rng(12).integers(0,100,size=(10000,100));weights=np.zeros((10000,100),dtype=np.int16);np.add.at(weights,(np.arange(10000)[:,None],draws),1)
report={'scope':'Independent re-summed question-cluster bootstrap using draw-count matrix; same10000 seed12 draws as declared','interval_scalars_verified':0,'settings_verified':0,'public_notinject':{}}
for suite,settings in bs['intervals'].items():
 rows=readl(BASE/f'predictions_{suite}.jsonl')
 for setting,mm in settings.items():
  rr=[r for r in rows if r['setting']==setting];qids=sorted({r['qid']for r in rr});qg={q:[r for r in rr if r['qid']==q]for q in qids};assert len(qids)==100
  pos=np.array([sum(r['label']for r in qg[q])for q in qids]);neg=20-pos
  tp=np.array([[sum(r['label']and r['blocked'][m]for r in qg[q])for m in methods]for q in qids]);fp=np.array([[sum(not r['label']and r['blocked'][m]for r in qg[q])for m in methods]for q in qids]);ctl=np.array([sum(r['family'].startswith('benign_')for r in qg[q])for q in qids]);cfp=np.array([[sum(r['family'].startswith('benign_')and r['blocked'][m]for r in qg[q])for m in methods]for q in qids])
  recall=(weights@tp)/np.maximum(1,weights@pos)[:,None];fpr=(weights@fp)/(weights@neg)[:,None];control=(weights@cfp)/np.maximum(1,weights@ctl)[:,None]
  for i,m in enumerate(methods):
   d=mm[m]
   if pos.sum():eq(np.quantile(recall[:,i],[.025,.975]),d['recall_ci95'],(suite,setting,m,'recallCI'));report['interval_scalars_verified']+=2
   eq(np.quantile(fpr[:,i],[.025,.975]),d['fpr_ci95'],(suite,setting,m,'FPRCI'));report['interval_scalars_verified']+=2
   if ctl.sum():eq(np.quantile(control[:,i],[.025,.975]),d['modified_control_fpr_ci95'],(suite,setting,m,'controlCI'));report['interval_scalars_verified']+=2
  for name,d in bs['paired'][suite][setting].items():
   a,b=name.split('_minus_');ai,bi=methods.index(a),methods.index(b)
   if pos.sum():eq(np.quantile(recall[:,ai]-recall[:,bi],[.025,.975]),d['recall_delta_ci95'],(suite,setting,name,'recallDelta'));report['interval_scalars_verified']+=2
   eq(np.quantile(fpr[:,ai]-fpr[:,bi],[.025,.975]),d['fpr_delta_ci95'],(suite,setting,name,'FPRDelta'));report['interval_scalars_verified']+=2
   if ctl.sum():eq(np.quantile(control[:,ai]-control[:,bi],[.025,.975]),d['modified_control_fpr_delta_ci95'],(suite,setting,name,'controlDelta'));report['interval_scalars_verified']+=2
  # Independently select topfive and count query exposure and slot capacity.
  gates=['none']+methods+['oracle'];counts=np.zeros((100,len(gates)));filled=np.zeros_like(counts)
  for qi,q in enumerate(qids):
   group=sorted(qg[q],key=lambda r:r['index'])
   for gi,g in enumerate(gates):
    selected=[r for r in group if (not r['label']if g=='oracle'else True if g=='none'else not r['blocked'][g])][:5];counts[qi,gi]=sum(r['label']for r in selected);filled[qi,gi]=len(selected)
  exposed=(counts>0).astype(float);eb=(weights@exposed)/100;cb=(weights@counts)/100;pm=pol['suites'][suite][setting]
  for gi,g in enumerate(gates):
   d=pm[g];assert d['attack_admitted_queries']==sum(exposed[:,gi]);eq(d['query_attack_admission_rate'],exposed[:,gi].mean(),(suite,setting,g,'admission'));eq(d['mean_adversarial_contexts'],counts[:,gi].mean(),(suite,setting,g,'contexts'));eq(d['malicious_slot_fraction_denom_500'],counts[:,gi].sum()/500,(suite,setting,g,'slots'));eq(d['mean_filled_contexts'],filled[:,gi].mean(),(suite,setting,g,'filled'));assert d['empty_query_contexts']==sum(filled[:,gi]==0);eq(d['query_attack_admission_ci95'],np.quantile(eb[:,gi],[.025,.975]),(suite,setting,g,'admissionCI'));eq(d['mean_adversarial_contexts_ci95'],np.quantile(cb[:,gi],[.025,.975]),(suite,setting,g,'contextCI'));report['interval_scalars_verified']+=4
  for name,d in pm['paired_differences'].items():
   a,b=name.split('_minus_');ai,bi=gates.index(a),gates.index(b);eq(d['query_admission_delta_ci95'],np.quantile(eb[:,ai]-eb[:,bi],[.025,.975]),(suite,setting,name,'admissiondeltaCI'));eq(d['mean_adv_contexts_delta_ci95'],np.quantile(cb[:,ai]-cb[:,bi],[.025,.975]),(suite,setting,name,'contextdeltaCI'));report['interval_scalars_verified']+=4
  report['settings_verified']+=1
# Public NotInject: unique texts, all five frozen threshold decisions and summaries.
ni=readl(BASE/'notinject_predictions.jsonl');ns=read(BASE/'notinject_results.json');assert len(ni)==339 and len({r['prompt']for r in ni})==339
cal=read(BASE/'calibration.json');taus=[r['threshold']for r in cal if r['variant']=='guard'];eq(taus,ns['thresholds'],'NIthresholds')
cache=BASE/'cache';texts=read(cache/'guard_ni_texts.json');arr=np.load(cache/'guard_ni.npy',mmap_mode='r');lookup={t:float(arr[i,0])for i,t in enumerate(texts)}
for r in ni:eq(r['risk'],lookup[r['prompt']],'NIfreshcache');assert r['blocked_by_fold']==[r['risk']>t for t in taus]
cohorts={'all':ni,'multilingual_category':[r for r in ni if r['category']=='Multilingual'],'other_category':[r for r in ni if r['category']!='Multilingual']}
for name,rows in cohorts.items():
 matrix=np.array([r['blocked_by_fold']for r in rows]);d=ns['cohorts'][name];assert d['unique_prompts']==len(rows);eq(d['fpr_by_fold'],matrix.mean(0),(name,'NIfoldFPR'));eq(d['mean_fold_fpr'],matrix.mean(),(name,'NImeanFPR'));eq(d['fixed_0_5_reference_fpr'],np.mean([r['risk']>=.5 for r in rows]),(name,'NIpoint5FPR'));report['public_notinject'][name]={'unique_prompts':len(rows),'fold_false_positive_counts':matrix.sum(0).tolist(),'mean_fold_fpr':float(matrix.mean())}
# Cross-fold document-ID overlap.
seen=collections.defaultdict(set);fold=read(BASE/'protocol.json')['fold_assignment']
for r in readl(BASE/'pools_main.jsonl'):
 if r['setting']=='none':
  for p in r['pool']:seen[p['id']].add(r['qid'])
expected={doc:sorted(qs)for doc,qs in seen.items()if len({fold[q]for q in qs})>1};doc=read(BASE/'document_overlap.json');assert expected==doc['cross_fold_document_ids'];report['cross_fold_document_ids']=expected
report['status']='passed';(ROOT/'improvement_audit/fresh_statistics_independent_audit.json').write_text(json.dumps(report,indent=2));print('FRESH STATISTICS AUDIT PASS',report)
