"""Validate completed generation artifacts without invoking any language model."""
from pathlib import Path
import argparse,hashlib,json,collections
from scoring import score
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent

def sha(b):return hashlib.sha256(b).hexdigest()
def stable(x):return json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=HERE/'output');ap.add_argument('--input',type=Path);a=ap.parse_args()
 summary=json.loads((a.output/'summary.json').read_text());meta=summary['metadata'];cfg=meta['config']
 raw_path=a.output/'raw_generations.jsonl';rows=[json.loads(x) for x in raw_path.read_text().splitlines()]
 input_path=a.input or Path(meta['input_file'])
 if not input_path.is_absolute():input_path=ROOT/input_path
 inputs=[json.loads(x) for x in input_path.read_text().splitlines()]
 assert len(rows)==len(inputs)==meta['n_requested_rows']==2800
 assert sha(input_path.read_bytes())==meta['input_sha256']==cfg['input_sha256']
 assert sha(raw_path.read_bytes())==meta['raw_generations_sha256']
 key=lambda r:(r['qid'],r['gate'],r['setting'])
 source={key(r):r for r in inputs};assert len(source)==2800
 unique={}
 for r in rows:
  assert key(r) in source
  assert all(r[k]==v for k,v in source[key(r)].items())
  assert sha(r['prompt'].encode())==r['prompt_sha256']
  assert sha(r['chat_prompt'].encode())==r['chat_prompt_sha256']
  assert all(r[k]==v for k,v in score(r['correct'],r['incorrect'],r['response']).items())
  assert r['config_sha256']==meta['config_sha256']
  assert not r['truncated'] and r['input_tokens']+64<=cfg['model_max_positions']
  k=r['chat_prompt_sha256']
  if k in unique:
   for f in ['response','batch_id','input_tokens','generated_tokens','hit_generation_cap']:
    assert r[f]==unique[k][f]
  else:unique[k]=r
 assert len({key(r) for r in rows})==2800
 assert len({r['qid'] for r in rows})==100
 assert len(unique)==meta['n_unique_prompts']
 keys=sorted(unique,key=lambda k:(unique[k]['input_tokens'],k));chunks=[keys[i:i+4] for i in range(0,len(keys),4)]
 assert sha(stable(chunks).encode())==cfg['fixed_batch_assignment_sha256']
 for chunk in chunks:
  bid=sha(stable(chunk).encode())
  assert all(unique[k]['batch_id']==bid for k in chunk)
  assert all(unique[k]['padded_input_tokens']==max(unique[j]['input_tokens'] for j in chunk) for k in chunk)
 assert sha(stable(cfg).encode())==meta['config_sha256']
 assert sha((HERE/'model_manifest.json').read_bytes())==cfg['model_manifest_sha256']
 for filename,field in [('qwen_cpu.py','model_code_sha256'),('scoring.py','scoring_code_sha256'),('run_generation.py','runner_code_sha256'),('protocol.json','protocol_sha256')]:
  assert sha((HERE/filename).read_bytes())==cfg[field]
 assert sha((HERE/'inputs'/'targets.json').read_bytes())==meta['targets_file_sha256']
 for row in summary['results']:
  sel=[r for r in rows if r['gate']==row['gate'] and r['setting']==row['setting']];assert len(sel)==row['n']==100
  clean={r['qid']:r for r in rows if r['gate']==row['gate'] and r['setting']=='none'}
  for f in ['correct_exact','target_exact','correct_mention','target_mention','abstention','both_mentioned']:
   assert sum(r[f] for r in sel)==row[f+'_count']
  c_nonhit=[r for r in sel if not clean[r['qid']]['target_mention']]
  assert len(c_nonhit)==row['clean_nonhit_denominator']
  assert sum(r['target_mention'] for r in c_nonhit)==row['new_target_count']
 result={'n_rows':len(rows),'n_qids':100,'n_unique_prompts':len(unique),'n_fixed_batches':len(chunks),'all_source_rows_preserved':True,'all_scores_recomputed':True,'all_prompt_hashes_verified':True,'all_cache_responses_consistent':True,'fixed_batch_assignment_verified':True,'all_summary_counts_recomputed':True,'no_truncation':True,'raw_generations_sha256':sha(raw_path.read_bytes()),'input_sha256':sha(input_path.read_bytes())}
 (a.output/'validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

if __name__=='__main__':main()
