"""Frozen official FLAN-T5-small, CPU PyTorch, deterministic greedy decoding."""
from pathlib import Path
import os,time
os.environ.setdefault('HF_HUB_OFFLINE','1')
os.environ.setdefault('TRANSFORMERS_OFFLINE','1')
os.environ.setdefault('HF_HUB_DISABLE_TELEMETRY','1')
import torch
from transformers import AutoModelForSeq2SeqLM,AutoTokenizer

class FlanTorch:
 def __init__(self, model_dir=None, threads=4, max_input_tokens=1024, max_new_tokens=32):
  self.model_dir=Path(model_dir or Path(__file__).resolve().parent/'models'/'flan-t5-small-torch')
  self.max_input_tokens=max_input_tokens
  self.max_new_tokens=max_new_tokens
  torch.set_num_threads(threads)
  torch.set_num_interop_threads(1)
  torch.manual_seed(764)
  self.tokenizer=AutoTokenizer.from_pretrained(str(self.model_dir),local_files_only=True)
  self.model=AutoModelForSeq2SeqLM.from_pretrained(str(self.model_dir),local_files_only=True,dtype=torch.float32).to('cpu').eval()
  for p in self.model.parameters():p.requires_grad_(False)
  self.parameter_count=sum(p.numel() for p in self.model.parameters())
 def generate(self,prompt):
  started=time.perf_counter()
  ids=self.tokenizer.encode(prompt,add_special_tokens=True,truncation=False)
  original_n=len(ids)
  if len(ids)>self.max_input_tokens:ids=ids[:self.max_input_tokens-1]+[1]
  encoded=torch.tensor([ids],dtype=torch.int64);mask=torch.ones_like(encoded)
  with torch.inference_mode():
   output=self.model.generate(input_ids=encoded,attention_mask=mask,max_new_tokens=self.max_new_tokens,do_sample=False,num_beams=1,decoder_start_token_id=0,eos_token_id=1,pad_token_id=0,use_cache=True)
  generated=output[0].tolist()
  if generated and generated[0]==0:generated=generated[1:]
  if generated and generated[-1]==1:generated=generated[:-1]
  return {'answer':self.tokenizer.decode(generated,skip_special_tokens=True),'input_tokens':original_n,'used_input_tokens':len(ids),'truncated':original_n>len(ids),'generated_tokens':len(generated),'seconds':time.perf_counter()-started}

if __name__=='__main__':
 import json
 model=FlanTorch()
 print(json.dumps({'parameter_count':model.parameter_count,'torch_version':torch.__version__}))
 for prompt in ['Answer the question using the context. Context: The library opens at 9 am. Question: At what time does the library open? Answer:', 'Answer the question using the context. Context: The laboratory has 42 microscopes. Question: How many microscopes does the laboratory have? Answer:']:
  print(json.dumps(model.generate(prompt)),flush=True)
