"""Export registered scopes with device, scoring and postanalysis completion gates.

The existing exporter still performs its original SQLite snapshot and closure.
Its optional stage callback adds the all-experiment requirements before either
the COMPLETE receipt or COMPLETE ZIP filename can be created.
"""
from pathlib import Path
import argparse,importlib.util,json

ROOT=Path(__file__).resolve().parents[2]
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def export(source,destination,project_root=ROOT):
 root=Path(project_root).resolve();destination=Path(destination).resolve();model=destination.parent.name;scope=destination.name
 collector=load(root/'generation/all_experiments/collect_all_results.py','group9_strong_export_collector')
 if model not in collector.MODELS or scope not in collector.SCOPES:raise ValueError('Destination must end in a registered model_key/scope')
 base=load(root/'generation/hf_gpu/export_hf_results.py','group9_base_closed_export')
 def validate(stage):
  # Preserve useful raw checkpoints quickly before scoring/postanalysis. Their
  # process or generator status can never promote them to COMPLETE here.
  required=['suite_scope_binding.json','scoring/scoring_manifest.json','postanalysis/postanalysis_manifest.json']
  missing=[name for name in required if not(Path(stage)/name).is_file()]
  if missing:return {'status':'INCOMPLETE_CHECKPOINT','issues':['Missing required complete-scope artifact: '+name for name in missing]}
  try:return collector.Inspector(root).validate_payload(stage,model,scope)
  except Exception as error:return {'status':'INCOMPLETE_OR_INVALID_RESULT','issues':[type(error).__name__+': '+str(error)]}
 return base.export(Path(source),destination,complete_validator=validate)

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',type=Path,required=True);parser.add_argument('--destination',type=Path,required=True);parser.add_argument('--project-root',type=Path,default=ROOT);a=parser.parse_args();print(json.dumps(export(a.source,a.destination,a.project_root),indent=2))
if __name__=='__main__':main()
