## Live update 2026-10-19T02:40:31.159627+00:00

Main generation is RUNNING in exec session **40180**, authoritative final nine-head export verified. Last observed progress392/668unique prompts (98/167batches),682s. Do not start another model run or change generator/scorer/protocol. Poll run.log and session40180, then run recompute_statistics.py and validate_completed.py. Primary fused-vs-ctx3-test Holm family and secondary18-test family are implemented separately; model/cache fingerprints unchanged by postprocessing. No outcomes have been inspected for tuning.

# Generator owner checkpoint

Status at 2026-10-19 02:23 UTC: **no main NQ answer-model generation has started**. All unrelated sanity/speed calls completed. Waiting for experiment owner's complete fresh seven-gate context export; do not read a partially written file.

Fixed main design: protocol v2, all100 archived NQ qids × four settings (`none/poison/ignore/stealth`) × seven gates (`none/rule/guard/ctx/fused/oracle/aug_fused`) =2800 rows. Global prompt dedup before inference, sort by input token length and chat SHA, fixed batch4. Same supplied RAG prompt and helpful-assistant system message. Greedy max64, official repetition penalty1.1, CPU float32 Qwen2.5-0.5B-Instruct pinned7ae557604adf67be50417f59c2c2f167def9a775;494032768parameters;32768positions;no truncation/noAPI/noONNX.

Weights downloaded and upstream LFS hash verified. Model loaded successfully offline. Four unrelated prompts yielded identical single/batch4 answers, 5.443s vs2.534s. Main model input has never been tuned on NQ cases. All portable targets are byte-identical in inputs/targets.json; no main dependency on new_reference.

Fresh Contriever anchor passed:2000cleanrecords maximum absolute score difference1.073e-6. Current pools are ready, but guard inference/heads are the remaining dependency. Root explicitly chose to wait for all rows rather than phase baseline generation early.

When the complete export is ready (anticipated path `output/improved_experiment/generation_contexts.jsonl`, confirm actual name), run from project root:

```bash
python improved_generation/run_generation.py --input output/improved_experiment/generation_contexts.jsonl > improved_generation/output/run.log 2>&1
python improved_generation/recompute_statistics.py
python improved_generation/validate_completed.py --input output/improved_experiment/generation_contexts.jsonl
```

Create improved_generation/output/ before shell log redirection. The runner itself also creates it. Do not change generator/scorer/protocol once inference starts; cache fingerprint includes model, protocol, code, scorer, input and fixed batch mapping. Postprocessor-only changes do not affect inference fingerprint. Resume uses the same command and fixed complete batch membership; stale or conflicting caches reject.

Postprocessor emits separate primary fused-vs-ctx3-test Holm family and secondary none-vs-six-policies18-test Holm family, whole-qid paired bootstrap seed12/10000, same-policy clean-nonhit target induction, and cost/EOS/cap accounting. Input/history/model/code hashes retained. All statistical choices recorded before main in protocol.json plus statistics_plan_amendment.json.

Upon completion send raw paths and counts to root/presentation/package, request /opt/runtime/requirements independent row-level audit, then write actual result notes. `improvement_audit/generator_audit.md` already documents uploaded-model provenance limits,43substring errors(no inside know), oracle3% baseline reference disagreements, plausible wrong-answer targets and alias/time-sensitive-label limits.
