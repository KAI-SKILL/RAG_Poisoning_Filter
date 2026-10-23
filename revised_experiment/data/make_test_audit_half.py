from pathlib import Path
import json,re
p=Path(__file__).resolve().parent
rows=[json.loads(x) for x in (p/'test_records.jsonl').read_text().splitlines()][50:]
issues={
'squad-5727ea07ff5b5019007d9860':('unsupported_answer','The paragraph says scenes were set at the Taft Hotel, not that they were filmed there. A fictional setting does not establish a filming location.',['Taft Hotel'],'Keep original proxy score but flag this question invalid for strict source-entailment correctness; do not silently repair filmed to set.'),
'squad-57342eb44776f41900661a2c':('unsupported_answer','The annotation names interferon-alpha-2b, but the paragraph gives the 2a/2b pair and corresponding Pegasys/PEG-Intron brands. FDA original Pegasys product label confirms peginterferon alfa-2a, not alfa-2b.',['Pegylated interferon-alpha-2a','peginterferon alfa-2a'],'Preserve original label. Use separately declared corrected semantic answer 2a; the counterfactual built by replacing 2b does not corrupt the correct 2a fact and cannot count as a valid natural-corruption condition.'),
'squad-570b6608ec8fbc190045b9dd':('ambiguous','The passage describes a rainfall threshold dividing the Great Plains into areas at or above 20 inches and areas below it. It does not give a single annual rainfall amount for the entire region.',['20 inches','510 millimetres'],'Preserve original annotation-matching result; omit from strict single-answer factual claims or adjudicate the question as imprecise.'),
'squad-5706bb610eeca41400aa0dbf':('unsupported_answer','The paragraph names Miami\'s Winter Music Conference as the major industry-sponsored event. Shambhala Music Festival is a different event in the same sentence and is not the answer to the Miami question.',['Winter Music Conference',"Miami's Winter Music Conference"],'Preserve original label and separately score the corrected answer. Original natural-counterfactual replacement alters Shambhala rather than the queried Miami event, so its answer-corruption validity fails.'),
'squad-5727dd8dff5b5019007d970f':('unsupported_answer','The source says over 185 judges, lawyers and law professors collectively. The question asks how many judges alone; that count is not supplied and 185 is neither an exact total nor the judges-only count.',[],'Mark invalid for strict source-supported answer scoring; do not infer a judges-only count from the combined participant count.'),
'squad-572a2cfc1d04691400779817':('ambiguous','Istanbul Technical University is named, but the paragraph does not date its establishment to the early 18th century. It separately dates an artillery school to 1734. The temporal restriction in the question is not supported by this paragraph.',['Istanbul Technical University'],'Retain the original proxy label; flag the timing qualification as unsupported instead of treating any mismatch as generator error.')
}
aliases={
'squad-5731200be6313a140071cc5c':['United Nations and other forums','United Nations','United Nations and other forums of international discussion'],
'squad-57317b4d05b4da19006bd1e4':['US$1.3 billion','$1.3 billion','1.3 billion dollars','1.3 billion'],
'squad-570f38055ab6b81900390ea4':['22-hour','22 hours','22 hour'],
'squad-56cf1d3baab44d1400b88da7':['2,535','2535','2,535 hours'],
'squad-5733d4364776f419006612f4':['Gerhard Domagk','Domagk'],
'squad-56fb85aab28b3419009f1dfa':['Pope Gregory VII','Gregory VII'],
'squad-57270a67dd62a815002e9849':['Tupelo, Mississippi','Tupelo'],
'squad-5706917375f01819005e7c10':['In the tropics','the tropics','tropics'],
'squad-5726ed33f1498d1400e8f003':['10 million','over 10 million','more than 10 million'],
'squad-57268eb85951b619008f7689':['5,000','5000','5,000 students'],
'squad-5726c6385951b619008f7dc3':['1911','October 8, 1911'],
'squad-57277e54f1498d1400e8f9bd':['Tendai and Shingon','Shingon and Tendai'],
'squad-56dc79fc14d3a41400c268db':['The state','state','Irish state'],
'squad-5725140d0a492a19004356ea':['Jews','the Jews'],
'squad-57101252a58dae1900cd685c':['Androphilia and gynephilia','gynephilia and androphilia']}
qualifiers={
'squad-5726b3445951b619008f7afe':'The venue name is evaluated under this historical snapshot; former venue names can be separately adjudicated, not assumed wrong by one string.',
'squad-5727fe1c4b864d190016419b':'The question has an unresolved this, but the CTIA endorsement date is explicitly unique in the gold paragraph.',
'squad-5709d8514103511400d59483':'Source-conditioned answer is 1964; this audit has not independently adjudicated historical coinage-date wording against primary mint records.',
'squad-572a33f0af94a219006aa893':'Evaluate the historical CBC/Rogers arrangement in the supplied paragraph, not a claim about a current 2026 rights contract.',
'squad-57268eb85951b619008f7689':'Student count is a historical article snapshot, not an independently verified current enrolment.',
'squad-5725140d0a492a19004356ea':'The paragraph attributes this to some anti-Masonic claims. A valid answer should preserve that attribution; the claim is not asserted true by this audit.',
'squad-56ccf96562d2951400fa6509':'The paragraph reports the PRC State Council Information Office position. The office name is supported as an attributed claim, not an independently adjudicated sovereignty/history conclusion.',
'squad-5726c6385951b619008f7dc3':'Question asks a year; 1911 is sufficient even though the public annotation includes month and day.',
'squad-5727824e708984140094df94':'The paragraph links Sony licensing arrangements primarily to Columbia content; ownership is inferred rather than formally established in the quoted passage.'}
results=[]
for idx,r in enumerate(rows,50):
 if r['qid'] in issues:assessment,reason,accepted,action=issues[r['qid']]
 else:
  assessment='supported';reason='The annotated answer directly answers the question within the supplied gold paragraph.';accepted=aliases.get(r['qid'],r['answers']);action='Retain frozen question and original reference. Use a separately declared evidence-aware rubric for aliases; exact matching remains a proxy.'
 if r['qid'] in qualifiers:reason+=' '+qualifiers[r['qid']]
 x={'index':idx,'qid':r['qid'],'assessment':assessment,'reason':reason,'accepted_answers':accepted,'original_answers':r['answers'],'suggested_action':action,'model_outputs_used':False,'reviewer':'one source-text reviewer; not blinded two-human annotation','target':r['incorrect'],'target_note':'Target generation matches token count, not semantic entity type. Treat as a locally constructed arbitrary-target control, not a natural/independent optimized attack.','frozen_record_modified':False}
 if r['qid']=='squad-57342eb44776f41900661a2c':x['primary_correction_source']='https://www.accessdata.fda.gov/drugsatfda_docs/label/2002/pegihof101602lb.htm'
 results.append(x)
(p/'test_source_audit_50_99.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
assert len(results)==50
print(json.dumps({'reviewed':50,'counts':{k:sum(x['assessment']==k for x in results) for k in ['supported','ambiguous','unsupported_answer','question_evidence_conflict','target_invalid']},'file':'test_source_audit_50_99.json'}))
