"""Download public immutable official Qwen artifacts; no inference or API keys."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,time,urllib.request
ROOT=Path(__file__).resolve().parent/'models'/'Qwen2.5-0.5B-Instruct'
REV='7ae557604adf67be50417f59c2c2f167def9a775'
REPO='Qwen/Qwen2.5-0.5B-Instruct'
FILES=['config.json','generation_config.json','tokenizer.json','tokenizer_config.json','model.safetensors','LICENSE','README.md']
ROOT.mkdir(parents=True,exist_ok=True)
def fetch(file):
 p=ROOT/file;url=f'https://huggingface.co/{REPO}/resolve/{REV}/{file}'
 if not p.exists():
  for attempt in range(4):
   try:
    with urllib.request.urlopen(url,timeout=60) as r,p.with_suffix(p.suffix+'.tmp').open('wb') as f:
     while block:=r.read(1<<20):f.write(block)
    p.with_suffix(p.suffix+'.tmp').replace(p);break
   except Exception:
    if attempt==3:raise
    time.sleep(2)
 print(file,p.stat().st_size,flush=True)
 return {'file':file,'url':url,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
with ThreadPoolExecutor(max_workers=4) as pool:records=list(pool.map(fetch,FILES))
manifest=json.dumps({'repository':REPO,'revision':REV,'files':records},indent=2)
(ROOT/'manifest.json').write_text(manifest)
(Path(__file__).resolve().parent/'model_manifest.json').write_text(manifest)
