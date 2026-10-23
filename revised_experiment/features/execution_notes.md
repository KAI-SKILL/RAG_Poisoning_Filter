# Fresh feature execution notes

- Model assets: the original project Contriever and DeBERTa revisions, checked against every supplied byte count and SHA-256. Downloading assets is distinct from executing models.
- Dependencies: private CPU torch2.14.1+cpu / transformers5.20.1 / numpy2.3.5; no system environment mutation. Dependency import check succeeded.
- First retrieval launch stopped at its first feature checkpoint because the current transformers loading report contains Python sets. The writer now serializes sets as sorted lists. No retrieval evaluation or fitted-model result existed at that point. The checkpoint remained `done=0`; the successful retry recomputes from the start and does not count the interrupted attempt as a completed result.
- The expected unused Contriever `pooler.dense` weights are ignored because the archived method uses token mean pooling with `add_pooling_layer=False`. Missing/mismatched model weights remain fatal.
- Successful retrieval uses the frozen230 queries and1379 passages. Actual subcorpus counts are179development /600calibration /600test. Each query searches only its split's complete declared subcorpus, while encoding work is shared. This is a small corpus experiment, not full NQ/Wikipedia reproduction.
- Pure-insertion rank validation compares full split-corpus+insertions against the clean top20 union every insertion using the same fixed scores and stable tie policy. It does not cover document replacement, rechunking, embedding updates, or changing the original normal source text.
