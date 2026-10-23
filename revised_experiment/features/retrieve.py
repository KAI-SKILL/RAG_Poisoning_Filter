#!/usr/bin/env python3
"""Exact Contriever dot-product retrieval over a declared shared small corpus.

This indexes/searches only the input corpus, not all NQ or Wikipedia. Metadata,
model identity, corpus hash and source-group split checks stay in the output.
"""
from pathlib import Path
import argparse,json,time,platform
from run_features import infer,doc_repr,relevance_scores,write,jsonl,digest_file,np

def load(p):
 t=Path(p).read_text();return json.loads(t)if t.lstrip().startswith('[')else[json.loads(s)for s in t.splitlines()if s.strip()]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--corpus',type=Path,required=True);p.add_argument('--queries',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--threads',type=int,default=4);p.add_argument('--batch',type=int,default=12);p.add_argument('--top-k',type=int,default=20);p.add_argument('--separate-corpus-by-split',action='store_true');a=p.parse_args()
 docs=load(a.corpus);queries=load(a.queries);a.output.mkdir(parents=True,exist_ok=True)
 assert len({d['id']for d in docs})==len(docs)
 assert len({q['qid']for q in queries})==len(queries)
 texts=sorted({q['question']for q in queries}|{doc_repr(d)for d in docs}|{d['text']for d in docs},key=lambda t:(len(t),t))
 start=time.perf_counter();E=infer(texts,'contriever',a.output,a.threads,a.batch,512)
 D=np.stack([E[doc_repr(d)]for d in docs]);rows=[];raw=[]
 for q in queries:
  s=relevance_scores(D,E[q['question']])
  allowed=np.array([i for i,d in enumerate(docs)if not a.separate_corpus_by_split or d.get('split')==q.get('split')],dtype=int)
  assert len(allowed)>=a.top_k,(q['qid'],len(allowed))
  order=allowed[np.argsort(-s[allowed],kind='stable')[:a.top_k]]
  pool=[{**docs[i],'score':float(s[i]),'label':0,'family':'clean'}for i in order]
  rows.append({**q,'setting':'none','pool':pool})
  raw.append({'qid':q['qid'],'top_ids':[d['id']for d in pool],'scores':[d['score']for d in pool],'gold_in_top20':bool(q.get('gold_document_id')in[d['id']for d in pool])if q.get('gold_document_id')else None})
 jsonl(a.output/'clean_retrieval.jsonl',rows);write(a.output/'retrieval_diagnostics.json',raw)
 write(a.output/'retrieval_manifest.json',{'status':'complete','method':'exact declared-corpus dot-product search with float64 fixed-axis product/sum','scope':'declared shared small corpus, not full NQ/Wikipedia','corpus_sha256':digest_file(a.corpus),'query_sha256':digest_file(a.queries),'script_sha256':digest_file(__file__),'corpus_passages':len(docs),'corpus_passages_by_split':{k:sum(d.get('split')==k for d in docs)for k in sorted({str(d.get('split'))for d in docs})},'separate_corpus_by_split':a.separate_corpus_by_split,'queries':len(queries),'top_k':a.top_k,'total_seconds':time.perf_counter()-start,'platform':platform.platform(),'query_split_counts':{k:sum(q.get('split')==k for q in queries)for k in sorted({str(q.get('split'))for q in queries})}})
 print(json.dumps({'status':'complete','corpus_passages':len(docs),'queries':len(queries),'output':str(a.output/'clean_retrieval.jsonl')}),flush=True)
if __name__=='__main__':main()
