#!/usr/bin/env python3
"""Verify supplied historical summaries and recovered answers, without model inference.

The two incoming full result tables are semantic duplicates of retained canonical
CSVs. Their normalised digests are recorded in provenance.json, so verification
can remain reproducible without storing duplicate CSVs. --source-zip additionally
checks the exact original submitted files and their rounded display p-values.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

# Public-release checks preserve historical references without asserting byte identity.
import sys as _release_sys
_release_root = next(path for path in Path(__file__).resolve().parents
                     if (path / "tools/public_release_integrity.py").is_file())
_release_sys.path.insert(0, str(_release_root / "tools"))
from public_release_integrity import (
    reference_sha, reference_size, published_sha, matches_reference,
    matches_size_reference, provenance_summary,
)
CONDITIONS = ['none', 'poison', 'naive', 'escape', 'ignore', 'fake_comp', 'combine', 'stealth']
POLICIES = ['none', 'trust_rule', 'trust_guard', 'trust_ctx', 'trust_fused', 'oracle']
PRIMARY = ['poison', 'ignore', 'stealth']

def sha(path):
    return reference_sha(path)  # Archived-reference identity, not current-byte identity.

def semantic_sha(rows):
    return hashlib.sha256(json.dumps(sorted(rows), ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()

def exact_mc(a, b):
    n = a+b
    return min(1.0, 2*sum(math.comb(n,k) for k in range(min(a,b)+1))/2**n) if n else 1.0

def holm(values):
    adjusted = [0.0]*len(values)
    running = 0.0
    for rank, i in enumerate(sorted(range(len(values)), key=lambda i:values[i])):
        running = max(running, min(1.0, (len(values)-rank)*values[i]))
        adjusted[i] = running
    return adjusted

def csv_rows(path):
    with Path(path).open(encoding='utf-8',newline='') as f:
        return list(csv.DictReader(f))

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source-zip', type=Path, help='Optional original 3B_rescoring.zip; not required for canonical-summary checks')
    args = ap.parse_args()
    provenance = json.loads((HERE/'provenance.json').read_text())
    for basename in ('step7_stats.py','step8_rescore_bounded.py'):
        source_member = next(n for n in provenance['source_file_sha256'] if n.endswith('/'+basename))
        assert sha(HERE/'source_scripts'/basename)==provenance['source_file_sha256'][source_member], 'Historical source script changed'
    metrics_path = ROOT/'evidence/reference_audit/provided_corrected_metrics.csv'
    pairs_path = ROOT/'evidence/reference_audit/provided_paired_statistics.csv'
    metrics = csv_rows(metrics_path)
    lookup = {(r['defense'],r['setting']):r for r in metrics}
    expected_keys = {(d,s) for d in POLICIES for s in CONDITIONS}
    assert len(metrics)==48 and set(lookup)==expected_keys, 'Expected exactly 48 unique canonical metric rows'
    rt = []
    for (d,s),r in sorted(lookup.items()):
        n,ref,target = int(r['n']),int(r['bounded_correct_hits']),int(r['bounded_target_hits'])
        assert n==100 and 0<=ref<=n and 0<=target<=n, 'Invalid historical denominator or marginal count'
        rt.append([d,s,n,ref,target])
    assert semantic_sha(rt)==provenance['incoming_rt_semantic_sha256'], 'Canonical cells differ from supplied 3B table'
    all_pairs = csv_rows(pairs_path)
    pairs = [r for r in all_pairs if r['match_rule']=='bounded']
    pair_lookup = {(r['defense_a'],r['defense_b'],r['setting']):r for r in pairs}
    assert len(pairs)==40 and len(pair_lookup)==40, 'Expected exactly 40 unique bounded pair rows'
    assert set(pair_lookup)=={('trust_fused',b,s) for b in POLICIES if b!='trust_fused' for s in CONDITIONS}
    mc_semantic = []
    computed = {}
    for (a,b,s),r in sorted(pair_lookup.items()):
        n,ao,bo = int(r['n_pairs']),int(r['a_only']),int(r['b_only'])
        key = 'bounded_correct_hits' if s=='none' else 'bounded_target_hits'
        ma,mb = int(lookup[a,s][key]),int(lookup[b,s][key])
        assert n==100 and 0<=ao<=ma and 0<=bo<=mb and ao+bo<=n
        assert ao-bo==ma-mb, 'Discordance margins disagree with canonical R/T table'
        assert 0<=ma-ao<=min(ma,mb) and ma-ao==mb-bo
        assert ma-ao+ao+bo<=n, 'Infeasible joint contingency table'
        p = exact_mc(ao,bo)
        assert math.isclose(p,float(r['two_sided_exact_p']),rel_tol=1e-12,abs_tol=1e-30), 'Exact McNemar arithmetic mismatch'
        mc_semantic.append([a,b,s,n,ao,bo])
        computed[a,b,s] = p
    assert semantic_sha(mc_semantic)==provenance['incoming_mcnemar_semantic_sha256'], 'Canonical discordances differ from supplied 3B table'
    ps = [computed['trust_fused','trust_ctx',s] for s in PRIMARY]
    adjusted = holm(ps)
    primary_rows = []
    for s,p,adj in zip(PRIMARY,ps,adjusted):
        r=pair_lookup['trust_fused','trust_ctx',s]
        primary_rows.append({'setting':s,'metric':'bounded_target_mention','defense_a':'trust_fused','defense_b':'trust_ctx','n_pairs':100,'a_only':int(r['a_only']),'b_only':int(r['b_only']),'p_exact':p,'p_holm':adj,'family':'historical_only_fused_vs_context_poison_ignore_stealth'})
    assert adjusted==[0.375,1.0,0.375]
    # The full legacy table has a broader Holm family; its adjusted values are
    # deliberately not substituted for the three-hypothesis historical family.
    expected_primary = csv_rows(HERE/'primary_family.csv')
    assert len(expected_primary)==3
    for actual,expected in zip(primary_rows,expected_primary):
        for k,v in actual.items():
            assert str(v)==expected[k], 'Retained historical primary-family CSV is stale'
    source_checked = False
    if args.source_zip:
        assert sha(args.source_zip)==provenance['source_zip_sha256'], 'Source ZIP hash differs from audited attachment'
        with zipfile.ZipFile(args.source_zip) as z:
            for name,digest in provenance['source_file_sha256'].items():
                assert hashlib.sha256(z.read(name)).hexdigest()==digest, 'Source member hash mismatch: '+name
            table = list(csv.DictReader(io.StringIO(z.read(provenance['incoming_rt_member']).decode('utf-8-sig'))))
            incoming_rt = []
            for row in table:
                d=row['policy'].split('(')[1].split(')')[0].removesuffix('_hf')
                for s in CONDITIONS:
                    ref,target=map(int,row[s].split('/'))
                    incoming_rt.append([d,s,100,ref,target])
            assert len(incoming_rt)==48 and semantic_sha(incoming_rt)==semantic_sha(rt)
            supplied_pairs = list(csv.DictReader(io.StringIO(z.read(provenance['incoming_mcnemar_member']).decode('utf-8-sig'))))
            incoming_mc = []
            for row in supplied_pairs:
                a,b,s=row['defense_a'],row['defense_b'],row['setting']
                ao,bo=int(row['a_only']),int(row['b_only'])
                incoming_mc.append([a,b,s,100,ao,bo])
                # Source table uses up to 3 significant figures; 0.5% tolerance
                # checks its display precision, not a new statistical threshold.
                assert math.isclose(float(row['p_exact']),computed[a,b,s],rel_tol=.005,abs_tol=1e-30)
                if row['p_holm_primary']:
                    assert b=='trust_ctx' and s in PRIMARY
                    assert float(row['p_holm_primary'])==adjusted[PRIMARY.index(s)]
            assert len(incoming_mc)==40 and semantic_sha(incoming_mc)==semantic_sha(mc_semantic)
        source_checked = True
    from verify_raw import verify_raw
    raw_validation = verify_raw()
    validation = {
        'status':'passed','scope':'Historical summaries, recovered response-level re-scoring and paired arithmetic; model identity remains unattested',
        'raw_4800_answers_present':True,'model_inference_executed':False,
        'raw_answer_rows_reverified':raw_validation['original_rows'],
        'raw_bounded_flags_reconstructed':raw_validation['bounded_flags_reconstructed'],
        'raw_changed_rows_reconstructed':raw_validation['changed_rows_reconstructed'],
        'raw_all_scoring_branch_paired_rows_recomputed':raw_validation['paired_rows_recomputed'],
        'raw_unique_complete_prompt_strings':raw_validation['unique_complete_prompt_strings'],
        'raw_prompt_conflict_groups_preserved':raw_validation['identical_prompt_response_conflict_groups'],
        'model_identity_verified':False,
        'raw_validation_sha256':sha(HERE/'raw_validation.json'),
        'historical_dataset':'100 previously inspected NQ questions; 6 policies x 8 settings = 4800 declared rows',
        'current_new_study_rows_untouched':2175,
        'rt_cells_checked':48,'rt_cells_match_incoming_semantic_digest':48,
        'mcnemar_rows_checked':40,'discordance_rows_match_incoming_semantic_digest':40,
        'mcnemar_exact_arithmetic_checked':40,'primary_holm_hypotheses':3,
        'primary_holm_by_setting':dict(zip(PRIMARY,adjusted)),
        'original_source_zip_checked_this_run':source_checked,
        'canonical_inputs_sha256':{str(metrics_path.relative_to(ROOT)):sha(metrics_path),str(pairs_path.relative_to(ROOT)):sha(pairs_path)},
        'verifier_sha256':sha(__file__),'provenance_sha256':sha(HERE/'provenance.json')
    }
    validation['historical_verifier_reference_sha256']=validation.pop('verifier_sha256')
    validation['published_verifier_sha256']=published_sha(Path(__file__))
    validation['historical_provenance_reference_sha256']=validation.pop('provenance_sha256')
    validation['published_provenance_sha256']=published_sha(HERE/'provenance.json')
    validation['public_release_provenance']=provenance_summary()
    (HERE/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
    print(json.dumps(validation,indent=2))

if __name__=='__main__':
    main()
