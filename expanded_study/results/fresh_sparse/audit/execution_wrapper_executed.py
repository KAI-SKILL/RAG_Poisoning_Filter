"""Actually execute unchanged evaluator, instrumenting forwarded predict calls only."""
from pathlib import Path
import collections,datetime,hashlib,importlib.util,json,os,sys,time,traceback
from zoneinfo import ZoneInfo
BASE=Path('/project')
ROOT=BASE/'outputs/Group9_Expanded_Attacks'
OUT=BASE/'outputs/Group9_Fresh_Sparse_2026-10-22'
EVALUATOR=ROOT/'code/evaluate_expanded.py'
EXTERNAL=BASE/'working/expanded_sources'
WRAPPER=Path(__file__).resolve()
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def stable(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
source_paths=[ROOT/'protocol_frozen.json',ROOT/'data/hosts.jsonl',ROOT/'data/cases.jsonl',ROOT/'data/corpus.jsonl',ROOT/'models/LR.joblib',ROOT/'models/LinearSVC.joblib',ROOT/'models/models_frozen.json',EVALUATOR,EXTERNAL/'injecagent_base_contexts.jsonl',EXTERNAL/'agentdojo_clean_tool_outputs_unique.jsonl',ROOT/'results/run_manifest.json']
before={str(p.relative_to(BASE)):sha(p)for p in source_paths}
assert not OUT.exists()or not any(OUT.iterdir()),'Never overwrite saved results'
spec=importlib.util.spec_from_file_location('fresh_expanded_evaluator',EVALUATOR)
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
original_load=e.joblib.load
counts=collections.defaultdict(lambda:{'loaded_models':0,'predict_calls_started':0,'predict_calls_returned':0,'texts_returned':0,'fit_calls':0})
class ForwardedFrozenModel:
 def __init__(self,model,kind):self.model=model;self.kind=kind
 def predict_proba(self,texts):return self.call('predict_proba',texts)
 def decision_function(self,texts):return self.call('decision_function',texts)
 def call(self,method,texts):
  c=counts[self.kind];c['predict_calls_started']+=1
  value=getattr(self.model,method)(texts)
  c['predict_calls_returned']+=1;c['texts_returned']+=len(texts)
  if c['predict_calls_returned']in [1,5]or c['predict_calls_returned']%50==0:
   print(stable({'stage':'actual_frozen_predict_forwarded','model':self.kind,'method':method,**c}),flush=True)
  return value
 def fit(self,*a,**k):counts[self.kind]['fit_calls']+=1;raise RuntimeError('Detector fitting forbidden')
def audited_load(path,*args,**kwargs):
 model=original_load(path,*args,**kwargs);kind=Path(path).stem
 if kind in ['LR','LinearSVC']:
  counts[kind]['loaded_models']+=1
  return ForwardedFrozenModel(model,kind)
 return model
e.joblib.load=audited_load
started=datetime.datetime.now(datetime.timezone.utc);tick=time.monotonic()
sys.argv=[str(EVALUATOR),'--root',str(ROOT),'--models',str(ROOT/'models'),'--output',str(OUT),'--externalroot',str(EXTERNAL),'--expected-per-template','1200','--batch-size','256','--bootstrap','2000','--threads','1']
error=None
try:e.main()
except BaseException as exc:
 error={'type':type(exc).__name__,'message':str(exc)};traceback.print_exc()
finally:
 e.joblib.load=original_load
 after={str(p.relative_to(BASE)):sha(p)for p in source_paths}
 receipt={'status':'COMPLETE_ACTUAL_FROZEN_SPARSE_AND_RETRIEVAL_RERUN'if error is None else'INCOMPLETE_ERROR','started_utc':started.isoformat(),'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'local_user_date_timezone':'Pacific/Auckland','local_user_finished':datetime.datetime.now(ZoneInfo('Pacific/Auckland')).isoformat(),'elapsed_total_seconds':time.monotonic()-tick,'evaluator_file':str(EVALUATOR),'executed_evaluator_sha256':sha(EVALUATOR),'instrumentation_wrapper_sha256':sha(WRAPPER),'instrumentation_scope':'joblib.load returns a forward-only proxy; each actual immutable Pipeline predict_proba/decision_function executes and returns its original values. No prediction source is copied or substituted.','actual_model_call_counters':dict(counts),'detector_fits':sum(c['fit_calls']for c in counts.values()),'neural_calls':0,'generator_calls':0,'source_hashes_before':before,'source_hashes_after':after,'source_bytes_unchanged':before==after,'error':error,'scope':'Actual fresh sparse scoring, ordinary-only calibration, bootstrap analysis, passive external screening and exact lexical retrieval. This is not LLM answer generation or attack-success measurement.'}
 if OUT.exists():
  receipt['outputs_sha256']={p.name:sha(p)for p in sorted(OUT.iterdir())if p.is_file()and not p.name.startswith('.')}
  (OUT/'execution_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(receipt,ensure_ascii=False,indent=2),flush=True)
 if before!=after:raise RuntimeError('Source byte identities changed')
if error is not None:raise SystemExit(1)
