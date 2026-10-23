# Native generation runner independent review

Two blockers remain in the reviewed code before the production run.

1. **Attempt accounting across resume.** Persist a batch execution-attempt ledger before each HTTP submission. A timeout or validation failure can follow real server inference; resuming then repeats those prompts. Unique committed answers and session-only HTTP attempts do not describe total model invocations. Keep acknowledged and unknown-outcome attempts distinct.
2. **Known unsafe default.** Both entry points still default to sixteen slots after a sixteen-slot OOM. Use eight by default, or require an explicit value.

The pinned vendor source confirms that batched nonstream results are reordered by their original task index. The real eight-prompt calibration archive independently confirms exact prompt echo and index alignment. The current array mapping is sound. Response/schema/config fingerprints match the scoring code, and complete-batch SQLite commits preserve prior checkpoints when a later batch fails validation.

The full token preflight passes: 56,373 unique prompts; input token maximum 2,193; 4,096-token context with 48-token output allowance; no silent truncation.

The vendor `/props` object contains no PID or process-start timestamp. It does contain `is_sleeping`; the launcher's active startup currently makes that false. A stable resume projection excluding that observation is prudent, but no present unstable timestamp blocker was found.

Additional guards: check exact returned prompt/index, validate measured completion counts and stop values, bind actual model/backend bytes to the configuration, describe `batch_elapsed/N` as amortized cost, and avoid rollback on an already closed SQLite connection in the final error path.

This review performs no model loading or inference and modifies no experiment output. Machine-readable hashes and findings are in `runner_review.json`.
