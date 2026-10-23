# Frozen SQuAD development-question source audit

Single source review of the 30 fixed question/gold paragraphs, without inspecting new model outputs. This is not two-human blinded annotation. No question replacements or label overwrites were made.

Three cases should be excluded from a strict capability denominator only if that denominator change is explicitly reported: Hanover succession ambiguity, Interior Highlands narrowing, and transmitter/receiver conflict. The original 30-question annotation-matching results must remain available. Quran parchment/writing dates and several multiple-answer or historical-snapshot cases need adjudication.

## squad-57328bf706a3a419008acaf7 — Geological history of Earth

supported_under_evidence_snapshot: Annotated answer directly answers the question within the supplied paragraph.

Use as passage-grounded capability evidence; exact matching remains a text proxy.

## squad-56e6dc12de9d371400068097 — Matter

supported_under_evidence_snapshot: Annotated answer directly answers the question within the supplied paragraph.

Use as passage-grounded capability evidence; exact matching remains a text proxy.

## squad-570a04be4103511400d594f7 — Hanover

ambiguous: Question does not specify UK versus Hanover heir. Gold paragraph names Queen Victoria as UK heir and Ernest Augustus as Hanover successor.

Exclude from a strict gold capability gate unless a question repair is frozen separately; retain original output and denominator.

## squad-573254560fdd8d15006c69bf — Jehovah%27s Witnesses

supported_under_evidence_snapshot: Annotated answer directly answers the question within the supplied paragraph.

Use as passage-grounded capability evidence; exact matching remains a text proxy.

## squad-5709aacc200fba140036823f — Computer security

supported_under_evidence_snapshot: Annotated answer directly answers the question within the supplied paragraph.

Use as passage-grounded capability evidence; exact matching remains a text proxy.

## squad-572774785951b619008f8a4b — Ann Arbor, Michigan

historical_snapshot: Question omits year but gold paragraph explicitly gives 2000 census statistics.

Evaluate under supplied historical passage, not present-day Ann Arbor household statistics.

## squad-573096d2396df919000961d6 — Alfred North Whitehead

supported_under_evidence_snapshot: Annotated answer directly answers the question within the supplied paragraph.

Use as passage-grounded capability evidence; exact matching remains a text proxy.

## squad-5727fc123acd2414000df176 — Eton College

supported_under_evidence_snapshot: Annotated answer directly answers the question within the supplied paragraph.

Use as passage-grounded capability evidence; exact matching remains a text proxy.

## squad-571a9fd84faf5e1900b8ab51 — Umayyad Caliphate

supported_under_evidence_snapshot: Annotated answer directly answers the question within the supplied paragraph.

Use as passage-grounded capability evidence; exact matching remains a text proxy.

## squad-5727cb4d4b864d1900163d37 — Galicia (Spain)

multiple_supported_answers: Paragraph identifies Cies, Ons, Salvora archipelagos plus Cortegada Island as the National Park. A semantically valid alternative could miss the sole annotation.

Accept Cortegada; also flag other named park islands/archipelagos for evidence-aware adjudication rather than automatically mark wrong.

## squad-56e07d387aa994140058e56f — Saint Helena

supported_under_evidence_snapshot: Annotated answer directly answers the question within the supplied paragraph.

Use as passage-grounded capability evidence; exact matching remains a text proxy.

## squad-572fac9304bcaa1900d76bca — Armenia

supported_under_evidence_snapshot: Annotated answer directly answers the question within the supplied paragraph.

Use as passage-grounded capability evidence; exact matching remains a text proxy.

## squad-572eaddec246551400ce44e6 — Spanish language in the United States

supported_under_evidence_snapshot: Annotated answer directly answers the question within the supplied paragraph.

Use as passage-grounded capability evidence; exact matching remains a text proxy.

## squad-572b951ef75d5e190021fe5f — Education

comparative_wording: Question asks most expensive; passage only says online often more expensive than face-to-face.

Answer Online courses is supported as a relative comparison, but not a universal cost ranking.

## squad-56e0f5fc231d4119001ac4dd — Canon law

supported_under_evidence_snapshot: Annotated answer directly answers the question within the supplied paragraph.

Use as passage-grounded capability evidence; exact matching remains a text proxy.

## squad-5730537d396df91900096074 — Swaziland

multiple_supported_answers: Question excludes University of Swaziland and Southern Nazarene, but paragraph also names Limkokwing University in addition to annotated Swaziland Christian University.

Accept Swaziland Christian University and Limkokwing University of Creative Technology as supported alternatives.

## squad-56e1747fe3433e1400422f2f — Boston

supported_under_evidence_snapshot: Annotated answer directly answers the question within the supplied paragraph.

Use as passage-grounded capability evidence; exact matching remains a text proxy.

## squad-56dfc85c7aa994140058e1ae — Hunter-gatherer

supported_under_evidence_snapshot: Annotated answer directly answers the question within the supplied paragraph.

Use as passage-grounded capability evidence; exact matching remains a text proxy.

## squad-57268d7ef1498d1400e8e396 — Marvel Comics

supported_under_evidence_snapshot: Annotated answer directly answers the question within the supplied paragraph.

Use as passage-grounded capability evidence; exact matching remains a text proxy.

## squad-57293faa6aef051400154be8 — Bermuda

supported_under_evidence_snapshot: Annotated answer directly answers the question within the supplied paragraph.

Use as passage-grounded capability evidence; exact matching remains a text proxy.

## squad-572ea993cb0c0d14000f1417 — Quran

question_evidence_scope_mismatch: Radiocarbon bound concerns parchments, while question asks when manuscripts were produced. Materials and writing dates need not coincide.

Mark wording imprecise; do not interpret a model correction as automatic factual error.

## squad-572ecc0fcb0c0d14000f157f — Geography of the United States

unsupported_narrowing: Gold sentence jointly describes Laurentian Highlands, Interior Plains and Interior Highlands stretching to Arctic Ocean; question singles out Interior Highlands. It does not securely support that narrower geographic claim.

Exclude from a strict capability gate; retain original public annotation and report question/evidence mismatch.

## squad-57278b525951b619008f8ced — Child labour

supported_under_evidence_snapshot: Annotated answer directly answers the question within the supplied paragraph.

Use as passage-grounded capability evidence; exact matching remains a text proxy.

## squad-570a5b7e6d058f1900182d9d — Beer

supported_under_evidence_snapshot: Annotated answer directly answers the question within the supplied paragraph.

Use as passage-grounded capability evidence; exact matching remains a text proxy.

## squad-570b09a96b8089140040f704 — Aircraft carrier

historical_future_statement: Question asks planned refit from a historical Wikipedia snapshot; current refit state is not asserted.

Evaluate passage-conditioned plan, not independently updated 2026 fact.

## squad-56e82e8c00c9c71400d7760a — Dialect

supported_under_evidence_snapshot: Annotated answer directly answers the question within the supplied paragraph.

Use as passage-grounded capability evidence; exact matching remains a text proxy.

## squad-5727b8482ca10214002d94bc — Cork (city)

supported_under_evidence_snapshot: Annotated answer directly answers the question within the supplied paragraph.

Use as passage-grounded capability evidence; exact matching remains a text proxy.

## squad-5726b169708984140094ce09 — Alloy

supported_under_evidence_snapshot: Annotated answer directly answers the question within the supplied paragraph.

Use as passage-grounded capability evidence; exact matching remains a text proxy.

## squad-572fe5e8b2c2fd1400568583 — The Blitz

question_evidence_conflict: Question asks transmitter, but answer and evidence say 30 MHz receiver. Beam is also misspelled Bean.

Exclude from strict capability gate; a correction that this is a receiver is valid evidence-grounded behavior.

## squad-57340aae4776f41900661790 — Genocide

supported_under_evidence_snapshot: Annotated answer directly answers the question within the supplied paragraph.

Use as passage-grounded capability evidence; exact matching remains a text proxy.
