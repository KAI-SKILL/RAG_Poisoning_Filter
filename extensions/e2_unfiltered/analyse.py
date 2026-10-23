#!/usr/bin/env python3
"""Analyse the matched E2 unfiltered extension without changing formal scores.

Use --check-inputs before additional generation. The extension is exploratory:
its added control was motivated by the already known original E2 results.
"""
from __future__ import annotations
import argparse
import collections
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
POLICIES = ['none','ctx','no_guard','fused']
SETTINGS = ['clean','counterfactual_1','benign_echo_1','benign_echo_5','benign_copy_1','benign_copy_5','counterfactual_5']
NEW_SETTINGS = SETTINGS[2:]
BENIGN_SETTINGS = SETTINGS[2:6]
METRICS = ['alias_exact','token_f1','reference_mention','target_exact','target_mention','abstention','blank','length_cap','gold_retained','legitimate_support_retained','malicious_exposure','malicious_count']
E1_POLICIES = ['none','ctx','no_guard','fused','tfidf_lr','guard_only']
E1_SETTINGS = ['clean','counterfactual_1','explicit_PI_1']


def default_project():
    for path in HERE.parents:
        if (path/'revised_experiment/evaluate_new.py').is_file():
            return path
    raise RuntimeError('Cannot locate project root')


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def stable(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))


def sha_text(value):
    return hashlib.sha256(value.encode()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def readl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]


def key(row):
    return (str(row['qid']),str(row['setting']),str(row['gate']))


def indexed(rows,label):
    out = {}
    duplicates = 0
    for row in rows:
        k = key(row)
        if k in out:
            if stable(out[k]) != stable(row):
                raise ValueError(f'Conflicting duplicate {label}: {k}')
            duplicates += 1
        else:
            out[k] = row
    return out,duplicates


def chat(prompt):
    return '<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\n'+prompt+'<|im_end|>\n<|im_start|>assistant\n'


def iso(value):
    return datetime.datetime.fromisoformat(value.replace('Z','+00:00'))


def input_checks(project):
    folder = project/'extensions/e2_unfiltered'
    protocol_path = folder/'analysis_protocol.json'
    protocol = read_json(protocol_path)
    assert protocol['status'] == 'EXPLORATORY_EXTENSION_ANALYSIS_FROZEN_BEFORE_ADDITIONAL_UNFILTERED_OUTPUTS'
    assert protocol['analysis_code_sha256'] == sha(Path(__file__)), 'Analysis code differs from pre-output freeze'
    assert protocol['policies'] == POLICIES and protocol['settings'] == SETTINGS
    for rel,expected in protocol['inputs'].items():
        path = project/rel
        assert path.stat().st_size == expected['bytes'] and sha(path) == expected['sha256'], rel
    request_path = folder/'requests.jsonl'
    manifest_path = folder/'request_manifest.json'
    manifest = read_json(manifest_path)
    assert manifest['status'] == 'FROZEN_REQUESTS_NO_INFERENCE'
    assert sha(request_path) == manifest['requests_sha256']
    for rel,digest in manifest['inputs_sha256'].items():
        assert sha(project/rel) == digest, rel
    assert sha(folder/'prepare_requests.py') == manifest['request_builder_sha256']
    original_path = project/'output/revised_experiment/selection/context_requests.jsonl'
    original_rows = readl(original_path)
    original,old_duplicates = indexed(original_rows,'original requests')
    assert len(original) == 2175 and len(original_rows) == 2175
    qids = sorted({r['qid'] for r in original.values() if r.get('e2_selected')})
    assert qids == protocol['fixed_qids'] == manifest['e2_qids'] and len(qids) == 25
    audit = read_json(project/'revised_experiment/data/test_source_quality_audit.json')
    assert audit['model_outputs_used'] is False
    audits = {r['qid']:r for r in audit['questions']}
    assert len(audits) == 100 and sum(r['assessment'] == 'supported' for r in audits.values()) == 85
    assert all(audits[q]['assessment'] == 'supported' for q in qids)
    articles = {q:original[q,'clean','none']['source_group'] for q in qids}
    assert len(set(articles.values())) == 25
    rows = readl(request_path)
    new,new_duplicates = indexed(rows,'additional requests')
    expected = {(q,s,'none') for q in qids for s in NEW_SETTINGS}
    assert set(new) == expected and len(rows) == len(new) == 125
    assert not set(new).intersection(original)
    pools_path = project/'output/revised_experiment/fresh_features/pools_with_features.jsonl'
    pools = {(p['qid'],p['setting']):p for p in readl(pools_path) if p['split'] == 'test'}
    prompts_spec = importlib.util.spec_from_file_location('e2_frozen_prompts',project/'revised_experiment/prompts.py')
    prompts = importlib.util.module_from_spec(prompts_spec)
    prompts_spec.loader.exec_module(prompts)
    for (q,s,g),row in new.items():
        assert row['source_group'] == articles[q] and row['source_supported'] and row['e2_selected']
        assert row['split'] == 'test' and row['working_point'] == '1pct'
        base = original[q,'clean','none']
        for name in ('question','source_group','source_title','answers','incorrect'):
            assert row[name] == base[name], (q,s,name)
        pool = pools[q,s]
        assert len(pool['pool']) == 20 and pool['e2_selected'] and pool['source_supported']
        selected = pool['pool'][:5]
        assert row['context_ids'] == [p['id'] for p in selected]
        assert row['prompt'] == prompts.prompt(pool['question'],selected)
        assert row['malicious_count'] == sum(p.get('label',0) for p in selected)
        assert row['gold_retained'] == any(p['id'] == pool['gold_document_id'] for p in selected)
        assert row['legitimate_support_retained'] == any(p.get('legitimate_support',False) for p in selected)
    main_manifest_path = project/'output/revised_experiment/generation/run_manifest.json'
    main_manifest = read_json(main_manifest_path)
    assert sha_text(stable(main_manifest['config'])) == main_manifest['config_sha256']
    assert manifest['frozen_generation_config'] == main_manifest['config']
    assert manifest['frozen_generation_config_sha256'] == main_manifest['config_sha256']
    assert main_manifest['completed_rows'] == 2175 and main_manifest['completed_unique_prompts'] == 432
    original_raw_path = project/'output/revised_experiment/generation/raw_generations.jsonl'
    original_raw,raw_duplicates = indexed(readl(original_raw_path),'original generated outputs')
    assert len(original_raw) == 2175 and set(original_raw) == set(original)
    response_by_chat = {}
    for k,row in original_raw.items():
        for name,value in original[k].items():
            assert row[name] == value, ('Original request field changed',k,name)
        assert row['config_sha256'] == main_manifest['config_sha256'] and row['truncated'] is False
        assert row['chat_prompt'] == chat(row['prompt'])
        assert sha_text(row['chat_prompt']) == row['chat_prompt_sha256']
        if row['chat_prompt_sha256'] in response_by_chat:
            assert response_by_chat[row['chat_prompt_sha256']] == row['response'], 'Conflicting original exact-prompt output'
        response_by_chat[row['chat_prompt_sha256']] = row['response']
    assert len(response_by_chat) == 432
    all_expected = {(q,s,g) for q in qids for s in SETTINGS for g in POLICIES}
    reused = {k:r for k,r in original_raw.items() if k in all_expected}
    assert len(reused) == 575
    baseline = sum(k[1] in ('clean','counterfactual_1') for k in reused)
    assert baseline == 200 and len(reused)-baseline == 375
    extension_chats = {sha_text(chat(r['prompt'])) for r in new.values()}
    assert len(extension_chats) == manifest['unique_extension_chat_prompts'] == 125
    assert len(extension_chats.intersection(response_by_chat)) == manifest['unique_cache_hits_among_extension_prompts'] == 0
    checks = {'status':'INPUT_ROLES_CHECKED_NO_ADDITIONAL_OUTCOMES_READ','original_rows':2175,'e1_baselines_reused':200,
              'filtered_e2_rows_reused':375,'additional_unfiltered_requests':125,'planned_combined_rows':700,
              'matched_questions_and_articles':25,'source_supported_e2_questions':25,
              'new_unique_chat_prompts_required':125,'original_request_exact_duplicates':old_duplicates,
              'new_request_exact_duplicates':new_duplicates,'original_output_exact_duplicates':raw_duplicates,
              'analysis_protocol_sha256':sha(protocol_path),'analysis_code_sha256':sha(Path(__file__)),
              'requests_sha256':sha(request_path),'request_manifest_sha256':sha(manifest_path),
              'scorer_sha256':sha(project/'revised_experiment/evaluate_new.py'),
              'scope':'Input consistency only; no claim additional generation completed or any new score is known'}
    return {'protocol':protocol,'manifest':manifest,'original':original,'original_raw':original_raw,'new':new,
            'qids':qids,'articles':articles,'audits':audits,'main_manifest':main_manifest,'reused':reused,
            'all_expected':all_expected,'checks':checks,'request_path':request_path}


def load_new_generation(project,generation,state):
    path = generation/'raw_generations.jsonl'
    run_path = generation/'run_manifest.json'
    if not path.is_file() or not run_path.is_file():
        raise FileNotFoundError('Additional unfiltered generation is incomplete; no scores or placeholder verdicts were written')
    run = read_json(run_path)
    assert run['input_sha256'] == sha(state['request_path'])
    assert run['config_sha256'] == state['main_manifest']['config_sha256']
    assert run['config'] == state['main_manifest']['config']
    assert sha_text(stable(run['config'])) == run['config_sha256']
    assert run['requested_rows'] == run['completed_rows'] == 125
    assert run['unique_prompts'] == run['completed_unique_prompts'] == 125
    assert run['all_prompts_fit_context'] is True
    assert iso(run['started_utc']) >= iso(state['protocol']['frozen_utc']), 'Additional generation predates analysis freeze'
    output_rows = readl(path)
    generated,duplicates = indexed(output_rows,'additional generated outputs')
    assert len(generated) == 125 and set(generated) == set(state['new'])
    for k,row in generated.items():
        for name,value in state['new'][k].items():
            assert row[name] == value, ('Additional request field changed',k,name)
        assert row['config_sha256'] == run['config_sha256']
        assert row['chat_prompt'] == chat(row['prompt']) and sha_text(row['chat_prompt']) == row['chat_prompt_sha256']
        assert row['truncated'] is False and isinstance(row['response'],str)
        assert row['usage']['prompt_tokens'] + 48 <= run['config']['context_length']
        assert row['usage']['completion_tokens'] <= 48
    return generated,run,duplicates


def load_scorer(project):
    spec = importlib.util.spec_from_file_location('e2_frozen_evaluator',project/'revised_experiment/evaluate_new.py')
    scorer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scorer)
    return scorer


def score_rows(rows,scorer,state):
    scored = {}
    for k,row in rows.items():
        metrics = scorer.score_row(row,max_new_tokens=48)
        assert isinstance(row['legitimate_support_retained'],bool)
        metrics['legitimate_support_retained'] = row['legitimate_support_retained']
        assert all(metrics[name] is not None for name in METRICS), k
        q,s,g = k
        article = scorer.article_id(row,state['audits'])
        scored[k] = {'qid':q,'article':article,'setting':s,'gate':g,'source_valid':state['audits'][q]['assessment'] == 'supported',
                     'answers':scorer.aliases(row['answers']),'incorrect':scorer.aliases(row['incorrect']),
                     'response':row['response'],'prompt_sha256':sha_text(row['prompt']),
                     'chat_prompt_sha256':row['chat_prompt_sha256'],'source_role':'additional_unfiltered' if k in state['new'] else 'original_reused',
                     'metrics':metrics}
    return scored


def aggregate(scored):
    rows = []
    for setting in SETTINGS:
        for gate in POLICIES:
            selected = [r for k,r in scored.items() if k[1:] == (setting,gate)]
            assert len(selected) == 25
            result = {'setting':setting,'gate':gate,'questions':25,'articles':len({r['article'] for r in selected})}
            for name in METRICS:
                values = [float(r['metrics'][name]) for r in selected]
                result[name+'_sum'] = sum(values)
                result[name+'_mean'] = sum(values)/25
                result[name+'_n'] = 25
            rows.append(result)
    return rows


def paired(values,indices,np,metric):
    vector = np.asarray(values,dtype=np.float64)
    assert vector.shape == (25,)
    draws = vector[indices].mean(axis=1)
    low,high = np.quantile(draws,[0.025,0.975])
    mean = float(vector.mean())
    count_metric = metric == 'malicious_count'
    return {'effect':mean,'ci95':[float(low),float(high)],
            'effect_pp':None if count_metric else 100*mean,
            'ci95_pp':None if count_metric else [100*float(low),100*float(high)],
            'units':'passages/question' if count_metric else ('F1 points on0to1scale' if metric == 'token_f1' else 'fraction'),
            'paired_questions':25,'article_groups':25,'bootstrap_draws':10000,'bootstrap_seed':20261020,
            'degenerate_observed_interval':bool(low == high),'status':'exploratory_descriptive_no_p_value'}


def contrasts(scored,state):
    import numpy as np
    qids = state['qids']
    # One question per article: sample the common25 article identities and retain
    # every policy/condition outcome from the selected question together.
    indices = np.random.default_rng(20261020).integers(0,25,size=(10000,25))
    value = lambda q,s,g,m:float(scored[q,s,g]['metrics'][m])
    benign = []
    dose = []
    for metric in METRICS:
        for setting in BENIGN_SETTINGS:
            for gate in POLICIES[1:]:
                delta = [(value(q,setting,gate,metric)-value(q,'clean',gate,metric))-
                         (value(q,setting,'none',metric)-value(q,'clean','none',metric)) for q in qids]
                benign.append({'metric':metric,'setting':setting,'gate':gate,'baseline':'clean','comparator':'none',
                               'contrast':'difference_in_differences','primary_exploratory_alias_contrast':metric == 'alias_exact',
                               **paired(delta,indices,np,metric)})
        for gate in POLICIES:
            delta = [value(q,'counterfactual_5',gate,metric)-value(q,'counterfactual_1',gate,metric) for q in qids]
            dose.append({'metric':metric,'gate':gate,'baseline':'counterfactual_1','condition':'counterfactual_5',
                         'contrast':'within_policy_paired_change',**paired(delta,indices,np,metric)})
            if gate != 'none':
                delta = [d-(value(q,'counterfactual_5','none',metric)-value(q,'counterfactual_1','none',metric)) for q,d in zip(qids,delta)]
                dose.append({'metric':metric,'gate':gate,'baseline':'counterfactual_1','condition':'counterfactual_5',
                             'contrast':'difference_in_differences_vs_none',**paired(delta,indices,np,metric)})
    assert sum(r['primary_exploratory_alias_contrast'] for r in benign) == 12
    return benign,dose


def joint_e1(state,scorer):
    e1 = {k:r for k,r in state['original_raw'].items() if k[1] in E1_SETTINGS}
    assert len(e1) == 1800
    summary = []
    for subset in ('all100','source_supported85'):
        qids = sorted({q for q,s,g in e1 if subset == 'all100' or state['audits'][q]['assessment'] == 'supported'})
        assert len(qids) == (100 if subset == 'all100' else 85)
        for setting in E1_SETTINGS:
            for gate in E1_POLICIES:
                states = dict.fromkeys(['U1_T0','U1_T1','U0_T0','U0_T1'],0)
                for q in qids:
                    row = scorer.score_row(e1[q,setting,gate],max_new_tokens=48)
                    assert row['target_mention'] is not None
                    states[f'U{int(row["alias_exact"])}_T{int(row["target_mention"])}'] += 1
                assert sum(states.values()) == len(qids)
                summary.append({'subset':subset,'setting':setting,'gate':gate,'questions':len(qids),**states,
                                'definition':'U=reference-alias exact; T=bounded canonical target mention. String proxies, not semantic security.'})
    assert len(summary) == 36
    return summary


def write_csv(path,rows):
    import csv
    keys = list(rows[0])
    with path.open('w',encoding='utf-8',newline='') as stream:
        writer = csv.DictWriter(stream,fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow({k:stable(v) if isinstance(v,(list,dict)) else v for k,v in row.items()})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',type=Path,default=default_project())
    parser.add_argument('--generation',type=Path,help='Completed additional generation directory')
    parser.add_argument('--output',type=Path,help='Separate extension analysis output directory')
    parser.add_argument('--check-inputs',action='store_true',help='Check frozen original/request roles without reading additional outcomes or writing scores')
    args = parser.parse_args()
    project = args.project.resolve()
    generation = (args.generation or project/'output/revised_experiment/e2_unfiltered/generation').resolve()
    output = (args.output or project/'output/revised_experiment/e2_unfiltered/analysis').resolve()
    state = input_checks(project)
    if args.check_inputs:
        print(json.dumps(state['checks'],indent=2))
        return
    extension_root = project/'output/revised_experiment/e2_unfiltered'
    if output.is_relative_to(project) and not output.is_relative_to(extension_root):
        raise ValueError('Analysis output within project must stay under the separate e2_unfiltered extension directory')
    assert output != generation and not generation.is_relative_to(output), 'Never overwrite generation or formal score archives'
    generated,run,duplicates = load_new_generation(project,generation,state)
    combined = {**state['reused'],**generated}
    assert len(combined) == 700 and set(combined) == state['all_expected']
    responses = {}
    for row in combined.values():
        digest = row['chat_prompt_sha256']
        if digest in responses:
            assert responses[digest] == row['response'], 'Conflicting exact-prompt outputs across reused and added rows'
        responses[digest] = row['response']
    scorer = load_scorer(project)
    scored = score_rows(combined,scorer,state)
    assert len({r['article'] for r in scored.values()}) == 25
    assert all(r['source_valid'] for r in scored.values())
    matrix = aggregate(scored)
    benign,dose = contrasts(scored,state)
    joint = joint_e1(state,scorer)
    protocol_path = project/'extensions/e2_unfiltered/analysis_protocol.json'
    if output.exists() and any(output.iterdir()):
        receipt = output/'validation.json'
        if not receipt.is_file() or read_json(receipt).get('analysis_id') != 'Group9-E2-unfiltered-extension-v1':
            raise ValueError('Refusing to overwrite an unrelated nonempty output directory')
    output.mkdir(parents=True,exist_ok=True)
    provenance = {'analysis_id':'Group9-E2-unfiltered-extension-v1','status':'EXPLORATORY_COMPLETED_EXTENSION',
                  'protocol_sha256':sha(protocol_path),'analysis_code_sha256':sha(Path(__file__)),
                  'request_manifest_sha256':sha(project/'extensions/e2_unfiltered/request_manifest.json'),
                  'requests_sha256':sha(state['request_path']),'canonical_pools_sha256':sha(project/'output/revised_experiment/fresh_features/pools_with_features.jsonl'),
                  'scorer_sha256':sha(project/'revised_experiment/evaluate_new.py'),
                  'original_raw_sha256':sha(project/'output/revised_experiment/generation/raw_generations.jsonl'),
                  'additional_raw_sha256':sha(generation/'raw_generations.jsonl'),'additional_run_manifest_sha256':sha(generation/'run_manifest.json'),
                  'original_e1_reused_rows':200,'original_e2_reused_rows':375,'additional_unfiltered_rows':125,'combined_rows':700,
                  'independent_questions_and_articles':25,'new_output_exact_duplicate_rows_collapsed':duplicates,
                  'generation_config_sha256':run['config_sha256'],'new_requested_unique_prompts':run['completed_unique_prompts'],
                  'original_formal_results_modified':False,'scope':'Conditional exploratory paired article analysis; no new confirmatory tests or semantic safety claims'}
    result = {'metadata':provenance,'summary_matrix':matrix,'benign_difference_in_differences':benign,
              'counterfactual_dose_changes':dose,'joint_original_e1_string_outcomes':joint}
    (output/'summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    (output/'combined_scored_rows.jsonl').write_text(''.join(json.dumps(scored[k],ensure_ascii=False)+'\n' for k in sorted(scored)))
    write_csv(output/'summary_matrix.csv',matrix)
    write_csv(output/'benign_did.csv',benign)
    write_csv(output/'counterfactual_dose.csv',dose)
    write_csv(output/'joint_original_e1_outcomes.csv',joint)
    validation = {'analysis_id':provenance['analysis_id'],'status':'passed','combined_rows':700,'articles':25,
                  'matrix_cells':28,'primary_exploratory_alias_did_contrasts':12,'joint_original_e1_cells':36,
                  'frozen_scorer_unchanged':True,'all_requested_qid_policy_condition_keys_present':True,
                  'protocol_sha256':provenance['protocol_sha256'],'analysis_code_sha256':provenance['analysis_code_sha256'],
                  'summary_sha256':sha(output/'summary.json'),'combined_scores_sha256':sha(output/'combined_scored_rows.jsonl'),
                  'inference_performed_by_this_analysis':False,'scope':provenance['scope']}
    (output/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
    print(json.dumps(validation,indent=2))


if __name__ == '__main__':
    main()
