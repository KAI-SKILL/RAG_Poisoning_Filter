#!/usr/bin/env python3
"""Download immutable public safetensors weights and verify every file by SHA-256."""
import hashlib,json,urllib.request
from pathlib import Path

HERE=Path(__file__).resolve().parent
manifest=json.loads((HERE/'model_manifest.json').read_text())
dst=HERE/'models'/'distilbert';dst.mkdir(parents=True,exist_ok=True)
for name,meta in manifest['files'].items():
    p=dst/name
    if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest()!=meta['sha256']:
        url=f"https://huggingface.co/{manifest['model']}/resolve/{manifest['revision']}/{name}"
        print('Downloading',name,flush=True)
        temp=p.with_suffix(p.suffix+'.partial')
        with urllib.request.urlopen(url,timeout=180) as source,temp.open('wb') as out:
            while block:=source.read(2**20):out.write(block)
        if hashlib.sha256(temp.read_bytes()).hexdigest()!=meta['sha256']:
            raise RuntimeError('SHA-256 mismatch: '+name)
        temp.replace(p)
    print('Verified',name,flush=True)
(dst/'provenance.json').write_text(json.dumps(manifest,indent=2))
