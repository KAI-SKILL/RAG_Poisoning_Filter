"""Download the immutable official 3B GGUF from the bundled audited manifest."""
from pathlib import Path
import argparse,hashlib,json,time,urllib.request
HERE=Path(__file__).resolve().parent

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--model-dir',type=Path,default=HERE/'models/Qwen2.5-3B-Instruct-GGUF');a=p.parse_args();a.model_dir.mkdir(parents=True,exist_ok=True)
 manifest=json.loads((HERE/'generator_model_manifest.json').read_text())
 for f in manifest['files']:
  out=a.model_dir/f['file']
  if not out.is_file()or hashlib.file_digest(out.open('rb'),'sha256').hexdigest()!=f['sha256']:
   tmp=out.with_suffix(out.suffix+'.partial');n=0;start=time.monotonic();last=start
   with urllib.request.urlopen(f['url'],timeout=180)as r,tmp.open('wb')as w:
    while b:=r.read(2**20):
     w.write(b);n+=len(b)
     if time.monotonic()-last>20:print(f['file'],n,'bytes',round(time.monotonic()-start,1),'seconds',flush=True);last=time.monotonic()
   assert tmp.stat().st_size==f['bytes']and hashlib.file_digest(tmp.open('rb'),'sha256').hexdigest()==f['sha256'];tmp.replace(out)
  print('Verified:',out.name,out.stat().st_size,flush=True)
 (a.model_dir/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
if __name__=='__main__':main()
