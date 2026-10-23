#!/usr/bin/env python3
"""Independent checks of grouping, calibration, decisions and exported counts."""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
import math
import re
from pathlib import Path


def load(path):
    return json.loads(Path(path).read_text())


def lines(path):
    with Path(path).open() as f:
        return [json.loads(x) for x in f if x.strip()]


def normalized(s):
    return " ".join(s.casefold().split())


def validate(project, output):
    protocol=load(output/"protocol.json")
    folds=protocol["fold_by_qid"]
    assert len(folds)==100 and sorted(collections.Counter(folds.values()).values())==[20]*5
    clean=load(project/"improved_experiment/inputs/clean_target_candidates.json")
    seen={}
    overlaps=0
    for q in sorted(folds):
        for d in clean[q]["docs"][:20]:
            keys=["id:"+d["id"],"text:"+normalized(d["text"])]
            if d.get("title"): keys.append("title:"+normalized(d["title"]))
            for key in keys:
                if key in seen:
                    assert seen[key][1]==folds[q],(q,seen[key][0],key)
                    overlaps+=1
                else: seen[key]=(q,folds[q])
    predictions=lines(output/"predictions_new.jsonl")
    assert len(predictions)==48000
    assert len({(r["suite"],r["qid"],r["setting"],r["index"]) for r in predictions})==len(predictions)
    fits={r["fold"]:r for r in load(output/"fit_metadata.json")}
    original={suite:{(r["qid"],r["setting"],r["index"]):r for r in lines(project/f"output/improved_experiment/predictions_{suite}.jsonl")} for suite in ["main","single_matched","single_supplied","benign_echo","benign_mirror"]}
    for r in predictions:
        old=original[r["suite"]][(r["qid"],r["setting"],r["index"])]
        assert r["features"]==old["features"] and r["label"]==old["label"] and r["text_hash"]==old["text_hash"]
        assert r["fold"]==folds[r["qid"]]
        for point in protocol["operating_points"]:
            for method,risk in r["risk_new"].items():
                assert math.isfinite(risk) and 0<=risk<=1
                assert r["blocked_new"][point][method] == (risk>fits[r["fold"]]["methods"][method]["thresholds"][point])
    reported=load(output/"detection_results.json")
    grouped=collections.defaultdict(list)
    for r in predictions: grouped[r["suite"],r["setting"]].append(r)
    for point in protocol["operating_points"]:
        for (suite,setting),rr in grouped.items():
            for method in protocol["new_fit_methods"]:
                m=reported[point][suite][setting][method]
                assert m["records"]==len(rr)
                assert m["tp"]==sum(r["label"] and r["blocked_new"][point][method] for r in rr)
                assert m["fp"]==sum(not r["label"] and r["blocked_new"][point][method] for r in rr)
    contexts=lines(output/"contexts_exploratory_1pct.jsonl")
    assert len(contexts)==100*4*5
    assert all(len(x["selected_ids"])<=5 for x in contexts)
    assert all(x["scope"].endswith("generation NOT executed") for x in contexts)
    # Exact higher-quantile and strict-threshold checks use freshly retained
    # calibration scores where available. The scores must reproduce saved tau.
    scores_checked=0
    for fit in fits.values():
        for method,s in fit["methods"].items():
            if "calibration_scores" not in s: continue
            scores=sorted(s["calibration_scores"])
            assert len(scores)==fit["calibration_questions"]*20
            for point,alpha in protocol["operating_points"].items():
                tau=scores[math.ceil((len(scores)-1)*(1-alpha))]
                assert tau==s["thresholds"][point]
                assert sum(x>tau for x in scores)/len(scores)==s["calibration_fpr"][point]
            scores_checked+=len(scores)
    report={"status":"passed","source_title_id_text_overlap_keys_kept_in_one_fold":overlaps,"source_groups":len(set(protocol["source_group_by_qid"].values())),"question_folds":5,"question_count":100,"reanalysed_candidate_rows":len(predictions),"new_fit_count":sum(len(x["methods"]) for x in fits.values()),"calibration_scores_rechecked":scores_checked,"context_rows_not_generations":len(contexts),"prediction_vs_source_features":"exact match; cached neural features reused","scope":"old100 exploratory grouped reanalysis; no new blind test; no neural inference; no new generation","negative_controls_preserved":True}
    (output/"validation.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(report,ensure_ascii=False))


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args();validate(a.project,a.output)
