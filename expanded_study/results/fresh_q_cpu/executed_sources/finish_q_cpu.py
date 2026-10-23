"""Formally score, summarize and export the completed standalone Q CPU run."""
from pathlib import Path
import datetime,hashlib,json,shutil,sqlite3,subprocess,sys
BASE=Path('/project');ROOT=BASE/'outputs/Group9_Expanded_Attacks';OUT=BASE/'outputs/Group9_Fresh_Q_CPU_2026-10-22'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def stable(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def require(x,m):
 if not x:raise ValueError(m)
def call(args,log):
 with (OUT/log).open('a')as handle:r=subprocess.run([str(a)for a in args],stdout=handle,stderr=subprocess.STDOUT)
 require(r.returncode==0,'Command failed; '+log)
def main():
 manifest=read(OUT/'run_manifest.json');require(manifest['status']=='COMPLETE'and manifest['completed_unique_prompts']==90 and manifest['requested_rows']==90,'Q is not complete')
 require(manifest['preexisting_exact_responses']==0,'Inherited responses are not allowed')
 require(manifest['cumulative_http_errors']==0 and manifest['cumulative_unknown_outcome_requested_prompts']==0,'Inspect unknown/error attempts before publication')
 config=manifest['config'];require(config['runner_sha256']==sha(ROOT/'code/generation/run_native_generation.py'),'Executed runner source changed')
 protocol=read(OUT/'scoring_protocol.json');require(protocol['standalone_cpu_binding']['launcher_sha256']==sha(ROOT/'code/generation/launch_native_run.py'),'Executed launcher changed')
 require(protocol['standalone_cpu_binding']['postanalysis_source_sha256']==sha(ROOT/'generation/all_experiments/postanalyse_scope.py'),'Postanalysis source changed')
 code=OUT/'executed_sources';code.mkdir(exist_ok=False)
 for source in [ROOT/'code/generation/launch_native_run.py',ROOT/'code/generation/run_native_generation.py',ROOT/'code/generation/score_generations.py',ROOT/'generation/all_experiments/score_native_scope.py',ROOT/'generation/all_experiments/run_model_suite.py',ROOT/'generation/all_experiments/postanalyse_scope.py',ROOT/'generation/hf_gpu/export_hf_results.py',Path(__file__)]:shutil.copy2(source,code/source.name)
 shutil.copy2(BASE/'working/expanded_generation_runtime/native_build_manifest.json',OUT/'native_build_manifest.json')
 shutil.copy2(BASE/'working/generation_models/Qwen2.5-3B-Instruct-GGUF/manifest.json',OUT/'model_manifest.json')
 shutil.copy2(ROOT/'generation/all_experiments/inputs/q/token_counts.sqlite',OUT/'token_counts.sqlite')
 shutil.copy2(ROOT/'generation/all_experiments/inputs/q/token_counts.json',OUT/'token_counts.json')
 (OUT/'executed_source_hashes.json').write_text(json.dumps({p.name:sha(p)for p in code.iterdir()},indent=2)+'\n')
 call([sys.executable,ROOT/'generation/all_experiments/score_native_scope.py','--project-root',ROOT,'--output',OUT],'scoring_console.log')
 call([sys.executable,ROOT/'generation/all_experiments/postanalyse_scope.py','--scope','Q','--run-dir',OUT],'postanalysis_console.log')
 scored=read(OUT/'scoring/scoring_manifest.json');require(scored['status']=='COMPLETE_GENERATION_SCORING'and scored['actual_unique_response_records']==90,'Formal scoring incomplete')
 groups=[]
 for group in read(OUT/'scoring/summary.json'):
  if group['level']!='all':continue
  require(group['condition']=='clean'and group['n']==30,'Unexpected Q condition coverage')
  metrics={m['metric']:m for m in group['metrics']}
  groups.append({'policy':group['policy'],'condition':'clean','article_groups':group['articles'],'n':group['n'],**{name:{k:metrics[name][k]for k in ['sum','eligible_n','value','ci95_article_percentile']}for name in ['reference_exact','reference_token_f1','abstention_strict','blank','length_cap']}})
 db=sqlite3.connect((OUT/'generation_responses.sqlite').resolve().as_uri()+'?mode=ro&immutable=1',uri=True)
 require(db.execute('PRAGMA integrity_check').fetchone()[0]=='ok','Response integrity failed')
 prompt_tokens,completion_tokens=db.execute('SELECT sum(prompt_tokens),sum(completion_tokens) FROM responses').fetchone()
 attempts=[dict(zip(['batch_id','prompt_count','returned_count','status'],r))for r in db.execute('SELECT batch_id,prompt_count,returned_count,status FROM attempts ORDER BY attempt_id')]
 require(sum(r['prompt_count']for r in attempts)==90 and all(r['status']=='COMMITTED'and r['prompt_count']==r['returned_count']for r in attempts),'Attempt accounting differs')
 batches=[dict(zip(['batch_id','prompts','wall_seconds','prompt_tokens','completion_tokens'],r))for r in db.execute('SELECT batch_id,count(*),sum(elapsed_seconds),sum(prompt_tokens),sum(completion_tokens) FROM responses GROUP BY batch_id ORDER BY batch_id')];db.close()
 summary={'status':'COMPLETE_STANDALONE_CPU_Q_UTILITY','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Q','source':'Final source-repaired v2 custom development Q30, three contexts each; all frozen aliases retained.','model_repository':config['model_manifest']['repository'],'model_revision':config['model_manifest']['revision'],'quantization':'Q4_K_M','execution_device':'cloud CPU','threads':4,'batch_size':8,'generation_parameters':config['generation_parameters'],'requested_rows':90,'actual_unique_responses':90,'preexisting_exact_responses':0,'committed_http_batches':len(attempts),'unknown_outcomes':0,'http_errors':0,'actual_prompt_tokens':prompt_tokens,'actual_completion_tokens':completion_tokens,'generation_session_wall_seconds':manifest['elapsed_this_session_seconds'],'combined_prompt_and_completion_tokens_per_generation_wall_second':(prompt_tokens+completion_tokens)/manifest['elapsed_this_session_seconds'],'config_sha256':manifest['config_sha256'],'native_inputs_sha256':sha(OUT/'native_inputs.sqlite'),'scoring_protocol_sha256':sha(OUT/'scoring_protocol.json'),'metric_source_sha256':protocol['scorer_sha256'],'main_12_gpu_slots_membership':False,'attack_conditions':0,'attack_success_rate_measured':False,'groups':groups,'actual_batches':batches,'claim_boundary':'Q is a complete answerability/utility check with string-based reference-alias scoring. It does not measure attack success or establish that any native BF16 GPU suite executed. Article intervals are conditional on observed outputs; the original source evidence limitations remain.'}
 (OUT/'results_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
 names={'none':'No retrieval','gold_evidence':'Gold evidence','tfidf_retrieval':'TF-IDF retrieval'}
 lines=['# Q30 standalone CPU answerability results','','This is a complete fresh generation check of the final source-repaired Q30 development set: 30 source articles, each evaluated under three frozen context conditions. All 90 unique prompts were generated and formally scored. Q contains no attacks and produces no attack success rate.','','Model: official pinned Qwen2.5-3B-Instruct Q4_K_M; CPU, 4 threads, batch 8, greedy, seed 12, context 4096, maximum 48 generated tokens. This standalone CPU run is separate from the 12 planned cluster GPU scope/model runs.','','| Context | Reference exact | 95% article interval | Mean token F1 | Strict abstention |','|---|---:|---:|---:|---:|']
 for group in sorted(groups,key=lambda r:['none','gold_evidence','tfidf_retrieval'].index(r['policy'])):
  exact=group['reference_exact'];low,high=exact['ci95_article_percentile']
  lines.append(f"| {names[group['policy']]} | {int(exact['sum'])}/30 ({100*exact['value']:.1f}%) | {100*low:.1f}–{100*high:.1f}% | {100*group['reference_token_f1']['value']:.1f}% | {int(group['abstention_strict']['sum'])}/30 |")
 lines+=['',f"Actual generation session wall time: {manifest['elapsed_this_session_seconds']:.3f} seconds; {prompt_tokens:,} measured input tokens and {completion_tokens:,} generated tokens. {len(attempts)} committed HTTP batches, zero inherited responses, zero HTTP errors and zero unknown outcomes.",'','Exact accuracy compares the whole normalized response with pre-frozen final reference aliases. Token F1 is a secondary string metric. Intervals use the frozen 2,000 article-cluster bootstrap draws and seed 20261022. The final source repairs and alias additions are preserved; remaining passage-snapshot/source wording limitations still apply. Raw server results, full response SQLite, attempt ledger, configuration, source hashes, per-request metrics and complete score files are included.']
 (OUT/'Results_Report.md').write_text('\n'.join(lines)+'\n')
 destination=OUT.with_name(OUT.name+'_Closed')
 call([sys.executable,ROOT/'generation/hf_gpu/export_hf_results.py','--source',OUT,'--destination',destination],'export_console.log')
 receipt=read(destination/'export_receipt.json');require(receipt['status']=='COMPLETE_GENERATION_AND_SCORING'and receipt['full_asr_ready'],'Closed export did not pass completion checks')
 print(json.dumps({'summary':summary,'closed_export':receipt,'archive':str(destination.with_name(destination.name+'_COMPLETE_Results.zip'))},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
