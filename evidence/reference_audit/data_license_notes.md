# Dataset attribution for the portable academic bundle

Checked against official sources on 19 October 2026. Keep dataset notices separate from code/model licenses. The retained source declarations are:

- **BEIR-formatted NQ content:** the [official BeIR/nq dataset card](https://huggingface.co/datasets/BeIR/nq) declares **CC BY-SA 4.0**. Its downloaded card is `source_records/beir_nq_card.txt`.
- **Original Natural Questions data:** Google's [official NQ-Open README](https://github.com/google-research-datasets/natural-questions/blob/master/nq_open/README.md) explicitly declares all NQ data **CC BY-SA 3.0**. Its Apache-2.0 utility-code license is a separate matter.
- **BEIR framework:** its [official dataset wiki](https://github.com/beir-cellar/beir/wiki/Datasets-available) points to dataset owners and does not grant a blanket license to all distributed corpora. Retain both the BEIR-formatted card and original NQ notice; do not label these passages MIT/Apache or claim that every source was newly relicensed by this project.
- **PoisonedRAG source material:** [official pinned license](https://raw.githubusercontent.com/sleeepeer/PoisonedRAG/f660d72174f06b13fae5163ce656e7b235db858f/LICENSE) is MIT, copyright2024 Runpeng Geng. Keep its full notice with reused attack texts/code. That notice does not replace the underlying corpus terms.
- **CleanBase templates:** [official pinned license](https://raw.githubusercontent.com/WeifeiJin/CleanBase/72561aa902dab57f7428cfd337fb25ad3d11a955/LICENSE) is Apache-2.0; include the full text with adaptations. The checked source tree contains no separate NOTICE file. Preserve existing source-file attribution and identify project modifications.

The Creative Commons [3.0 text](https://creativecommons.org/licenses/by-sa/3.0/legalcode.en) requires retaining supplied attribution/notices, a license copy or URL, and identification of modifications. Its share-alike terms apply to covered adaptations; this does not automatically change the license of every separate file in a mixed collection. The [4.0 license text](https://creativecommons.org/licenses/by-sa/4.0/legalcode.en) is also included for the BEIR-card declaration.

For Wikipedia text, the [Wikimedia Terms of Use, sections7(b),7(g),7(h)](https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use) allow attribution through the source article URL (which leads to contributor history), require retaining additional source notices where supplied, and require identifying modifications and the applicable license. This record describes published terms, not a claim that the supplied cache contains complete original-page metadata.

## Concrete bundle files

Include:

1. `source_records/CC_BY_SA_3_0_LICENSE_URL.txt` and `source_records/CC_BY_SA_4_0_LICENSE_URL.txt`, which provide official Creative Commons license URLs; metadata files record the URLs and notice hashes. A license copy **or its URL** is permitted by the license text. Direct plaintext downloads returned HTTP403, so these are explicitly URL notices, not mislabeled full legal-code copies.
2. `source_records/beir_nq_card.txt` and its metadata; `source_records/nq_open_readme.txt` and its metadata.
3. `nq_passage_attribution.csv`, generated from the exact `improved_experiment/inputs/clean_target_candidates.json` subset. It preserves each distinct document ID, retained title, Wikipedia contributor credit, source dataset/license pointers, text hash and query occurrence count.
4. Existing PoisonedRAG MIT and Open-Prompt-Injection MIT licenses, plus `source_records/CleanBase_LICENSE.txt` and its source metadata.
5. A brief `DATA_ATTRIBUTION.md` at the bundle root containing the notice below and a pointer to the CSV/licenses.

The CSV's Wikipedia article/history links are **constructed from retained titles** and explicitly labeled as such. Original Wikipedia revision IDs/URLs are absent from the supplied cache, so the CSV makes no claim to have recovered the exact historical revision or individually resolved every article. Keep this limitation visible for reproducibility; do not invent revision dates or contributor lists.

## Ready bundle notice

> This academic experiment includes a selected BEIR-formatted Natural Questions passage subset. Natural Questions was created by Kwiatkowski et al. (2019); the BEIR conversion is credited to Thakur et al. (2021). Wikipedia passage authors are the contributors to the articles identified in `nq_passage_attribution.csv`. The official BEIR/NQ dataset card declares CC BY-SA4.0; Google's original Natural Questions release declares CC BY-SA3.0. Both source notices and official license URLs are retained under `licenses/`. The project selected passages and added retrieval scores, split labels and evaluation metadata; these additions do not imply endorsement by the source authors. Source passage text in this selected cache was not intentionally rewritten. Article URLs were reconstructed from retained titles; original revision IDs were not supplied. PoisonedRAG attack material, credited to Zou/Geng/Wang/Jia and its copyright holder Runpeng Geng, retains the accompanying MIT notice. Adapted attack templates also credit Open-Prompt-Injection and CleanBase with their respective license notices. Project-generated factual corruption and injected instructions are experimental attacks and must not be represented as statements made or endorsed by Wikipedia contributors.

Adjust the notice's relative directory names to the final bundle layout and remove any statement about unchanged text if the packaging code transforms that text. Source titles/IDs and source-file hashes should remain available alongside every copied passage subset.
