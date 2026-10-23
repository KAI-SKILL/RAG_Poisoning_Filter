import urllib.request,json,concurrent.futures,hashlib
from pathlib import Path
root=Path(__file__).resolve().parent/'sources'
def get(repo):
 url=f'https://api.github.com/repos/{repo}/git/trees/main?recursive=1'
 try:
  b=urllib.request.urlopen(url,timeout=25).read();a=json.loads(b);(root/(repo.replace('/','_')+'_tree.json')).write_bytes(b)
  return repo, a.get('sha'), [(x['path'],x.get('size',0)) for x in a.get('tree',[]) if x['type']=='blob']
 except Exception as e:return repo,str(e)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as p:
 for x in p.map(get,['sleeepeer/PoisonedRAG','zhangbl6618/CorruptRAG','rajpurkar/SQuAD-explorer']):print(json.dumps(x))
