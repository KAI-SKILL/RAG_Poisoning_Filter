"""Read external evaluation only: no fitting, threshold selection, or calibration.

Usage: from public_data.load_public_data import load_records
       records = load_records()  # dictionaries include text, label and provenance
Labels: 0 benign, 1 indirect-injection attack payload.
"""
from pathlib import Path
import hashlib
import json
import re
import unicodedata

ROOT = Path(__file__).resolve().parent

def normalize_text(text):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFKC', text)).strip().casefold()

def iter_records(dataset='all'):
    """Yield dictionaries with text/label/source/license; never reshuffle or fit."""
    if dataset not in {'all', 'notinject', 'bipia'}:
        raise ValueError('dataset must be all, notinject or bipia')
    if dataset in {'all', 'notinject'}:
        for subset in ['one', 'two', 'three']:
            filename = f'NotInject_{subset}.json'
            samples = json.loads((ROOT / filename).read_text(encoding='utf-8'))
            for i, sample in enumerate(samples):
                yield {
                    'id': f'notinject:{subset}:{i}', 'text': sample['prompt'], 'label': 0,
                    'dataset': 'NotInject', 'subset': subset,
                    'category': sample['category'], 'family': f'notinject:{subset}',
                    'language_cohort': ('Multilingual-category' if sample['category'] == 'Multilingual'
                                        else 'other-category'),
                    'source': 'https://github.com/leolee99/PIGuard/blob/main/datasets/' + filename,
                    'original_source': 'https://huggingface.co/datasets/leolee99/NotInject',
                    'license': 'MIT', 'usage': 'external evaluation only',
                    'unit': 'benign standalone prompt',
                }
    if dataset in {'all', 'bipia'}:
        for kind in ['text', 'code']:
            filename = f'{kind}_attack_test.json'
            attacks = json.loads((ROOT / filename).read_text(encoding='utf-8'))
            for family, texts in attacks.items():
                for i, text in enumerate(texts):
                    yield {
                        'id': f'bipia:{kind}:{family}:{i}', 'text': text, 'label': 1,
                        'dataset': 'BIPIA', 'subset': kind,
                        'category': family, 'family': f'bipia:{kind}:{family}',
                        'language_cohort': 'not-stratified',
                        'source': 'https://github.com/microsoft/BIPIA/blob/main/benchmark/' + filename,
                        'license': 'MIT (attack assets; contextual benchmark sources have exceptions)',
                        'usage': 'external evaluation only',
                        'unit': 'attack payload without surrounding retrieved context',
                    }

def load_records(dataset='all'):
    return list(iter_records(dataset))

if __name__ == '__main__':
    from collections import Counter
    records = load_records()
    assert len(records) == 464
    assert Counter(r['label'] for r in records) == {0: 339, 1: 125}
    train = []
    for kind in ['text', 'code']:
        data = json.loads((ROOT/f'{kind}_attack_train.json').read_text())
        train.extend(t for values in data.values() for t in values)
    test_attacks = [r['text'] for r in records if r['dataset'] == 'BIPIA']
    overlap = sorted(set(map(normalize_text, train)) & set(map(normalize_text, test_attacks)))
    stats = {
        'n_records': len(records), 'labels': dict(Counter(r['label'] for r in records)),
        'dataset_counts': dict(Counter(r['dataset'] for r in records)),
        'notinject_categories': dict(Counter(r['category'] for r in records if r['dataset']=='NotInject')),
        'notinject_language_cohorts': dict(Counter(r['language_cohort'] for r in records if r['dataset']=='NotInject')),
        'bipia_family_count': len(set(r['family'] for r in records if r['dataset']=='BIPIA')),
        'normalized_duplicate_rows': len(records)-len(set(normalize_text(r['text']) for r in records)),
        'bipia_train_test_normalized_overlap_count': len(overlap),
        'training_and_tuning_use': 'none; test-only release',
    }
    (ROOT/'public_eval.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records),encoding='utf-8')
    (ROOT/'data_statistics.json').write_text(json.dumps(stats,indent=2)+'\n')
    print(json.dumps(stats,indent=2))
