#!/usr/bin/env python3
"""Single-pass CPU latency of fresh per-pool neural features (no text cache).

Measures first five lexicographic QIDs, clean and ignore settings, 20 passages
per pool. Excludes model loading, warm-up, original retrieval, head prediction,
and generation. This timing run does not fit or select any detector setting.
"""
from __future__ import annotations
import os
os.environ['HF_HUB_DISABLE_TELEMETRY']='1'
os.environ['HF_HUB_OFFLINE']='1'
os.environ['TRANSFORMERS_OFFLINE']='1'
os.environ['TOKENIZERS_PARALLELISM']='false'
os.environ['OMP_NUM_THREADS']='4'
os.environ['MKL_NUM_THREADS']='4'
import argparse
import hashlib
import json
import platform
import resource
import subprocess
import time
from pathlib import Path
import numpy as np
import torch
from transformers import AutoModel, AutoModelForSequenceClassification, AutoTokenizer
from run import PATTERNS

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
OUT=ROOT/'output'/'improved_experiment'
THREADS=4
BATCH=12
MAXTOK=512
WARM_TEXT='The library opens at nine.'

def read_json(path):return json.loads(Path(path).read_text())
def snapshot():
    cpu_model=None
    try:
        for line in Path('/proc/cpuinfo').read_text().splitlines():
            if line.startswith('model name'):
                cpu_model=line.split(':',1)[1].strip();break
    except OSError:pass
    cgroup={}
    for name in ['cpu.max','memory.max','memory.current']:
        path=Path('/sys/fs/cgroup')/name
        if path.exists():cgroup[name]=path.read_text().strip()
    processes=[]
    # Names/PIDs/aggregate resource use only; do not expose command arguments.
    try:
        raw=subprocess.check_output(['ps','-eo','pid,pcpu,rss,comm'],text=True)
        for line in raw.splitlines()[1:]:
            parts=line.split(None,3)
            if len(parts)==4 and ('python' in parts[3] or float(parts[1])>1):
                processes.append({'pid':int(parts[0]),'lifetime_cpu_percent':float(parts[1]),
                                  'rss_kib':int(parts[2]),'name':parts[3]})
    except (OSError,subprocess.SubprocessError):pass
    return {'wall_clock_unix':time.time(),'platform':platform.platform(),
            'cpu_model':cpu_model,'os_cpu_count':os.cpu_count(),
            'affinity_cpu_count':len(os.sched_getaffinity(0)) if hasattr(os,'sched_getaffinity') else None,
            'load_average':list(os.getloadavg()),'cgroup':cgroup,'processes':processes,
            'this_process_max_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}

def check_loading(info,allow_pooler=False):
    if info.get('missing_keys') or info.get('mismatched_keys') or info.get('error_msgs'):
        raise RuntimeError('Unexpected model loading inconsistency: '+str(info))
    allowed={'pooler.dense.weight','pooler.dense.bias'} if allow_pooler else set()
    if not set(info.get('unexpected_keys',[])).issubset(allowed):
        raise RuntimeError('Unrecognized extra checkpoint keys: '+str(info))

def load_models():
    torch.set_num_threads(THREADS)
    torch.set_num_interop_threads(1)
    start=time.perf_counter()
    cdir=HERE/'models'/'contriever';gdir=HERE/'models'/'guard'
    ctok=AutoTokenizer.from_pretrained(str(cdir),local_files_only=True)
    gtok=AutoTokenizer.from_pretrained(str(gdir),local_files_only=True)
    encoder,ci=AutoModel.from_pretrained(str(cdir),local_files_only=True,
            weights_only=True,add_pooling_layer=False,output_loading_info=True)
    guard,gi=AutoModelForSequenceClassification.from_pretrained(str(gdir),
            local_files_only=True,use_safetensors=True,output_loading_info=True)
    check_loading(ci,True);check_loading(gi)
    assert str(guard.config.id2label[1]).upper()=='INJECTION'
    encoder.eval();guard.eval()
    load_seconds=time.perf_counter()-start
    start=time.perf_counter()
    with torch.inference_mode():
        for tok,model in [(ctok,encoder),(gtok,guard)]:
            encoded=tok([WARM_TEXT],return_tensors='pt',truncation=True,max_length=MAXTOK)
            model(**encoded)
    return ctok,encoder,gtok,guard,{
        'excluded_load_seconds':load_seconds,'excluded_warmup_seconds':time.perf_counter()-start,
        'warmup_text':WARM_TEXT,'warmup_examples_per_model':1,
        'contriever_loading_info':ci,'guard_loading_info':gi}

def guard_features(texts,tok,model):
    values=[];lengths=[]
    with torch.inference_mode():
        for start in range(0,len(texts),BATCH):
            encoded=tok(texts[start:start+BATCH],padding=True,truncation=True,
                        max_length=MAXTOK,return_tensors='pt')
            output=model(**encoded)
            values.append(output.logits.float().softmax(-1)[:,1].cpu().numpy())
            lengths.extend(encoded['attention_mask'].sum(1).tolist())
    return np.concatenate(values),lengths

def density_features(texts,tok,model):
    values=[];lengths=[]
    with torch.inference_mode():
        for start in range(0,len(texts),BATCH):
            encoded=tok(texts[start:start+BATCH],padding=True,truncation=True,
                        max_length=MAXTOK,return_tensors='pt')
            output=model(**encoded)
            mask=encoded['attention_mask'][...,None].float()
            pooled=(output.last_hidden_state*mask).sum(1)/mask.sum(1)
            values.append(pooled.cpu().numpy())
            lengths.extend(encoded['attention_mask'].sum(1).tolist())
    vectors=np.concatenate(values)
    vectors/=np.linalg.norm(vectors,axis=1,keepdims=True)+1e-9
    similarities=vectors@vectors.T
    np.fill_diagonal(similarities,-1)
    return similarities.max(axis=1),lengths

def summarize(values):
    a=np.asarray(values,dtype=float)
    return {'n':len(a),'median':float(np.median(a)),
            'p95':float(np.quantile(a,.95,method='linear')),
            'mean':float(a.mean()),'min':float(a.min()),'max':float(a.max())}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--concurrency-note',default='Host activity recorded; timing is environment-specific.')
    args=parser.parse_args()
    source=OUT/'pools_main.jsonl'
    source_bytes=source.read_bytes()
    allrows=[json.loads(line) for line in source_bytes.decode().splitlines() if line.strip()]
    qids=sorted({str(r['qid']) for r in allrows})[:5]
    lookup={(str(r['qid']),r['setting']):r for r in allrows}
    selected=[lookup[q,setting] for q in qids for setting in ['none','ignore']]
    assert len(qids)==5 and len(selected)==10 and all(len(r['pool'])==20 for r in selected)
    before=snapshot()
    ctok,encoder,gtok,guard,loading=load_models()
    timing_before=snapshot()
    records=[]
    for row in selected:
        texts=[p['text'] for p in row['pool']]
        total_start=time.perf_counter();cpu_start=time.process_time()
        t=time.perf_counter()
        guard_scores,guard_lengths=guard_features(texts,gtok,guard)
        guard_seconds=time.perf_counter()-t
        t=time.perf_counter()
        density,density_lengths=density_features(texts,ctok,encoder)
        density_seconds=time.perf_counter()-t
        t=time.perf_counter()
        scores=np.asarray([p['score'] for p in row['pool']])
        score_z=(scores-scores.mean())/(scores.std()+1e-6)
        rules=np.asarray([sum(bool(pattern.search(text)) for pattern in PATTERNS)/len(PATTERNS)
                          for text in texts])
        features=np.column_stack([guard_scores,rules,score_z,density])
        assert features.shape==(20,4) and np.isfinite(features).all()
        cheap_seconds=time.perf_counter()-t
        total_seconds=time.perf_counter()-total_start
        cpu_seconds=time.process_time()-cpu_start
        record={'qid':row['qid'],'setting':row['setting'],'passages':20,
            'guard_tokenization_forward_seconds':guard_seconds,
            'density_tokenization_forward_cosine_seconds':density_seconds,
            'regex_scorez_feature_assembly_seconds':cheap_seconds,
            'total_feature_construction_seconds':total_seconds,
            'process_cpu_seconds':cpu_seconds,
            'guard_max_observed_tokens':max(guard_lengths),
            'guard_at_cap_passages':sum(x==MAXTOK for x in guard_lengths),
            'density_max_observed_tokens':max(density_lengths),
            'density_at_cap_passages':sum(x==MAXTOK for x in density_lengths),
            'ordered_texts_sha256':hashlib.sha256('\n'.join(texts).encode()).hexdigest(),
            'features_sha256':hashlib.sha256(features.tobytes()).hexdigest()}
        records.append(record)
        (OUT/'latency_cold_pools.json').write_text(json.dumps({'status':'running','reported_timing_attempt':2,'raw_pool_times':records},indent=2,default=lambda x:sorted(x) if isinstance(x,set) else str(x))+'\n')
        print(f"LATENCY {row['qid']} {row['setting']}: guard={guard_seconds:.3f}s density={density_seconds:.3f}s total={total_seconds:.3f}s",flush=True)
    after=snapshot()
    timing_keys=['guard_tokenization_forward_seconds','density_tokenization_forward_cosine_seconds',
                 'regex_scorez_feature_assembly_seconds','total_feature_construction_seconds']
    by_query=[]
    for qid in qids:
        rr=[r for r in records if str(r['qid'])==qid]
        by_query.append({'qid':qid,'pools':len(rr),**{key:sum(r[key] for r in rr) for key in timing_keys}})
    result={'status':'complete','protocol':{
        'purpose':'Latency measurement only; no fitting, tuning, generator calls, or performance-based selection.',
        'selection':'First five lexicographic QIDs, each none then ignore, exactly 20 candidate passages.',
        'qid_selection':qids,'n_pools':10,'n_passages_counting_repeated_texts':200,
        'repeats_in_reported_pass':1,'measurement_attempts_executed':2,'reported_attempt':2,
        'technical_rerun_reason':'The first fixed 10-pool pass completed, but final output serialization failed on a set in Transformers loading_info before full-precision raw times were saved. The same fixed selection and timing/model settings were rerun once solely to preserve the artifact. The second pass is reported regardless of speed; no faster-pass selection.',
        'batch_size':BATCH,'max_tokens':MAXTOK,'torch_threads':THREADS,'torch_interop_threads':1,
        'backend':'Local PyTorch CPU float32','torch_version':torch.__version__,
        'cache_policy':'Every passage is tokenized and encoded anew for every pool by both models; no text, tokenization, embedding or guard cache is reused.',
        'cold_definition':'Fresh per-pool features with resident warmed model weights; excludes loading and one fixed tiny-text warm-up per model. This is not process-cold model startup.',
        'guard_definition':'Tokenizer + forward + class-1 softmax + CPU output conversion.',
        'density_definition':'Tokenizer + Contriever forward + attention-mask mean pooling + L2 normalization + within-pool pairwise cosine and max cosine to another candidate.',
        'total_definition':'Guard and density stages plus regex, per-pool score-z and feature assembly.',
        'excluded':['Model loading','Fixed tiny-text warmup','Original retrieval/query encoding and ranking','Head prediction','Generation','File reading','Summary computation'],
        'original_retrieval_scores':'Taken from pools_main.jsonl; z scores recomputed per pool.',
        'p95_estimator':'NumPy linear interpolation; 10 pools or 5 paired-query totals, descriptive small-sample estimates.',
        'concurrency_note':args.concurrency_note},
        'source_pools_sha256':hashlib.sha256(source_bytes).hexdigest(),
        'model_manifests':{key:read_json(HERE/'models'/key/'model_manifest.json') for key in ['contriever','guard']},
        'excluded_loading_and_warmup':loading,
        'host_before_model_loading':before,'host_before_timing':timing_before,'host_after_timing':after,
        'per_query_pool_seconds':{key:summarize([r[key] for r in records]) for key in timing_keys},
        'per_query_two_setting_totals_seconds':{key:summarize([r[key] for r in by_query]) for key in timing_keys},
        'raw_pool_times':records,'raw_query_two_setting_totals':by_query}
    destination=OUT/'latency_cold_pools.json'
    destination.write_text(json.dumps(result,indent=2,default=lambda x:sorted(x) if isinstance(x,set) else str(x))+'\n')
    print('LATENCY_COMPLETE',json.dumps(result['per_query_pool_seconds']),flush=True)
if __name__=='__main__':main()
