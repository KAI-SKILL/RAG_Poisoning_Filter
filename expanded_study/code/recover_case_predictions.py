"""Recover a missing serialized case-prediction tail from frozen score archives.

No model is loaded and no prediction is executed. Recovery is permitted only if
the saved file is an exact byte prefix of deterministic reconstruction, every
document score agrees with the full document-prediction archive, and all saved
insertion-set confusion cells are unchanged. Original bytes and manifest remain
under audit/recovery. The canonical manifest records the serialization repair.
"""
from pathlib import Path
import argparse
import collections
import datetime
import hashlib
import json
import math
import os
import shutil

MODELS = ('LR', 'LinearSVC')
POINTS = (('new_normal_1pct', 'threshold_1pct'), ('new_normal_5pct', 'threshold_5pct'), ('previous_external_5pct', 'previous_threshold'))
DIMS = ('family_id', 'template_id', 'placement', 'encoding_mode', 'language_mode', 'objective', 'threat_type')
COMMON = ('case_id', 'family_id', 'template_id', 'question_id', 'article_id', 'placement', 'encoding_mode', 'language_mode', 'objective', 'threat_type')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def atomic_json(path, value):
    temporary = path.with_name(path.name + '.tmp')
    with temporary.open('wb') as stream:
        data = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()
        assert stream.write(data) == len(data)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    results = root / 'results'
    canonical = results / 'case_predictions.jsonl'
    manifest_path = results / 'run_manifest.json'
    manifest = json.loads(manifest_path.read_text())
    freeze = json.loads((results / 'execution_freeze.json').read_text())
    for entry in freeze['inputs'].values():
        assert sha(root / entry['path']) == entry['sha256'], 'Frozen input changed'
    for name, expected in manifest['outputs'].items():
        assert sha(results / name) == expected, 'Pre-recovery output hash mismatch: ' + name
    before_manifest_sha = sha(manifest_path)
    original_sha = sha(canonical)
    original_bytes = canonical.stat().st_size
    original_rows = sum(1 for line in canonical.open('rb') if line.strip())
    sources = {
        'cases_sha256': sha(root / 'data/cases.jsonl'),
        'score_cache_sha256': sha(results / 'unique_document_scores.jsonl'),
        'document_predictions_sha256': sha(results / 'document_predictions.jsonl'),
        'thresholds_sha256': sha(results / 'thresholds_frozen.json'),
        'classification_summary_sha256': sha(results / 'classification_summary.json'),
    }
    cache = {}
    for line in (results / 'unique_document_scores.jsonl').open():
        row = json.loads(line)
        key = (row['text_sha256'], row['model'])
        assert key not in cache
        assert math.isfinite(row['score'])
        cache[key] = row['score']
    thresholds = json.loads((results / 'thresholds_frozen.json').read_text())
    counters = collections.defaultdict(collections.Counter)
    temporary = results / 'case_predictions_reconstruction.tmp'
    expected_rows = 0
    document_rows_checked = 0
    prefix_bytes_checked = 0
    expected_hash = hashlib.sha256()
    with canonical.open('rb') as original, (results / 'document_predictions.jsonl').open() as document_stream, temporary.open('wb') as target:
        for line in (root / 'data/cases.jsonl').open():
            case = json.loads(line)
            common = {key: case.get(key, 'unspecified') for key in COMMON}
            for condition, field, label in [('attack', 'attack_documents', 1), ('matched_benign', 'matched_benign_documents', 0)]:
                docs = case[field]
                expected = {**common, 'condition': condition, 'label': label, 'documents': len(docs), 'score_aggregation': 'maximum frozen passage score over this insertion set; not a learned contextual guard', 'scores': {}}
                scores = {name: [] for name in MODELS}
                for index, doc in enumerate(docs):
                    fingerprint = hashlib.sha256(doc['text'].encode()).hexdigest()
                    saved_line = next(document_stream)
                    saved = json.loads(saved_line)
                    assert saved['case_id'] == case['case_id'] and saved['condition'] == condition
                    assert saved['document_id'] == doc.get('doc_id', doc.get('document_id'))
                    assert saved['insertion_index'] == index and saved['text_sha256'] == fingerprint
                    for name in MODELS:
                        score = cache[fingerprint, name]
                        assert score == saved['scores'][name]
                        scores[name].append(score)
                    document_rows_checked += 1
                for name in MODELS:
                    expected['scores'][name] = max(scores[name])
                data = (json.dumps(expected, ensure_ascii=False) + '\n').encode()
                existing_prefix = original.read(len(data))
                assert data.startswith(existing_prefix), 'Original case file differs before its saved endpoint'
                prefix_bytes_checked += len(existing_prefix)
                assert target.write(data) == len(data)
                expected_hash.update(data)
                expected_rows += 1
                cohorts = ['all'] + [key + ':' + str(common[key]) for key in DIMS]
                for name in MODELS:
                    for point, key in POINTS:
                        blocked = expected['scores'][name] > thresholds[name][key]
                        cell = 'tp' if label and blocked else 'fn' if label else 'fp' if blocked else 'tn'
                        for cohort in cohorts:
                            counters[name, point, cohort][cell] += 1
        assert not original.read(), 'Original case file extends beyond declared expected cases'
        assert next(document_stream, None) is None, 'Document archive has undeclared extra records'
        target.flush()
        os.fsync(target.fileno())
    assert prefix_bytes_checked == original_bytes
    assert sha(temporary) == expected_hash.hexdigest()
    assert sum(1 for line in temporary.open('rb') if line.strip()) == expected_rows == 57600
    assert document_rows_checked == 67200
    cells_checked = 0
    for row in json.loads((results / 'classification_summary.json').read_text()):
        if row['level'] != 'insertion_set':
            continue
        counts = counters[row['model'], row['operating_point'], row['cohort']]
        assert sum(counts.values()) == row['n']
        for key in ('tp', 'fp', 'tn', 'fn'):
            assert counts[key] == row[key], (row['model'], row['operating_point'], row['cohort'], key)
        cells_checked += 1
    if original_bytes == temporary.stat().st_size:
        temporary.unlink()
        print(json.dumps({'status': 'ALREADY_COMPLETE', 'rows': expected_rows, 'confusion_summary_cells_checked': cells_checked}, indent=2))
        return
    assert original_rows < expected_rows
    archive = root / 'audit/recovery'
    archive.mkdir(parents=True, exist_ok=True)
    for source, name in [(canonical, 'case_predictions_truncated_original.jsonl'), (manifest_path, 'run_manifest_before_serialization_recovery.json')]:
        destination = archive / name
        assert not destination.exists(), 'Recovery archive already exists; do not overwrite it'
        shutil.copy2(source, destination)
        assert sha(destination) == sha(source)
    os.replace(temporary, canonical)
    assert sha(canonical) == expected_hash.hexdigest()
    assert sum(1 for line in canonical.open('rb') if line.strip()) == expected_rows
    receipt = {
        'status': 'RECOVERED_COMPLETE_CASE_PREDICTIONS_FROM_FROZEN_SCORES',
        'timestamp_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'script_sha256': sha(__file__), 'pre_recovery_manifest_sha256': before_manifest_sha,
        'original_rows': original_rows, 'recovered_rows': expected_rows - original_rows, 'final_rows': expected_rows,
        'original_bytes': original_bytes, 'final_bytes': canonical.stat().st_size,
        'original_sha256': original_sha, 'final_sha256': sha(canonical),
        'original_exact_prefix_bytes_verified': prefix_bytes_checked,
        'document_prediction_scores_checked': document_rows_checked,
        'insertion_set_summary_cells_reconstructed_unchanged': cells_checked,
        'sources': sources,
        'new_model_fits': 0, 'new_model_scoring_calls': 0, 'neural_calls': 0, 'generator_calls': 0,
        'scope': 'Serialization-only tail recovery; input cases, labels, all underlying model scores, thresholds, summaries and intervals remain unchanged.',
        'cause': 'The first saved case file ended early at a complete record despite the complete document and score archives. The physical truncation mechanism is not established by available evidence.',
        'preserved_originals': ['audit/recovery/case_predictions_truncated_original.jsonl', 'audit/recovery/run_manifest_before_serialization_recovery.json'],
    }
    atomic_json(root / 'audit/serialization_recovery.json', receipt)
    manifest['status'] = 'COMPLETE_WITH_DOCUMENTED_CASE_SERIALIZATION_RECOVERY'
    manifest['pre_recovery_manifest_sha256'] = before_manifest_sha
    manifest['outputs']['case_predictions.jsonl'] = sha(canonical)
    manifest['serialization_recovery'] = {'receipt': 'audit/serialization_recovery.json', 'receipt_sha256': sha(root / 'audit/serialization_recovery.json'), 'new_model_scoring_calls': 0, 'final_case_rows': expected_rows}
    atomic_json(manifest_path, manifest)
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
