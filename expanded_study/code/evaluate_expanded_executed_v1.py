"""Score expanded paired RAG constructions using immutable sparse detectors.

No detector fitting, neural inference, generation, or target-tool execution occurs.
The optional retrieval stage fits an ordinary TF-IDF index on the declared normal
test corpus and evaluates document delivery, not answer correctness or attack ASR.
"""
from __future__ import annotations

import argparse
import collections
import csv
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import sys
import time

import joblib
import numpy as np
import scipy
from scipy.stats import beta
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import average_precision_score, roc_auc_score
from threadpoolctl import threadpool_limits

SEED = 20261022
MODELS = ('LR', 'LinearSVC')
POINTS = (('new_normal_1pct', 'threshold_1pct'), ('new_normal_5pct', 'threshold_5pct'), ('previous_external_5pct', 'previous_threshold'))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def text_sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def load_rows(path):
    with Path(path).open(encoding='utf-8') as stream:
        return [json.loads(line) for line in stream if line.strip()]


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def write_rows(path, rows):
    with Path(path).open('w', encoding='utf-8') as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + '\n')


def csv_rows(path, rows):
    flat = [{k: v for k, v in row.items() if not isinstance(v, (dict, list))} for row in rows]
    columns = list(dict.fromkeys(k for row in flat for k in row))
    with Path(path).open('w', newline='', encoding='utf-8-sig') as stream:
        writer = csv.DictWriter(stream, columns)
        writer.writeheader()
        writer.writerows(flat)


def document_id(doc):
    return str(doc.get('doc_id', doc.get('document_id', '')))


def corpus_text(doc):
    return str(doc.get('title', '')) + '\n' + str(doc['text'])


def detector_scores(model, kind, texts, batch_size):
    result = []
    for start in range(0, len(texts), batch_size):
        batch = texts[start:start + batch_size]
        value = model.predict_proba(batch)[:, 1] if kind == 'LR' else model.decision_function(batch)
        result.append(np.asarray(value, dtype=np.float64))
    return np.concatenate(result) if result else np.empty(0, dtype=np.float64)


def grouped_interval(groups, values, draws=2000):
    bins = collections.defaultdict(lambda: [0.0, 0])
    for group, value in zip(groups, values):
        bins[group][0] += float(value)
        bins[group][1] += 1
    array = np.asarray([bins[key] for key in sorted(bins)], dtype=np.float64)
    if not len(array):
        return None
    rng = np.random.default_rng(SEED)
    selected = rng.integers(0, len(array), size=(draws, len(array)))
    totals = array[selected].sum(axis=1)
    estimates = totals[:, 0] / totals[:, 1]
    point = float(np.mean(values))
    return {
        'point': point,
        'ci95_article_percentile': np.quantile(estimates, [.025, .975]).tolist(),
        'article_groups': len(array),
        'draws': draws,
        'warning': ('Fewer than ten article groups; interval unstable.' if len(array) < 10 else '') +
                   (' Empirical zero/all-event cells cannot establish zero population uncertainty.' if point in (0.0, 1.0) else ''),
        'scope': 'Resampling observed article groups with fitted models fixed; construction-conditional, not universal robustness.',
    }


def classification_metrics(labels, scores, threshold, articles, draws):
    y = np.asarray(labels, dtype=np.int8)
    s = np.asarray(scores, dtype=np.float64)
    blocked = s > threshold
    good = y == 0
    bad = y == 1
    assert np.all(good | bad)
    tp = int(np.sum(blocked & bad))
    fn = int(np.sum(~blocked & bad))
    fp = int(np.sum(blocked & good))
    tn = int(np.sum(~blocked & good))
    mixed = bool(np.any(good) and np.any(bad))
    result = {
        'n': len(y), 'articles': len(set(articles)),
        'malicious_or_joint_attack_sets': int(np.sum(bad)), 'benign': int(np.sum(good)),
        'tp': tp, 'fp': fp, 'tn': tn, 'fn': fn,
        'recall': tp / (tp + fn) if tp + fn else None,
        'fpr': fp / (fp + tn) if fp + tn else None,
        'precision': tp / (tp + fp) if mixed and tp + fp else None,
        'f1': 2 * tp / (2 * tp + fp + fn) if mixed and 2 * tp + fp + fn else None,
        'accuracy': (tp + tn) / len(y) if mixed else None,
        'auroc': float(roc_auc_score(y, s)) if mixed else None,
        'average_precision': float(average_precision_score(y, s)) if mixed else None,
        'metric_scope': 'Constructed cohort prevalence; precision/AP do not estimate deployment prevalence.' if mixed else 'Single-class set: report recall or FPR only.',
    }
    article_array = np.asarray(articles)
    if np.any(bad):
        result['recall_uncertainty'] = grouped_interval(article_array[bad], blocked[bad], draws)
    if np.any(good):
        result['fpr_uncertainty'] = grouped_interval(article_array[good], blocked[good], draws)
    return result


def cohort_indexes(records):
    cohorts = {'all': list(range(len(records)))}
    for dimension in ('family_id', 'template_id', 'placement', 'encoding_mode', 'language_mode', 'objective', 'threat_type'):
        bins = collections.defaultdict(list)
        for index, row in enumerate(records):
            bins[str(row.get(dimension, 'unspecified'))].append(index)
        for value, indexes in sorted(bins.items()):
            cohorts[dimension + ':' + value] = indexes
    return cohorts


def validate_inputs(hosts, cases, corpus, expected_per_template):
    host_map = {str(row['source_id']): row for row in hosts}
    assert len(host_map) == len(hosts), 'Duplicate source_id'
    calibration = [r for r in hosts if r['split'] == 'calibration']
    test = [r for r in hosts if r['split'] == 'test']
    assert len(calibration) >= 1000, 'At least1000 ordinary calibration examples required'
    assert len(test) >= expected_per_template
    assert {r['article_id'] for r in calibration}.isdisjoint(r['article_id'] for r in test), 'Article calibration/test overlap'
    assert {text_sha(r['context']) for r in calibration}.isdisjoint(text_sha(r['context']) for r in test), 'Exact context calibration/test overlap'
    assert len({row['case_id'] for row in cases}) == len(cases), 'Duplicate case_id'
    template_counts = collections.Counter(row['template_id'] for row in cases)
    assert all(n == expected_per_template for n in template_counts.values()), template_counts
    template_sources = collections.defaultdict(set)
    for row in cases:
        host = host_map[str(row['question_id'])]
        assert host['split'] == 'test'
        assert row['article_id'] == host['article_id']
        assert row['query'] == host['question']
        template_sources[row['template_id']].add(row['question_id'])
        for field in ('attack_documents', 'matched_benign_documents'):
            assert row[field] and all(document_id(doc) and isinstance(doc['text'], str) and doc['text'].strip() for doc in row[field])
            assert len({document_id(doc) for doc in row[field]}) == len(row[field]), 'Duplicate insertion document identities in one case'
        assert len(row['attack_documents']) == len(row['matched_benign_documents']), 'Matched conditions must share insertion count'
    assert all(len(v) == expected_per_template for v in template_sources.values()), 'Every template needs unique source questions'
    corpus_ids = {document_id(doc) for doc in corpus}
    assert len(corpus_ids) == len(corpus) and '' not in corpus_ids
    assert {r['document_id'] for r in test}.issubset(corpus_ids), 'All source evidence must exist in normal corpus'
    for row in cases:
        for field in ('attack_documents', 'matched_benign_documents'):
            assert not corpus_ids.intersection(document_id(doc) for doc in row[field]), 'Insertion identity overlaps normal corpus'
    calibration_articles = {r['article_id'] for r in calibration}
    assert not calibration_articles.intersection(r.get('article_id') for r in corpus), 'Calibration article present in test retrieval corpus'
    return host_map, calibration, test, template_counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--models', type=Path, help='Frozen LR.joblib, LinearSVC.joblib and models_frozen.json; defaults to ROOT/models')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--externalroot', type=Path, help='Optional passive pinned external source folder')
    parser.add_argument('--expected-per-template', type=int, default=1200)
    parser.add_argument('--batch-size', type=int, default=256)
    parser.add_argument('--bootstrap', type=int, default=2000)
    parser.add_argument('--threads', type=int, default=1)
    parser.add_argument('--no-retrieval', action='store_true', help='Diagnostic classification-only execution; manifest records omission.')
    args = parser.parse_args()
    root, output = args.root.resolve(), args.output.resolve()
    args.models = (args.models or root / 'models').resolve()
    if output.exists() and any(output.iterdir()):
        parser.error('Output must be new or empty; saved evidence is never overwritten')
    output.mkdir(parents=True, exist_ok=True)
    paths = {name: root / 'data' / (name + '.jsonl') for name in ('hosts', 'cases', 'corpus')}
    for path in paths.values():
        assert path.is_file(), str(path)
    hosts, cases, corpus = (load_rows(paths[k]) for k in ('hosts', 'cases', 'corpus'))
    host_map, calibration, test, template_counts = validate_inputs(hosts, cases, corpus, args.expected_per_template)
    protocol = root / 'protocol_frozen.json'
    if not protocol.is_file():
        protocol = root / 'protocol.json'
    assert protocol.is_file(), 'Protocol must exist before scoring'
    external_paths = []
    external_rows = []
    if args.externalroot:
        external_paths = [args.externalroot / name for name in ['injecagent_base_contexts.jsonl', 'agentdojo_clean_tool_outputs_unique.jsonl']]
        for path in external_paths:
            assert path.is_file(), str(path)
            external_rows.extend(load_rows(path))
        assert len({r['id'] for r in external_rows}) == len(external_rows)
    validation_bins = collections.defaultdict(list)
    for case in cases:
        validation_bins[case['template_id']].append(case)
    args._rank_validation_case_ids = [min(rows, key=lambda r:text_sha(r['case_id']))['case_id'] for _,rows in sorted(validation_bins.items())]
    old_thresholds = json.loads((args.models / 'models_frozen.json').read_text())
    input_bindings = {name: {'path': str(path.relative_to(root)), 'sha256': sha(path)} for name, path in paths.items()}
    freeze = {
        'status': 'INPUTS_AND_ANALYSIS_BOUND_BEFORE_CALIBRATION_AND_TEST_SCORING',
        'protocol_sha256': sha(protocol), 'script_sha256': sha(__file__),
        'inputs': input_bindings, 'protocol_file':protocol.name,
        'rank_validation_case_ids':args._rank_validation_case_ids,
        'passive_external_inputs': [{'name':p.name,'sha256':sha(p)}for p in external_paths],
        'detector_sources': {name: {'file_sha256': sha(args.models / (name + '.joblib')), 'previous_threshold': old_thresholds[name]['threshold']} for name in MODELS},
        'old_threshold_metadata_sha256': sha(args.models / 'models_frozen.json'),
        'case_count': len(cases), 'questions': len(test), 'test_articles': len({r['article_id'] for r in test}),
        'calibration_questions': len(calibration), 'calibration_articles': len({r['article_id'] for r in calibration}),
        'template_counts': dict(sorted(template_counts.items())), 'seed': SEED, 'bootstrap': args.bootstrap,
        'normal_calibration_targets': [.01, .05], 'strict_rejection': 'score > higher empirical99th/95th percentile', 'primary_working_point': 'new_normal_1pct',
        'detector_fits': 0, 'neural_calls': 0, 'generator_calls': 0,
        'clock_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    write_json(output / 'execution_freeze.json', freeze)
    started = time.perf_counter()
    timers, model_states, score_cache = {}, {}, {name: {} for name in MODELS}
    # Calibrate on ordinary context bodies alone. This occurs before any test
    # call to either immutable detector. Thresholds remain fixed thereafter.
    calibration_records = []
    with threadpool_limits(limits=args.threads):
        for name in MODELS:
            model = joblib.load(args.models / (name + '.joblib'))
            t = time.perf_counter()
            scores = detector_scores(model, name, [r['context'] for r in calibration], args.batch_size)
            threshold = float(np.quantile(scores, .95, method='higher'))
            rank = int(math.ceil(.95 * (len(scores) - 1))) + 1
            state = {
                'threshold_5pct': threshold, 'threshold_1pct': float(np.quantile(scores, .99, method='higher')), 'previous_threshold': float(old_thresholds[name]['threshold']),
                'calibration_n': len(scores), 'calibration_rejected': int(np.sum(scores > threshold)),
                'order_statistic_one_based_rank': rank,
                'iid_continuous_one_sided95_tail_tolerance_upper': float(beta.ppf(.95, len(scores) + 1 - rank, rank)),
                'warning': 'Ordinary-only descriptive calibration; article dependence and source shift preclude a deployment FPR guarantee.',
                'model_sha256': sha(args.models / (name + '.joblib')),
            }
            state['per_working_point_calibration'] = {}
            for point, alpha in [('new_normal_1pct', .01), ('new_normal_5pct', .05)]:
                qrank = int(math.ceil((1-alpha)*(len(scores)-1)))+1
                qthreshold = float(np.quantile(scores, 1-alpha, method='higher'))
                state['per_working_point_calibration'][point] = {'target':alpha,'threshold':qthreshold,'n':len(scores),'rejected':int(np.sum(scores>qthreshold)),'order_statistic_one_based_rank':qrank,'iid_continuous_one_sided95_tail_tolerance_upper':float(beta.ppf(.95,len(scores)+1-qrank,qrank))}
            for row, score in zip(calibration, scores):
                calibration_records.append({'model': name, 'source_id': row['source_id'], 'article_id': row['article_id'], 'text_sha256': text_sha(row['context']), 'score': float(score)})
            score_cache[name].update((r['context'], float(s)) for r, s in zip(calibration, scores))
            timers[name] = {'ordinary_calibration_seconds': time.perf_counter() - t}
            model_states[name] = {'model': model, **state}
    write_json(output / 'thresholds_frozen.json', {k: {a: b for a, b in v.items() if a != 'model'} for k, v in model_states.items()})
    write_rows(output / 'calibration_scores.jsonl', calibration_records)
    # Source text, attack carrier text, and controls all receive the same frozen
    # passage-only input view, without a model tokenizer truncation.
    all_texts = dict.fromkeys([r['context'] for r in test] + [r['text'] for r in corpus])
    for case in cases:
        for field in ('attack_documents', 'matched_benign_documents'):
            for doc in case[field]:
                all_texts.setdefault(doc['text'], None)
    for row in external_rows:
        all_texts.setdefault(row['text'], None)
    texts = list(all_texts)
    with threadpool_limits(limits=args.threads):
        for name in MODELS:
            missing = [s for s in texts if s not in score_cache[name]]
            t = time.perf_counter()
            scores = detector_scores(model_states[name]['model'], name, missing, args.batch_size)
            timers[name]['test_and_corpus_scoring_seconds'] = time.perf_counter() - t
            timers[name]['unique_new_texts_scored'] = len(missing)
            score_cache[name].update(zip(missing, map(float, scores)))
    write_rows(output / 'unique_document_scores.jsonl', (
        {'text_sha256': text_sha(text), 'model': name, 'score': score_cache[name][text]}
        for text in texts for name in MODELS
    ))
    local_records, set_records = [], []
    with (output / 'document_predictions.jsonl').open('w', encoding='utf-8') as document_file, (output / 'case_predictions.jsonl').open('w', encoding='utf-8') as case_file:
        for case in cases:
            common = {k: case.get(k, 'unspecified') for k in ('case_id', 'family_id', 'template_id', 'question_id', 'article_id', 'placement', 'encoding_mode', 'language_mode', 'objective', 'threat_type')}
            for condition, field, label in [('attack', 'attack_documents', 1), ('matched_benign', 'matched_benign_documents', 0)]:
                docs = case[field]
                set_row = {**common, 'condition': condition, 'label': label, 'documents': len(docs), 'score_aggregation': 'maximum frozen passage score over this insertion set; not a learned contextual guard', 'scores': {}}
                for name in MODELS:
                    values = [score_cache[name][doc['text']] for doc in docs]
                    value = max(values)
                    set_row['scores'][name] = value
                for index, doc in enumerate(docs):
                    local_label = doc.get('local_attack_label', None if str(case.get('label_scope', '')).startswith('joint') and label else label)
                    if not label:
                        local_label = 0
                    row = {**common, 'condition': condition, 'insertion_index': index, 'document_id': document_id(doc), 'text_sha256': text_sha(doc['text']), 'local_label': local_label, 'scores': {name: score_cache[name][doc['text']] for name in MODELS}}
                    document_file.write(json.dumps(row, ensure_ascii=False) + '\n')
                    if local_label is not None:
                        local_records.append(row)
                case_file.write(json.dumps(set_row, ensure_ascii=False) + '\n')
                set_records.append(set_row)
    summary = []
    for level, records, label_field in [('insertion_set', set_records, 'label'), ('local_document', local_records, 'local_label')]:
        for cohort, indexes in cohort_indexes(records).items():
            rr = [records[i] for i in indexes]
            labels = [r[label_field] for r in rr]
            articles = [r['article_id'] for r in rr]
            for name in MODELS:
                scores = [r['scores'][name] for r in rr]
                for point, key in POINTS:
                    threshold = model_states[name][key]
                    summary.append({'level': level, 'cohort': cohort, 'model': name, 'operating_point': point, 'threshold': threshold, **classification_metrics(labels, scores, threshold, articles, args.bootstrap)})
    # Ordinary test-context false positives are independent of inserted payloads.
    for name in MODELS:
        for point, key in POINTS:
            summary.append({'level': 'ordinary_context', 'cohort': 'all', 'model': name, 'operating_point': point, 'threshold': model_states[name][key], **classification_metrics([0] * len(test), [score_cache[name][r['context']] for r in test], model_states[name][key], [r['article_id'] for r in test], args.bootstrap)})
    write_json(output / 'classification_summary.json', summary)
    paired = classification_pairs(set_records,model_states,args.bootstrap)
    write_json(output/'classification_paired_differences.json',paired)
    csv_rows(output/'classification_paired_differences.csv',paired)
    csv_rows(output / 'classification_summary.csv', summary)
    external_metadata = evaluate_external(external_rows, score_cache, model_states, output, args.bootstrap) if external_rows else None
    retrieval_metadata = None
    if not args.no_retrieval:
        retrieval_metadata = evaluate_retrieval(args, hosts, cases, corpus, host_map, score_cache, model_states, output)
    timers['total_seconds'] = time.perf_counter() - started
    timers['scope'] = 'CPU vectorization and sparse classification, analysis and optional exact TF-IDF delivery; no neural/generator execution.'
    write_json(output / 'timing.json', timers)
    manifest = {
        'status': 'COMPLETE_FROZEN_DETECTOR_EXPANDED_STRESS_TEST',
        'protocol_sha256': sha(protocol), 'script_sha256': sha(__file__),
        'input_freeze_sha256': sha(output / 'execution_freeze.json'),
        'threshold_freeze_sha256': sha(output / 'thresholds_frozen.json'),
        'cases': len(cases), 'case_conditions': len(set_records), 'local_labeled_documents': len(local_records),
        'unique_scored_texts': len(texts), 'detector_fits': 0, 'reused_detectors': 2,
        'neural_calls': 0, 'generator_calls': 0, 'target_tool_calls': 0,
        'retrieval': retrieval_metadata, 'passive_external': external_metadata,
        'software': {'python': platform.python_version(), 'numpy': np.__version__, 'scipy': scipy.__version__, 'sklearn': sklearn.__version__, 'joblib': joblib.__version__},
        'hardware': {'platform': platform.platform(), 'processor': platform.processor(), 'logical_cpus': os.cpu_count(), 'threadpool_limit': args.threads},
        'outputs': {p.name: sha(p) for p in sorted(output.iterdir()) if p.is_file()},
        'independence_scope': 'Paired sources reused across templates; article-group resampling. Case rows and models are not independent tasks. Unknown upstream training exposure remains.',
    }
    write_json(output / 'run_manifest.json', manifest)
    print(json.dumps({k: v for k, v in manifest.items() if k not in ('outputs',)}, indent=2))


def classification_pairs(records, model_states, draws):
    result = []
    for cohort, indexes in cohort_indexes(records).items():
        if not (cohort == 'all' or cohort.startswith(('family_id:', 'template_id:'))):
            continue
        rr = [records[i] for i in indexes]
        for label, metric in [(1, 'recall'), (0, 'fpr')]:
            selected = [r for r in rr if r['label'] == label]
            for point, key in POINTS:
                differences = [int(r['scores']['LinearSVC'] > model_states['LinearSVC'][key]) - int(r['scores']['LR'] > model_states['LR'][key]) for r in selected]
                result.append({'cohort': cohort, 'metric': metric, 'operating_point': point, 'contrast': 'LinearSVC_minus_LR', 'n': len(selected), **grouped_interval([r['article_id'] for r in selected], differences, draws), 'scope': 'Paired article resampling over the same insertion sets with fixed fitted detectors; no model-selection claim.'})
    return result


def evaluate_external(rows, score_cache, model_states, output, draws):
    """Passive classification of benchmark tool-output strings only."""
    parent = {}

    def find(key):
        parent.setdefault(key, key)
        while parent[key] != key:
            parent[key] = parent[parent[key]]
            key = parent[key]
        return key

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    for row in rows:
        if row['dataset'].startswith('AgentDojo'):
            groups = row.get('all_source_groups') or [row['source_group']]
            for group in groups:
                union(groups[0], group)
    for row in rows:
        if row['dataset'].startswith('AgentDojo'):
            row['_primary_group'] = find((row.get('all_source_groups') or [row['source_group']])[0])
        else:
            row['_primary_group'] = row.get('payload_parent') or row['source_group']
    predictions = []
    for row in rows:
        predictions.append({
            **{k: row.get(k) for k in ('id', 'dataset', 'label', 'family', 'source_group', 'payload_parent', 'upstream_repo', 'upstream_revision')},
            'cluster_id': row['_primary_group'], 'text_sha256': text_sha(row['text']),
            'scores': {name: score_cache[name][row['text']] for name in MODELS},
            'blocked': {name: {point: bool(score_cache[name][row['text']] > model_states[name][key]) for point, key in POINTS} for name in MODELS},
        })
    write_rows(output / 'external_predictions.jsonl', predictions)
    cohorts = collections.defaultdict(list)
    for row in rows:
        cohorts[row['dataset']].append(row)
        cohorts[row['dataset'] + '/family:' + row['family']].append(row)
    summary = []
    for cohort, rr in sorted(cohorts.items()):
        for name in MODELS:
            for point, key in POINTS:
                scores = [score_cache[name][row['text']] for row in rr]
                metrics = classification_metrics([row['label'] for row in rr], scores, model_states[name][key], [row['_primary_group'] for row in rr], draws)
                # These are source/attack-parent clusters, not article units.
                metrics['clusters'] = metrics.pop('articles')
                for metric in ('recall_uncertainty', 'fpr_uncertainty'):
                    if metrics.get(metric):
                        value = metrics[metric]
                        value['cluster_groups'] = value.pop('article_groups')
                        value['ci95_cluster_percentile'] = value.pop('ci95_article_percentile')
                        value['warning'] = value['warning'].replace('article groups', 'clusters')
                        value['scope'] = 'Fixed detector; resample observed payload parents (InjecAgent) or task components linked by repeated clean outputs (AgentDojo).'
                result = {
                    'cohort': cohort, 'model': name, 'operating_point': point,
                    'threshold': model_states[name][key], **metrics,
                    'payload_parent_groups': len({row['payload_parent'] for row in rr if row.get('payload_parent')}),
                    'user_task_parent_groups': len({row['source_group'] for row in rr}),
                    'scope': 'Passive full-tool-output detector probe using supplied benchmark labels; no target-agent/tool execution or measured downstream harm.',
                }
                # Two crossed dependence views are reported separately; neither
                # increases the number of distinct tasks or mechanisms.
                if all(row['label'] == 1 for row in rr):
                    blocked = [score > model_states[name][key] for score in scores]
                    alternative = grouped_interval([row['source_group'] for row in rr], blocked, draws)
                    alternative['user_task_groups'] = alternative.pop('article_groups')
                    alternative['ci95_user_task_percentile'] = alternative.pop('ci95_article_percentile')
                    alternative['scope'] = 'Alternative one-way task-parent resampling; crossed task/payload dependence is not fully captured.'
                    result['alternative_user_task_group_recall'] = alternative
                summary.append(result)
    write_json(output / 'external_summary.json', summary)
    csv_rows(output / 'external_summary.csv', summary)
    return {
        'rows': len(rows), 'datasets': dict(collections.Counter(r['dataset'] for r in rows)),
        'target_agent_executions': 0, 'target_tool_executions': 0,
        'scope': 'Benchmark strings passively scored with unchanged text-only classifiers; no benchmark task replay or attack success measurement.',
    }


def evaluate_retrieval(args, hosts, cases, corpus, host_map, score_cache, model_states, output):
    """Actual exact index delivery in a separate lexical retrieval harness."""
    t = time.perf_counter()
    ids = np.asarray([document_id(doc) for doc in corpus])
    assert len(ids) >= 20
    corpus_by_id = {document_id(doc): doc for doc in corpus}
    retriever = TfidfVectorizer(ngram_range=(1, 2), lowercase=True, sublinear_tf=True, max_features=50000, dtype=np.float64)
    with threadpool_limits(limits=args.threads):
        matrix = retriever.fit_transform([corpus_text(doc) for doc in corpus])
        test_hosts = [r for r in hosts if r['split'] == 'test']
        query_vectors = retriever.transform([r['question'] for r in test_hosts])
    qindex = {r['source_id']: i for i, r in enumerate(test_hosts)}
    top20 = {}
    clean_rows = []
    policies = [('none', None, None)] + [(name + '__' + point, name, key) for name in MODELS for point, key in POINTS]
    validation_case_ids = set(args._rank_validation_case_ids)
    validation_question_ids = {c['question_id'] for c in cases if c['case_id'] in validation_case_ids}
    validation_full_normal_scores = {}
    validation_receipts = []
    for host in test_hosts:
        q = query_vectors[qindex[host['source_id']]]
        sims = (q @ matrix.T).toarray().ravel()
        selected = np.lexsort((ids, -sims))[:20]
        base = [(float(sims[i]), str(ids[i]), corpus_by_id[str(ids[i])], False) for i in selected]
        top20[host['source_id']] = base
        if host['source_id'] in validation_question_ids:
            validation_full_normal_scores[host['source_id']] = sims
        clean_policies = {}
        for policy,name,key in policies:
            keep = base if name is None else [row for row in base if not score_cache[name][row[2]['text']] > model_states[name][key]]
            chosen=keep[:5]
            clean_policies[policy]={'selected_ids':[row[1]for row in chosen],'annotated_original_support_retained':host['document_id'] in [row[1]for row in chosen],'empty_context':not chosen,'selected_count':len(chosen)}
        clean_rows.append({'question_id': host['source_id'], 'article_id': host['article_id'], 'gold_document_id': host['document_id'], 'ranked_top20': [row[1] for row in base], 'gold_in_top20': host['document_id'] in [row[1] for row in base], 'gold_in_top5': host['document_id'] in [row[1] for row in base[:5]],'policies':clean_policies})
    write_rows(output / 'normal_retrieval.jsonl', clean_rows)
    aggregate = collections.defaultdict(list)
    delivery_count = 0
    # Processing insertion vectors one case at a time avoids retaining a large
    # sparse matrix for tens of thousands of repeated-host carriers.
    with (output / 'retrieval_delivery.jsonl').open('w', encoding='utf-8') as stream:
        for case in cases:
            host = host_map[str(case['question_id'])]
            query = query_vectors[qindex[case['question_id']]]
            base = top20[case['question_id']]
            for condition, field in [('attack', 'attack_documents'), ('matched_benign', 'matched_benign_documents')]:
                inserted = case[field]
                insert_ids = {document_id(doc) for doc in inserted}
                assert not insert_ids.intersection(corpus_by_id), 'Insertion identities must be new'
                vectors = retriever.transform([corpus_text(doc) for doc in inserted])
                similarities = (query @ vectors.T).toarray().ravel()
                ranked = sorted(base + [(float(score), document_id(doc), doc, True) for doc, score in zip(inserted, similarities)], key=lambda row: (-row[0], row[1]))[:20]
                if case['case_id'] in validation_case_ids:
                    full_scores=validation_full_normal_scores[case['question_id']]
                    full_sorted=sorted([(float(score),str(doc_id))for score,doc_id in zip(full_scores,ids)]+[(float(score),document_id(doc))for doc,score in zip(inserted,similarities)],key=lambda row:(-row[0],row[1]))[:20]
                    expected=[r[1]for r in full_sorted];actual=[r[1]for r in ranked]
                    assert expected==actual, 'Full frozen-index insertion sorting disagrees with shortcut'
                    validation_receipts.append({'case_id':case['case_id'],'template_id':case['template_id'],'condition':condition,'full_index_top20':expected,'shortcut_top20':actual,'passed':True})
                scores_by_policy = {}
                for policy, name, key in policies:
                    survivors = ranked if name is None else [row for row in ranked if not score_cache[name][row[2]['text']] > model_states[name][key]]
                    chosen = survivors[:5]
                    chosen_ids = [row[1] for row in chosen]
                    present = insert_ids.intersection(chosen_ids)
                    support = host['document_id'] in chosen_ids
                    item = {
                        'selected_ids': chosen_ids,
                        'inserted_documents_selected': len(present),
                        'any_inserted_document_present': bool(present),
                        'all_inserted_documents_present': len(present) == len(insert_ids),
                        'annotated_original_support_retained': support,
                        'known_benign_source_support_retained': (support or bool(present)) if condition == 'matched_benign' else None,
                        'selected_count': len(chosen),
                        'empty_context': not chosen,
                        'normal_records_rejected_in_pool': 0 if name is None else sum(not row[3] and score_cache[name][row[2]['text']] > model_states[name][key] for row in ranked),
                    }
                    scores_by_policy[policy] = item
                    for cohort in ['all', 'family_id:' + case['family_id'], 'template_id:' + case['template_id']]:
                        aggregate[condition, policy, cohort].append((case['article_id'], item))
                row = {'case_id': case['case_id'], 'question_id': case['question_id'], 'article_id': case['article_id'], 'family_id': case['family_id'], 'template_id': case['template_id'], 'condition': condition, 'label_scope': case.get('label_scope', 'local_document'), 'ranked_top20': [row[1] for row in ranked], 'insertion_count': len(inserted), 'inserted_ids': sorted(insert_ids), 'policies': scores_by_policy}
                stream.write(json.dumps(row, ensure_ascii=False) + '\n')
                delivery_count += 1
    assert len(validation_receipts)==2*len(validation_case_ids), 'Missing declared full-sort validation cases'
    write_json(output/'retrieval_validation.json',{'scope':'Actual full normal-index plus insertions sorting versus shortcut; frozen vocabulary/IDF; stable tie ordering','selected_before_test_scoring':True,'case_ids_frozen_in_execution_freeze':sorted(validation_case_ids),'checks':len(validation_receipts),'all_passed':all(r['passed']for r in validation_receipts),'records':validation_receipts})
    summary = []
    for (condition, policy, cohort), records in sorted(aggregate.items()):
        groups = [r[0] for r in records]
        row = {'condition': condition, 'policy': policy, 'cohort': cohort, 'n': len(records), 'articles': len(set(groups))}
        for metric in ['any_inserted_document_present', 'all_inserted_documents_present', 'annotated_original_support_retained', 'known_benign_source_support_retained', 'empty_context']:
            values = [r[1][metric] for r in records]
            if values[0] is None:
                continue
            row[metric + '_count'] = int(sum(values))
            row[metric + '_rate'] = float(np.mean(values))
            row[metric + '_uncertainty'] = grouped_interval(groups, values, args.bootstrap)
        row['scope'] = 'Delivered-document structure only; attacker-document presence is not generator attack success, semantic adoption, or factual accuracy.'
        summary.append(row)
    for policy,_,_ in policies:
        records=[(r['article_id'],r['policies'][policy])for r in clean_rows]
        row={'condition':'clean','policy':policy,'cohort':'all','n':len(records),'articles':len({r[0]for r in records})}
        for metric in ['annotated_original_support_retained','empty_context']:
            values=[r[1][metric]for r in records];row[metric+'_count']=int(sum(values));row[metric+'_rate']=float(np.mean(values));row[metric+'_uncertainty']=grouped_interval([r[0]for r in records],values,args.bootstrap)
        row['scope']='Ordinary unmodified top20 pools; original supporting paragraph identity only.'
        summary.append(row)
    retrieval_pairs=[]
    for (condition,policy,cohort), records in sorted(aggregate.items()):
        if not policy.endswith('__new_normal_1pct'):
            continue
        baseline=aggregate[condition,'none',cohort]
        assert len(records)==len(baseline) and all(a[0]==b[0]for a,b in zip(records,baseline))
        metrics=['any_inserted_document_present','all_inserted_documents_present','annotated_original_support_retained'] if condition=='attack' else ['annotated_original_support_retained','known_benign_source_support_retained']
        for metric in metrics:
            differences=[int(row[1][metric])-int(base[1][metric])for row,base in zip(records,baseline)]
            retrieval_pairs.append({'condition':condition,'policy':policy,'cohort':cohort,'metric':metric,'contrast':policy+'_minus_none','n':len(records),**grouped_interval([r[0]for r in records],differences,args.bootstrap)})
    for policy,_,_ in policies:
        if not policy.endswith('__new_normal_1pct'):
            continue
        for metric in ['annotated_original_support_retained','empty_context']:
            differences=[int(r['policies'][policy][metric])-int(r['policies']['none'][metric])for r in clean_rows]
            retrieval_pairs.append({'condition':'clean','policy':policy,'cohort':'all','metric':metric,'contrast':policy+'_minus_none','n':len(clean_rows),**grouped_interval([r['article_id']for r in clean_rows],differences,args.bootstrap)})
    write_json(output/'retrieval_paired_differences.json',retrieval_pairs)
    csv_rows(output/'retrieval_paired_differences.csv',retrieval_pairs)
    write_json(output / 'retrieval_summary.json', summary)
    csv_rows(output / 'retrieval_summary.csv', summary)
    return {
        'kind': 'Exact word1-2 TF-IDF cosine, separate expanded harness',
        'normal_corpus_documents': len(corpus), 'questions': len(test_hosts),
        'retriever_index_fits': 1, 'detector_fits': 0, 'vocabulary_size': len(retriever.vocabulary_),
        'candidates': 20, 'delivery_budget': 5, 'new_queries_after_filtering': 0,
        'insertion_ranking': 'Stable score-descending then document-id ordering over normal top20 plus new insertions; pure append equivalence to full sorting with vocabulary and IDF held fixed.',
        'delivery_records': delivery_count, 'independent_full_sort_validation_checks':len(validation_receipts), 'elapsed_seconds': time.perf_counter() - t,
        'scope': 'Small-corpus lexical delivery experiment, not a rerun of Contriever/Qwen or any published poisoning optimizer.',
    }


if __name__ == '__main__':
    main()
