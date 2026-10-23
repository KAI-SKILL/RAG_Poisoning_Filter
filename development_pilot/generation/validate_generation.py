"""Validate the supplied completed pilot artifacts without model inference."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output'/'generation'

def main():
 p=OUT/'raw_generations.jsonl';rows=[json.loads(x) for x in p.read_text().splitlines()]
 assert len(rows)==1152
 assert len({(r['group_id'],r['gate'],r['condition']) for r in rows})==1152
 assert len({r['group_id'] for r in rows})==96
 # Completed-run finding, checked against raw strings, independently of scoring.
 assert all(r['answer'].strip()==r['gold_answer'].strip() for r in rows)
 cache={}
 for r in rows:
  assert hashlib.sha256(r['prompt'].encode()).hexdigest()==r['prompt_sha256']
  assert not r['truncated']
  key=r['prompt_sha256']
  if key in cache:assert cache[key]==r['answer']
  else:cache[key]=r['answer']
 assert len(cache)==213
 manifest=ROOT/'generation'/'model_manifest.json'
 model_dir=ROOT/'generation'/'models'/'flan-t5-small-torch'
 model_files=json.loads(manifest.read_text())['files']
 weights_present=all((model_dir/f['file']).exists() for f in model_files)
 if weights_present:
  for f in model_files:
   fp=model_dir/f['file']
   assert fp.stat().st_size==f['bytes']
   assert hashlib.sha256(fp.read_bytes()).hexdigest()==f['sha256']
 meta={'n_rows':len(rows),'n_groups':96,'n_unique_prompts':len(cache),'all_raw_answers_equal_gold_verbatim':True,'all_prompt_sha256_verified':True,'all_cached_prompt_answers_identical':True,'exactly_one_row_per_group_gate_condition':True,'no_truncation':True,'all_local_model_file_hashes_verified':True if weights_present else None,'raw_generations_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'context_file_sha256':hashlib.sha256((OUT/'evaluation_contexts.jsonl').read_bytes()).hexdigest(),'model_manifest_sha256':hashlib.sha256(manifest.read_bytes()).hexdigest()}
 (OUT/'validation.json').write_text(json.dumps(meta,indent=2));print(json.dumps(meta,indent=2))

if __name__=='__main__':main()
