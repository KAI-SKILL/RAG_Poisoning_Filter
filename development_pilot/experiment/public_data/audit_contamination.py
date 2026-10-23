"""Audit textual overlap with disclosed detector dataset (NOT train/tune)."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json,hashlib,urllib.request
from load_public_data import load_records,normalize_text
ROOT=Path(__file__).resolve().parent

def get_page(pair):
 split,offset=pair
 url=f'https://datasets-server.huggingface.co/rows?dataset=deepset%2Fprompt-injections&config=default&split={split}&offset={offset}&length=100'
 with urllib.request.urlopen(url,timeout=40) as r: data=json.load(r)
 assert not data.get('partial',False)
 return split,[x['row'] for x in data['rows']]

if __name__=='__main__':
 groups={'train':[], 'test':[]}
 with ThreadPoolExecutor(max_workers=8) as ex:
  for split,rows in ex.map(get_page, [('train',i) for i in range(0,546,100)]+[('test',i) for i in range(0,116,100)]):groups[split].extend(rows)
 assert len(groups['train'])==546 and len(groups['test'])==116
 external=load_records()
 report={'comparison_dataset':'deepset/prompt-injections',
   'comparison_revision_observed':'4f61ecb038e9c3fb77e21034b22511b523772cdd',
   'caveat':'Rows API serves current dataset, not proven exact historical July 2023 model training snapshot. Original model training recipe and exact records are not released. This is a disclosed-source overlap audit, not proof of no pretraining/finetuning contamination.',
   'source_card_license_conflict':'Top-level Apache-2.0, nested dataset_info cc-by-4.0. Dataset text is not redistributed by this audit.',
   'comparison_rows':{s:len(rows) for s,rows in groups.items()}, 'overlaps':{}}
 for dataset in ['NotInject','BIPIA']:
  ext=[r for r in external if r['dataset']==dataset]
  report['overlaps'][dataset]={'n_external':len(ext)}
  for split,rows in groups.items():
   exact={r['text'] for r in rows};norm={normalize_text(r['text']) for r in rows}
   report['overlaps'][dataset][split]={'exact':sum(r['text'] in exact for r in ext),'normalized':sum(normalize_text(r['text']) in norm for r in ext),
       'matching_external_ids':[r['id'] for r in ext if normalize_text(r['text']) in norm]}
 (ROOT/'contamination_audit.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))
