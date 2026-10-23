#!/usr/bin/env python3
"""Precache a pinned official model; no GPU inference or scheduler action."""
from pathlib import Path
import argparse, json

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('model_key',choices=['qwen3_8b','llama31_8b'])
    p.add_argument('--cache-dir',type=Path,required=True)
    p.add_argument('--plan',action='store_true')
    a=p.parse_args()
    registry=json.loads(Path(__file__).with_name('model_registry.json').read_text())
    model=registry[a.model_key]
    if a.plan:
        print(json.dumps({'model':model,'cache_dir':str(a.cache_dir),'download_executed':False,'inference_executed':False},indent=2));return
    from huggingface_hub import snapshot_download
    directory=snapshot_download(repo_id=model['model_id'],revision=model['revision'],cache_dir=str(a.cache_dir),allow_patterns=['*.json','*.safetensors','*.model','*.txt','*.jinja','LICENSE*','README*'])
    print(json.dumps({'status':'MODEL_CACHE_READY_NOT_INFERENCE','model_id':model['model_id'],'revision':model['revision'],'snapshot_directory':directory,'inference_executed':False},indent=2))

if __name__=='__main__':main()
