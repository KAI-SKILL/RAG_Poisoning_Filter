#!/usr/bin/env python3
"""Publish the complete registered Q/E1/E2/E3 grid without model inference.

The existing pinned GGUF tokenizer receipts are validated against exact input
keys and measured token rows. Native HF renderers/tokenizers must still perform
their own full-grid length preflight before native BF16 generation.
"""
from pathlib import Path
import argparse, datetime, hashlib, json, os, sqlite3, tempfile

# Public-release checks preserve historical references without asserting byte identity.
import sys as _release_sys
_release_root = next(path for path in Path(__file__).resolve().parents
                     if (path / "tools/public_release_integrity.py").is_file())
_release_sys.path.insert(0, str(_release_root / "tools"))
from public_release_integrity import (
    reference_sha, reference_size, published_sha, matches_reference,
    matches_size_reference, provenance_summary,
)

_ARCHIVED_REFERENCE_CHECK = False

SCHEMA = 'Group9-all-experiments-v1'
MODELS = ('qwen25_3b_gguf', 'qwen3_8b', 'llama31_8b')
SCOPES = ('Q', 'E1', 'E2', 'E3')
EXPECTED = {'Q': (90, 90), 'E1': (1800, 432), 'E2': (700, 204), 'E3': (176400, 56373)}
GGUF_SHA = '626b4a6678b86442240e33df819e00132d3ba7dddfe1cdc4fbb18e0a9615c62d'
METRIC_SHA = 'b12f63e6076a14c6fd18904861ef00e67c69d4a467731ef9b4b4a1160a740b9e'


def stable(x): return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)
def require(ok, message):
 if not ok: raise ValueError(message)
def sha(path):
 return reference_sha(path) if _ARCHIVED_REFERENCE_CHECK else published_sha(path)
def read(path): return json.loads(Path(path).read_text())
def readonly(path): return sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro&immutable=1', uri=True)


def normalize_groups(value):
 if isinstance(value, dict): value = [{'condition': c, 'policy': p, 'rows': n} for c, ps in value.items() for p, n in ps.items()]
 require(isinstance(value, list) and value, 'Missing condition-policy counts')
 keys = set(); result = []
 for row in value:
  require(set(row) == {'condition', 'policy', 'rows'}, 'Condition-policy row fields differ')
  require(row['condition'] in ('clean', 'attack', 'matched_benign'), 'Unexpected condition')
  require(isinstance(row['policy'], str) and row['policy'], 'Invalid policy')
  require(type(row['rows']) is int and row['rows'] > 0, 'Invalid coverage row count')
  key = (row['condition'], row['policy']); require(key not in keys, 'Duplicate coverage row'); keys.add(key)
  result.append(dict(row))
 return sorted(result, key=lambda x: (x['condition'], x['policy']))


def artifact(root, path):
 path = path.resolve()
 require(path.is_file() and path.is_relative_to(root), 'Missing/outside-project artifact: ' + str(path))
 return str(path.relative_to(root)), sha(path)


def inspect_scope(root, scope):
 if scope == 'E3':
  folder = root / 'generation/input'; protocol_path = root / 'generation/scoring_protocol_frozen.json'
 else:
  folder = root / 'generation/all_experiments/inputs' / scope.lower(); protocol_path = folder / 'scoring_protocol.json'
 inputs = folder / 'generation_inputs.sqlite'; tokens = folder / 'token_counts.sqlite'; receipt_path = folder / 'token_counts.json'
 entry = {}
 for field, path in [('inputs', inputs), ('protocol', protocol_path), ('tokens', tokens), ('token_receipt', receipt_path)]:
  entry[field + '_file'], entry[field + '_sha256'] = artifact(root, path)
 protocol = read(protocol_path); receipt = read(receipt_path)
 require(protocol_path.with_suffix('.sha256').read_text().split()[0] == entry['protocol_sha256'], scope + ': protocol hash receipt differs')
 require(protocol['inputs_sqlite_sha256'] == entry['inputs_sha256'], scope + ': protocol/input hash differs')
 require(protocol['scorer_sha256'] == METRIC_SHA == sha(root / 'code/generation/score_generations.py'), 'Frozen metric source differs')
 if 'scope' in protocol: require(protocol['scope'].upper() == scope, 'Source protocol scope differs')
 db = readonly(inputs)
 try:
  require(db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok', scope + ': input integrity failed')
  require(not db.execute('PRAGMA foreign_key_check').fetchall(), scope + ': input foreign-key violation')
  count = db.execute('SELECT count(*) FROM requests').fetchone()[0]
  unique = db.execute('SELECT count(*) FROM prompts').fetchone()[0]
  require((count, unique) == EXPECTED[scope] == (protocol['requested_rows'], protocol['unique_prompts']), scope + ': count differs')
  groups = [{'condition': c, 'policy': p, 'rows': n} for c, p, n in db.execute('SELECT condition,policy,count(*) FROM requests GROUP BY condition,policy ORDER BY condition,policy')]
  require(groups == normalize_groups(groups), 'Coverage normalization differs')
  policies = [r[0] for r in db.execute('SELECT DISTINCT policy FROM requests ORDER BY policy')]
  require(set(policies) == set(protocol['policies']), 'Protocol/policy coverage differs')
  if 'condition_policy_counts' in protocol: require(groups == normalize_groups(protocol['condition_policy_counts']), 'Protocol condition-policy coverage differs')
  require(db.execute('SELECT count(*) FROM requests WHERE prompt_sha256 NOT IN(SELECT prompt_sha256 FROM prompts)').fetchone()[0] == 0, 'Broken request mapping')
  require(db.execute('SELECT count(*) FROM prompts WHERE prompt_sha256 NOT IN(SELECT prompt_sha256 FROM requests)').fetchone()[0] == 0, 'Orphan prompt')
  require(db.execute('SELECT count(*) FROM(SELECT request_id FROM requests GROUP BY request_id HAVING count(*)<>1)').fetchone()[0] == 0, 'Duplicate request IDs')
  measured = readonly(tokens)
  try:
   require(measured.execute('PRAGMA integrity_check').fetchone()[0] == 'ok', 'Token SQLite integrity failed')
   require(measured.execute('SELECT count(*) FROM tokens').fetchone()[0] == unique, 'Token row coverage differs')
   measured.execute('ATTACH DATABASE ? AS source', (inputs.resolve().as_uri() + '?mode=ro&immutable=1',))
   require(measured.execute('SELECT count(*) FROM tokens WHERE prompt_sha256 NOT IN(SELECT prompt_sha256 FROM source.prompts)').fetchone()[0] == 0, 'Unexpected token key')
   require(measured.execute('SELECT count(*) FROM source.prompts WHERE prompt_sha256 NOT IN(SELECT prompt_sha256 FROM tokens)').fetchone()[0] == 0, 'Missing token key')
   require(measured.execute('SELECT count(*) FROM tokens WHERE typeof(prompt_tokens)<>\'integer\' OR prompt_tokens<0 OR prompt_tokens+48>4096').fetchone()[0] == 0, 'Invalid/overflow token count')
   minimum, maximum = measured.execute('SELECT min(prompt_tokens),max(prompt_tokens) FROM tokens').fetchone()
   require((minimum, maximum) == (receipt['input_tokens_min'], receipt['input_tokens_max']), 'Measured token range differs')
  finally: measured.close()
  for key, chat in db.execute('SELECT prompt_sha256,chat_prompt FROM prompts'):
   require(hashlib.sha256(chat.encode('utf-8')).hexdigest() == key, 'Full prompt SHA differs')
 finally: db.close()
 require(receipt['status'] == 'PASS_ALL_FULL_PROMPTS_FIT', 'Token preflight did not pass')
 require(receipt['input_sqlite_sha256'] == entry['inputs_sha256'] and receipt['token_file_sha256'] == entry['tokens_sha256'], 'Token preflight byte bindings differ')
 require(receipt['model_sha256'] == GGUF_SHA and receipt['producer_sha256'] == sha(root / 'code/generation/preflight_tokens.py'), 'Pinned GGUF tokenizer/producer differs')
 require(receipt['unique_prompts'] == unique and receipt['context_tokens'] == 4096 and receipt['maximum_new_tokens'] == 48, 'Token preflight configuration differs')
 require(receipt['generation_calls'] == 0 and receipt['overflow_count'] == 0 and not receipt['overflow_prompts'] and receipt['truncation_permitted'] is False, 'Token receipt inference/overflow/truncation mismatch')
 require(receipt['add_bos'] is False and receipt['parse_special'] is True, 'Tokenizer special token handling differs')
 entry.update(requested_rows=count, source_unique_prompts=unique, policies=list(protocol['policies']), condition_policy_counts=groups,
  required_models=list(MODELS), scoring_version=protocol['scoring_version'], scorer_sha256=protocol['scorer_sha256'],
  gguf_token_preflight={'status': receipt['status'], 'model_sha256': receipt['model_sha256'], 'tokenizer_runtime': receipt['tokenizer_runtime'],
   'input_tokens_min': minimum, 'input_tokens_max': maximum, 'context_tokens': 4096, 'maximum_new_tokens': 48,
   'generation_calls': 0, 'truncation_permitted': False})
 return entry


def build(root, created):
 postanalysis = root / 'generation/all_experiments/postanalyse_scope.py'
 postanalysis_file, postanalysis_hash = artifact(root, postanalysis)
 scopes = {scope: inspect_scope(root, scope) for scope in SCOPES}
 registry = {'schema': SCHEMA, 'created_utc': created, 'status': 'READY_INPUTS_NOT_NEW_GENERATION_RESULTS',
  'required_models': list(MODELS), 'scopes': scopes, 'producer_file': 'generation/all_experiments/build_registry.py',
  'producer_sha256': sha(Path(__file__)), 'metric_source_file': 'code/generation/score_generations.py', 'metric_source_sha256': METRIC_SHA,
  'postanalysis_source_file': postanalysis_file, 'postanalysis_source_sha256': postanalysis_hash,
  'mapped_request_rows_per_model': sum(s['requested_rows'] for s in scopes.values()),
  'independent_scope_unique_prompt_budget_per_model': sum(s['source_unique_prompts'] for s in scopes.values()),
  'all_models_mapped_request_rows': len(MODELS) * sum(s['requested_rows'] for s in scopes.values()),
  'all_models_independent_scope_unique_prompt_budget': len(MODELS) * sum(s['source_unique_prompts'] for s in scopes.values()),
  'deduplication_scope': 'Each scope and model has an independent response store. Cross-scope shared source prompts are not reused as executed new responses.',
  'token_preflight_scope': 'Registered token files measure only the pinned Qwen2.5-3B GGUF exact ChatML prompts. Each native HF model rerenders and remeasures its full grid before generation; GGUF lengths are not an HF fit claim.',
  'input_and_protocol_mutation': False, 'model_generation_calls_by_registry_builder': 0}
 require(registry['mapped_request_rows_per_model'] == 178990, 'Complete mapped row total differs')
 require(registry['independent_scope_unique_prompt_budget_per_model'] == 57099, 'Independent scope prompt budget differs')
 require(sha(postanalysis) == postanalysis_hash, 'Postanalysis source changed during validation')
 # Recheck every file identity after all streaming validation reads.
 for entry in scopes.values():
  for name in ('inputs', 'protocol', 'tokens', 'token_receipt'):
   require(sha(root / entry[name + '_file']) == entry[name + '_sha256'], 'Registered file changed during validation')
 return registry


def publish(path, value):
 path.parent.mkdir(parents=True, exist_ok=True)
 data = (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode()
 fd, name = tempfile.mkstemp(prefix=path.name + '.', suffix='.partial', dir=path.parent); temporary = Path(name)
 try:
  with os.fdopen(fd, 'wb') as handle:
   require(handle.write(data) == len(data), 'Short registry write'); handle.flush(); os.fsync(handle.fileno())
  expected = hashlib.sha256(data).hexdigest(); require(sha(temporary) == expected, 'Staged registry SHA differs')
  require(stable(read(temporary)) == stable(value), 'Staged registry read-back differs')
  os.replace(temporary, path)
  require(sha(path) == expected and stable(read(path)) == stable(value), 'Published registry read-back differs')
 finally: temporary.unlink(missing_ok=True)


def main():
 global _ARCHIVED_REFERENCE_CHECK
 parser = argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
 parser.add_argument('--output', type=Path)
 parser.add_argument('--check', action='store_true', help='Read-only reconstruction of the published registry')
 parser.add_argument('--overwrite', action='store_true')
 args = parser.parse_args(); _ARCHIVED_REFERENCE_CHECK = args.check; root = args.root.resolve(); output = (args.output or root / 'generation/all_experiments/experiment_registry.json').resolve()
 if args.check:
  existing = read(output); expected = build(root, existing['created_utc'])
  require(stable(existing) == stable(expected), 'Published registry differs from validated source artifacts')
 else:
  require(args.overwrite or not output.exists(), 'Refuse registry overwrite; use --check or --overwrite')
  expected = build(root, datetime.datetime.now(datetime.timezone.utc).isoformat()); publish(output, expected)
 print(json.dumps({'status': 'PASS_REGISTRY_AND_ALL_TOKEN_RECEIPTS', 'registry_file': str(output), 'published_registry_sha256': published_sha(output), 'historical_registry_reference_sha256': reference_sha(output) if args.check else None, 'public_release_provenance': provenance_summary() if args.check else None,
  'scopes': {s: {k: entry[k] for k in ('requested_rows', 'source_unique_prompts', 'gguf_token_preflight')} for s, entry in expected['scopes'].items()},
  'mapped_request_rows_per_model': expected['mapped_request_rows_per_model'], 'independent_scope_unique_prompt_budget_per_model': expected['independent_scope_unique_prompt_budget_per_model'],
  'generation_calls': 0, 'source_inputs_and_protocols_modified': False}, indent=2))


if __name__ == '__main__': main()
