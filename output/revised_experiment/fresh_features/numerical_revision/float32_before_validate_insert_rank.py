#!/usr/bin/env python3
"""Verify pure-insertion top-K delivery against direct declared-corpus search.

Every case must include its original normal top-K candidates plus ALL inserted
records before truncation. The complete split corpus is independently scored by
matrix dot product. Both selections use those same fixed scores and stable
normal-original-order / insertion-append tie handling. Optionally compare the
actual feature-pipeline selected IDs too, exposing numerical rank differences.
"""
from pathlib import Path
import argparse,json
from run_features import doc_repr,digest_file,write,np

def load(p):
 t=Path(p).read_text();return json.loads(t)if t.lstrip().startswith('[')else[json.loads(s)for s in t.splitlines()if s.strip()]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--corpus',type=Path,required=True);p.add_argument('--case-pools',type=Path,required=True);p.add_argument('--embedding-cache',type=Path,action='append',required=True);p.add_argument('--actual-selected-pools',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--top-k',type=int,default=20);a=p.parse_args()
 corpus=load(a.corpus);cases=load(a.case_pools);byid={d['id']:d for d in corpus};assert len(byid)==len(corpus)
 E={};cfgs=[]
 for folder in a.embedding_cache:
  cfg=json.loads((folder/'cache/contriever_config.json').read_text());state=json.loads((folder/'cache/contriever_progress.json').read_text());texts=json.loads((folder/'cache/contriever_texts.json').read_text());assert state['done']==len(texts)
  arr=np.load(folder/'cache/contriever.npy',mmap_mode='r')
  if cfgs:assert cfg['model_manifest_sha256']==cfgs[0]['model_manifest_sha256']and cfg['max_tokens']==cfgs[0]['max_tokens']
  for i,t in enumerate(texts):
   if t in E:assert np.array_equal(E[t],arr[i]),'Same text/model has inconsistent cached vectors; cannot claim fixed scores.'
   E[t]=np.asarray(arr[i]).copy()
  cfgs.append({'path':str(folder),'model_manifest_sha256':cfg['model_manifest_sha256'],'max_tokens':cfg['max_tokens'],'array_sha256':digest_file(folder/'cache/contriever.npy')})
 actual={}
 if a.actual_selected_pools:
  actual_rows=load(a.actual_selected_pools)
  actual={(r['qid'],r['setting']):[p['id']for p in r['pool']]for r in actual_rows}
  assert len(actual)==len(actual_rows),'Duplicate actual case key'
 assert len({(r['qid'],r['setting'])for r in cases})==len(cases),'Duplicate input case key'
 checks=[]
 for r in cases:
  normals=[d for d in corpus if d['split']==r['split']];ni={d['id']:i for i,d in enumerate(normals)}
  base=[d for d in r['pool']if d['id']in byid];extra=[d for d in r['pool']if d['id']not in byid]
  assert len({d['id']for d in r['pool']})==len(r['pool'])
  for d in base:
   assert d['id']in ni,'Cross-split normal candidate'
   assert d['text']==byid[d['id']]['text']and d.get('title','')==byid[d['id']].get('title',''),'This validation supports insertion, not replacement/modification.'
  assert len(base)>=a.top_k,(r['qid'],r['setting'],'insufficient clean base')
  all_docs=normals+extra;D=np.stack([E[doc_repr(d)]for d in all_docs]);q=E[r['question']];scores=D@q
  # Stable ties: every original corpus passage precedes every appended insertion.
  full_order=np.argsort(-scores,kind='stable')[:a.top_k];full_ids=[all_docs[i]['id']for i in full_order]
  clean_top=np.argsort(-scores[:len(normals)],kind='stable')[:a.top_k]
  expected_base=[normals[i]['id']for i in clean_top]
  supplied_base=[d['id']for d in base]
  base_match=set(expected_base)==set(supplied_base)
  # Preserve original normal order for ties, even if input base is rank-sorted.
  subset_indices=sorted(ni[d['id']]for d in base)+list(range(len(normals),len(all_docs)))
  subset_order=sorted(subset_indices,key=lambda i:-float(scores[i]))[:a.top_k]
  subset_ids=[all_docs[i]['id']for i in subset_order]
  eq=full_ids==subset_ids
  if a.actual_selected_pools:assert (r['qid'],r['setting'])in actual,'Missing actual selected case'
  ar=actual.get((r['qid'],r['setting']))
  checks.append({'qid':r['qid'],'setting':r['setting'],'split':r['split'],'normal_corpus_size':len(normals),'inserted_records':len(extra),'normal_top20_matches_input':base_match,'direct_equals_top20_union_insert':eq,'actual_feature_ids_equal_direct':None if ar is None else ar==full_ids,'direct_selected_ids':full_ids,'subset_selected_ids':subset_ids})
 report={'status':'passed'if all(x['normal_top20_matches_input']and x['direct_equals_top20_union_insert']and x['actual_feature_ids_equal_direct']is not False for x in checks)else'failed','scope':'Pure insertion into unchanged declared split subcorpora, with fixed embeddings/scores and identical stable tie policy; no full-Wikipedia claim.','cases':len(checks),'top_k':a.top_k,'all_normal_top20_inputs_match':all(x['normal_top20_matches_input']for x in checks),'all_direct_and_union_selected_ids_identical':all(x['direct_equals_top20_union_insert']for x in checks),'actual_feature_comparison_supplied':bool(actual),'all_actual_selected_ids_match':None if not actual else all(x['actual_feature_ids_equal_direct']for x in checks),'corpus_sha256':digest_file(a.corpus),'case_pools_sha256':digest_file(a.case_pools),'script_sha256':digest_file(__file__),'embedding_caches':cfgs,'case_checks':checks}
 write(a.output,report);print(json.dumps({k:v for k,v in report.items()if k not in ('case_checks','embedding_caches')}),flush=True)
 if report['status']!='passed':raise SystemExit(1)
if __name__=='__main__':main()
