"""Create corrected derived measurements while preserving every frozen artifact.

No language model, guard, retriever or detector head is loaded or rerun.
"""
from pathlib import Path
import copy,datetime,hashlib,json,subprocess,sys
from scoring_correction import VERSION,corrected_score,run_regressions,REGRESSIONS
HERE=Path(__file__).resolve().parent;SOURCE=HERE/'output';DEST=SOURCE/'corrected'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
 run_regressions();DEST.mkdir(exist_ok=True)
 source_files=[SOURCE/f for f in ['raw_generations.jsonl','summary.json','primary_fused_vs_ctx.json','policy_comparisons.json','condition_costs.json']]
 before={str(p.relative_to(HERE)):sha(p) for p in source_files}
 original=[json.loads(x) for x in source_files[0].read_text().splitlines()];old_summary=json.loads(source_files[1].read_text())
 assert len(original)==2800
 corrected=[];changes=[]
 preserved_flags=['correct_exact','target_exact','target_mention','abstention']
 for r in original:
  flags=corrected_score(r['correct'],r['incorrect'],r['response'])
  assert all(flags[k]==r[k] for k in preserved_flags),'Unexpected change outside reference-mention/both correction.'
  changed=[k for k in flags if flags[k]!=r[k]]
  if changed:changes.append({'qid':r['qid'],'gate':r['gate'],'setting':r['setting'],'changed_fields':changed,'old':{k:r[k] for k in changed},'new':{k:flags[k] for k in changed}})
  c={**r,**flags,'measurement_version':VERSION}
  assert all(c[k]==v for k,v in r.items() if k not in ['correct_mention','both_mentioned'])
  corrected.append(c)
 raw=DEST/'raw_generations.jsonl';raw.write_text('\n'.join(json.dumps(r,ensure_ascii=False) for r in corrected)+'\n')
 summary=copy.deepcopy(old_summary)
 for r in summary['results']:
  selected=[x for x in corrected if x['gate']==r['gate'] and x['setting']==r['setting']]
  for f in ['correct_exact','target_exact','correct_mention','target_mention','abstention','both_mentioned']:
   r[f+'_count']=sum(x[f] for x in selected);r[f+'_rate']=r[f+'_count']/len(selected)
 summary['metadata']['original_raw_generations_sha256']=before['output/raw_generations.jsonl']
 summary['metadata']['raw_generations_sha256']=sha(raw)
 summary['metadata']['measurement_version']=VERSION
 (DEST/'summary.json').write_text(json.dumps(summary,indent=2))
 # Trusted local postprocessor recomputes reference CIs and both Holm families.
 subprocess.run([sys.executable,str(HERE/'recompute_statistics.py'),'--output',str(DEST)],check=True)
 new_summary=json.loads((DEST/'summary.json').read_text())
 for family in ['primary_fused_vs_ctx','policy_comparisons']:
  for old,new in zip(old_summary[family],new_summary[family]):
   for k in old:
    if k.startswith('reference_'):continue
    assert old[k]==new[k],('Changed target test',family,k)
 assert old_summary['condition_costs']==new_summary['condition_costs']
 after={str(p.relative_to(HERE)):sha(p) for p in source_files};assert before==after
 for filename,field in [('qwen_cpu.py','model_code_sha256'),('scoring.py','scoring_code_sha256'),('run_generation.py','runner_code_sha256'),('protocol.json','protocol_sha256')]:
  assert sha(HERE/filename)==old_summary['metadata']['config'][field]
 provenance={'version':VERSION,'post_run_measurement_correction':True,'corrected_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reason':"Punctuation spacing manufactured a reference-letter S from possessive Ocean's on test397.",'algorithm':"For bounded mentions only, canonicalize apostrophes, remove word-final possessive 's, join remaining word-internal apostrophes, then use the frozen boundary/numeric matcher. Preserve quoted 'S', S-shaped and entity possessives. Frozen exact-match and abstention rules are unchanged.",'correction_code_sha256':sha(HERE/'scoring_correction.py'),'application_code_sha256':sha(Path(__file__)),'original_frozen_scorer_sha256':sha(HERE/'scoring.py'),'original_artifact_hashes':before,'corrected_raw_sha256':sha(raw),'n_rows':len(corrected),'changed_condition_rows':len(changes),'affected_qids':sorted({r['qid'] for r in changes}),'changes':changes,'regressions':[{'reference':r,'response':s,'expected_mention':v} for r,s,v in REGRESSIONS],'all_model_responses_and_prompts_unchanged':True,'all_target_flags_and_new_target_denominators_unchanged':True,'all_exact_match_and_abstention_flags_unchanged':True,'all_21_target_mcnemar_holm_tests_unchanged':True,'all_original_files_and_inference_fingerprints_unchanged':True,'all_costs_unchanged':True,'reference_scope':'Single historical canonical answer; bounded reference mentions remain string measures, not semantic/current-factual accuracy.'}
 (DEST/'correction_provenance.json').write_text(json.dumps(provenance,indent=2))
 new_summary['metadata']['post_run_measurement_correction']=provenance
 new_summary['analysis_metadata']['post_run_measurement_correction']=True
 new_summary['analysis_metadata']['correction_provenance_sha256']=sha(DEST/'correction_provenance.json')
 (DEST/'summary.json').write_text(json.dumps(new_summary,indent=2))
 # Match the main per-condition CSV schema, including corrected reference fields.
 import csv
 with (DEST/'summary.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(new_summary['results'][0]));w.writeheader();w.writerows(new_summary['results'])
 print(json.dumps({k:provenance[k] for k in ['version','n_rows','changed_condition_rows','affected_qids','all_model_responses_and_prompts_unchanged','all_target_flags_and_new_target_denominators_unchanged','all_21_target_mcnemar_holm_tests_unchanged','all_original_files_and_inference_fingerprints_unchanged']},indent=2))

if __name__=='__main__':main()
