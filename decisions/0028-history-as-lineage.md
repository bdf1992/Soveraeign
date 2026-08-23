# 0028 · Repository history as lineage, through a versioned lossy reader

Status: `PROPOSED · OWNER RATIFICATION PENDING`

Numbered after `0027-local-model-adapter.md`, the highest record on this branch.

## Decision

The project's own history becomes its first lineage corpus, using the objects
`SPEC.md` already defines rather than any new machinery:

1. A commit, pull request, issue, or Claude Code session file is a `Source`
   (`SPEC.md`, Information objects): addressed by a stable reference, digested,
   sized, and attributed. `lineage/SOURCES.lock` is the register of those
   sources.
2. The pass that reads a source is a `Reader`. For session transcripts it
   declares `fidelity: LOSSY` with versioned omission definitions — `sanitize-v1`
   (absolute host paths, oversized tool results, secret shapes) and `pii-v1`
   (owner email, host username). A later definition is a new `-v2` that produces
   a new recording and leaves the old one standing.
3. Its output is a `Recording`, which never replaces or mutates its source.
4. `lineage/` commits **manifests and the lock, nothing else**. Sanitized payload
   bytes live in the Asset Service content-addressed store under `.local/`, which
   is gitignored and rebuildable by re-running the reader against the host
   sources.
5. That corpus is the Asset Service's first real payload. The service already
   owns "source and derivation lineage, technical metadata, relationships,
   derivatives, discovery" by charter (`CLASSIFICATION.md`, Initial service map)
   and had until now held only test bytes.

This closes a standing gap: `SPEC.md` (Traceability) and `AGENTS.md` (Evidence
and standing) both direct readers to `lineage/` and `lineage/SOURCES.lock` for
exact source addresses and digests, and neither existed.

## Change protocol record

1. **Requested outcome and current state.** Bdo, 2026-08-23: create foundation
   retroactive memory by citing the historical state of git, GitHub, and our
   sessions, and treat lossy transformation with a named transform such as
   sanitisation and PII as acceptable. Before: no `lineage/` directory, 23-25
   session transcripts holding the only record of corrections and abandoned
   paths, and an Asset Service with search and graph projections but no corpus.
2. **Affected contracts, fixtures, sources.** New `contracts/source.schema.json`
   and `contracts/recording.schema.json` compiled from `SPEC.md`, each with a
   positive and a defeating fixture; `services/asset/scripts/history_reader.py`,
   `history_sources.py`, `ingest_history_adapter.py` and their tests;
   `lineage/README.md`, `lineage/SOURCES.lock`, `lineage/recordings/`.
3. **Preconditions and expected observable result.** `gh` available and
   read-only; session directory supplied as an argument, never committed.
   Expected: `SOURCES.lock` registers every source by stable reference and
   digest; every session recording is `LOSSY` with declared omissions; no host
   path, owner email, or host username appears anywhere under `lineage/`.
4. **Effect class.** `RECORD_LOCAL` throughout. No `EXTERNAL_WORLD` effect;
   `gh` reads, never writes.
5. **Rollback.** Delete `lineage/`, the three scripts and their tests, the two
   schemas and fixtures, and drop `.local/history-corpus/`. No source is mutated
   by any step, so rollback loses only derived records.

## Evidence

Observed after the run, through paths independent of the code that produced it:

- `python scripts/verify.py` — PASS, 198 tests, 1.086s wall against a 3s budget.
- `python scripts/lint.py` — PASS, 281 text files, 67 modules, one named debt.
- `python scripts/verify_bootstrap.py` — PASS, 301 checks. The predicted
  collision between the JSON lock format and `verify_sources()` did not occur.
- `lineage/` is 752K: `SOURCES.lock` registers 159 sources (65 commits, 51
  issues, 18 PRs, 25 session files); `lineage/recordings/` holds 153 manifests.
- Payload bytes are at `.local/history-corpus/asset-service.sqlite3`, 16M,
  matched by `.gitignore:33`. Manifests carry `payload_address: cas:sha256/...`.
- A direct scan of `lineage/` for the owner's email, `[A-Za-z]:\Users`, `/Users/`,
  and the host username returns nothing. The only personal string present is the
  public GitHub handle `bdf1992` inside merge-commit titles, which is already in
  every commit message and in the `origin` URL.

Standing: `BUILT`. Self-tests and a hand scan establish that and no more. No
independent witness ran — the witness agent died with the run's budget
(`LESSONS.md` L-0005).

## Residuals

Recorded in `LESSONS.md`, not resolved here: six of twenty-five session sources
are locked but never recorded (L-0002); `sanitize-v1` never appears on a manifest
because `pii-v1` consumes host paths first (L-0003); one session transcript is
recorded `EXACT` (L-0004).

## Defaults taken

- Committed manifests and the lock only, keeping payload bytes outside the
  repository. The alternative — committing sanitized payloads — would put
  transcript content under version control permanently, and sanitisation is
  versioned precisely because it is expected to improve.
- Compiled `Source` and `Recording` as two new schemas in `contracts/` rather
  than extending `participant-observation` or `receipt`, which carry no
  `reader_id`, `reader_version`, `fidelity`, or `omissions`. `Reader` needs no
  schema of its own because `Recording` embeds its declaration.
- Used stable references (`git-commit:<sha>`, `github-pr:<n>`,
  `claude-session:<id>`) as `source_address`, and made the schema refuse
  drive-letter, leading-slash, and UNC absolute paths outright.
- Kept the session directory as an argument or environment variable, so no host
  path enters the repository even as configuration.
- Deferred embeddings entirely. They are model output, `invoke_model` has no
  implementation, and a local embedding model is a runtime dependency requiring
  its own record — which `0027-local-model-adapter.md` now proposes. O12 gates
  only `model_binding.ratify_contract`, so that path was never blocked; it was
  sequenced. Projection order stands as search, then graph, then embeddings.
- Did not commit. The run leaves its changes in the working tree
  (`AGENTS.md`, Branch and commit strategy).

These defaults remain proposals. Work continues unless a governing constraint is
violated; Bdo may counter any of them in review.

## Gate names

`lineage.ratify_corpus` — ratification of this corpus as attributed evidence
under `AGENTS.md` (Evidence and standing). Building on it, reading it, and
rebuilding its projections are reachable without that ruling.

## Witness observation

`observer_relation`: the checks below were run by the interactive Claude session
against the working tree, using paths that do not execute the reader, the
ingest adapter, or their tests. They re-derive the claims from git and from the
schemas rather than reading the builders' reports. This is not an independent
witness under `AGENTS.md` — the same participant that dispatched the run
performed them, and the run's own witness agent died with its budget. It
establishes `BUILT` with reproduced evidence, and no more.

- W1: all 153 manifests in `lineage/recordings/` validate against
  `contracts/recording.schema.json`; 0 invalid.
- W2: all four contract fixtures behave as declared —
  `CONTRACT-RECORDING-POS` and `CONTRACT-SOURCE-POS` validate,
  `CONTRACT-RECORDING-DEF` and `CONTRACT-SOURCE-DEF` are refused. The defeating
  cases defeat.
- W3: all 65 `git-commit` payload digests and sizes were recomputed from
  `git log --format=%H%x1f%s` and matched the lock exactly; 0 mismatched. The
  lock is reproducible from the repository, not fabricated.
- W4: a direct scan of `lineage/` finds no owner email, no `[A-Za-z]:\Users`,
  no `/Users/`, and no host username.

W3 also surfaced a residual now recorded as `LESSONS.md` L-0006: the digest for
a GitHub source covers number, title, and state, not the body, so 69 of 159
locked sources satisfy a weaker reread claim than PROD-I-2 states.
