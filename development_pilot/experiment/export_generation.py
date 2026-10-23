#!/usr/bin/env python3
"""Export frozen detector gates for paired downstream generation evaluation.

For clean contexts, remove the malicious passage and recompute the label-blind
retrieval feature against the remaining five peers. The neural text score is
unchanged because each retained passage's text is unchanged. Fusion weights and
all thresholds are loaded from the completed detector run and never refitted.
"""
import json
from pathlib import Path
import numpy as np
from scipy.special import expit
from benchmark import HERE,OUT,retrieval_scores

def main():
    summary=json.loads((OUT/'results.json').read_text())
    groups=[json.loads(x) for x in (HERE/'data'/'groups.jsonl').read_text().splitlines()]
    pred={r['id']:r for r in map(json.loads,(OUT/'predictions.jsonl').read_text().splitlines())}
    methods=['acceptall','keyword','lexical','retrieval','neural','combined']
    coef=summary['fusion']['weights'];intercept=summary['fusion']['intercept'];out=[]
    for group in groups:
        if not group['split'].startswith('test'):continue
        for condition in ['clean','attacked']:
            gg={**group,'passages':[p for p in group['passages'] if condition=='attacked' or p['label']==0]}
            retrieval,_=retrieval_scores([gg])
            for method in methods:
                accepted=[]
                for i,p in enumerate(gg['passages']):
                    if method=='acceptall':keep=True
                    else:
                        score=pred[p['id']]['scores'][method]
                        if condition=='clean' and method=='retrieval':score=float(retrieval[i])
                        if condition=='clean' and method=='combined':score=float(expit(intercept+coef[0]*pred[p['id']]['scores']['neural']+coef[1]*retrieval[i]))
                        t=summary['thresholds'][method];keep=score<(float('inf') if t is None else t)
                    if keep:accepted.append(p)
                out.append(dict(group_id=group['group_id'],split=group['split'],family=next(p['family'] for p in group['passages'] if p['label']),gate=method,condition=condition,query=group['question'],gold_answer=group['gold_answer'],attack_target=group['attack_target'],context='\n\n'.join(p['text'] for p in accepted),retained_ids=[p['id'] for p in accepted],empty_context=len(accepted)==0,contains_benign_attack_quotation=True))
    with (OUT/'generation_contexts.jsonl').open('w') as f:
        for row in out:f.write(json.dumps(row)+'\n')
    counts={}
    for s in ['test_topic','test_joint','test_poison']:
        counts[s]={m:{c:sum(r['empty_context'] for r in out if r['split']==s and r['gate']==m and r['condition']==c) for c in ['clean','attacked']} for m in methods}
    (OUT/'empty_context_counts.json').write_text(json.dumps(counts,indent=2))
    print('Exported',len(out),'paired clean/attacked contexts. Clean contexts retain benign target-bearing quotations; retrieval peer scores recomputed independently.')
if __name__=='__main__':main()
