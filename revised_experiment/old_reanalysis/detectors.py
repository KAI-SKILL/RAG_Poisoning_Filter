"""Reusable frozen linear detectors for the revised, separately locked E1.

No neural model is loaded here. New rows must already have genuinely computed
query/peer-dependent features. Source independence remains a caller obligation.
"""
from pathlib import Path
import hashlib
import json

try:
    from .reanalyse import METHODS,POINTS,fit_detectors,score_rows,read_jsonl,values
except ImportError:
    from reanalyse import METHODS,POINTS,fit_detectors,score_rows,read_jsonl,values


def archived_training_rows(project_root, allowed_qids):
    """Read only original main-pool rows for the explicitly allowed train QIDs.

    Original neural features are reused; this is not fresh encoder inference.
    Stealth stays held out. Normal repeated passages remain repeated exactly as
    in the context-head training rows, so the sparse baseline shares weighting.
    """
    root=Path(project_root)
    allowed=set(allowed_qids)
    pools=read_jsonl(root/'output/improved_experiment/pools_main.jsonl')
    text={(p['qid'],p['setting'],i):d['text'] for p in pools for i,d in enumerate(p['pool']) if p['qid'] in allowed and p['setting']!='stealth'}
    rows=[]
    for r in read_jsonl(root/'output/improved_experiment/predictions_main.jsonl'):
        if r['qid'] not in allowed or r['setting']=='stealth':
            continue
        body=text[r['qid'],r['setting'],r['index']]
        assert hashlib.sha256(body.encode()).hexdigest()==r['text_hash']
        rows.append({**{k:r[k] for k in ['qid','setting','index','id','label','family','features','text_hash']},'text':body})
    assert {r['qid'] for r in rows}==allowed
    assert all(r['setting']!='stealth' for r in rows)
    return rows


def freeze_detectors(train_rows, normal_calibration_rows, test_rows=None):
    """Fit fixed hyperparameters on train, then calibrate only on normal rows.

    If test rows are supplied their QIDs must not overlap train or calibration.
    IDs alone cannot establish provenance: caller must additionally verify
    source article/near-duplicate groups before invoking this function.
    """
    if test_rows is not None:
        test_ids={r['qid'] for r in test_rows}
        assert test_ids.isdisjoint(r['qid'] for r in train_rows)
        assert test_ids.isdisjoint(r['qid'] for r in normal_calibration_rows)
    return fit_detectors(train_rows,normal_calibration_rows)


def apply_detectors(rows, frozen_states, point='1pct'):
    """Apply without fitting, recalibrating, choosing a model, or changing rows."""
    assert point in POINTS
    risks=score_rows(rows,frozen_states)
    return [{
        **{k:r[k] for k in ['qid','setting','index','id','label','family'] if k in r},
        'risk':{m:float(risks[m][i]) for m in METHODS},
        'blocked':{m:bool(risks[m][i]>frozen_states[m]['thresholds'][point]) for m in METHODS},
        'operating_point':point,
    } for i,r in enumerate(rows)]


def fit_summary(frozen_states):
    """JSON-safe fit/calibration provenance without pickle model instances."""
    return {m:{k:v for k,v in state.items() if k!='model'} for m,state in frozen_states.items()}
