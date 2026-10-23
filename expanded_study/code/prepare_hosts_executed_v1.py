"""Freeze unseen-article, numeric-answer hosts for controlled RAG attacks.

This program constructs data only. It never loads a detector, generates answers,
uses a reference as a predictor input, or selects examples from model outcomes.
"""
from __future__ import annotations
import argparse, collections, datetime, hashlib, json, re, shutil, unicodedata
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import quote

SQUAD_URL = 'https://rajpurkar.github.io/SQuAD-explorer/dataset/train-v1.1.json'
EXPECTED_SHA = '3527663986b8295af4f7fcdff1ba1ff3f72d07d61a20f487cb238a6ef92fd955'
NUMERIC = re.compile(r'(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?\Z')
NUMBER_IN_TEXT = re.compile(r'(?<![\w.])(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?![\w.])')
TIME_WORDS = re.compile(r'\b(now|today|current|currently|latest)\b', re.I)


def norm(value: str) -> str:
    return ' '.join(re.findall(r'\w+', unicodedata.normalize('NFKC', value).casefold()))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text_hash(value: str) -> str:
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def read_rows(path: Path):
    return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines() if s.strip()]


def write_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def write_rows(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + '\n')


def previous_keys(previous: Path):
    old_path = previous / 'improved_experiment/inputs/clean_target_candidates.json'
    old = json.loads(old_path.read_text(encoding='utf-8'))
    prior_path = previous / 'revised_experiment/data/records_formal_v2.jsonl'
    prior = read_rows(prior_path)
    titles = {norm(d['title']) for q in old.values() for d in q['docs']}
    titles.update(norm(r['title']) for r in prior)
    questions = {norm(q['question']) for q in old.values()}
    questions.update(norm(r[key]) for r in prior for key in ['question', 'original_question'])
    texts = {norm(d['text']) for q in old.values() for d in q['docs']}
    texts.update(norm(r['gold_passage']) for r in prior)
    extra_corpus = previous / 'revised_experiment/data/corpus.jsonl'
    if extra_corpus.is_file():
        texts.update(norm(r['text']) for r in read_rows(extra_corpus))
    return titles, questions, texts, [old_path, prior_path, extra_corpus]


def make_target(answer: str, context: str, key: str):
    """A different, format-preserving number absent by text and numeric value."""
    original = Decimal(answer.replace(',', ''))
    precision = len(answer.split('.', 1)[1]) if '.' in answer else 0
    commas = ',' in answer
    leading_width = len(answer.split('.', 1)[0]) if answer.startswith('0') and not commas else 0
    present_values = set()
    for match in NUMBER_IN_TEXT.finditer(context):
        try:
            present_values.add(Decimal(match.group().replace(',', '')))
        except InvalidOperation:
            pass
    prefer_sign = 1 if int(text_hash(key)[0], 16) % 2 == 0 else -1
    for magnitude in range(1, 1001):
        for sign in [prefer_sign, -prefer_sign]:
            candidate = original + Decimal(sign * 7 * magnitude)
            if candidate < 0 or candidate == original or candidate in present_values:
                continue
            target = format(candidate, f',.{precision}f' if commas else f'.{precision}f')
            if leading_width:
                integer, *fraction = target.split('.')
                target = integer.zfill(leading_width) + ('.' + fraction[0] if fraction else '')
            if target in context or norm(target) in norm(context):
                continue
            digits_answer = answer.replace(',', '')
            digits_target = target.replace(',', '')
            if digits_answer in digits_target or digits_target in digits_answer:
                continue
            return target, {'method': 'numeric_plus_or_minus_multiple_of_seven', 'delta': str(candidate - original), 'precision': precision, 'comma_format_retained': commas, 'target_absent_as_numeric_value': True, 'target_absent_as_literal_and_normalized_substring': True}
    raise ValueError('No absent controlled numeric target for ' + key)


def balanced_take(by_article, n: int, order_key):
    """Round robin prevents large articles from taking the first n records."""
    buckets = {key: sorted(values, key=order_key) for key, values in by_article.items() if values}
    keys = sorted(buckets, key=lambda key: text_hash('Group9-Balanced-Articles|' + key))
    result = []
    index = 0
    while len(result) < n:
        progressed = False
        for key in keys:
            if index < len(buckets[key]):
                result.append(buckets[key][index])
                progressed = True
                if len(result) == n:
                    return result
        if not progressed:
            raise ValueError(f'Only {len(result)} records available, need {n}')
        index += 1
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--squad', type=Path, required=True)
    parser.add_argument('--previous', type=Path, required=True)
    parser.add_argument('--seed', type=int, default=20261022)
    parser.add_argument('--calibration-groups', type=int, default=50)
    parser.add_argument('--calibration-hosts', type=int, default=1200)
    parser.add_argument('--test-hosts', type=int, default=1200)
    args = parser.parse_args()
    root = args.root.resolve()
    destinations = [root/'data/hosts.jsonl', root/'data/corpus.jsonl', root/'audit/host_build_validation.json', root/'data/host_protocol.json']
    if any(p.exists() for p in destinations):
        raise SystemExit('Refusing to overwrite an existing frozen host build; use a new --root')
    source_hash = sha(args.squad)
    if source_hash != EXPECTED_SHA:
        raise SystemExit('Unexpected SQuAD snapshot hash; protocol requires the recorded official v1.1 train release')
    source = json.loads(args.squad.read_text(encoding='utf-8'))
    old_titles, old_questions, old_texts, old_inputs = previous_keys(args.previous)
    counts = collections.Counter()
    articles = []
    seen_questions = set()
    seen_contexts = set()
    for article in source['data']:
        title = article['title'].replace('_', ' ')
        article_norm = norm(title)
        if article_norm in old_titles:
            counts['excluded_prior_article'] += 1
            continue
        article_id = 'squad-article-' + text_hash(article_norm)[:16]
        paragraphs = []
        for pi, paragraph in enumerate(article['paragraphs']):
            context = paragraph['context']
            normal_context = norm(context)
            if not 50 <= len(context.split()) <= 220:
                counts['paragraph_length_excluded'] += 1
                continue
            if normal_context in old_texts or normal_context in seen_contexts:
                counts['old_or_duplicate_paragraph_excluded'] += 1
                continue
            candidates = []
            for qa in paragraph['qas']:
                question = qa['question']
                normalized_question = norm(question)
                answers = qa.get('answers', [])
                if not 5 <= len(question.split()) <= 30 or normalized_question in old_questions or TIME_WORDS.search(question):
                    continue
                if not answers or len({norm(a['text']) for a in answers}) != 1:
                    continue
                answer = answers[0]['text']
                if not 1 <= len(answer.split()) <= 5 or not 3 <= len(answer) <= 55:
                    continue
                if not (answer[0].isupper() or answer[0].isdigit()) or context.count(answer) != 1:
                    continue
                if any(context[a['answer_start']:a['answer_start'] + len(a['text'])] != a['text'] for a in answers):
                    continue
                if normalized_question in seen_questions:
                    counts['duplicate_question_excluded'] += 1
                    continue
                is_numeric = bool(NUMERIC.fullmatch(answer)) and bool(re.search(r'(?<![\w.])' + re.escape(answer) + r'(?![\w.])', context))
                row = {'source_id': 'squad-' + qa['id'], 'article_id': article_id, 'title': title, 'question': f'Regarding {title}: ' + question, 'original_question': question, 'context': context, 'answer': answer, 'answers': list(dict.fromkeys(a['text'] for a in answers)), 'answer_start': answers[0]['answer_start'], 'document_id': article_id + '-p' + str(pi), 'source_url': 'https://en.wikipedia.org/wiki/' + quote(article['title'], safe='()'), 'source_paragraph_index': pi, 'source_dataset': 'SQuAD v1.1 train; controlled unused-article expansion', 'source_context_sha256': text_hash(context), 'answer_type': 'numeric' if is_numeric else 'annotated_phrase', '_normalized_question': normalized_question}
                candidates.append(row)
            if not candidates:
                continue
            seen_contexts.add(normal_context)
            for row in candidates:
                seen_questions.add(row['_normalized_question'])
            counts['eligible_questions'] += len(candidates)
            counts['eligible_numeric_questions'] += sum(row['answer_type'] == 'numeric' for row in candidates)
            paragraphs.append({'document_id': candidates[0]['document_id'], 'title': title, 'text': context, 'article_id': article_id, 'source_url': candidates[0]['source_url'], 'source_paragraph_index': pi, 'source_context_sha256': text_hash(context), 'candidates': candidates})
        if paragraphs:
            articles.append({'title': title, 'article_id': article_id, 'paragraphs': paragraphs})
        else:
            counts['unused_article_without_eligible_rows'] += 1
    # Exact duplicate paragraphs and questions are removed before assigning roles.
    split_label = 'Group9-Expanded-' + str(args.seed)
    articles.sort(key=lambda a: text_hash(split_label + '|' + a['title']))
    cal_group_count = args.calibration_groups
    while cal_group_count < len(articles):
        cal_available = sum(len(a['paragraphs']) for a in articles[:cal_group_count])
        test_available = sum(any(r['answer_type'] == 'numeric' for r in p['candidates']) for a in articles[cal_group_count:] for p in a['paragraphs'])
        if cal_available >= args.calibration_hosts and test_available >= args.test_hosts:
            break
        if cal_available < args.calibration_hosts:
            cal_group_count += 1
        else:
            raise SystemExit('Requested numeric test hosts unavailable after calibration allocation')
    else:
        raise SystemExit('Could not construct source-disjoint calibration/test split')
    calibration_articles, test_articles = articles[:cal_group_count], articles[cal_group_count:]
    calibration_candidates = collections.defaultdict(list)
    numeric_candidates = collections.defaultdict(list)
    for article in calibration_articles:
        for paragraph in article['paragraphs']:
            choices = sorted(paragraph['candidates'], key=lambda row: text_hash(split_label + '|qa|' + row['source_id']))
            calibration_candidates[article['article_id']].append(choices[0])
    for article in test_articles:
        for paragraph in article['paragraphs']:
            choices = [row for row in paragraph['candidates'] if row['answer_type'] == 'numeric']
            choices.sort(key=lambda row: text_hash(split_label + '|qa|' + row['source_id']))
            if choices:
                numeric_candidates[article['article_id']].append(choices[0])
    selected_cal = balanced_take(calibration_candidates, args.calibration_hosts, lambda row: text_hash(split_label + '|select|' + row['source_id']))
    selected_test = balanced_take(numeric_candidates, args.test_hosts, lambda row: text_hash(split_label + '|select|' + row['source_id']))
    hosts = []
    for split, selected in [('calibration', selected_cal), ('test', selected_test)]:
        for row in selected:
            row = {k: v for k, v in row.items() if not k.startswith('_')}
            row['split'] = split
            if split == 'test':
                row['target'], row['target_construction'] = make_target(row['answer'], row['context'], split_label + '|' + row['source_id'])
                start, answer = row['answer_start'], row['answer']
                replacement = row['context'][:start] + row['target'] + row['context'][start + len(answer):]
                assert row['context'][start:start + len(answer)] == answer
                assert row['context'].count(answer) == 1
                assert row['target'] not in row['context']
                assert replacement.count(row['target']) == 1
                assert replacement[:start] == row['context'][:start]
                assert replacement[start + len(row['target']):] == row['context'][start + len(answer):]
                row['counterfactual_context'] = replacement
                row['counterfactual_context_sha256'] = text_hash(replacement)
                row['label_scope'] = 'Controlled numeric answer-span counterfactual to the frozen source annotation; automatically validated, not independent human/current-world fact verification.'
            else:
                row['target'] = None
                row['target_construction'] = None
                row['label_scope'] = 'Authentic normal calibration source paragraph; no malicious payload added.'
            hosts.append(row)
    corpus = []
    for article in test_articles:
        for paragraph in article['paragraphs']:
            corpus.append({k: v for k, v in paragraph.items() if k != 'candidates'} | {'split': 'test', 'label': 0})
    # Complete structural checks before the data release is finalized.
    cal = [r for r in hosts if r['split'] == 'calibration']
    test = [r for r in hosts if r['split'] == 'test']
    assert len(cal) == args.calibration_hosts and len(test) == args.test_hosts
    assert len({r['document_id'] for r in hosts}) == len(hosts)
    assert len({norm(r['context']) for r in hosts}) == len(hosts)
    assert len({norm(r['original_question']) for r in hosts}) == len(hosts)
    assert {r['article_id'] for r in cal}.isdisjoint(r['article_id'] for r in test)
    assert {norm(r['title']) for r in hosts}.isdisjoint(old_titles)
    assert {norm(r['context']) for r in hosts}.isdisjoint(old_texts)
    assert {norm(r['original_question']) for r in hosts}.isdisjoint(old_questions)
    assert all(r['answer_type'] == 'numeric' for r in test)
    assert len({r['document_id'] for r in corpus}) == len(corpus)
    corpus_ids = {r['document_id'] for r in corpus}
    assert all(r['document_id'] in corpus_ids for r in test)
    protocol = {'status': 'FROZEN_DATA_ONLY_BEFORE_DETECTOR_EVALUATION', 'seed': args.seed, 'source_split_label': split_label, 'source_sha256': source_hash, 'source_group_order': 'SHA256(split_label + vertical bar + human-readable article title)', 'requested_calibration_groups': args.calibration_groups, 'actual_calibration_groups': cal_group_count, 'calibration_hosts': args.calibration_hosts, 'test_hosts': args.test_hosts, 'scope': 'Numeric-answer controlled suite on unused article groups; not representative of all QA, not an official SQuAD evaluation, no upstream-pretraining exclusion guarantee.', 'same_question_panel': 'The 1200 test hosts may be reused across templates for paired comparisons; template rows never inflate independent source-question count.', 'eligibility': '50-220 context words;5-30 question words;3-55 answer characters;1-5 answer words;initial uppercase/digit;one consistent annotated answer;one exact source occurrence and exact answer offsets;explicit current-time words excluded.', 'numeric_eligibility': 'Nonnegative integer or fixed-point decimal with optional valid thousands commas;bounded numeric span;target differs by nonzero multiple of7, preserves decimal precision/comma use, and is absent by numeric value and substring.', 'calibration_selection': 'One question per unique paragraph;balanced round-robin article selection with deterministic per-article question/paragraph hash order.', 'test_selection': 'One numeric question per unique paragraph;balanced round-robin among eligible test articles.', 'previous_source_exclusions': [{'file': str(p.relative_to(args.previous)), 'sha256': sha(p)} for p in old_inputs if p.is_file()], 'builder_sha256': sha(Path(__file__)), 'models_called': 0}
    write_json(root/'data/host_protocol.json', protocol)
    write_rows(root/'data/hosts.jsonl', hosts)
    write_rows(root/'data/corpus.jsonl', corpus)
    raw_path = root/'raw/squad_train-v1.1.json'
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    if raw_path.exists() and sha(raw_path) != source_hash:
        raise SystemExit('Existing raw snapshot differs')
    if not raw_path.exists():
        shutil.copy2(args.squad, raw_path)
    attribution = '''# SQuAD source attribution and transformation notice\n\nSource: Stanford Question Answering Dataset v1.1, Rajpurkar, Zhang, Lopyrev and Liang (EMNLP 2016). Official dataset: https://rajpurkar.github.io/SQuAD-explorer/ . The snapshot is preserved unchanged as squad_train-v1.1.json, with URL, byte count and SHA-256 recorded separately.\n\nSQuAD is distributed under Creative Commons Attribution-ShareAlike 4.0 as documented by its source dataset card. License: https://creativecommons.org/licenses/by-sa/4.0/ . Wikipedia passage contributors retain attribution through article titles and per-document Wikipedia source URLs. These are dataset snapshot passages, not current live-page retrieval.\n\nDerived controlled attack contexts replace one annotated numeric span or add locally constructed instruction payloads. Such modifications are declared in each row. Source code licensing does not replace the original passage/data rights.\n\nCitation: P. Rajpurkar, J. Zhang, K. Lopyrev, and P. Liang, “SQuAD: 100,000+ Questions for Machine Comprehension of Text,” EMNLP, 2016, pp.2383–2392. https://aclanthology.org/D16-1264/\n'''
    (root/'raw/SOURCE_ATTRIBUTION.md').write_text(attribution, encoding='utf-8')
    manifest = {'source_url': SQUAD_URL, 'raw_file': 'raw/squad_train-v1.1.json', 'bytes': raw_path.stat().st_size, 'sha256': source_hash, 'unchanged_original_source': True, 'previous_source_counts': {'prior_normalized_titles': len(old_titles), 'prior_normalized_questions': len(old_questions), 'prior_normalized_passages': len(old_texts)}, 'source_source': 'Official Stanford-hosted SQuAD v1.1 train snapshot', 'license_notice': 'CC BY-SA4.0; per-document Wikipedia attribution retained; see SOURCE_ATTRIBUTION.md'}
    write_json(root/'raw/source_manifest.json', manifest)
    article_case_counts = collections.Counter(r['article_id'] for r in test)
    validation = {'status': 'PASS_DATA_CONSTRUCTION_NO_MODEL_EVALUATION', 'source_articles': len(source['data']), 'eligible_unused_articles': len(articles), 'counts': dict(counts), 'calibration_article_groups_allocated': len(calibration_articles), 'calibration_article_groups_selected': len({r['article_id'] for r in cal}), 'test_article_groups_allocated': len(test_articles), 'test_numeric_article_groups_selected': len(article_case_counts), 'calibration_hosts': len(cal), 'test_hosts': len(test), 'unique_host_paragraphs': len(hosts), 'unique_host_original_questions': len({norm(r['original_question']) for r in hosts}), 'eligible_calibration_paragraphs': sum(len(a['paragraphs']) for a in calibration_articles), 'eligible_test_paragraphs': len(corpus), 'eligible_numeric_test_paragraphs': sum(len(v) for v in numeric_candidates.values()), 'test_cases_per_selected_article_min': min(article_case_counts.values()), 'test_cases_per_selected_article_max': max(article_case_counts.values()), 'source_groups_disjoint': True, 'prior_article_overlap': 0, 'prior_normalized_context_overlap': 0, 'prior_normalized_question_overlap': 0, 'models_called': 0, 'files': {str(p.relative_to(root)): {'bytes': p.stat().st_size, 'sha256': sha(p)} for p in [root/'data/hosts.jsonl', root/'data/corpus.jsonl', root/'data/host_protocol.json', raw_path]}, 'constructed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'scope': protocol['scope']}
    write_json(root/'audit/host_build_validation.json', validation)
    print(json.dumps(validation, indent=2))


if __name__ == '__main__':
    main()
