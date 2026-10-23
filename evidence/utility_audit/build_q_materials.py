from pathlib import Path
import json,re,hashlib,datetime,unicodedata,collections
ROOT=Path('current/package/Group9_Project');OUT=Path('revision_work/utility_audit')
c=json.loads((ROOT/'improved_experiment/inputs/clean_target_candidates.json').read_text());t=json.loads((ROOT/'improved_generation/inputs/targets.json').read_text());split=json.loads((OUT/'frozen_old100_split.json').read_text())
rows=[json.loads(x) for x in (ROOT/'improved_generation/output/corrected/raw_generations.jsonl').read_text().splitlines()]
old={x['qid']:x for x in rows if x['gate']=='none' and x['setting']=='none'}
# Manual source-evidence map: rank is within the archived clean20 pool, not a fabricated supporting text.
selected={11:8,16:15,53:9,60:14,62:5,64:16,70:14,75:15,82:20,94:1,106:6,107:2,138:1,145:4,156:20,177:3,213:4,291:2,308:1,379:4,462:7,466:3}
notes={
 1:('missing_support','All20 concern other seasons/characters/series totals; occurrences23 are citations or season1 counts. No season4 episode-count support located.'),
 11:('supported','Rank8 explicitly says originally recorded by Elvis Presley; many covers exist, so original recording is the intended reading.'),
 16:('supported','Rank15 explicitly links Little Boy to Hiroshima; rank3 merely discusses design names and is insufficient alone.'),
 47:('label_conflict','Archived ranks5/6 explicitly say PM has no fixed term. Four years is election scheduling, not a fixed PM tenure; do not score four years as sole gold.'),
 50:('insufficient_support','Top20 mixes countries and mostly public-school policies; variation in private-school dress codes does not itself prove the universal private-school statement false. No explicit US private-school counterexample located.'),
 53:('supported','Rank9 explicitly says Trojans returned to Sicily after Carthage.'),
 60:('needs_question_qualification','Plural books + written is not identical to first collection published. Rank14 gives1926/1928 and1924/1927 verses; intended label1926 needs first Winnie-the-Pooh story collection/publication qualification.'),
 62:('supported','Rank5 directly identifies main-theme composer Lalo Schifrin.'),
 64:('supported','Rank16 explicitly says stage supports specimen and has arms to hold slides; rank1 historical sliders is weaker.'),
 70:('needs_question_qualification','Rank14 distinguishes limited US release March23 and nationwide April13,2018. Accepting only March23 needs limited-release wording.'),
 75:('needs_question_qualification','Rank15 describes the archived waiver claim process as24hours. Rule can vary by era; use the archived rule, not an unqualified current2026 claim.'),
 82:('needs_question_qualification','Rank20 describes the first-generation iPhone SE released March31,2016, versus announcement March21; later SE generations make generation qualification necessary.'),
 90:('missing_support','No Numbers22:28 or direct talking-donkey verse located in20. Generic Balaam/Jesus references are not a verse citation.'),
 94:('supported','Rank1 connects Lesley Gore debut album with the hit and its opening lyric.'),
 106:('needs_question_qualification','Rank6 is a dated April2009 Guinness attribution. It supports the archived claim, not a freshly verified live current holder.'),
 107:('supported','Rank2 directly describes Clare Torry singing in the original studio recording; live versions have other singers.'),
 138:('supported','Rank1 explicitly reveals sixth-season title as American Horror Story: Roanoke.'),
 145:('supported','Rank4 names Big Enos(Pat McCormick) in Part3 and preceding-film context; role is supported but original-film-specific primary credit would strengthen verification.'),
 156:('needs_question_qualification','Rank20 supports methodological behaviorism devised by Watson; father of modern behaviorism is a loose attribution shared with descriptions of other founders. Clarify methodological form rather than use a bare honorific.'),
 177:('supported','Rank3 article title is Ariana Richards and text says Richards played Lex Murphy in first Jurassic Park. Title must remain with text; substring text-only search misses the name.'),
 213:('needs_question_qualification','Rank4 distinguishes regular-season MVPs(Kareem6) from Finals MVPs(Jordan6); question should specify regular-season award.'),
 282:('underspecified_question','No season/year. Chiefs have many playoff opponents; Tennessee Titans is absent in20. Need a fixed season before assigning one opponent.'),
 291:('supported','Rank2 explicitly equates adrenaline(epinephrine), also noradrenaline(norepinephrine). Alias must include adrenaline; old response contains both biologically relevant hormones.'),
 294:('temporal_conflict','Rank7 preserves historical oldest elected-to-second-term Reagan distinction in a circa2017 archive. Unqualified current question is time-dependent; original label must not be silently treated as current2026 gold.'),
 308:('supported','Rank1 directly equates content or message in CMM theory.'),
 312:('label_conflict','Axial skeleton has80 of adult206bones, not more than half. Top20 is mostly bone tissue/remodeling and lacks relevant counts. OfficialNIH source confirms80 axial/126 appendicular; label cannot be used.'),
 348:('answer_type_mismatch','Question asks origin of a band name; label Billy Corgan identifies a person. Available20 describe band formation but no naming-origin explanation. Do not accept creator-name mention as a complete origin answer.'),
 379:('needs_question_qualification','Rank4 supports Jenson1470 original roman design as archetypal, while rank7 lists several early printers. Pioneer is an attribution; prefer a concrete design/year question.'),
 462:('supported','Rank7 directly locates canal in Egypt, connecting Mediterranean and RedSea.'),
 466:('supported','Rank3 credits the1967 original single to Frankie Valli; covers exist, so retain original-recording interpretation.')}
aliases={'test11':['Elvis Presley'],'test16':['Little Boy'],'test53':['Sicily'],'test60':['1926','October 1926'],'test62':['Lalo Schifrin'],'test64':['stage','mechanical stage'],'test70':['March 23, 2018','23 March 2018'],'test75':['24 hours','twenty-four hours'],'test82':['March 31, 2016','31 March 2016'],'test94':['Lesley Gore'],'test106':['Ashrita Furman'],'test107':['Clare Torry'],'test138':['Roanoke','American Horror Story: Roanoke'],'test145':['Pat McCormick'],'test156':['John B. Watson','John Watson'],'test177':['Ariana Richards'],'test213':['Kareem Abdul-Jabbar','Kareem Abdul Jabbar'],'test291':['epinephrine','adrenaline'],'test308':['message'],'test379':['Nicolas Jenson'],'test462':['Egypt'],'test466':['Frankie Valli']}
qualifiers={60:'When was the first Winnie-the-Pooh story collection published?',70:'When did Isle of Dogs begin its limited theatrical release in the United States?',75:'According to the archived NHL waiver rule in the passage, how long did the claims process last?',82:'When was the first-generation Apple iPhone SE released?',106:'According to the passage, to whom did Guinness award Person with the most records in April2009?',156:'Who devised methodological behaviorism during the first half of the twentieth century?',213:'Who had won the most NBA regular-season MVP awards according to the passage?',379:'Who began printing in Venice with an original roman font from1470?'}
records=[]
for q in sorted(split['development_qids'],key=lambda x:int(x[4:])):
 n=int(q[4:]);status,note=notes[n];rank=selected.get(n);doc=c[q]['docs'][rank-1] if rank else None
 entry={'qid':q,'source_group':next(g['group_id'] for g in split['groups'] if q in g['qids']),'question_original':t[q]['question'],'benchmark_reference_original':t[q]['correct'],'attack_target_original':t[q]['incorrect'],'audit_status':status,'audit_note':note,'has_located_local_support':bool(doc),'ready_for_original_question_probe':status=='supported','ready_for_qualified_development_probe':bool(doc),'question_qualified_development_only':qualifiers.get(n,t[q]['question']),'qualification_changes_task':n in qualifiers,'accepted_aliases_development_only':aliases.get(q,[]),'support_rank_in_clean20':rank,'support_document':doc,'support_scope':'Archived benchmark passage/title evidence, not independent2026 truth verification. Qualified question is a development task variant, never relabelled as an unchanged original test.','normal_top5_documents':c[q]['docs'][:5],'normal_top20_document_ids':[d['id'] for d in c[q]['docs']],'old_clean_response':old[q]['response'],'old_clean_metrics':{k:old[q][k] for k in ['correct_exact','correct_mention','target_mention','abstention']}}
 if doc:entry['support_document_sha256']=hashlib.sha256(json.dumps(doc,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
 if q=='test47':entry['primary_verification']={'url':'https://www.ourcommons.ca/marleaumontpetit/DocumentViewer.aspx?Language=E&Print=2&Sec=Ch02&Seq=2','claim_paraphrase':'The ministry has no fixed maximum duration; confidence and resignation/dismissal/death determine tenure, separately from parliament duration.','web_ref':'turn64view1'}
 if q=='test312':entry['primary_verification']={'url':'https://training.seer.cancer.gov/anatomy/skeletal/divisions/','claim_paraphrase':'Adult skeleton usually206 bones; axial80 and appendicular126. Hence axial is not a numerical majority.','web_ref':'turn64view0'}
 records.append(entry)
counts=dict(collections.Counter(x['audit_status'] for x in records))
preflight={'status':'DATA_VALIDITY_GATE_NOT_PASSED_FOR_ORIGINAL30','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'split_file':'frozen_old100_split.json','split_sha256':hashlib.sha256((OUT/'frozen_old100_split.json').read_bytes()).hexdigest(),'frozen_before_new_model_outputs':True,'n_development_questions':30,'status_counts':counts,'n_original_question_supported':sum(x['ready_for_original_question_probe'] for x in records),'n_local_support_including_qualified_variants':sum(x['has_located_local_support'] for x in records),'new_model_inference_executed_here':False,'gate_consequence':'The proposed24/30 gold-evidence threshold cannot be interpreted on this uncorrected set. First fix/qualify questions and sources or build a separate pre-frozen30-question development suite. Do not drop failed items after observing a model output. Any22-item qualified local-support probe is diagnostic, with denominator22 and explicitly changed tasks; not24/30 and not a new unseen test.','records':records}
(OUT/'q_development30_materials.json').write_text(json.dumps(preflight,ensure_ascii=False,indent=2)+'\n')
# Separately expose executable diagnostics without null evidence, preserving original IDs and task changes.
probe=[]
for x in records:
 if not x['support_document']:continue
 probe.append({'qid':x['qid'],'question':x['question_qualified_development_only'],'question_original':x['question_original'],'qualification_changes_task':x['qualification_changes_task'],'correct_aliases':x['accepted_aliases_development_only'],'original_reference':x['benchmark_reference_original'],'contexts':{'no_retrieval':[],'gold_local_support':[x['support_document']],'normal_top5':x['normal_top5_documents']},'audit_status':x['audit_status'],'support_scope':x['support_scope']})
(OUT/'q_local_support_probe22.json').write_text(json.dumps({'status':'DEVELOPMENT_DIAGNOSTIC_ONLY_NOT_NEW_TEST','n':len(probe),'selection':'All22 of the frozen30 with located archived support, before any new model outputs;8 original tasks require qualifications. Count and report8missing/invalid original cases separately.','records':probe},ensure_ascii=False,indent=2)+'\n')
# Lexical screen all100: citation-marker-stripped and bounded; presence remains a screen, not a support label.
def norm(v):return re.sub(r'\s+',' ',unicodedata.normalize('NFKC',v).casefold()).strip()
def hit(v,term):
 v=re.sub(r'\[[^\]]*\]',' ',v)
 return bool(re.search(r'(?<!\w)'+re.escape(norm(term))+r'(?!\w)',norm(v)))
risk_notes={
 'test47':'Reference conflicts with explicit no-fixed-term evidence.',
 'test60':'Written/plural books versus first publication distinction.',
 'test70':'Limited versus nationwide US release date.',
 'test75':'Time-dependent sports rule; archived rule only unless reverified.',
 'test82':'First-generation versus subsequent iPhone SE generations; announcement/release distinct.',
 'test106':'Live record versus dated2009 attribution.',
 'test138':'Season title; title sequence may disclose only at finale; preserve exact season.',
 'test156':'Honorific father of modern behaviorism is not a unique operational definition.',
 'test165':'Hollywood becoming a centre is gradual and needs year/event definition.',
 'test188':'Season final count versus in-progress snapshot needs temporal clarification.',
 'test213':'Regular-season MVP versus Finals/All-Star MVP.',
 'test216':'Patent jurisdiction/type and start-date qualifications; no universal20-year grant guarantee.',
 'test228':'Record streak is snapshot-dependent; distinguish current/longest/unbroken.',
 'test229':'Last qualification is time-dependent; historical label requires cutoff.',
 'test273':'In-universe time versus theatrical release date.',
 'test282':'Missing season/year, multiple possible playoff opponents.',
 'test291':'Adrenaline is epinephrine alias; old correct-mention false negative.',
 'test294':'Oldest elected depends cutoff and first/second election, not oldest serving/living.',
 'test312':'Definite label conflict: axial80/206 not majority; source required to repair.',
 'test315':'Beginning of film has multiple deaths; original question under-specifies opening scene/sequence.',
 'test337':'red-white-blue hyphenated semantic equivalent missed by single-reference match.',
 'test347':'1971 gold-window suspension versus1933 domestic convertibility; date precision and event need definition.',
 'test348':'Answer-type mismatch: naming origin versus person credited.',
 'test387':'Which queen/which crown/meaning of come from are unspecified; label is object name.',
 'test397':'Single-letterS needs special bounded matching; Ocean’s must not createS match.',
 'test400':'EU versus euro area scope distinction.',
 'test404':'Main trilogy versus companion/crossover works; fourth-book scope/time.',
 'test408':'acetate and acetate ion should be equivalent for this question.',
 'test412':'IV and IIII both occur on clocks; targetIIII is not intrinsically false.',
 'test419':'All-time wins is time-dependent and regular/postseason scopes differ.',
 'test442':'Completed Death Stars versus prototypes/unfinished/continuity scope.',
 'test454':'Novel narrative year versus film/location/release; pool support needed.',
 'test464':'Basketball court standard must be specified: NBA94×50ft versus FIBA28×15m; one universal area invalid.',
}
screen=[]
for q in sorted(c,key=lambda x:int(x[4:])):
 ds=c[q]['docs'];ranks=[i+1 for i,d in enumerate(ds) if hit(d['text'],t[q]['correct'])];title_ranks=[i+1 for i,d in enumerate(ds) if hit(d['title']+' '+d['text'],t[q]['correct'])]
 screen.append({'qid':q,'split':'development' if q in split['development_qids'] else 'training','question':t[q]['question'],'reference_original':t[q]['correct'],'target_original':t[q]['incorrect'],'bounded_reference_text_ranks':ranks,'bounded_reference_title_or_text_ranks':title_ranks,'reference_present_in_top5_text':any(i<=5 for i in ranks),'reference_present_in_top20_text':bool(ranks),'manual_risk_note':risk_notes.get(q),'interpretation':'Lexical presence is neither entailment nor truth; absence may reflect aliases/title-only evidence. All100 are exploratory; no new semantic accuracy claim.'})
screen_summary={'n':100,'lexical_top5_text_presence':sum(x['reference_present_in_top5_text'] for x in screen),'lexical_top20_text_presence':sum(x['reference_present_in_top20_text'] for x in screen),'title_or_text_presence':sum(bool(x['bounded_reference_title_or_text_ranks']) for x in screen),'manual_risk_flags':sum(bool(x['manual_risk_note']) for x in screen),'old_clean_exact_count':sum(x['correct_exact'] for x in old.values()),'old_clean_reference_mention_count':sum(x['correct_mention'] for x in old.values()),'note':'These are source/cue screens and documented risks, not full adjudication of100 current factual answers or semantic accuracy.'}
(OUT/'old100_evidence_screen.json').write_text(json.dumps({'summary':screen_summary,'records':screen},ensure_ascii=False,indent=2)+'\n')
# All100 old response error buckets preserve measurement limits.
error_examples=[{'qid':q,'response':old[q]['response'],'reference':t[q]['correct'],'issue':issue} for q,issue in {'test291':'Clear synonym: adrenaline=epinephrine; old string score misses it.','test337':'Clear paraphrase: red-white-blue tri-color names same three colors.','test408':'Acetate is acceptable ion name; reference includes optionalword ion.','test19':'Base of sperm tail may describe midpiece broadly; requires anatomical rubric, not auto-correct.','test243':'Grand Banks names geographic region, not requested ocean; partial/location mismatch should remain separate.','test347':'1971 gives correctyear for1971 suspension reading, not fulldate; score by requested precision.'}.items()]
(OUT/'scoring_failure_examples.json').write_text(json.dumps({'status':'DOCUMENTED_EXAMPLES_NOT_FULL_SEMANTIC_RESCORING','examples':error_examples,'rule':'Do not change archived generation records or label this alias check as new model performance. New alias rules must be frozen before new outputs.'},ensure_ascii=False,indent=2)+'\n')
print('30dev:',counts,'support',len(probe),'screen',screen_summary)
