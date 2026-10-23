import urllib.request,json,hashlib,time
from pathlib import Path
root=Path(__file__).resolve().parent/'sources'
urls={
 'squad_train-v1.1.json':'https://rajpurkar.github.io/SQuAD-explorer/dataset/train-v1.1.json',
 'poisonedrag_prepare.py':'https://raw.githubusercontent.com/sleeepeer/PoisonedRAG/main/prepare_dataset.py',
 'poisonedrag_gen_adv.py':'https://raw.githubusercontent.com/sleeepeer/PoisonedRAG/main/gen_adv.py',
 'poisonedrag_readme.md':'https://raw.githubusercontent.com/sleeepeer/PoisonedRAG/main/README.md',
 'squad_README.md':'https://raw.githubusercontent.com/rajpurkar/SQuAD-explorer/master/README.md',
}
manifest=[]
for name,url in urls.items():
 try:
  with urllib.request.urlopen(url,timeout=30) as r:
   data=r.read(25_000_000)
  (root/name).write_bytes(data)
  row={'file':name,'url':url,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'status':'downloaded'}
 except Exception as e:row={'file':name,'url':url,'error':str(e),'status':'failed'}
 manifest.append(row);print(json.dumps(row),flush=True)
(root/'source_manifest.json').write_text(json.dumps(manifest,indent=2))
