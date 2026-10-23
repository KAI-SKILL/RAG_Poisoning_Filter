from pathlib import Path
import json,hashlib,re,datetime,unicodedata
ROOT=Path('current/package/Group9_Project')
OUT=Path('revision_work/utility_audit')
clean_path=ROOT/'improved_experiment/inputs/clean_target_candidates.json'
target_path=ROOT/'improved_generation/inputs/targets.json'
clean=json.loads(clean_path.read_text());targets=json.loads(target_path.read_text())
parent={q:q for q in clean}
def find(q):
 while parent[q]!=q:
  parent[q]=parent[parent[q]];q=parent[q]
 return q
def union(a,b):
 a,b=find(a),find(b)
 if a!=b:parent[max(a,b)]=min(a,b)
def norm(t):return re.sub(r'\W+',' ',unicodedata.normalize('NFKC',t).casefold()).strip()
seen={}
for q,x in clean.items():
 for d in x['docs']:
  keys=[('id',d['id']),('text',hashlib.sha256(norm(d['text']).encode()).hexdigest()),('title',norm(d['title']))]
  for k in keys:
   if k in seen:union(q,seen[k])
   else:seen[k]=q
clusters={}
for q in clean:clusters.setdefault(find(q),[]).append(q)
groups=sorted([sorted(v,key=lambda q:int(q[4:])) for v in clusters.values()],key=lambda g:hashlib.sha256(('Group9-Q-development-v1|'+'|'.join(g)).encode()).hexdigest())
# Deterministic subset-sum selection closest to 30, independent of outputs/answerability.
dp={0:[]}
for i,g in enumerate(groups):
 for n,idxs in list(dp.items())[::-1]:
  if n+len(g) not in dp:dp[n+len(g)]=idxs+[i]
size=min(dp,key=lambda n:(abs(n-30),n>30,n))
chosen=set(dp[size]);dev=[q for i,g in enumerate(groups) if i in chosen for q in g];train=[q for i,g in enumerate(groups) if i not in chosen for q in g]
split={'status':'FROZEN_BEFORE_NEW_MODEL_OUTPUTS','frozen_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'seed_label':'Group9-Q-development-v1','purpose':'Old100 exploration/training/development only; neither split is a new unseen test.','selection':'Union groups by same docID, normalized exact text or Wikipedia title; deterministic hashed group order and subset-sum nearest30; no model outcome or answerability selection.','source_inputs':{str(clean_path):hashlib.sha256(clean_path.read_bytes()).hexdigest(),str(target_path):hashlib.sha256(target_path.read_bytes()).hexdigest()},'grouping_criteria':['same docID','normalized exact passage text','normalized Wikipedia title (conservative source article grouping)'],'group_count':len(groups),'group_sizes':sorted([len(g) for g in groups],reverse=True),'train_qids':train,'development_qids':dev,'groups':[{'group_id':f'source-{i:03}','qids':g,'split':'development' if i in chosen else 'training'} for i,g in enumerate(groups)],'new_normal_calibration':'Not available in old100; must separately lock new source groups.','new_test':'Not available in old100; do not relabel these as unseen test.'}
path=OUT/'frozen_old100_split.json'
if path.exists():raise SystemExit('Refuse overwrite frozen split')
path.write_text(json.dumps(split,ensure_ascii=False,indent=2)+'\n')
print('frozen',len(train),len(dev),'groups',len(groups),'largest',split['group_sizes'][:8])
for q in sorted(clean,key=lambda q:int(q[4:])):
 t=targets[q]
 hits=[(i+1,d['id'],d['title'],d['text']) for i,d in enumerate(clean[q]['docs']) if norm(t['correct']) in norm(d['text'])]
 print(q,'DEV' if q in dev else 'TRAIN',t['question'],'=>',t['correct'],'vs',t['incorrect'],'label-hit-ranks',[h[0] for h in hits])
(OUT/'label_hits_all100.json').write_text(json.dumps({q:{'question':targets[q]['question'],'correct':targets[q]['correct'],'incorrect':targets[q]['incorrect'],'hits':[{'rank':i+1,**d} for i,d in enumerate(clean[q]['docs']) if norm(targets[q]['correct']) in norm(d['text'])]} for q in clean},ensure_ascii=False,indent=2))
