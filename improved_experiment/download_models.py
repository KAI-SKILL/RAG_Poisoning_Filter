#!/usr/bin/env python3
"""Download only pinned public local-model assets and verify SHA-256."""
import hashlib,json,urllib.request
from pathlib import Path
HERE=Path(__file__).resolve().parent
for kind,manifest in json.loads((HERE/'model_manifests.json').read_text()).items():
    root=HERE/'models'/kind;root.mkdir(parents=True,exist_ok=True)
    for name,meta in manifest['downloaded_files'].items():
        p=root/name
        if not p.exists()or hashlib.sha256(p.read_bytes()).hexdigest()!=meta['sha256']:
            temp=p.with_suffix(p.suffix+'.partial')
            with urllib.request.urlopen(meta['url'],timeout=180)as src,temp.open('wb')as dst:
                while block:=src.read(2**20):dst.write(block)
            assert hashlib.sha256(temp.read_bytes()).hexdigest()==meta['sha256'],name
            temp.replace(p)
        print('Verified',kind,name,flush=True)
    (root/'model_manifest.json').write_text(json.dumps(manifest,indent=2))
