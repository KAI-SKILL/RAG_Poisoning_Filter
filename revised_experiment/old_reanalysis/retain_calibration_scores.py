#!/usr/bin/env python3
"""Retain calibration audit scores from this run's own trusted linear artifacts.

This enriches provenance by recomputing probabilities. It never refits a model.
"""
import argparse
import json
from pathlib import Path
import joblib
from reanalyse import read_json,read_jsonl,values,write_json

p=argparse.ArgumentParser(description=__doc__)
p.add_argument("--project",type=Path,required=True)
p.add_argument("--output",type=Path,required=True)
a=p.parse_args()
protocol=read_json(a.output/"protocol.json")
metadata=read_json(a.output/"fit_metadata.json")
pools=read_jsonl(a.project/"output/improved_experiment/pools_main.jsonl")
lookup={(r["qid"],r["setting"],i):d["text"] for r in pools for i,d in enumerate(r["pool"])}
rows=read_jsonl(a.project/"output/improved_experiment/predictions_main.jsonl")
for r in rows: r["text"]=lookup[r["qid"],r["setting"],r["index"]]
for fit in metadata:
    f=fit["fold"]
    states=joblib.load(a.output/f"linear_models_fold{f}.joblib")
    val=[r for r in rows if protocol["fold_by_qid"][r["qid"]]==(f+1)%5 and r["setting"]=="none"]
    for method,s in states.items():
        scores=s["model"].predict_proba(values(val,s["columns"]))[:,1]
        fit["methods"][method]["calibration_scores"]=[float(x) for x in scores]
write_json(a.output/"fit_metadata.json",metadata)
print('Saved calibration audit scores; no refitting or neural inference.')
