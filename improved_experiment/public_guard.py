#!/usr/bin/env python3
"""Standalone NotInject stress test, using the five frozen guard thresholds.

No fusion is evaluated without an actual query and retrieved peer pool. The same
339 texts are evaluated under each fold threshold; these are not 1695 independent
examples and are not used for training or calibration.
"""
import numpy as np
from run import HERE,OUT,read,write,jsonl,cached_inference

def main():
    records=read(HERE/'inputs/notinject.json');assert len(records)==339
    texts=sorted({r['prompt']for r in records},key=lambda s:(len(s),s));scores=cached_inference(texts,'guard_ni')
    taus=[r['threshold']for r in read(OUT/'calibration.json')if r['variant']=='guard'];assert len(taus)==5
    rows=[{**r,'risk':float(scores[r['prompt']][0]),'blocked_by_fold':[bool(scores[r['prompt']][0]>t)for t in taus]}for r in records]
    cohorts={'all':rows,'multilingual_category':[r for r in rows if r['category']=='Multilingual'],'other_category':[r for r in rows if r['category']!='Multilingual']}
    summary={'scope':'External standalone benign prompt stress test, no queries/peers; no fusion or generator claims; frozen per-fold thresholds, no retuning. Cohorts use supplied category rather than detected language.','thresholds':taus,'cohorts':{}}
    for name,rr in cohorts.items():
        matrix=np.array([r['blocked_by_fold']for r in rr]);summary['cohorts'][name]={'unique_prompts':len(rr),'fpr_by_fold':matrix.mean(0).tolist(),'mean_fold_fpr':float(matrix.mean()),'fixed_0_5_reference_fpr':float(np.mean([r['risk']>=.5 for r in rr]))}
    jsonl(OUT/'notinject_predictions.jsonl',rows);write(OUT/'notinject_results.json',summary);print(summary)
if __name__=='__main__':main()
