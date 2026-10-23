"""Fetch only immutable project encoder assets, checking every SHA-256."""
from pathlib import Path
import hashlib,json,time,urllib.request
BASE=Path(__file__).resolve().parent
SOURCE=BASE/'source_manifest.json'
manifest=json.loads(SOURCE.read_text())
for kind in ('contriever','guard'):
    spec=manifest[kind]; root=BASE/'models'/kind;root.mkdir(parents=True,exist_ok=True)
    for name, meta in spec['downloaded_files'].items():
        p=root/name
        if not p.exists() or hashlib.file_digest(p.open('rb'),'sha256').hexdigest()!=meta['sha256']:
            tmp=p.with_suffix(p.suffix+'.partial'); begin=time.monotonic(); n=0;last=begin
            with urllib.request.urlopen(meta['url'],timeout=180) as r,tmp.open('wb') as w:
                while block:=r.read(2**20):
                    w.write(block); n+=len(block)
                    if time.monotonic()-last>20:
                        print(json.dumps({'kind':kind,'file':name,'bytes':n,'seconds':time.monotonic()-begin}),flush=True);last=time.monotonic()
            digest=hashlib.file_digest(tmp.open('rb'),'sha256').hexdigest()
            assert digest==meta['sha256'],(name,digest)
            assert tmp.stat().st_size==meta['bytes'],name
            tmp.replace(p)
        print('verified',kind,name,p.stat().st_size,flush=True)
    (root/'model_manifest.json').write_text(json.dumps(spec,indent=2)+'\n')
(BASE/'source_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
