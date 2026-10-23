from pathlib import Path
import json,time
from qwen_cpu import PinnedQwen
model=PinnedQwen()
prompts=['What is 2 plus 3? Reply with the number only.', 'Use this fictional note to answer briefly. Note: The Aster library opens at 10 am on Tuesday. Question: At what time does it open on Tuesday?', 'Answer with the colour only. Fictional note: The laboratory marker is purple. Question: What colour is the laboratory marker?', 'Use this fictional note. The Kestrel ferry crosses in 18 minutes. State the crossing duration briefly.']
t=time.perf_counter();single=[model.generate(p) for p in prompts];single_time=time.perf_counter()-t
t=time.perf_counter();batch=model.generate_batch(prompts);batch_time=time.perf_counter()-t
result={'unrelated_prompts':prompts,'single_answers':[r['response'] for r in single],'batch_answers':[r['response'] for r in batch],'all_answers_identical':[r['response'] for r in single]==[r['response'] for r in batch],'single_total_seconds':single_time,'batch4_total_seconds':batch_time,'selected_batch_size':4 if batch_time<single_time and [r['response'] for r in single]==[r['response'] for r in batch] else 1,'note':'No NQ questions or attacks used; decision fixed before main generation.'}
Path(__file__).with_name('batch_benchmark.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
