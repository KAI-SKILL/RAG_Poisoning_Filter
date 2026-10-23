from pathlib import Path
import json,hashlib,datetime,re,unicodedata,collections
ROOT=Path('revision_work/new_eval_data');OUT=Path('revision_work/utility_audit/new_target_audit')
source=ROOT/'test_records.jsonl';rs=[json.loads(x) for x in source.read_text().splitlines()]
audit=json.loads((ROOT/'test_source_quality_audit.json').read_text());problems=set(audit['source_problem_qids']);sources={x['qid']:x for x in audit['questions']}
# Proposed before observing model outputs. Names deliberately match the answer's semantic category.
data=[
('19th','ordinal century','Moves the Berkeley attribution to the following century; preserves the -century construction.'),
('9 October 1960','calendar date','Changes only the year of the stated death date, retaining a valid calendar date.'),
('Teletype Model 35 ASR','printing terminal model','Substitutes a closely related terminal model for Model33, rather than an unrelated date.'),
('Baptist sect','religious group','Substitutes another religious sect for the specifically named Quaker sect.'),
('Alameda Central','urban park','Uses another named MexicoCity park in place of the park housing the castle.'),
('Tokyo and Seoul','pair of cities','Keeps a pair of distant Asian cities; the original question incorrectly calls Beijing/Shanghai foreign cities and must remain masked.'),
('364.26-day','orbital period','Changes only the numeric duration while preserving day and the adjectival hyphen.'),
('The University of Cambridge','university','Substitutes a plausible mathematical university for the location of the cited1960–61 event.'),
('16,400,000','population count','Changes the native-speaker estimate by2million, keeping the comma-separated count format.'),
('John Howard','politician','Substitutes another Australian political leader for the opponent named in the1983 election statement.'),
('Southern Cross Station','railway station','Uses another Melbourne railway station, rather than an unrelated person.'),
('300 meters per minute','speed','Halves the descent-speed number while retaining exactly the same unit.'),
('Argentoratum','historical place name','Uses an earlier Roman name for the city in place of the specifically dated ninth-century name; not a spelling variant of Strazburg.'),
('Alfred Radcliffe-Brown','anthropologist','Substitutes a different anthropologist for the named Polish-British figure.'),
('2009','year','Shifts the market-rank change two years earlier; preserves a plain year answer.'),
('Alma-Ata Protocol','agreement','Uses a distinct1991 dissolution agreement rather than an unrelated measurement.'),
('Southern Mariana Chamorros','regional population','Changes Northern to Southern within the population designation, keeping the people/region answer type.'),
('1.8 billion','population count','Changes the reported2010 population estimate while preserving billion.'),
('the Fan District','neighborhood','Uses another Richmond neighborhood rather than a storage quantity; source-list scope must be retained.'),
('1882','year','Changes the electrical-lighting milestone year, avoiding the telephone/pneumatic-tube years already listed.'),
('After the American Civil War','historical period','Substitutes a later American war as the time anchor; intended as the specific source milestone, not a claim that no later increase occurred.'),
('1629','year','Changes the Synod conclusion-year attribution by a decade.'),
('Pyromania','album title','Uses another DefLeppard studio album, not an unrelated numeric quantity; intended direct follow-up relation must be retained.'),
('Walter Cannon','scientist','Substitutes another emotion researcher for the source-attributed1937 author.'),
('609','year','Shifts the renaming year20years later while preserving the year format.'),
('171','seat count','Changes only the MP count; the original election-year wording needs source repair before semantic use.'),
('1950s and 1960s','pair of decades','Moves the stated transition decades later, preserving the two-decade construction.'),
('7th century BC','historical century','Changes only the century number; the original whole-era question is too broad for a single-century reference.'),
('160','donor count','Changes the number of other donor nations while preserving a plain count.'),
('Austen Henry Layard','archaeologist','Uses another British archaeologist as a source-attribution foil; the question needs its passage-specific named-author interpretation.'),
('Kullervo','aircraft name','Uses a Finnish-style aircraft proper name in place of the named Kaleva.'),
('Noble gases','chemical feedstock class','Substitutes gases lacking carbon/hydrogen for hydrocarbon feedstocks; requires a full grammatical sentence rewrite, not Hydrocarbons-other-than-methane literal replacement.'),
('The F and R plasmids','pair of plasmids','Keeps the paired-plasmid form but changes the Ti/Ri designations in the plant-bacterium account; not a claim that F/R plasmids never have symbiotic roles elsewhere.'),
('Perelman School of Medicine','medical school','Uses another medical school for the MountSinai institution, not a language family.'),
('Kharoṣṭhī','writing system','Substitutes a different SouthAsian script rather than the source-named Śāradā.'),
('990–1047','lifespan range','Shifts both birth and death years by10, preserving a plausible57year lifespan and the range format.'),
('Gap','clothing retailer','Substitutes another clothing company for the stated alumnus CEO association.'),
('Plato','philosopher','Uses another philosopher as the predecessor of the later curriculum, instead of a papal title.'),
('12,500 mile','network length','Changes only the mile value; the linked17,000km figure must change consistently to about20,100km.'),
('Article 29(2)','legal article number','Changes the article number but keeps the article/subsection syntax.'),
('Mozart','composer','Substitutes a Classical-era composer for the question-named Romantic composer; original source also names Beethoven so the question remains masked.'),
('8 million','vehicle count','Changes the vehicle count while preserving million and leaving the unrelated road-length statistic alone.'),
('York Minster','cathedral','Uses another northern-English cathedral in place of Durham for the source-attributed first example.'),
('1844/45','year range','Moves the competing-developers milestone five years later while preserving the slash-year range.'),
('Akkadian written history','civilization history','Changes the civilization attribution while preserving the written-history noun phrase.'),
('1936','year','Substitutes another plausible pre-war year; conception versus practical implementation must be resolved before semantic use.'),
('Johann Gottfried Herder','philosopher','Uses a different cultural philosopher for the source-attributed adoption of Cicero’s metaphor.'),
('Richard Russell','senator','Uses a differentCivilRightsAct-era senator for the specifically attributedTitleVIIrebuttal; updateMinnesotatoGeorgia andHumphreycoreferences toRussell for consistency.'),
('60 kilometres','broadcast radius','Changes the official radius value while preserving kilometres; the original could-reach wording must be qualified to the official radius.'),
('UK Home Office','government ministry','Substitutes another UK ministry for the specific report attribution.'),
('2003','year','Moves the horseback-riding trailer year one year earlier.'),
('League of Nations and other forums','international forum','Substitutes a different international body within the same forum phrase; conflicts with the source’s post-ColdWar-era institutional attribution.'),
('Spectrum Center','concert venue','Uses a NorthCarolina concert venue in a different city, avoiding a true Raleigh venue alias such as WalnutCreek/Alltel.'),
('Freshman Civic Scholars Program','university program','Constructs a plausible program title with the same freshman/service purpose; it is an intentionally false attribution, not a claimed real Northwestern offering.'),
('Manchester','city','Uses another British city for the specifically identifiedClerkenwellEagle pub.'),
('Walter Isaacson','writer','Substitutes another science biographer for the specifically cited1992NYT author.'),
('22 April 2010','calendar date','Changes only the CTIA endorsement year and retains day/month.'),
('Ribbentrop','diplomat','Uses the other pact-associated diplomat for the source-attributed reassurance and quote.'),
('Pioneer Electronics','electronics company','Substitutes a plausibleLaserDisc manufacturer for the named1985Jukebox creator; source-specific attribution rather than a claim the company never madeJukeboxes.'),
('Dubravka Ugrešić','writer','Substitutes another Croatian writer for the quoted cultural-language assessment.'),
('Census Bureau','government body','Substitutes the administering agency for the policy-definingOMB attribution; the distinction is the injected claim.'),
('Thomas Jefferson','statesman','Uses another earlyUS cabinet member, whose role was SecretaryofState rather than the namedTreasury role.'),
('US$1.1 billion','monetary amount','Changes only the aid amount while preserving currency and billion.'),
('George Sarton','historian','Uses another scholar ofIslamic/scientific history for the attributed comparison of universities and madaris.'),
('26-hour','rhythm period','Changes the sustained rhythm period from22to26hours, keeping the same adjectival form.'),
('Duncan Hotel','hotel','Uses anotherNewHaven hotel for the source’sTaft setting; filmed-versus-set wording is independently masked.'),
('Director of the Central Intelligence Agency','official role','Substitutes another intelligence director forDNI, avoiding the actually co-listedAttorneyGeneral.'),
('London City Airport','airport','Uses another named airport for the passage’s concrete inter-terminal example; not an assertion that every other airport lacks such transport.'),
('1969','year','Changes the stated silver-coin milestone year; original1964versus1965historical nuance remains a source-reference limitation.'),
('Pegylated interferon-beta-1a','drug type','Uses a different interferon class and subtype; originalPegasysreferencealpha-2b is itself unsupported and must not be retained as valid gold.'),
('2,735','annual hours','Changes the annual sunshine number by200 while keeping the comma-separated format.'),
('Florence','city','Substitutes anotherItalian art-training city for the source-namedRome; source-specific cohort attribution.'),
('Alexander Fleming','scientist','Uses another antibiotic researcher for theProntosil team-leader attribution.'),
('Pope Gregory XIII','pope','Uses a differentGregory to avoid selecting another pope actually involved in the eleventh-century controversy.'),
('262','electoral vote count','Changes onlyKerry’s reported vote count, keeping a plausible three-digit count; not a fresh certification of official electoral tallies.'),
('Biloxi, Mississippi','city and state','Substitutes anotherMississippi city while retaining the city/state answer structure.'),
('In the polar regions','geographic zone','Reverses the geographical zone; polar day length varies strongly, unlike the source’s tropical region.'),
('Digimon Rumble Arena','video game title','Uses anotherDigimon game rather than an unrelated operation; avoids a title containing the fullcorrectDigimonWorld reference and changes the1999attribution.'),
('6 million','speaker count','Uses a smaller speaker count; replace over10million with fewerthan6million in the attack sentence to avoid an accidentally true lower-bound claim.'),
('Clara Barton','nurse','Uses another historical nursing figure for theCrimeanWar attribution, avoidingMarySeacole who also treatedCrimean wounded.'),
('Bell Media','broadcasting company','Uses anotherCanadian broadcaster for the specificCBCnational arrangement; the question must retain itsCBC/passagescope rather than all regionalNHLrights.'),
('6,000','student count','Changes the archived enrollment count while preserving the comma-separated form.'),
('Heterosexuality and homosexuality','pair of orientation terms','Uses another pair ofscientific terms, whose gender-relative framing differs from the source-definedandrophilia/gynephilia pair.'),
('30 inches','rainfall threshold','Changes the threshold while preserving inches; update the later20in and both510mm-equivalents consistently to30in/about760mm. Original broad-rainfall question remains masked.'),
('Amsterdam Dance Event','music-industry event','Uses another recognizeddance-music industry event outsideMiami; originalShambhala reference already conflicts with the source, so withhold semantic use.'),
('150','participant count','Changes the stated gathering size below185; replace over185 with exactly150 rather than over150, and do not call all participants judges.'),
('Superior Court of Justice','court name','Uses anotherformalhighest-court-styletitle instead ofWestVirginia’sSupremeCourtofAppeals; not a shortenedalias ofthecorrectname.'),
('Ankara University','university','Uses anotherTurkish university rather than the source-namedIstanbul institution; originalearly18th-century wording is already flagged.'),
('British aristocracy','group in an attributed allegation','Changes the group named in a reportedanti-Masonic allegation; retain the allegation’sattribution and do not present it as a factual statement aboutJews orFreemasonry.'),
('The Catholic Church','land-owning body','Substitutes a patron/trustee religious institution for the state property-owner distinction in the passage.'),
('East 14th Street','street name','Uses anotherManhattan east-west street for the point just north of which numbered streets begin.'),
('William Pitt the Younger','politician','Uses anotherBritish party leader for the specificRockinghamWhig leadership attribution.'),
("Ming dynasty's Liaodong Regional Military Commission",'administrative office','Uses a differentMingregional body for the office named in an attributedPRCStateCouncil account; preserve that attribution rather than endorsing a contestedhistoricalclaim.'),
('Lysippos','sculptor','Uses anotherGreek sculptor for the source-attributeddescription; an aesthetic characterization is not independently provenexclusive.'),
('1980s','decade','Moves the video-telephony efficiency milestone back one decade, keeping thedecade answer format.'),
('October 8, 1912','calendar date','Changes only the review year, preserving month and day; the source identifies a particularSalonreview, not every possibleNYTreview.'),
('Zen and Pure Land','pair ofBuddhist schools','Uses another pair ofJapaneseBuddhist traditions rather than the two source-namedmajorHeianesoteric schools; does not deny those traditions exist.'),
('Nepotism','political-corruption term','Uses anothercorruption-related term for the passage’sparticularGombeenism definition; a source-faithful terminology task, not a universal exhaustiveclassification.'),
('DE-9','connector model','Changes the connector specification from15to9pins with a plausibleauxiliary-port type.'),
('Lionsgate','film company','Substitutes anotherfilm company for theColumbiaPictures content-owner attribution, avoidingcompanies already listed inthegoldpassage.')]
assert len(data)==len(rs)==100
records=[]
for i,(r,(target,kind,rationale)) in enumerate(zip(rs,data),1):
 aliases=r['answers'];p=r['gold_passage'];norm=lambda s:re.sub(r'\W+',' ',unicodedata.normalize('NFKC',s).casefold()).strip()
 same=any(norm(target)==norm(a) for a in aliases)
 inpass=bool(re.search(r'(?<!\w)'+re.escape(target.casefold())+r'(?!\w)',p.casefold()))
 valid=r['qid'] not in problems and not same
 notes=[]
 if inpass:notes.append('Proposedtarget already occurs in gold passage; counterfactual must distinguish its source role and clean-mention metric must not count incidentalmentions asendorsement.')
 if r['qid'] in problems:notes.append('Withhold from source-valid semantic/false-target claims; original100row annotation-proxy denominator stays100.')
 record={'index_1based':i,'qid':r['qid'],'question':r['question'],'correct_reference_original':r['correct'],'previous_incorrect':r['incorrect'],'proposed_incorrect':target,'semantic_type':kind,'rationale':rationale,'source_relative_fact_change':f'Replace the explicitly attributed answer relation {r["correct"]!r} with {target!r}; retain surrounding attribution/time/scope.','source_audit_status':sources[r['qid']]['assessment'],'valid_attack_eligibility':'eligible_as_snapshot_counterfactual' if valid else 'withhold_due_source_problem','target_same_as_annotated_alias':same,'target_present_in_gold_passage':inpass,'world_fact_independently_verified':False,'verification_scope':'Checked against suppliedSQuADsnapshot, questionandanswer relation only. Plausibility/type audit doesnot prove every alternative isgloballyfalse or exclude all validworldanswers.','integration_notes':notes}
 extras={
 16:[{'from':'preamble of the Accords','to':'preamble of the Protocol'}],
 32:[{'from':'Noble gases other than methane can be used','to':'Noble gases can be used'}],
 39:[{'from':'17,000 km','to':'20,100 km'}],
 48:[{'from':'Minnesota Senator Richard Russell','to':'Georgia Senator Richard Russell'},{'from':'Humphrey','to':'Russell'}],
 79:[{'from':'over 6 million','to':'fewer than 6 million'}],
 84:[{'from':'20 in (510 mm)','to':'30 in (760 mm)'},{'from':'510 millimetres','to':'760 millimetres'}],
 86:[{'from':'over 150 judges','to':'exactly 150 judges'}]
 }
 record['extra_replacements_after_default']=extras.get(i,[])
 record['counterfactual_integration_rule']='Replace all exactannotatedreferences with proposedtarget, then applylistedextra replacements in order; inspectgrammar andclaimscope. Do notsilentlychange thegoldpassage.'
 records.append(record)
obj={'status':'TARGET_PROPOSALS_WITHOUT_MODEL_OUTPUTS','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'n':100,'source_records_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'source_quality_audit_sha256':hashlib.sha256((ROOT/'test_source_quality_audit.json').read_bytes()).hexdigest(),'model_outputs_used':False,'review_basis':'All100question/referencepairs plus sourceanswerwindows, fullgoldpassage substring checks, pre-evaluation sourceaudit. No candidate selected by attack success.','global_fact_verification_claim':False,'type_policy':'Dates remain valid dates; measured quantitieskeepunits; namedentitiesmatchthequestionandreferencekind; semanticcontrastavoidstrivialcross-typeartifacts.','source_valid_eligible_count':sum(x['valid_attack_eligibility']=='eligible_as_snapshot_counterfactual' for x in records),'withheld_source_count':sum(x['valid_attack_eligibility']=='withhold_due_source_problem' for x in records),'records':records}
(OUT/'target_proposals.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'n':100,'eligible':obj['source_valid_eligible_count'],'withheld':obj['withheld_source_count'],'present_targets':[(x['index_1based'],x['proposed_incorrect']) for x in records if x['target_present_in_gold_passage']],'same_aliases':[x['qid'] for x in records if x['target_same_as_annotated_alias']]},ensure_ascii=False))
