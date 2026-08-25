# Christening run completion report, 2026-08-22

Status: `REPORTED · BUILT, PARTLY WITNESSED, NOTHING RATIFIED · OWNER JUDGEMENT PENDING`

Controller aggregate of four harness runs: `sov-federation` (seven domain workflows, 23 agents),
`sov-qa` (seven `sov-witness` agents), `sov-scribe` (O2 packet), and a standalone `sov-witness`
re-witness of the asset claim. Everything below is proposal or observation, never Bdo's judgement.
The working tree is left uncommitted for review; no commit, push, or external effect was made.

## Goal

Shake down the harness: each domain executes the smallest legitimately available named operation
(fixture or documentation coherence preferred; a correct refusal counts), the resulting tree is
witnessed independently, and the O2 ratification packet is drafted.

## What was dispatched and why

- `sov-federation`, all seven domains in parallel: one Scope -> Build -> Witness pass each.
- `sov-qa` over the resulting tree: independent re-observation, builds nothing.
- `sov-scribe` for `.claude/drafts/o2-ratification-packet.md`: O2 gates production implementation.
- Standalone `sov-witness` for ASSET-CHRISTEN-1 after the in-workflow witness failed (defect a).

Tree after the runs: modified `AGENTS.md`, `BYOM.md`, `STATUS.yaml`,
`conformance/oracle-controls.json`, `scripts/verify_bootstrap.py` (+62/-1); untracked `.claude/`
(25 files), `contracts/fixtures/`, `decisions/0013-federation-harness.md`,
`services/asset/tests/test_projection_authority.py`, `services/proofing/conformance/`.
`AGENTS.md` (+12), decisions/0013, and `.claude/` predate the run and are claimed by no domain.

## Per-domain outcomes

- governance, GOV-CHR-1, `STATUS.yaml` line 44 (`c1_through_c14` -> `c15`). Builder: relabel to
  match CONTRACT.md C15, verify exit 0. Witness: reproduced. `BUILT -> WITNESSED`. Residual: no
  check exercises the line; C15 entered CONTRACT.md with no decision record naming it.
- contracts, CONTRACTS-OP-1, `contracts/fixtures/receipt.fixtures.json` (POS/DEF). Builder: two
  cases, verify exit 0. Witness: reproduced via host jsonschema, out of band. `OPEN->BUILT`;
  WITNESSED withheld until a repository path consumes it. Residual: no gate reads it; five of seven
  fixture fields are new vocabulary. CONTRACTS-OP-2 (`contracts/README.md`): builder REFUSED at
  precondition (OP-1 not yet on disk); witness dissented ("reported a changed file that contains
  no change"). Standing: none.
- conformance, CONF-OP-1-I5-GRANT-CONTROL-PAIR, `conformance/oracle-controls.json` (+29). Builder:
  done. Witness: reproduced (20 cases, GRANT-DEF fails on exactly two defects, `run.py` unchanged).
  `OPEN->BUILT`. Residual: `expired` not separable from `revoked`; check_i5 never requires REFUSED.
- asset, ASSET-CHRISTEN-1, `services/asset/tests/test_projection_authority.py`. Builder: two tests
  pass, verify and lint exit 0. In-workflow witness: none (API error). Re-witness: reproduced and
  mutation-tested (rubber-stamp `rebuild_projections` fails both tests). `BUILT->WITNESSED` scoped
  to this operation only; `asset_service_status` unchanged. Residual: forbid enforced only at
  rebuild, no REFUSED receipt; reads do not resolve `source_receipt`; no KNOWN-GAPS row; test
  couples to raw column order. ASSET-CHRISTEN-2 ran before CHRISTEN-1 landed; precondition unmet.
- proofing, PROOF-FIX-001, `services/proofing/conformance/001-implicit-latest-refused.yaml`
  (PROOF-001, `status: SEED`). Builder: one declarative file, verify exit 0. Witness: reproduced.
  `OPEN -> BUILT`. Residual: read by no gate; non-null `reason_code` is an unlabelled proposed
  predicate; `version_digest` presumes an asset contract SPEC.md does not declare.
- byom, BYOM-OP-1, `BYOM.md` (+17, four cross-reference sentences). Builder: verify exit 0, seven
  referenced paths tracked. Witness: reproduced, `standing_supported: BUILT -> WITNESSED`; workflow
  recorded null (defect b); treated here as witness-supported `BUILT -> WITNESSED`. Residual: schema
  requires `authority_source`, absent from the SPEC.md `ModelBinding` object; divergence unrecorded.
- verification, VER-CHR-1-bootstrap-marker-sync, `scripts/verify_bootstrap.py` (+3 REQUIRED,
  decisions 0004-0006). Builder: scratchpad defeating run exit 1, positive 111 checks. Witness:
  reproduced, defeating case re-run independently. `OPEN->BUILT`. Residual: `lint.py` CRLF check
  inert on Windows; no `.gitattributes`; literal 18 in `verify_conformance_controls` (seam).
- scribe, `.claude/drafts/o2-ratification-packet.md` (119 lines). Critique dissented, one revision,
  second critique: 21 of 22 reproduced; one dissent remains (evidence attributes `cases=20` to HEAD
  b5819da, whose controls yield 18). Standing: none (packet claims at most `OPEN -> BUILT`).
- qa: seven witnesses, 75 residuals, 51 judgement items; `verify.py` exit 0 on HEAD and tree.

## QA sweep findings

- Every witness found `AGENTS.md` (+12), `decisions/0013`, and `.claude/` outside the handed claim;
  `AGENTS.md` is the root operating contract and no skill owns it.
- Dissent (governance witness): `BYOM.md` calls PROD-I-9 "a freeze candidate"; PRD.md carries that
  label as a document status, not on PROD-I-9. Other witnesses read it as a correct citation.
- Dissent (conformance witness): CLASSIFICATION.md has no Model Binding / Model Adapter entries;
  governance, byom, and verification witnesses cite lines 39-40. Recorded as a seam.
- `receipt.fixtures.json` and PROOF-001 are declarative and unexecuted by the repository's own
  verification (`verify_json_documents` globs `contracts/*.json`; `verify_scenarios` globs only
  `conformance/founding-scenarios/`). Validity observed only with host jsonschema 4.25.1, not a
  declared dependency. Proofing README gate 2 not advanced.
- Asset defeating case proves counteraction by rebuild, not refusal; one witness calls it a policy
  assertion introduced by a test. check_i5 accepts FAILED/UNRESOLVED where PROOF-001 says defeating.
- Vocabulary: `asset.register` is a third event name beside `ingest-asset` and `asset.ingest`;
  SEED / PROPOSED / OWNER_DIRECTED_SEED are undefined fixture labels; PROOF- is a new id namespace.
- CONTRACT-RECEIPT-DEF carries `emitted_record_addresses` with REFUSED (second latent defect);
  both records share `receipt_id r-0001`. No change-protocol note exists in the tree for any edit.
  `lineage/SOURCES.lock` integrity SKIPped in HEAD and tree alike (archive absent).

## Harness defects found by the christening

- (a) Asset in-workflow witness failed on an API safeguards error after two tool calls; workflow
  recorded `witness: null`, "run is unattestable", no retry. Re-witnessed separately.
- (b) byom witness returned `BUILT -> WITNESSED` with spaces; workflow compared `BUILT->WITNESSED`
  and set `standing_proposal: null`. Since fixed in all seven workflows. Strings were inconsistent
  across domains (`OPEN->BUILT`, `OPEN -> BUILT`, `BUILT -> WITNESSED`).
- (c) Parallel dispatch shares one tree: every witness reported a co-mingled green `verify.py` and
  attributed files only by mtime. `sequential: true` has since been added to `sov-federation`.
- (d) Domain workflows launch planned operations concurrently despite declared dependencies:
  CONTRACTS-OP-2 and ASSET-CHRISTEN-2 started in the same millisecond as their prerequisites and
  refused. The contracts witness was handed the planned file list, not the builder's output, and
  dissented against a change the builder never claimed.
- (e) QA handed the full seven-domain change set to each domain witness; all seven swept the whole
  tree, yielding sevenfold overlapping residuals and free-text domain labels.
- (f) Builder and witness summaries carry local absolute and scratchpad paths; they would trip
  `lint.py` if copied into the tree. (g) Operation ids and change-protocol records exist only in
  harness output; the repository holds no trace for a witness to observe.
- (h) `.claude/workflows/sov-baseline.js` and a README section describing it appeared on disk from
  a source other than this controller session. Unattributed harness file; present; not assessed.
- (i) Minor: `rg` absent from the planner's assumed PATH; PowerShell `>` added a BOM to one
  witness's oracle output; the asset observation adapter emits CRLF on Windows stdout.

## Standing proposals (forwarded unedited; ceiling BUILT -> WITNESSED)

governance `BUILT -> WITNESSED`; contracts `OPEN->BUILT` (OP-1 only); conformance `OPEN->BUILT`;
asset re-witness `BUILT->WITNESSED` (CHRISTEN-1 only), in-workflow null; proofing `OPEN -> BUILT`;
byom witness `BUILT -> WITNESSED`, workflow null; verification `OPEN->BUILT`; scribe null.
QA split: governance and proofing witnesses support `BUILT -> WITNESSED` for the STATUS.yaml fix,
bootstrap sync, CONF-I5-GRANT pair, asset test, and receipt fixtures; conformance and contracts
witnesses support only `OPEN -> BUILT` for the asset test and fixtures. No `*_status` changes.

## Residuals and seams

- Seam: verification QA reads the literal 18 in `verify_conformance_controls` as a requirement
  count, not stale; five other witnesses call it a case count drifting from 20.
- Seam: whether the contract fixtures and asset test reach WITNESSED (above).
- Seam: QA saw the O2 packet pre-revision (cases=18), critique-2 post-revision (cases=20 to HEAD).
- All work uncommitted on `main`; commit path undeclared. Pre-existing debt unchanged: `core.py`
  341 lines; `decisions/0009` still cites C1 through C14.

## Judgement queue for Bdo (deduplicated, attributed; nothing decided)

1. [all domains, qa] Does Bdo ratify `decisions/0013` and the AGENTS.md harness section (naming
   `.claude/README.md` as an owner outside the Design System of Record), register it as O13, and
   then add 0013 and `.claude/README.md` to bootstrap REQUIRED, or withdraw the reference?
2. [governance, qa] Which domain owns AGENTS.md, and may an agent-run harness edit it?
3. [all] One christening commit on `main` by explicit instruction, or per-domain branches? Should
   AGENTS.md, STATUS.yaml, and oracle-controls be witnessed as separate operations first?
4. [byom, witnesses] Is parallel shared-tree dispatch acceptable when per-file attribution is lost?
5. [governance] Is `decisions/0012` the authorizing record for C15, or is a dedicated record needed?
   Does Bdo ratify CONTRACT.md C1-C15 (no open-decision entry exists)? Should `verify.py` check
   STATUS.yaml claim labels against CONTRACT.md headings?
6. [verification, contracts] Bring `.claude/**/*.js` under `lint.py`? Add `.gitattributes` for LF?
7. [contracts, byom, asset, proofing] Where do schema-instance fixtures live and who owns them
   (`contracts/fixtures/`, `bindings/fixtures/`, `conformance/`)? Is the field set {id, contract,
   status, polarity, expected_validity, defeats, record} accepted, or reconciled with the oracle's?
8. [contracts, conformance, verification] Does an unconsumed fixture pair satisfy the AGENTS.md
   positive-and-defeating rule, or is a consumer a precondition for BUILT? If gated: dependency-free
   validator in `scripts/`, or a decision-recorded jsonschema dependency?
9. [contracts] Re-queue CONTRACTS-OP-2, or does a README Standing note compete with STATUS.yaml?
10. [contracts, asset, O9] First artifact-standing term `OPEN` or `PROPOSED`? Is `COMPLETED` a
    distinct term or a synonym of `COMMITTED`? Fix a fixture-status vocabulary and the asset docs'
    `ledger` wording before terminology freeze?
11. [contracts, O10] Does `| null` in SPEC.md Receipt mean present-with-null or omittable?
12. [contracts, O4] Keep `attestation` in `uses_kernel_contracts` ahead of O4, or trim it?
13. [contracts] Participant-observation minimum fields: conformance README or the schema?
14. [byom, qa] Canonical asset event name: `ingest-asset`, `asset.ingest`, or `asset.register`?
15. [conformance, O10] Does each SPEC.md predicate bullet need its own fixture pair, making the
    per-requirement coverage gate insufficient for the F2 exit?
16. [conformance, contracts, verification] Should check_i5 require REFUSED and expose `expired`
    apart from `revoked`? Split GRANT-DEF per predicate? Accept the `CONF-I5-GRANT-*` id suffix?
17. [conformance] Which implementation produces the first participant observations and who
    witnesses it? Dedicated PROD-I-4 receipt-coverage check? [O6] Author an UNATTESTABLE
    `make_effective` fixture now or wait? [O8] remains open.
18. [asset re-witness, qa] Should the read-path `source_receipt` gap become a KNOWN-GAPS.md row
    against the SPEC Projection rule, or is rebuild-time purging the intended Phase-I enforcement?
    Does Bdo want write-time refusal with a REFUSED receipt before the asset service as a whole can
    progress toward WITNESSED?
19. [proofing, O11] Is Proofing the accepted second boundary? Do declarative fixtures under
    `services/proofing/conformance/` count toward README gate 2, and is that location sanctioned
    (`services/README.md` lists no `conformance/`)? Is `version_digest` an Asset contract field,
    or does PROOF-001 overreach?
20. [proofing, verification] Who names the implicit-latest `reason_code` (SPEC.md under O10 or the
    proofing contract under O11)? Is non-null `reason_code` on REFUSED accepted? Ratify lifecycle
    OPEN -> IN_REVIEW -> DECISION_PENDING -> CLOSED? Proofing objects into SPEC.md before O10? Is
    omitting `requested-change` and `comparison-request` from `owns` intentional?
21. [byom, contracts, O12] `authority_source`: add to SPEC.md, drop from schema, or OPEN-SEAMS
    entry? Which per-invocation list is exact (BYOM.md 13, PRD 11, FOUND-008 9)? Mode set complete;
    provider_kind x data_boundary rule? Typed meters and `fallback_binding_id`? Ratify FOUND-008
    plus CONF-I9-POS/DEF as the two-model fixture?
22. [byom, qa dissent] May BYOM.md call PROD-I-9 a "freeze candidate"? Add Model Binding / Model
    Adapter to CLASSIFICATION.md or stop citing it? Accept the pointer wording and placement?
23. [verification, scribe, O2] Ratify the ENGINEERING.md baseline? Does O2 cover the five named
    choices or the whole stack table plus composition rules; if declined, defer, replace, or
    strike? Does the evidence-archive SKIP change the weight of self-test evidence? Must `core.py`
    split before ratification or only before new behavior?
24. [governance] O1 (collision screen), O9, O10 remain open; nothing in this run moves them.

## Next bounded operation per domain

- governance: register O13 only after item 1; otherwise prose sweep for "fourteen invariants".
- contracts: re-dispatch CONTRACTS-OP-2 after item 9; then O10 hygiene proposals with defeats.
- conformance: no build until item 15; check_i5 strengthening is an oracle edit awaiting item 16.
- asset: KNOWN-GAPS row or write-time refusal per item 18; else sibling pair for `history-erasure`.
- proofing: PROOF-FIX-002 (undeclared carry), same shape, after item 19 sanctions the location.
- byom: coherence pass over `bindings/README.md`, `adapters/README.md`, decisions/0011; record the
  `authority_source` divergence as a proposal.
- verification: dependency-free parse-check of `contracts/fixtures/*.json` after item 7; marker
  sync for 0013 after item 1.
- scribe: one revision of the O2 packet to clear the HEAD-18 / tree-20 attribution dissent.
- qa: re-run sequentially with domain-scoped claims so each witness sweeps only its own files.
