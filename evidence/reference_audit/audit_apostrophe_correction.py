"""Independent post-run measurement correction audit; original generator kept frozen."""
from pathlib import Path
import json,re,unicodedata,hashlib,sys
from decimal import Decimal
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'improved_generation/output'
def read(p):return json.loads(p.read_text())
def readl(p):return[json.loads(l)for l in p.read_text().splitlines()if l.strip()]
def mention_text(s):
 s=unicodedata.normalize('NFKC',str(s)).replace('‘',"'").replace('’',"'").replace('ʼ',"'")
 s=re.sub(r"(?<=\w)'s\b",'',s,flags=re.I)
 return re.sub(r"(?<=\w)'(?=\w)",'',s)
def norm(s):
 s=unicodedata.normalize('NFKC',str(s)).lower().strip();v=s.rstrip('.!?')
 if re.fullmatch(r'[+-]?(?:\d+(?:,\d{3})*(?:\.\d+)?|\.\d+)%?',v):return str(Decimal(v.rstrip('%').replace(',','')).normalize())+('%'if v.endswith('%')else'')
 s=''.join(' 'if unicodedata.category(c).startswith('P')else c for c in s);return' '.join(re.sub(r'\b(a|an|the)\b',' ',s).split())
def exact(a,s):return bool(norm(a))and norm(a)==norm(s)
def mention(a,s):
 a=unicodedata.normalize('NFKC',mention_text(a)).lower().strip().removesuffix('.');s=unicodedata.normalize('NFKC',mention_text(s)).lower()
 if re.fullmatch(r'[+-]?(?:\d+(?:,\d{3})*(?:\.\d+)?|\.\d+)%?',a):
  return any(norm(m.group())==norm(a)for m in re.finditer(r'(?<![\w.])[+-]?(?:\d+(?:,\d{3})*(?:\.\d+)?|\.\d+)%?(?!\w|\.\d)',s))
 return bool(norm(a))and(' '+norm(a)+' ')in(' '+norm(s)+' ')
def corrected(r):
 d={'correct_exact':exact(r['correct'],r['response']),'target_exact':exact(r['incorrect'],r['response']),'correct_mention':mention(r['correct'],r['response']),'target_mention':mention(r['incorrect'],r['response'])};d['both_mentioned']=d['correct_mention']and d['target_mention'];return d
# General measurement regressions, independent of whether they occur in benchmark.
tests=[('S',"Ocean's shape",False),('S','Ocean’s shape',False),('S',"'S'",True),('S','“S”',True),('S','S-shaped',True),('S','The letter S.',True),('S',"S's curved shape.",True),('John Smith',"John Smith's record.",True),("O'Brien",'O’Brien’s record.',True),('James',"James' record.",True),('O',"O'Brien's record.",False),('S',"Jessica's answer is O",False),('no',"I don't know",False),('no','I dont know',False),('no','The answer is no.',True),('24','24.',True),('24','24.0.',True),('24','There are 24 episodes.',True),('24','240',False),('24','124',False),('24','24.5',False),('2','2.4',False)]
for a,s,want in tests:assert mention(a,s)==want,(a,s,want)
rows=readl(BASE/'raw_generations.jsonl');changes=[]
for r in rows:
 d=corrected(r);fields=[k for k,v in d.items()if r[k]!=v]
 if fields:changes.append({'qid':r['qid'],'gate':r['gate'],'setting':r['setting'],'fields':fields,'response':r['response'],'old':{k:r[k]for k in fields},'corrected':{k:d[k]for k in fields}})
assert len(changes)==23 and{r['qid']for r in changes}=={'test397'}
assert all(set(r['fields'])<= {'correct_mention','both_mentioned'}for r in changes)
sens=read(BASE/'apostrophe_sensitivity.json');assert len(sens['changes'])==len(changes)
for r,s in zip(changes,sens['changes']):
 assert(r['qid'],r['gate'],r['setting'],r['fields'])==(s['qid'],s['gate'],s['setting'],s['changed_fields']);assert r['old']==s['old']and r['corrected']==s['apostrophe_aware']
report={'status':'passed_original_sensitivity','regressions':len(tests),'changed_rows':changes,'n_changed':23,'unique_affected_qids':['test397'],'no_target_exact_or_mention_changes':True,'no_reference_exact_changes':True,'original_raw_sha256':hashlib.sha256((BASE/'raw_generations.jsonl').read_bytes()).hexdigest()}
if len(sys.argv)>1:
 correctedbase=Path(sys.argv[1]);new=readl(correctedbase/'raw_generations.jsonl');assert len(new)==len(rows)
 for old,r in zip(rows,new):
  d=corrected(old)
  for k,v in old.items():
   assert r[k]==(d[k]if k in d else v),('correctedfield',old['qid'],old['gate'],old['setting'],k)
  assert all(r[k]==v for k,v in d.items())
 prov=read(correctedbase/'correction_provenance.json')
 def fh(p):return hashlib.sha256(p.read_bytes()).hexdigest()
 assert prov['original_frozen_scorer_sha256']==fh(ROOT/'improved_generation/scoring.py')
 assert prov['correction_code_sha256']==fh(ROOT/'improved_generation/scoring_correction.py')
 for name,h in prov['original_artifact_hashes'].items():assert fh(ROOT/'improved_generation'/name)==h,('frozenfile',name)
 assert prov['corrected_raw_sha256']==fh(correctedbase/'raw_generations.jsonl')
 for regression in prov['regressions']:assert mention(regression['reference'],regression['response'])==regression['expected_mention']
 report['correction_provenance_hashes']='passed';report['owner_regressions_independently_repeated']=len(prov['regressions'])
 summary=read(correctedbase/'summary.json')
 for s in summary['results']:
  sel=[r for r in new if r['gate']==s['gate']and r['setting']==s['setting']]
  for k in['correct_exact','target_exact','correct_mention','target_mention','both_mentioned','abstention']:
   n=sum(r[k]for r in sel);assert s[k+'_count']==n and abs(s[k+'_rate']-n/100)<1e-12
 clean=next(s for s in summary['results']if(s['gate'],s['setting'])==('none','none'));assert clean['correct_mention_count']==24 and clean['correct_exact_count']==13
 report['status']='passed_corrected_raw_and_summaries';report['corrected_directory']=str(correctedbase);report['corrected_raw_sha256']=hashlib.sha256((correctedbase/'raw_generations.jsonl').read_bytes()).hexdigest()
(ROOT/'improvement_audit/apostrophe_correction_independent_audit.json').write_text(json.dumps(report,indent=2));print(report['status'],len(tests),len(changes))
