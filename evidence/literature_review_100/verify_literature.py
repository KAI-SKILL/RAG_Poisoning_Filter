"""Check the current 100-study review ledger without downloading papers."""
from pathlib import Path
import collections
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent

def main():
    source = json.loads((HERE/'Paper_100_Provenance.json').read_text())
    papers = source['reviewed_papers']
    assert source['selected_studies'] == len(papers) == 100
    assert len({p['id'] for p in papers}) == len({p['paper_id'] for p in papers}) == 100
    assert {p['paper_id'] for p in papers} == {f'P{i:03d}' for i in range(1,101)}
    dates = [p['first_public_date'] for p in papers]
    assert dates == sorted(dates,reverse=True)
    assert max(dates) <= source['cutoff_date'] == '2026-10-20'
    counts = collections.Counter(p['publication_evidence_category'] for p in papers)
    assert dict(counts) == source['publication_evidence_counts']
    official = 'publisher_or_official_venue_record_verified'
    workshop = 'official_nonarchival_workshop_only'
    assert set(counts) <= {official,workshop,'author_reported_venue_not_independently_verified','preprint_or_publication_not_verified'}
    tool_ref = re.compile(r'\bturn\d+(?:search|view|fetch|academia)\d+\b')
    assert not tool_ref.search(json.dumps(source,ensure_ascii=False))
    for p in papers:
        assert p['primary_source_online_rechecked'] and p['fulltext_core_sections_re_read']
        assert p['study_count'] == 1 and p['sections_read'] and p['concrete_design_implication'] and p['limitations']
        arxiv_id = p['id'].removeprefix('arXiv:')
        assert re.fullmatch(r'https://arxiv\.org/(?:abs|html)/'+re.escape(arxiv_id)+r'(?:v\d+)?',p['primary_url'])
        assert p['text_sources'] and p['read_version']
        for text in p['text_sources']:
            assert re.fullmatch('[0-9a-f]{64}',text['sha256']) and text['characters'] > 1000 and text['sections_read']
        if p['publication_evidence_category'] in {official,workshop}:
            assert p['publication_title'] and p['publication_venue'] and p['publication_version_note']
            assert p['publication_primary_url'].startswith('https://') and p['publication_sources']
    ragpart = next(p for p in papers if p['paper_id']=='P046')
    assert ragpart['publication_evidence_category'] == workshop
    assert ragpart['publication_status'] == 'verified_workshop_presentation_nonarchival'
    ledger = (HERE/'RAG_Security_100_Papers_Newest_First.md').read_text()
    assert len(re.findall(r'^## P\d{3}$',ledger,re.M)) == 100
    bib = (HERE/'RAG_Security_100_Papers.bib').read_text()
    assert len(re.findall(r'^@misc\{p\d{3},$',bib,re.M)) == 100
    assert not tool_ref.search(ledger+bib)
    receipt = json.loads((HERE/'Corpus_Validation.json').read_text())
    assert receipt['publication_evidence_counts'] == source['publication_evidence_counts']
    assert receipt['publication_verification_overlays_sha256'] == source['publication_verification_overlays_sha256']
    assert set(receipt['official_formal_or_accepted_studies']) == {p['paper_id'] for p in papers if p['publication_evidence_category']==official}
    assert set(receipt['official_nonarchival_workshop_studies']) == {'P046'}
    for field,name in [('metadata_sha256','Paper_100_Provenance.json'),('ledger_sha256','RAG_Security_100_Papers_Newest_First.md'),('bibtex_sha256','RAG_Security_100_Papers.bib')]:
        assert receipt[field] == hashlib.sha256((HERE/name).read_bytes()).hexdigest(),name
    assert receipt['status'] == 'passed'
    print(json.dumps({'status':'passed','unique_studies':100,'publication_evidence_counts':dict(counts),
                      'scope':'Offline ledger, version and evidence integrity; online source checks and fulltext reading are recorded review work, not repeated here.'},indent=2))

if __name__ == '__main__':
    main()
