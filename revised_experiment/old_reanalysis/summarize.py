#!/usr/bin/env python3
"""Produce compact tables without confusing records, exposures and answers."""
import argparse
import collections
import json
from pathlib import Path
from reanalyse import read_json,read_jsonl,write_json,grouped_bootstrap_ci

p=argparse.ArgumentParser(description=__doc__)
p.add_argument("--output",type=Path,required=True)
a=p.parse_args();out=a.output
protocol=read_json(out/"protocol.json")
det=read_json(out/"detection_results.json")
adm=read_json(out/"admission_results.json")
rows=read_jsonl(out/"predictions_new.jsonl")
paired={}
for point in protocol["operating_points"]:
    paired[point]={}
    base={(r["qid"],r["id"]):r for r in rows if r["suite"]=="main" and r["setting"]=="none"}
    for method in protocol["new_fit_methods"]:
        paired[point][method]={}
        for suite,prefix in [("benign_echo","echo:"),("benign_mirror","mirror:")]:
            rr=[r for r in rows if r["suite"]==suite and r["family"]==suite]
            baseline=[base[r["qid"],r["id"].removeprefix(prefix)]["blocked_new"][point][method] for r in rr]
            changed=[r["blocked_new"][point][method] for r in rr]
            paired[point][method][suite]={"matched_passages":len(rr),"questions":len({r["qid"] for r in rr}),"original_fp":sum(baseline),"transformed_fp":sum(changed),"original_fpr":sum(baseline)/len(rr),"transformed_fpr":sum(changed)/len(rr),"transformation_scope":"All five change simultaneously; includes changed peer statistics/ranking, not pure text-only causal effect."}
write_json(out/"paired_benign_controls.json",paired)
comparisons={}
for point in protocol["operating_points"]:
    tables=read_json(out/f"admission_per_question_{point}.json")
    comparisons[point]={}
    for setting in ["poison","ignore","stealth"]:
        rr=[r for r in tables["main"] if r["setting"]==setting]
        diff={r["qid"]:int(r["methods"]["tfidf_lr"]["malicious_exposed"])-int(r["methods"]["fused"]["malicious_exposed"]) for r in rr}
        comparisons[point][setting]=grouped_bootstrap_ci(diff,protocol["source_group_by_qid"],2000)
write_json(out/"sparse_vs_fused_exposure.json",comparisons)
compact={"status":"EXECUTED_EXPLORATORY_REANALYSIS", "data":"Already inspected old100; 83 conservative source groups, source-group-disjoint five-fold rotation; no new blind test.","new_computation":"20 fitted linear models including word+char TF-IDF LR; reused archived encoder features, no neural inference.","experiment_1":{"purpose":"Neural increment, sparse baseline, clean-FPR and top5 exposure at normal-only calibration points", "primary":"1pct", "secondary":"5pct detection sensitivity", "detection":{pt:det[pt]["main"] for pt in det},"admission":{pt:adm[pt]["main"] for pt in adm},"neural_increment":read_json(out/"primary_neural_increment.json")},"experiment_2":{"purpose":"Count shift and hard-benign mechanism suite, grouped reanalysis of archived constructed pools", "paired_benign_controls":paired,"single_matched_admission":{pt:adm[pt]["single_matched"] for pt in adm},"new_8_cell_matrix_status":"NOT_EXECUTED; new pools need frozen verified documents and new query/peer-dependent neural features."},"generation_status":"NOT_EXECUTED in this revision; exported 2000 prompts are inputs only.","independent_external_adaptive_status":"NOT_EXECUTED", "claim_limits":["Top5 malicious exposure is not semantic attack success.","Comparable calibration FPR does not imply identical test FPR or answer utility.","Sparse baseline superiority changes with work point; no universal winner.","Degenerate paired bootstrap CI for identical observed outcomes is not an equivalence test or unseen-data guarantee.","No timing comparison against archived 10-pool neural measurements across different environments."]}
write_json(out/"compact_results.json",compact)
md=['# 精简实验：已执行的分组再分析','',
'状态：本次真实执行20个线性模型拟合；旧100题探索性再分析，不是新盲测。原Contriever/guard特征逐条复用且已核对，没有新神经推理或回答生成。',
'','## 实验1：神经增量与强稀疏基线','',
'沿用原候选池及旧攻击，将83个共享docID、规范化精确文本或Wikipedia题名的来源联通组完整分入五折，每折20题。训练与正常校准、轮换评估来源组均无交叠。每折训练60题、正常校准20题；stealth不参加训练。1%为主校准点，5%仅检测敏感性。',
'','TF-IDF LR读取段落文本，word1–2与char3–5，最多25,000+35,000特征，C=1、balanced、固定liblinear。词表/IDF只拟合训练行，没有用测试结果选超参。监督标签在本项目中表示恶意段落，不能把此模型泛称为复现的公开指令检测器。',
'','以下“进入”表示每题最终top5至少包含一段恶意文本，分母均为100题。它不等于攻击目标被生成模型采纳。','']
for pt in ['1pct','5pct']:
    md += [f'### {pt}校准工作点','', '| 策略 | 正常误删 | poison进入/100 | ignore进入/100 | stealth进入/100 |','|---|---:|---:|---:|---:|']
    for m in ['ctx','no_guard','fused','tfidf_lr']:
        md.append(f'| {m} | {det[pt]["main"]["none"][m]["fp"]}/2000 ({100*det[pt]["main"]["none"][m]["fpr"]:.2f}%) | '+ ' | '.join(str(adm[pt]['main'][s][m]['malicious_exposed_questions']) for s in ['poison','ignore','stealth'])+' |')
    md.append('')
md += ['在两个工作点，fused与no_guard对poison/ignore/stealth的逐题“至少一毒进入”结果均完全相同。1%主条件8000条候选决策有17处差异，5%有5处；不能把进入率相同说成所有段落决策相同。来源组配对bootstrap的此项差值为0，退化区间不构成等效证明。',
'','1%下稀疏基线的poison/stealth进入数低于融合；5%下poison相同而stealth更高。因此结果说明工作点取舍与强基线必要性，不能宣称某一方法普遍最优。',
'','## 实验2：数量迁移与困难良性机制','',
'matched-single、echo、copy并入同一机制套件；supplied-single保留为同时改变数量与构造的附加敏感性，不当纯数量因果对照。下面对同500个原段落与其变换版本配对。',
'','| 工作点/策略 | echo原文误删/500 | echo后误删/500 | copy原文误删/500 | copy后误删/500 |','|---|---:|---:|---:|---:|']
for pt in ['1pct','5pct']:
    for m in ['ctx','no_guard','fused','tfidf_lr']:
        e=paired[pt][m]['benign_echo'];c=paired[pt][m]['benign_mirror']
        md.append(f'| {pt} / {m} | {e["original_fp"]} | {e["transformed_fp"]} | {c["original_fp"]} | {c["transformed_fp"]} |')
md += ['', '这些控制尚无本轮问答生成，不能直接推论删掉多少段就损失多少回答质量。新的25题、8cell机制矩阵没有执行；现有归档没有独立自然改写及新peer集合的编码，不能拼接旧density冒充新实验。',
'','## 复现与边界','',
'运行`reanalyse.py`会新拟合线性头，并在新输出目录生成2000条明确标注未执行的生成请求。`validate_reanalysis.py`独立核对来源隔离、48000行特征复用、阈值/决策、汇总整数与请求数。',
'','`fit_detectors(train_rows, calibration_rows)`可接入后续锁定数据；调用方还须传入真正独立来源组并对新pool重新计算相关特征。旧70/30训练开发分割用于Q，本五折用于探索性再分析，两个角色不混同。',
'','统计按83来源组重采样，区间只条件于这次固定拟合的五折；没有重复encoder推理、全库索引、外域测试或自适应攻击，也没有将新线性运行时间与历史神经计时作不公平速度比较。','']
(out/'RESULTS_中文.md').write_text('\n'.join(md))
print('Compact results, paired controls and interpretation written.')
