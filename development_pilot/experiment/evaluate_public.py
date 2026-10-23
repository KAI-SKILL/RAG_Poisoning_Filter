#!/usr/bin/env python3
"""External detector stress test, never full-context RAG or generator ASR."""
import csv,json,time
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from benchmark import HERE,OUT,SEED,KEYWORD,neural_scores
from public_data.load_public_data import load_records

def main():
    rows=load_records();summary=json.loads((OUT/'results.json').read_text())
    train=[r for r in map(json.loads,(HERE/'data'/'passages.jsonl').read_text().splitlines()) if r['split']=='train']
    v=TfidfVectorizer(ngram_range=(1,2),min_df=2,sublinear_tf=True,max_features=30000)
    clf=LogisticRegression(C=1,max_iter=1000,class_weight='balanced',random_state=SEED).fit(v.fit_transform([r['text'] for r in train]),[r['label'] for r in train])
    lexical=clf.predict_proba(v.transform([r['text'] for r in rows]))[:,1]
    neural,latency=neural_scores(rows,HERE/'models'/'distilbert')
    scores={'neural':neural,'lexical':lexical,'keyword':np.array([float(bool(KEYWORD.search(r['text']))) for r in rows])}
    predictions=[]
    for i,row in enumerate(rows):
        predictions.append({**row,'scores':{n:float(x[i]) for n,x in scores.items()},'blocked':{n:bool(x[i]>=summary['thresholds'][n]) if summary['thresholds'][n] is not None else False for n,x in scores.items()}})
    result={'scope':'Standalone public prompt/payload detector stress test. NotInject is benign; BIPIA payloads lack external task context. No retrieval feature/fusion, no threshold retuning, no downstream ASR.','threshold_source':'synthetic dev only; fixed keyword rule','latency':latency,'datasets':{}}
    cohorts={'NotInject_all':lambda r:r['dataset']=='NotInject','NotInject_multilingual_category':lambda r:r['dataset']=='NotInject' and r['language_cohort']=='Multilingual-category','NotInject_other_category':lambda r:r['dataset']=='NotInject' and r['language_cohort']!='Multilingual-category','BIPIA_all':lambda r:r['dataset']=='BIPIA','BIPIA_text':lambda r:r['dataset']=='BIPIA' and r['subset']=='text','BIPIA_code':lambda r:r['dataset']=='BIPIA' and r['subset']=='code'}
    for name,fn in cohorts.items():
        rr=[r for r in predictions if fn(r)]
        if not rr:continue
        result['datasets'][name]={'n':len(rr),'label':rr[0]['label'],'metric':'false_positive_rate' if rr[0]['label']==0 else 'payload_detection_rate','methods':{m:{'blocked':sum(r['blocked'][m] for r in rr),'rate':sum(r['blocked'][m] for r in rr)/len(rr)} for m in scores}}
    with (OUT/'public_predictions.jsonl').open('w') as f:
        for row in predictions:f.write(json.dumps(row)+'\n')
    (OUT/'public_results.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
