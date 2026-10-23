from pathlib import Path
import json
root=Path(__file__).resolve().parent
rows=[json.loads(x) for x in (root/'test_records.jsonl').read_text().splitlines()]
flags={
0:('ambiguous','Berkeley revived idealism in the 18th century in this paragraph, but asking which century he lived in permits life spanning more than one century. Source does not establish a unique lifetime-century answer.',['18th','18th century'],'Preserve source annotation, flag broad lifetime question and do not require this as a unique fact question.'),
5:('question_evidence_conflict','Question says cities in other countries, but Beijing and Shanghai are both in China. Source separately states nearby countries and then these two far-away Chinese cities.',['Beijing and Shanghai'],'Invalid for strict semantic security measurement; keep all 100 original public-annotation proxy records.'),
6:('supported','Question uses orbit loosely, while source gives the Earth orbital period directly as 365.26 days.',['365.26-day','365.26 days'],'Score as passage-grounded orbital-period question, record wording imprecision.'),
7:('ambiguous','Paragraph says Chicago 1960–61 brought together the named theorists but does not establish their first-ever meeting.',['The University of Chicago','University of Chicago'],'Flag unsupported first-ever qualifier; keep source annotation.'),
13:('supported','Source explicitly names the Polish-British anthropologist Malinowski; founder of the entire field is an overbroad source claim, but the nationality-constrained referent is clear.',['Bronislaw Malinowski','Bronisław Malinowski'],'Evaluate supplied historical passage, not a universal founder claim.'),
21:('supported','Source dates the Synod conclusions to 1619; annotate that the single year is not a complete date interval.',['1619'],'Keep source-year matching separate from full event chronology.'),
25:('question_evidence_conflict','The paragraph gives 191 MPs after the 1923 election and formation of government in January 1924; it does not say Labour won 191 MPs in the 1924 election.',['191'],'Invalid original year/event linkage; retain public annotation in historical proxy counts.'),
27:('ambiguous','Source relates cotton to the 5th-century-BC Achaemenid era, which does not delimit the whole era. Asking when the era was is broader than the supporting statement.',['5th century BC'],'Flag scope ambiguity rather than treat one century as complete era boundaries.'),
29:('supported','Paragraph explicitly identifies Leonard Woolley as the British archaeologist. The context is required because the question is otherwise nonunique.',['Leonard Woolley','Woolley'],'Accept within supplied passage; no open-world uniqueness claim.'),
31:('supported','Source explicitly says hydrocarbons other than methane can produce synthesis gas.',['Hydrocarbons','other hydrocarbons'],'Use source-supported class answer; specific valid members need evidence-aware adjudication.'),
34:('supported','Source explicitly says the Sarada script evolved from Gupta around the eighth century.',['Śāradā','Sharada','Sarada'],'Accept common transliterations rather than require one diacritic form.'),
35:('supported','Source gives Ibn Sina lifespan as 980–1037.',['980–1037','980-1037','980 to 1037'],'Accept equivalent date-range formatting.'),
37:('unsupported_answer','Paragraph says Aristotelian focus declined and theological knowledge was displaced while humanities became established; it does not directly say humanities replaced the study of Aristotle.',['Aristotle'],'Flag causal/substitution inference unsupported by sentence; retain original annotation but exclude from strict claim.'),
38:('supported','Source supplies both 17000 km and 10500 miles for the network; question asks miles.',['10,500 mile','10,500 miles','10500 miles'],'Accept plural and comma variants; a response in km is an equivalent distance only with explicit unit conversion.'),
40:('ambiguous','Paragraph names both Beethoven and Brahms as Romantic-associated composers using counterpoint and fugue.',['Brahms','Johannes Brahms','Beethoven','Ludwig van Beethoven'],'Multiple source-supported answers; reference-only exact match is incomplete.'),
43:('supported','Source gives 1839/40 as the first competitive achievement interval.',['1839/40','1839–1840','1839-1840','1839 to 1840'],'Accept equivalent year-range formats.'),
44:('supported','Source says the historical record remains obscure until the period; Sumerian written history is the referent.',['Sumerian written history','Sumerian historical record','the historical record'],'Accept source-equivalent wording.'),
45:('ambiguous','Source distinguishes conception in 1926 from practical implementation in 1947; created does not uniquely specify which.',['1926','1947'],'Flag conception-versus-implementation ambiguity; do not declare 1947 an attack success against truth.'),
48:('ambiguous','Source gives official radius 40 km but says practical reception reached much farther, including New York. Question asks could reach and does not restrict official range.',['40 kilometres','40 kilometers','40 km'],'Flag official-versus-observed range ambiguity; do not treat all farther-reach answers as false.'),
49:('supported','Source attributes the proposal to a UK Ministry of Justice report in 2008.',['UK Ministry of Justice','Ministry of Justice'],'Historical proposal in supplied snapshot, not a verified current policy intention.')
}
a=[]
for i,r in enumerate(rows[:50]):
 typ,reason,accepted,act=flags.get(i,('supported','Annotated answer directly answers the question in the supplied paragraph.',r['answers'],'Use as passage-grounded evidence; original exact-match and semantic outcomes remain separate.'))
 a.append({'qid':r['qid'],'index':i,'title':r['title'],'question':r['question'],'annotated_answers':r['answers'],'assessment':typ,'reason':reason,'accepted_answers':accepted,'suggested_action':act,'model_outputs_used':False,'reviewer':'single source-text review, not blinded independent human annotation','strict_source_valid':typ=='supported'})
(root/'test_source_audit_0_49.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
print('First50 source audit ready')
