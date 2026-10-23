"""Reproduce the revised small-corpus evaluation in a NEW run directory.

The pinned old70 training features are deliberately reused. This executes fresh
normal retrieval, new attack/control features and 3B generation; it never
relabels the archived0.5B run as new execution or overwrites the delivered run.
"""
from pathlib import Path
import argparse,datetime,subprocess,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent

def run(*parts):
 cmd=[sys.executable,'-X','utf8',*[str(x)for x in parts]];print('Running:',*cmd,flush=True);subprocess.run(cmd,cwd=ROOT,check=True)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--download-models',action='store_true');p.add_argument('--output',type=Path);p.add_argument('--threads',type=int,default=4);a=p.parse_args()
 out=a.output.resolve()if a.output else ROOT/'output/revised_reruns'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
 if out.exists()and any(out.iterdir()):p.error('Use a new empty output directory; individual guarded stage runners support exact-config resume.')
 out.mkdir(parents=True,exist_ok=True);data=HERE/'data';feat=HERE/'features';model=HERE/'models/Qwen2.5-3B-Instruct-GGUF/qwen2.5-3b-instruct-q4_k_m.gguf'
 if a.download_models:run(feat/'download_models.py');run(HERE/'download_generator.py')
 if not model.is_file():p.error('Pinned GGUF absent: run with --download-models first, or download_generator.py.')
 run(feat/'retrieve.py','--corpus',data/'corpus.jsonl','--queries',data/'records_formal_v2.jsonl','--output',out/'retrieval','--threads',a.threads,'--separate-corpus-by-split')
 run(HERE/'prepare_pools.py','--records',data/'records_formal_v2.jsonl','--retrieval',out/'retrieval/clean_retrieval.jsonl','--source-audit',data/'test_source_quality_audit.json','--output',out/'cases')
 run(feat/'run_features.py','--input',out/'cases/input_pools.jsonl','--output',out/'fresh_features','--reuse-feature-cache',out/'retrieval','--threads',a.threads)
 run(feat/'validate_insert_rank.py','--corpus',data/'corpus.jsonl','--case-pools',out/'cases/input_pools.jsonl','--embedding-cache',out/'retrieval','--embedding-cache',out/'fresh_features','--actual-selected-pools',out/'fresh_features/pools_with_features.jsonl','--output',out/'fresh_features/insert_rank_validation.json')
 run(HERE/'fit_and_select.py','--features',out/'fresh_features/candidate_features.jsonl','--pools',out/'fresh_features/pools_with_features.jsonl','--old-split',ROOT/'evidence/utility_audit/frozen_old100_split.json','--output',out/'selection')
 run(HERE/'gguf_generate.py','--model',model,'--input',out/'selection/context_requests.jsonl','--output',out/'generation','--threads',a.threads)
 run(HERE/'evaluate_new.py','--input',out/'generation/raw_generations.jsonl','--source-audit',data/'test_source_quality_audit.json','--output',out/'new_scores')
 print('Fresh run complete:',out,flush=True)
 print('Delivered report/presentation remain tied to their documented run. Compare new results and regenerate dependent material before submission.',flush=True)
if __name__=='__main__':main()
