"""LLM back-ends for the generation step.

  openai : any OpenAI-compatible API (default gpt-4o-mini). Needs OPENAI_API_KEY
           (set OPENAI_BASE_URL to use another compatible provider).
  hf     : local HuggingFace instruct model, batched (default Qwen/Qwen2.5-3B-Instruct,
           fits a free Colab T4 in fp16).
  mock   : no model - returns the answer stated in the first context passage it can find.
           For smoke tests only.
Greedy / temperature-0 decoding everywhere so runs are reproducible.
"""
import os
import re


class OpenAILLM:
    def __init__(self, model="gpt-4o-mini", max_tokens=64):
        from openai import OpenAI
        self.client = OpenAI(base_url=os.environ.get("OPENAI_BASE_URL") or None)
        self.model, self.max_tokens = model, max_tokens

    def generate(self, prompts):
        outs = []
        for p in prompts:
            try:
                r = self.client.chat.completions.create(
                    model=self.model, temperature=0, max_tokens=self.max_tokens,
                    messages=[{"role": "system", "content": "You are a helpful assistant."},
                              {"role": "user", "content": p}])
                outs.append(r.choices[0].message.content or "")
            except Exception as e:  # keep going; empty answer counts as failure for both metrics
                print("API error:", e)
                outs.append("")
        return outs


class HFLLM:
    def __init__(self, model="Qwen/Qwen2.5-3B-Instruct", max_tokens=64, batch_size=8):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.torch = torch
        self.tok = AutoTokenizer.from_pretrained(model, padding_side="left")
        if self.tok.pad_token is None:
            self.tok.pad_token = self.tok.eos_token
        self.model = AutoModelForCausalLM.from_pretrained(
            model, torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto").eval()
        self.max_tokens, self.bs = max_tokens, batch_size

    def generate(self, prompts):
        outs = []
        for i in range(0, len(prompts), self.bs):
            chats = [self.tok.apply_chat_template(
                [{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": p}],
                tokenize=False, add_generation_prompt=True) for p in prompts[i:i + self.bs]]
            enc = self.tok(chats, return_tensors="pt", padding=True).to(self.model.device)
            with self.torch.no_grad():
                gen = self.model.generate(**enc, max_new_tokens=self.max_tokens, do_sample=False,
                                          pad_token_id=self.tok.pad_token_id)
            outs += self.tok.batch_decode(gen[:, enc["input_ids"].shape[1]:], skip_special_tokens=True)
        return outs


class MockLLM:
    """Pretends to be a gullible LLM: obeys 'output X' / 'answer is X' patterns, else echoes passage 1."""

    def generate(self, prompts):
        outs = []
        for p in prompts:
            ctx = p.split("Contexts:")[1].split("Query:")[0]
            m = re.search(r"(?:please output|answer is|respond with exactly:|must answer|should be|verified answer is) ([^.;\n]+)", ctx)
            outs.append(m.group(1) if m else ctx.strip()[:80])
        return outs


def get_llm(backend, model=None, **kw):
    if backend == "openai":
        return OpenAILLM(model or "gpt-4o-mini", **kw)
    if backend == "hf":
        return HFLLM(model or "Qwen/Qwen2.5-3B-Instruct", **kw)
    if backend == "mock":
        return MockLLM()
    raise ValueError(backend)
