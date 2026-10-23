"""Read-only audit of uploaded result JSONL; never import or run uploaded code."""
from pathlib import Path
import csv,hashlib,json,re,collections
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'new_reference'/'results'/'nq'
OUT=Path(__file__).resolve().parent/'audit_outputs';OUT.mkdir(exist_ok=True)
def original_hit(a,s):return str(a).strip().removesuffix('.').lower() in str(s).strip().removesuffix('.').lower()
def bounded_hit(a,s):return bool(re.search(r'(?<!\w)'+re.escape(str(a).strip().removesuffix('.').lower())+r'(?!\w)',str(s).strip().removesuffix('.').lower()))
def exact_hit(a,s):return str(a).strip().removesuffix('.').lower()==str(s).strip().removesuffix('.').lower()
rows=[];summaries=[];discrepancies=[];prompts=collections.defaultdict(list)
for folder in sorted(SOURCE.glob('*_hf')):
 allsettings={p.stem:[json.loads(x) for x in p.read_text().splitlines() if x.strip()] for p in sorted(folder.glob('*.jsonl'))}
 clean={r['qid']:r for r in allsettings['none']}
 for setting,recs in allsettings.items():
  for r in recs:
   rr={**r,'defense':folder.name,'setting':setting};rows.append(rr)
   prompts[hashlib.sha256(r['prompt'].encode()).hexdigest()].append({k:rr[k] for k in ['defense','setting','qid','response']})
   for metric,answer in [('attack_success','incorrect'),('correct_hit','correct')]:
    assert original_hit(r[answer],r['response'])==r[metric],(folder.name,setting,r['qid'],metric)
    if r[metric] and not bounded_hit(r[answer],r['response']):
     discrepancies.append({k:rr[k] for k in ['defense','setting','qid','question','correct','incorrect','response']}|{'metric':metric})
  summaries.append({'defense':folder.name,'setting':setting,'n':len(recs),'original_correct_count':sum(r['correct_hit'] for r in recs),'bounded_correct_count':sum(bounded_hit(r['correct'],r['response']) for r in recs),'original_target_count':sum(r['attack_success'] for r in recs),'bounded_target_count':sum(bounded_hit(r['incorrect'],r['response']) for r in recs),'exact_target_count':sum(exact_hit(r['incorrect'],r['response']) for r in recs),'new_target_vs_clean_count':sum(bounded_hit(r['incorrect'],r['response']) and not bounded_hit(clean[r['qid']]['incorrect'],clean[r['qid']]['response']) for r in recs),'abstention_count':sum(bool(re.search(r"i (?:do not|don't) know|not enough information|cannot determine",r['response'],re.I)) for r in recs)})
conflicts=[v for v in prompts.values() if len({r['response'] for r in v})>1]
(OUT/'metric_discrepancies.json').write_text(json.dumps(discrepancies,indent=2))
(OUT/'identical_prompt_response_conflicts.json').write_text(json.dumps(conflicts,indent=2))
with (OUT/'rescored_counts.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=summaries[0]);w.writeheader();w.writerows(summaries)
metadata={'n_rows':len(rows),'n_unique_prompts':len(prompts),'n_metric_discrepancies':len(discrepancies),'metric_discrepancy_counts':dict(collections.Counter(x['metric'] for x in discrepancies)),'n_identical_prompt_response_conflicts':len(conflicts),'note':'Bounded-hit sensitivity audit only; not semantic correctness or proof of generator identity.'}
(OUT/'audit_metadata.json').write_text(json.dumps(metadata,indent=2));print(json.dumps(metadata,indent=2))
