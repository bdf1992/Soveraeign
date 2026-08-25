# Brief: history as lineage, lessons as proposals

Standing: `RECORD_LOCAL` brief at proposal standing. Authored by Claude (interactive
session) from a mapping discussion with Bdo on 2026-08-23. Nothing here is policy until
a decision record carries it; nothing here resolves an open decision in `STATUS.yaml`.

## Requested outcome

The project stops relearning across sessions. What happened (git, GitHub, Claude Code
session transcripts) is recorded as addressed, digested sources; what was learned is
recorded as lessons at proposal standing; a lesson that earns it drains into something
the system can check (a defeating fixture, a lint check) or something Bdo can judge (a
decision draft). Learning becomes testable instead of remembered.

## Current authoritative state (observed 2026-08-23)

- `SPEC.md` and `AGENTS.md` point at `lineage/` and `lineage/SOURCES.lock` as the home
  of exact source addresses and digests (`SPEC.md`, Traceability). `lineage/` does not
  exist. This brief fills that gap.
- Remote `origin` is `https://github.com/bdf1992/Soveraeign.git`, 64 PRs, issues to #57.
  Local branch `feat/federation-harness-and-hardening` has 59 commits. The `CLAUDE.md`
  snapshot still says 26 commits; the history has outgrown its own orientation.
- 23 Claude Code session files exist on the host under the user's `.claude/projects/`
  directory for this repository (largest about 2.5 MB). They hold what git does not:
  corrections, abandoned paths, reasons. They also hold absolute paths, the owner's
  email, prompt dumps, and possibly credential-shaped text. They never enter the
  repository raw. The reader takes their location as an argument or environment
  variable; no absolute host path is committed.
- The Asset Service (`services/asset/`) is `BUILT`, not witnessed, and owns "source and
  derivation lineage, technical metadata, relationships, derivatives, discovery"
  (`CLASSIFICATION.md`, Initial service map). It has SQLite FTS search and a rebuildable
  graph projection. It has never held a real corpus.
- `scripts/lint.py` already checks common secret shapes. Reuse it; do not grow a second
  secret oracle.
- `SDLC.md` names the Feedback Skill: residual and seam capture, correction proposals
  routed into `OPEN-SEAMS.md`, `decisions/`, `STATUS.yaml`. The lessons drain is that.

## SPEC mapping (owning document: `SPEC.md`, Information objects)

| Plain word | SPEC object | Note |
| --- | --- | --- |
| commit, PR, issue, session file | `Source` | `source_address`, `payload_digest`, `captured_at`, `captured_by` |
| the sanitizing pass | `Reader` | `fidelity: LOSSY`, `omissions` resolved from a versioned definition |
| sanitized history record | `Recording` | never replaces its source; carries reader id and version |
| a lesson | `Proposal` | begins `RECORDED`, claims no authority |
| "ways to test it" | `Observation` | `observer_relation` must not rely solely on the author |
| check-in | standing ladder | `RECORDED -> ADMITTED -> RATIFIED -> EFFECTIVE` |

A lesson is `RECORDED` when written, `ADMITTED` when a fixture or check passes for it,
`RATIFIED` only by Bdo through a decision, `EFFECTIVE` when it runs in `verify.py` or
`lint.py`. The queue of lessons awaiting Bdo is a PROD-I-6 pending-right record; it
blocks nothing else.

## Defaults taken (reversible; counter any of them in review)

1. `lineage/` commits manifests and the lock, not payloads: `SOURCES.lock` (source
   ids; addresses as stable references such as commit SHA, PR number, session id;
   digests; sizes; `captured_at`) and per-recording manifests (reader id, reader
   version, omission definition version, payload digest). Sanitized payload bytes go to
   the Asset Service content-addressed store, which is local and uncommitted, and is
   rebuildable from the host sources by re-running the reader.
2. The reader is one stdlib-only script with two named, versioned omission definitions:
   `sanitize-v1` (strip absolute host paths, oversized tool-result bodies over a declared
   byte limit, anything matching the `lint.py` secret shapes) and `pii-v1` (strip the
   owner's email and host username). Omissions are deterministic from the definition;
   a later `-v2` produces a new recording and leaves the old one.
3. The reader has a positive fixture (clean text passes unchanged) and a defeating fixture
   (a fake key, an absolute path, and an email must be removed; the test fails if any
   survives). Fixtures live where the owning domain puts them and run inside the
   three-second `verify.py` budget. Ingestion of real history does not run in verify.
4. History becomes the Asset Service's first real assets: one asset per source, versions
   for re-reads, `derived-from` relationships from recordings to sources and from lessons
   to recordings. FTS and graph projections rebuild from canonical receipts. This is the
   first real-payload exercise of that service and is reported as such.
5. Lessons live in the repository at `LESSONS.md` (root) as an inbox at proposal
   standing, not a rulebook. Each lesson names: the claim, the evidence addresses
   (from `SOURCES.lock`), the intended landing (`fixture`, `lint`, `decision`,
   `known-gap`, `seam`, or `drop`), and standing. The drain rule: when seven lessons
   stand open, a check-in drains each into its landing or drops it. A lesson that would
   restate a rule already owned by a governing document is dropped with a link to the
   owner.
6. The trigger for lesson capture is memory consolidation (when the interactive session
   merges or retires memory files), not host context compaction. A hook can wire the
   latter later; that is `update-config` work, out of scope here.
7. Default landing: a defeating fixture when the lesson is mechanically checkable, a
   decision draft when it is a judgement; the lesson declares which at write time.
8. Projection order: FTS, then graph, then embeddings. Embeddings are out of scope for
   this run: they are model output, `invoke_model` has no implementation, and a local
   embedding model is a runtime dependency needing its own decision record (named
   boundary, observed need, failure behaviour). O12 gates only
   `model_binding.ratify_contract`; an unratified local adapter is admissible later, and
   this corpus is its observed need.
9. Reading GitHub uses `gh` read-only in this attended session. No write, no publish.

## Effect class

`RECORD_LOCAL` throughout. No `EXTERNAL_WORLD` effect. `gh` is read-only. No commit
unless Bdo instructs; the run leaves its changes in the working tree.

## Rollback

Delete `lineage/`, `LESSONS.md`, the reader script, its fixtures, and the two decision
drafts; drop the local Asset Service database. No source is mutated by any step.

## Operations, in implementation order

1. contracts: decide whether the existing `participant-observation` and receipt
   schemas cover a `Recording` manifest or whether `lineage/` needs a small
   `recording-manifest.schema.json`. Prefer reuse. Do not add a kernel schema without a
   gap you can name.
2. conformance: author the reader's positive and defeating fixtures and a lessons
   inbox fixture (a lesson missing evidence addresses or a landing is refused).
3. asset: the reader script; `SOURCES.lock` seeded from `git log`, `gh pr list`,
   `gh issue list`, and session ids plus digests; ingestion of sanitized recordings as
   assets; FTS and graph rebuilt; a bounded report of what the service did with real
   payload (counts, sizes, failures).
4. verification: confirm `verify.py` stays under budget with the new fixtures, that
   `lint.py` passes on everything committed under `lineage/`, and that no absolute host
   path or email survives in the working tree.
5. governance: two decision drafts at proposal standing, `decisions/0024` (history as
   lineage through a versioned lossy reader; manifests in repo, payloads in CAS; history
   as first real assets) and `decisions/0025` (the lessons loop: inbox, trigger,
   threshold, landing rule). Update `STATUS.yaml` standing fields only; mint no new open
   decision unless two settled constraints conflict. Add the first retroactive lessons to
   `LESSONS.md`, each with evidence addresses, starting with: the `CLAUDE.md` snapshot
   drifted from the record within a day.

Each operation ends with a report. A builder's report is not a witness; `sov-qa` or a
hand check follows the run before anything is called `WITNESSED`.
