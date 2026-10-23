"""Official pinned Qwen2.5-0.5B-Instruct; local-only CPU float32 inference."""
from pathlib import Path
import os,time
os.environ.setdefault('HF_HUB_OFFLINE','1')
os.environ.setdefault('TRANSFORMERS_OFFLINE','1')
os.environ.setdefault('HF_HUB_DISABLE_TELEMETRY','1')
import torch
from transformers import AutoModelForCausalLM,AutoTokenizer

class PinnedQwen:
 def __init__(self,threads=4,max_new_tokens=64):
  self.model_dir=Path(__file__).resolve().parent/'models'/'Qwen2.5-0.5B-Instruct'
  torch.set_num_threads(threads);torch.set_num_interop_threads(1);torch.manual_seed(12)
  self.max_new_tokens=max_new_tokens
  self.tokenizer=AutoTokenizer.from_pretrained(str(self.model_dir),local_files_only=True,padding_side='left')
  if self.tokenizer.pad_token is None:self.tokenizer.pad_token=self.tokenizer.eos_token
  self.model=AutoModelForCausalLM.from_pretrained(str(self.model_dir),local_files_only=True,dtype=torch.float32).to('cpu').eval()
  for p in self.model.parameters():p.requires_grad_(False)
  self.parameter_count=sum(p.numel() for p in self.model.parameters())
  self.max_positions=self.model.config.max_position_embeddings
 def render(self,prompt):
  return self.tokenizer.apply_chat_template([{'role':'system','content':'You are a helpful assistant.'},{'role':'user','content':prompt}],tokenize=False,add_generation_prompt=True)
 def generate_batch(self,prompts):
  chats=[self.render(p) for p in prompts];t=time.perf_counter()
  encoded=self.tokenizer(chats,return_tensors='pt',padding=True,truncation=False)
  width=encoded['input_ids'].shape[1]
  if width+self.max_new_tokens>self.max_positions:raise ValueError(f'Padded input {width}+generation exceeds context {self.max_positions}; refusing truncation.')
  with torch.inference_mode():
   generated=self.model.generate(**encoded,max_new_tokens=self.max_new_tokens,do_sample=False,pad_token_id=self.tokenizer.pad_token_id)
  seconds=time.perf_counter()-t;results=[]
  for i,chat in enumerate(chats):
   new=generated[i,width:].tolist()
   eos=self.model.generation_config.eos_token_id
   eos=set(eos if isinstance(eos,list) else [eos])
   first=next((j for j,x in enumerate(new) if x in eos),None)
   if first is not None:new=new[:first+1]
   results.append({'response':self.tokenizer.decode(new,skip_special_tokens=True),'chat_prompt':chat,'input_tokens':int(encoded['attention_mask'][i].sum()),'padded_input_tokens':width,'generated_tokens':len(new),'batch_seconds':seconds,'batch_size':len(prompts),'seconds':seconds/len(prompts),'truncated':False,'at_generation_cap':len(new)>=self.max_new_tokens,'ended_with_eos':first is not None,'hit_generation_cap':len(new)>=self.max_new_tokens and first is None})
  return results
 def generate(self,prompt):
  chat=self.render(prompt);t=time.perf_counter()
  encoded=self.tokenizer(chat,return_tensors='pt',padding=False,truncation=False)
  n=encoded['input_ids'].shape[1]
  if n+self.max_new_tokens>self.max_positions:raise ValueError(f'Input {n}+generation allowance exceeds model context {self.max_positions}; refusing silent truncation.')
  with torch.inference_mode():
   gen=self.model.generate(**encoded,max_new_tokens=self.max_new_tokens,do_sample=False,pad_token_id=self.tokenizer.pad_token_id)
  new=gen[0,n:].tolist()
  eos=self.model.generation_config.eos_token_id;eos=set(eos if isinstance(eos,list) else [eos])
  ended=bool(new and new[-1] in eos)
  answer=self.tokenizer.decode(new,skip_special_tokens=True)
  return {'response':answer,'chat_prompt':chat,'input_tokens':n,'generated_tokens':len(new),'seconds':time.perf_counter()-t,'truncated':False,'at_generation_cap':len(new)>=self.max_new_tokens,'ended_with_eos':ended,'hit_generation_cap':len(new)>=self.max_new_tokens and not ended}

if __name__=='__main__':
 import json
 model=PinnedQwen()
 prompts=['What is 2 plus 3? Reply with the number only.', 'Use this fictional note to answer briefly. Note: The Aster library opens at 10 am on Tuesday. Question: At what time does it open on Tuesday?']
 print(json.dumps({'parameter_count':model.parameter_count,'torch_version':torch.__version__,'max_positions':model.max_positions}))
 for p in prompts:print(json.dumps({'prompt':p,**model.generate(p)}),flush=True)
