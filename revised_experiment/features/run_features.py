#!/usr/bin/env python3
"""Pinned local Contriever/DeBERTa features for arbitrary declared candidate pools.

Input JSONL rows: {qid, question, setting, split?, source_group?, pool:[
{id, title?, text, label?, family?} ...]}. Other row fields are retained.
Candidate ranking is recomputed with title+text, stable descending, top K.
No fitted classifier, attack generation, or dataset selection occurs here.
"""
from __future__ import annotations
import argparse,gc,hashlib,json,os,platform,re,sys,time
from pathlib import Path
BASE=Path(__file__).resolve().parent
# Project-private dependencies never alter the host interpreter or other tasks.
PRIVATE=BASE.parent/'encoder_runtime'
if PRIVATE.exists():sys.path.insert(0,str(PRIVATE))
os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
os.environ['HF_HUB_DISABLE_TELEMETRY']='1';os.environ['TOKENIZERS_PARALLELISM']='false'
import numpy as np
RULES=[r'\b(ignore|disregard|forget)\b.{0,30}\b(previous|prior|above|earlier|all|context|instructions?)\b',r'\binstructions?\b',r'\btask\s+(is\s+)?(complete|completed|done|finished|fulfilled)\b',r'\bnew task\b',r'\byou must\b',r'\bplease output\b',r'\brespond with\b',r'\bwhen you are asked\b',r'^\s*answer\s*:',r'\b(void|irrelevant)\b']
PATTERNS=[re.compile(p,re.I|re.M)for p in RULES]
FEATURES=['guard','rule','score_z','density']

def digest_file(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def sha(s):return hashlib.sha256(s.encode('utf-8')).hexdigest()
def write(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 temp=p.with_suffix(p.suffix+'.tmp');temp.write_text(json.dumps(x,ensure_ascii=False,indent=2,default=lambda v:sorted(v)if isinstance(v,set)else str(v))+'\n');temp.replace(p)
def jsonl(p,rows):Path(p).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n'for r in rows))
def read_rows(p):
 text=Path(p).read_text()
 rows=json.loads(text) if text.lstrip().startswith('[') else [json.loads(s)for s in text.splitlines()if s.strip()]
 if not rows:raise ValueError('No input rows')
 for r in rows:
  assert r.get('qid') and r.get('question') and r.get('setting') and r.get('pool'),r.keys()
  assert all(isinstance(p.get('text'),str)and p['text'].strip()and p.get('id')for p in r['pool'])
 return rows
def doc_repr(p):return (p.get('title','')+' '+p['text']).strip()
def relevance_scores(document_vectors,query_vector):
 # Fixed axis reduction in float64 makes identical vectors have identical scores
 # regardless of BLAS matrix shape or row position. No tolerance/tie rounding.
 d=np.asarray(document_vectors,dtype=np.float64)
 q=np.asarray(query_vector,dtype=np.float64)
 return np.sum(d*q[None,:],axis=1,dtype=np.float64)
def collect(rows):
 embed=set();guard=set()
 for r in rows:
  embed.add(r['question'])
  for p in r['pool']:
   embed.update((doc_repr(p),p['text']));guard.add(p['text'])
 return sorted(embed,key=lambda t:(len(t),t)),sorted(guard,key=lambda t:(len(t),t))
def verify_model(kind):
 root=BASE/'models'/kind; spec=json.loads((root/'model_manifest.json').read_text())
 for filename,meta in spec['downloaded_files'].items():
  p=root/filename
  assert p.stat().st_size==meta['bytes'],(kind,filename,'size')
  assert digest_file(p)==meta['sha256'],(kind,filename,'sha256')
 return root,spec

def infer(texts,kind,out,threads=4,batch=12,max_tokens=512):
 begin_wall=time.perf_counter()
 import torch,transformers
 from transformers import AutoTokenizer,AutoModel,AutoModelForSequenceClassification
 root,spec=verify_model(kind);is_guard=kind=='guard'
 cache=out/'cache';cache.mkdir(parents=True,exist_ok=True)
 cfg={'kind':kind,'model_repository':spec.get('repo'),'model_revision':spec['revision'],'model_manifest_sha256':digest_file(root/'model_manifest.json'),'text_list_sha256':sha(json.dumps(texts,ensure_ascii=False)),'text_count':len(texts),'max_tokens':max_tokens,'batch_size':batch,'threads':threads,'torch':torch.__version__,'transformers':transformers.__version__,'backend':'cpu_float32','representation':'guard=text only; encoder mean pooling; relevance=title+text dot query; density=text-only cosine'}
 cp=cache/f'{kind}_config.json';sp=cache/f'{kind}_progress.json';ap=cache/f'{kind}.npy'
 if cp.exists():
  assert json.loads(cp.read_text())==cfg,'Cache configuration mismatch; choose another output directory.'
  arr=np.lib.format.open_memmap(ap,mode='r+');state=json.loads(sp.read_text())
 else:
  write(cp,cfg);write(cache/f'{kind}_texts.json',texts)
  arr=np.lib.format.open_memmap(ap,mode='w+',dtype='float32',shape=(len(texts),1 if is_guard else 768))
  state={'done':0,'batch_seconds':0.,'batches':0,'at_cap_count':0,'truncated_text_count':0,'max_original_tokens':0,'max_observed_tokens':0};write(sp,state)
 if state['done']<len(texts):
  torch.set_num_threads(threads)
  if not getattr(torch,'_group9_interop_set',False):
   torch.set_num_interop_threads(1);torch._group9_interop_set=True
  torch.manual_seed(12)
  start=time.perf_counter();tok=AutoTokenizer.from_pretrained(str(root),local_files_only=True)
  if is_guard:
   model,loading=AutoModelForSequenceClassification.from_pretrained(str(root),local_files_only=True,use_safetensors=True,output_loading_info=True)
   assert str(model.config.id2label[1]).upper()=='INJECTION',model.config.id2label
  else:
   model,loading=AutoModel.from_pretrained(str(root),local_files_only=True,weights_only=True,output_loading_info=True,add_pooling_layer=False)
  if loading.get('missing_keys')or loading.get('mismatched_keys')or loading.get('error_msgs'):raise RuntimeError(str(loading))
  model.to('cpu').eval();state.update({'load_seconds':time.perf_counter()-start,'loading_info':loading})
  with torch.inference_mode():model(**tok(['The library opens at nine.'],return_tensors='pt',truncation=True,max_length=max_tokens))
  last=time.monotonic()
  for begin in range(state['done'],len(texts),batch):
   xx=texts[begin:begin+batch]
   # Full lengths are recorded only, never used to fit or select a model.
   full_lengths=[len(z)for z in tok(xx,truncation=False)['input_ids']]
   t=time.perf_counter();enc=tok(xx,padding=True,truncation=True,max_length=max_tokens,return_tensors='pt')
   with torch.inference_mode():
    pred=model(**enc)
    if is_guard:vals=pred.logits.float().softmax(-1)[:,1,None]
    else:
     mask=enc['attention_mask'][...,None].float();vals=(pred.last_hidden_state*mask).sum(1)/mask.sum(1)
   arr[begin:begin+len(xx)]=vals.cpu().numpy();arr.flush()
   lengths=enc['attention_mask'].sum(1).tolist()
   state['batch_seconds']+=time.perf_counter()-t;state['batches']+=1;state['done']=begin+len(xx)
   state['at_cap_count']+=sum(x==max_tokens for x in lengths)
   state['truncated_text_count']+=sum(x>max_tokens for x in full_lengths)
   state['max_original_tokens']=max(state['max_original_tokens'],max(full_lengths));state['max_observed_tokens']=max(state['max_observed_tokens'],max(lengths));write(sp,state)
   if time.monotonic()-last>15 or begin==0:
    print(json.dumps({'stage':kind,'done':state['done'],'total':len(texts),'batch_seconds':state['batch_seconds']}),flush=True);last=time.monotonic()
  del model,tok;gc.collect()
 state['call_wall_seconds']=time.perf_counter()-begin_wall
 state['timing_scope']='One feature-cache call: hashing/model setup/full-length token audit/batched text inference/cache writes; not end-to-end RAG latency or per-query independence.'
 try:
  import resource
  state['process_peak_rss_bytes']=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)*(1 if sys.platform=='darwin'else 1024)
 except ImportError:state['process_peak_rss_bytes']=None
 write(out/f'{kind}_inference_metadata.json',{'configuration':cfg,'execution':state})
 return {t:np.asarray(arr[i]).copy()for i,t in enumerate(texts)}
def infer_reusing(texts,kind,out,source,threads=4,batch=12,max_tokens=512):
 """Reuse exact frozen-model vectors, infer only unseen texts, retain lineage."""
 source=Path(source)
 existing=out/'cache'/f'{kind}_config.json'
 if existing.exists():
  own=json.loads(existing.read_text())
  assert own['text_list_sha256']==sha(json.dumps(texts,ensure_ascii=False)),'Cache text mismatch; choose a new output directory.'
  return load_cache(texts,kind,out)
 oldcfg=json.loads((source/'cache'/f'{kind}_config.json').read_text())
 oldtexts=json.loads((source/'cache'/f'{kind}_texts.json').read_text())
 oldstate=json.loads((source/'cache'/f'{kind}_progress.json').read_text())
 root,spec=verify_model(kind)
 assert oldcfg['model_manifest_sha256']==digest_file(root/'model_manifest.json')
 assert oldcfg['max_tokens']==max_tokens and oldcfg['backend']=='cpu_float32'
 assert oldstate['done']==len(oldtexts) and oldcfg['text_list_sha256']==sha(json.dumps(oldtexts,ensure_ascii=False))
 oldarr=np.load(source/'cache'/f'{kind}.npy',mmap_mode='r')
 available={t:i for i,t in enumerate(oldtexts)};missing=[t for t in texts if t not in available]
 extra=infer(missing,kind,out/'new_only',threads,batch,max_tokens) if missing else {}
 cache=out/'cache';cache.mkdir(parents=True,exist_ok=True)
 arr=np.lib.format.open_memmap(cache/f'{kind}.npy',mode='w+',dtype='float32',shape=(len(texts),1 if kind=='guard'else 768))
 for i,t in enumerate(texts):arr[i]=oldarr[available[t]]if t in available else extra[t]
 arr.flush()
 cfg={**oldcfg,'text_list_sha256':sha(json.dumps(texts,ensure_ascii=False)),'text_count':len(texts),'composed_cache':True,'source_cache':str(source),'source_array_sha256':digest_file(source/'cache'/f'{kind}.npy'),'source_texts_sha256':digest_file(source/'cache'/f'{kind}_texts.json'),'new_only_texts':len(missing)}
 state={'done':len(texts),'reused_text_count':len(texts)-len(missing),'newly_inferred_text_count':len(missing),'note':'Composed frozen-model features; timings belong to source cache and new_only metadata, not a new inference of every row.'}
 write(cache/f'{kind}_config.json',cfg);write(cache/f'{kind}_texts.json',texts);write(cache/f'{kind}_progress.json',state)
 write(out/f'{kind}_inference_metadata.json',{'configuration':cfg,'execution':state})
 return {t:np.asarray(arr[i]).copy()for i,t in enumerate(texts)}

def load_cache(texts,kind,out):
 cfg=json.loads((out/'cache'/f'{kind}_config.json').read_text());state=json.loads((out/'cache'/f'{kind}_progress.json').read_text())
 assert cfg['text_list_sha256']==sha(json.dumps(texts,ensure_ascii=False)) and state['done']==len(texts),'Incomplete or mismatched feature cache'
 arr=np.load(out/'cache'/f'{kind}.npy',mmap_mode='r')
 return {t:np.asarray(arr[i]).copy()for i,t in enumerate(texts)}
def assemble(rows,E,G,k):
 result=[];flat=[]
 for r in rows:
  qv=E[r['question']]
  score_values=relevance_scores(np.stack([E[doc_repr(p)]for p in r['pool']]),qv)
  pp=[{**p,'score':float(score)}for p,score in zip(r['pool'],score_values)]
  pp=sorted(pp,key=lambda p:-p['score'])[:k]
  vectors=np.stack([E[p['text']]for p in pp]);vectors/=np.linalg.norm(vectors,axis=1,keepdims=True)+1e-9
  sim=vectors@vectors.T;np.fill_diagonal(sim,-1)
  scores=np.asarray([p['score']for p in pp]);z=(scores-scores.mean())/(scores.std()+1e-6)
  for i,p in enumerate(pp):
   f={'guard':float(G[p['text']][0]),'rule':sum(bool(rule.search(p['text']))for rule in PATTERNS)/len(PATTERNS),'score_z':float(z[i]),'density':float(sim[i].max())}
   p['features']=f
   flat.append({**{k:v for k,v in r.items()if k!='pool'},'index':i,'id':p['id'],'title':p.get('title',''),'text':p['text'],'text_hash':sha(p['text']),'label':p.get('label',0),'family':p.get('family','clean'),'score':p['score'],'features':f})
  result.append({**r,'pool':pp})
 return result,flat

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--stage',choices=['prepare','contriever','guard','assemble','all'],default='all');p.add_argument('--threads',type=int,default=4);p.add_argument('--batch',type=int,default=12);p.add_argument('--max-tokens',type=int,default=512);p.add_argument('--pool-size',type=int,default=20);p.add_argument('--reuse-feature-cache',type=Path);a=p.parse_args()
 a.output.mkdir(parents=True,exist_ok=True);rows=read_rows(a.input);et,gt=collect(rows)
 manifest={'input_path':str(a.input),'input_sha256':digest_file(a.input),'script_sha256':digest_file(__file__),'input_rows':len(rows),'questions':len({r['qid']for r in rows}),'unique_embedding_texts':len(et),'unique_guard_texts':len(gt),'pool_size':a.pool_size,'feature_order':FEATURES,'platform':platform.platform(),'cpu_count':os.cpu_count(),'max_tokens':a.max_tokens,'ranking':'stable descending title+text query dot product; float64 element product with fixed axis sum; retain top K','density':'max other text-only normalized Contriever cosine','truncation':'512 tokens by default; original/capped lengths recorded; no claim all text represented','status':'prepared'}
 write(a.output/'input_manifest.json',manifest)
 if a.stage=='prepare':print(json.dumps(manifest),flush=True);return
 E=None;G=None
 if a.stage in ('contriever','all'):
  E=infer_reusing(et,'contriever',a.output,a.reuse_feature_cache,a.threads,a.batch,a.max_tokens)if a.reuse_feature_cache and(a.reuse_feature_cache/'cache/contriever_config.json').exists()else infer(et,'contriever',a.output,a.threads,a.batch,a.max_tokens)
 if a.stage in ('guard','all'):
  G=infer_reusing(gt,'guard',a.output,a.reuse_feature_cache,a.threads,a.batch,a.max_tokens)if a.reuse_feature_cache and(a.reuse_feature_cache/'cache/guard_config.json').exists()else infer(gt,'guard',a.output,a.threads,a.batch,a.max_tokens)
 if a.stage in ('assemble','all'):
  E=E if E is not None else load_cache(et,'contriever',a.output);G=G if G is not None else load_cache(gt,'guard',a.output)
  scored,flat=assemble(rows,E,G,a.pool_size);jsonl(a.output/'pools_with_features.jsonl',scored);jsonl(a.output/'candidate_features.jsonl',flat)
  manifest.update({'status':'complete','output_pool_rows':len(scored),'output_candidate_rows':len(flat),'pool_features_sha256':digest_file(a.output/'pools_with_features.jsonl'),'flat_features_sha256':digest_file(a.output/'candidate_features.jsonl')});write(a.output/'input_manifest.json',manifest)
  print(json.dumps(manifest),flush=True)
if __name__=='__main__':main()
