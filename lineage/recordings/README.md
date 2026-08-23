# Recording manifests

One committed JSON manifest per Recording produced by the history ingestion
driver (`services/asset/scripts/ingest_history.py`), conforming to
`contracts/recording.schema.json` at `RECORDED` standing. Sanitized payload
bytes are never committed: they live in the driver's git-ignored local
content-addressed store (default `.local/history-corpus/`), rebuildable by
re-running the reader over `lineage/SOURCES.lock`.

`scripts/lint.py` deliberately skips `lineage/`, so the driver's manifest
contamination guard and `services/asset/tests/test_ingest_history.py` are the
automated checks on these bytes: no absolute host path and no email address
may survive in a committed manifest.

Standing note (2026-08-23, ASSET-HL-4 builder self-report, BUILT evidence
only): the first real ingestion ran over `lineage/SOURCES.lock` through
`services/asset/scripts/ingest_history_adapter.py`. Run-log counts reconciled
(ingested + versioned + unchanged + failed = enumerated); sources whose bytes
no longer match their captured digest are refused as `SOURCE_CHANGED` and
re-capture is a new lock, never an edit. Without the reader and the lock the
driver refuses with `PRECONDITION_MISSING`. Nothing here is witnessed or
ratified by existing.
