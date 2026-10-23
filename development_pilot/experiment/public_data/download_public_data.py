"""Download original, public evaluation data; never used for fitting/tuning."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib, json, urllib.request, time
ROOT = Path(__file__).resolve().parent
BASE = 'https://raw.githubusercontent.com/leolee99/PIGuard/main/'
FILES = {'NotInject_one.json': 'https://raw.githubusercontent.com/leolee99/PIGuard/main/datasets/NotInject_one.json', 'NotInject_two.json': 'https://raw.githubusercontent.com/leolee99/PIGuard/main/datasets/NotInject_two.json', 'NotInject_three.json': 'https://raw.githubusercontent.com/leolee99/PIGuard/main/datasets/NotInject_three.json', 'BIPIA_text.json': 'https://raw.githubusercontent.com/leolee99/PIGuard/main/datasets/BIPIA_text.json', 'BIPIA_code.json': 'https://raw.githubusercontent.com/leolee99/PIGuard/main/datasets/BIPIA_code.json', 'PIGuard_LICENSE': 'https://raw.githubusercontent.com/leolee99/PIGuard/main/LICENSE', 'PIGuard_README.md': 'https://raw.githubusercontent.com/leolee99/PIGuard/main/README.md', 'PIGuard_eval_hf.py.txt': 'https://raw.githubusercontent.com/leolee99/PIGuard/main/eval_hf.py', 'NotInject_dataset_metadata.json': 'https://huggingface.co/api/datasets/leolee99/NotInject', 'NotInject_dataset_card.md': 'https://huggingface.co/datasets/leolee99/NotInject/raw/847ae76cf8fea5ed325429e569ae8cfef022d2e0/README.md', 'BIPIA_LICENSE': 'https://raw.githubusercontent.com/microsoft/BIPIA/main/LICENSE', 'text_attack_train.json': 'https://raw.githubusercontent.com/microsoft/BIPIA/main/benchmark/text_attack_train.json', 'text_attack_test.json': 'https://raw.githubusercontent.com/microsoft/BIPIA/main/benchmark/text_attack_test.json', 'code_attack_train.json': 'https://raw.githubusercontent.com/microsoft/BIPIA/main/benchmark/code_attack_train.json', 'code_attack_test.json': 'https://raw.githubusercontent.com/microsoft/BIPIA/main/benchmark/code_attack_test.json', 'DistilBERT_ONNX_card.md': 'https://huggingface.co/protectai/fmops-distilbert-prompt-injection-onnx/raw/fcd250e33cdb9b78f3ee84ff13d59ff7aae2faf5/README.md', 'DistilBERT_ONNX_metadata.json': 'https://huggingface.co/api/models/protectai/fmops-distilbert-prompt-injection-onnx', 'DistilBERT_source_card.md': 'https://huggingface.co/fmops/distilbert-prompt-injection/raw/main/README.md', 'DistilBERT_source_metadata.json': 'https://huggingface.co/api/models/fmops/distilbert-prompt-injection', 'DistilBERT_ONNX_commits.json': 'https://huggingface.co/api/models/protectai/fmops-distilbert-prompt-injection-onnx/commits/main', 'DistilBERT_source_commits.json': 'https://huggingface.co/api/models/fmops/distilbert-prompt-injection/commits/main', 'deepset_training_metadata.json': 'https://huggingface.co/api/datasets/deepset/prompt-injections', 'deepset_training_card.md': 'https://huggingface.co/datasets/deepset/prompt-injections/raw/main/README.md', 'BIPIA_README.md': 'https://raw.githubusercontent.com/microsoft/BIPIA/main/README.md', 'DistilBERT_ONNX_tree_fcd250e33cdb9b78f3ee84ff13d59ff7aae2faf5.json': 'https://huggingface.co/api/models/protectai/fmops-distilbert-prompt-injection-onnx/tree/fcd250e33cdb9b78f3ee84ff13d59ff7aae2faf5?recursive=true', 'DistilBERT_ONNX_tree_aa128590e6e1e8a86b42cc678a8084524ea833d6.json': 'https://huggingface.co/api/models/protectai/fmops-distilbert-prompt-injection-onnx/tree/aa128590e6e1e8a86b42cc678a8084524ea833d6?recursive=true', 'DistilBERT_source_tree_c5da1fefd33c98c447b50dd806fe86aeb9e8c26c.json': 'https://huggingface.co/api/models/fmops/distilbert-prompt-injection/tree/c5da1fefd33c98c447b50dd806fe86aeb9e8c26c?recursive=true'}

def get(item):
 name,url=item
 for attempt in range(3):
  try:
   with urllib.request.urlopen(url,timeout=35) as r: data=r.read()
   (ROOT/name).write_bytes(data)
   return name,dict(url=url,bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
  except Exception:
   if attempt==2: raise
   time.sleep(1)
if __name__=='__main__':
 with ThreadPoolExecutor(max_workers=8) as ex: manifest=dict(ex.map(get,FILES.items()))
 (ROOT/'download_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 for name,info in manifest.items(): print(name,info['bytes'])
