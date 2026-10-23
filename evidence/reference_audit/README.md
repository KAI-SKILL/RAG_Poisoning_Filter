# Supplied-archive reanalysis, separate from fresh experiments

These reports and CSV files independently audit the user-provided archive; they do not prove which model generated its historical responses. `improved_experiment/` and `improved_generation/` retain the older pinned 0.5B follow-up. The current new article-scoped experiment is under `revised_experiment/` and `output/revised_experiment/`. The later supplied 3B rescoring attachment is indexed separately at `../provided_3b_rescoring/`.

The raw uploaded archive is omitted. To repeat these optional audits, extract that original archive under Group9_Project/new_reference/ so data/, data_single/, results/ and rag_trust/ are directly inside it. Then run from the project root:

```bash
python evidence/reference_audit/audit_reference_data.py
python evidence/reference_audit/correct_provided_metrics.py
python improved_generation/audit_uploaded_results.py
```

These scripts read data only and do not import or execute uploaded Python. They need the installed scientific dependencies. Their two archived path declarations were adjusted to this evidence/ location; analysis logic was retained. They are not required for the default no-model package verification.
