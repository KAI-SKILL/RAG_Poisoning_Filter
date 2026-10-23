"""Passive, revision-pinned academic benchmark retrieval; executes no tools."""
from pathlib import Path
import urllib.request,json,hashlib,datetime,concurrent.futures,re,collections
ROOT=Path(__file__).resolve().parent
AGENTDOJO_REPO='ethz-spylab/agentdojo'
AGENTDOJO_SHA='089ed468cf3ed0322acc66b0211f26d9d90dbf60'
INJECAGENT_REPO='uiuc-kang-lab/InjecAgent'
INJECAGENT_SHA='f19c9f2c79a41046eb13c03c51a24c567a8ffa07'
USER_AGENT='COMPSCI764-academic-benchmark-audit'
def get(repo,sha,rel,folder):
 url=f'https://raw.githubusercontent.com/{repo}/{sha}/{rel}'
 req=urllib.request.Request(url,headers={'User-Agent':USER_AGENT})
 data=urllib.request.urlopen(req,timeout=60).read()
 p=ROOT/folder/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 return {'relative_path':str(p.relative_to(ROOT)),'source_url':url,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
def main():
 paths=json.loads((ROOT/'agentdojo_clean_paths.json').read_text())
 assert len(paths)==97
 requests=[(AGENTDOJO_REPO,AGENTDOJO_SHA,n,'agentdojo')for n in ['README.md','LICENSE']+paths]
 requests += [(INJECAGENT_REPO,INJECAGENT_SHA,n,'InjecAgent')for n in ['README.md','data/test_cases_dh_base.json','data/test_cases_ds_base.json','data/attacker_cases_dh.jsonl','data/attacker_cases_ds.jsonl','data/user_cases.jsonl','data/tools.json']]
 with concurrent.futures.ThreadPoolExecutor(max_workers=8)as ex:manifest=list(ex.map(lambda x:get(*x),requests))
 (ROOT/'primary_download_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 malicious=[]
 for code,name in [('dh','test_cases_dh_base.json'),('ds','test_cases_ds_base.json')]:
  for i,row in enumerate(json.loads((ROOT/'InjecAgent/data'/name).read_text())):
   instruction=row['Attacker Instruction'];question=row['User Instruction'];context=row['Tool Response']
   payload_parent=hashlib.sha256(instruction.encode()).hexdigest()
   user_parent=hashlib.sha256((row['User Tool']+'\n'+question).encode()).hexdigest()
   malicious.append({'id':f'injecagent-{code}-{i:04}','dataset':'InjecAgent_base','label':1,'family':row['Attack Type'],'threat_class':'indirect_tool_output_injection','question':question,'text':context,'payload':instruction,'payload_parent':payload_parent,'source_group':user_parent,'user_tool':row['User Tool'],'attacker_tools':row['Attacker Tools'],'original_file':f'InjecAgent/data/{name}','original_row':i,'upstream_repo':INJECAGENT_REPO,'upstream_revision':INJECAGENT_SHA,'label_scope':'malicious in this task/tool-output placement; detector probe only, no agent execution'})
 benign=[];errors=0
 for rel in sorted(paths):
  row=json.loads((ROOT/'agentdojo'/rel).read_text())
  assert not row['injections'] and row['attack_type'] is None and row['injection_task_id']is None
  question=next((m['content']for m in row['messages']if m['role']=='user'),'')
  for i,message in enumerate(row['messages']):
   if message['role']!='tool':continue
   if message.get('error')is not None:errors+=1;continue
   text=message.get('content')
   if not isinstance(text,str)or not text.strip():continue
   source_group=row['suite_name']+'/'+row['user_task_id']
   benign.append({'id':f'agentdojo-{row["suite_name"]}-{row["user_task_id"]}-message{i}','dataset':'AgentDojo_clean_tool_output','label':0,'family':row['suite_name'],'threat_class':'benign_tool_output','question':question,'text':text,'source_group':source_group,'payload_parent':None,'function':message.get('tool_call',{}).get('function'),'text_sha256':hashlib.sha256(text.encode()).hexdigest(),'original_file':'agentdojo/'+rel,'original_message_index':i,'upstream_repo':AGENTDOJO_REPO,'upstream_revision':AGENTDOJO_SHA,'label_scope':'no-injection archived run; tool output screening only, not a new live replay or human semantic annotation'})
 def write(name,rows):
  (ROOT/name).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n'for r in rows))
 write('injecagent_base_contexts.jsonl',malicious)
 write('agentdojo_clean_tool_outputs_all.jsonl',benign)
 seen=collections.OrderedDict()
 for r in benign:
  key=r['text_sha256']
  if key not in seen:seen[key]={**r,'all_source_groups':[],'all_original_ids':[]}
  entry=seen[key]
  if r['source_group']not in entry['all_source_groups']:entry['all_source_groups'].append(r['source_group'])
  entry['all_original_ids'].append(r['id'])
 dedup=list(seen.values())
 write('agentdojo_clean_tool_outputs_unique.jsonl',dedup)
 summary={'InjecAgent':{'repo':INJECAGENT_REPO,'revision':INJECAGENT_SHA,'base_context_records':len(malicious),'attack_type_counts':dict(collections.Counter(r['family']for r in malicious)),'unique_payload_parents':len(set(r['payload_parent']for r in malicious)),'unique_user_task_parents':len(set(r['source_group']for r in malicious)),'unique_rendered_contexts':len(set(r['text']for r in malicious)),'license_observation':'No standalone LICENSE file found in pinned repository tree; preserve source attribution and do not assert a permissive data license.'},'AgentDojo':{'repo':AGENTDOJO_REPO,'revision':AGENTDOJO_SHA,'pipeline':'gpt-4o-2024-05-13','clean_archived_tasks':len(paths),'tool_output_records':len(benign),'exact_unique_tool_outputs':len(dedup),'nonempty_successful_tool_output_policy':True,'excluded_error_tool_messages':errors,'task_groups':len(set(r['source_group']for r in benign)),'suite_counts':dict(collections.Counter(r['family']for r in benign)),'license_observation':'MIT repository LICENSE downloaded unchanged.','scope':'Archived public no-injection tool traces, passively downloaded; no new environment replay, tool use, or agent generation.'}}
 (ROOT/'source_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
 print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
