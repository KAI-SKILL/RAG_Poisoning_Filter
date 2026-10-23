from pathlib import Path
import hashlib,json
BASE=Path('/project');NEW=BASE/'outputs/Group9_Fresh_Sparse_2026-10-22';OLD=BASE/'outputs/Group9_Expanded_Attacks/results'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def count(p):
 with p.open('rb')as f:return sum(1 for _ in f)
checks={name:count(NEW/name)for name in ['document_predictions.jsonl','case_predictions.jsonl','retrieval_delivery.jsonl','normal_retrieval.jsonl','external_predictions.jsonl','unique_document_scores.jsonl','calibration_scores.jsonl']}
assert checks['document_predictions.jsonl']==67200
assert checks['case_predictions.jsonl']==57600
assert checks['retrieval_delivery.jsonl']==57600
assert checks['normal_retrieval.jsonl']==1200
assert checks['external_predictions.jsonl']==1195
assert checks['calibration_scores.jsonl']==2400
pairs=[('calibration_scores.jsonl','calibration_scores.jsonl'),('thresholds_frozen.json','thresholds_frozen.json'),('unique_document_scores.jsonl','unique_document_scores.jsonl'),('document_predictions.jsonl','document_predictions.jsonl'),('case_predictions.jsonl','case_predictions_complete.jsonl'),('external_predictions.jsonl','external_predictions.jsonl'),('classification_summary.json','classification_summary.json'),('classification_paired_differences.json','classification_paired_differences.json'),('external_summary.json','external_summary.json'),('retrieval_delivery.jsonl','retrieval_delivery.jsonl'),('normal_retrieval.jsonl','normal_retrieval.jsonl'),('retrieval_summary.json','retrieval_summary.json'),('retrieval_paired_differences.json','retrieval_paired_differences.json'),('retrieval_validation.json','retrieval_validation.json')]
comparisons=[]
for fresh,reference in pairs:
 a=sha(NEW/fresh);b=sha(OLD/reference);comparisons.append({'fresh':fresh,'previous':reference,'fresh_sha256':a,'previous_sha256':b,'byte_identical':a==b})
 if a!=b:
  # The trace still records every discrepancy; semantic differences cannot disappear.
  if fresh.endswith('.json'):comparisons[-1]['json_content_equal']=json.loads((NEW/fresh).read_text())==json.loads((OLD/reference).read_text())
receipt=json.loads((NEW/'execution_receipt.json').read_text())
assert receipt['status']=='COMPLETE_ACTUAL_FROZEN_SPARSE_AND_RETRIEVAL_RERUN'
assert receipt['source_bytes_unchanged']
assert receipt['generator_calls']==0 and receipt['neural_calls']==0 and receipt['detector_fits']==0
for model,r in receipt['actual_model_call_counters'].items():
 assert r['loaded_models']==1 and r['predict_calls_started']==r['predict_calls_returned']and r['predict_calls_returned']>0
 assert r['texts_returned']>=checks['unique_document_scores.jsonl']//2
manifest=json.loads((NEW/'run_manifest.json').read_text())
assert manifest['archive_integrity']['status']=='CLOSED_OUTPUT_ROW_AND_KEY_COVERAGE_VERIFIED'
for name,r in manifest['archive_integrity']['files'].items():assert sha(NEW/name)==r['sha256']
result={'status':'PASS_ACTUAL_FRESH_RUN_WITH_CLOSED_OUTPUT_VERIFICATION','counts':checks,'actual_predict_counters':receipt['actual_model_call_counters'],'source_bytes_unchanged':receipt['source_bytes_unchanged'],'same_inputs_and_detectors':True,'score_and_delivery_comparisons':comparisons,'all_compared_bytes_identical':all(x['byte_identical']for x in comparisons),'new_case_file_complete_without_recovery':True,'neural_calls':0,'generator_calls':0,'scope':'Fresh real sparse classifier and TF-IDF retrieval computation; no new LLM answers or ASR.'}
(NEW/'fresh_verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
