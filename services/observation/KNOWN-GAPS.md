# Observation Service Reference Gaps

Observed differences between the chartered boundary and what exists. Five of the eight declared
operations run; every row below is either a remaining gap or a default taken while building the
thin slice, so the next reader can overturn it rather than inherit it.

Standing under `decisions/0041-the-observation-service.md`.

## Remaining gaps

| Gap | Observed behavior | Required behavior | Contract |
| --- | --- | --- | --- |
| Three operations | `list-pending-observations`, `counter-observation`, and `attest-observation` are declared, `PROPOSED`, and have no code | The full loop the charter describes, including countering an observation later shown wrong | `contracts/service.json` |
| Direct-edge set | Five edges implemented in `relation.py`; the set is still proposed, not agreed | Bdo named the rule, not the edge set; a missing edge is a way past the check | `decisions/0041`, Ruling 2 |
| Receipt ownership | The service records its own receipts in memory, one per attempt | Either that, or a `terminal-receipt` in the Record Service journal. Four services own a private receipt type and nothing says how they relate to the journal's | `contracts/receipt.schema.json`; `services/record/contracts/service.json` |
| Durable state | Requests, declarations, inferences, observations, and receipts live in the `ObservationService` instance | A projection over the journal or a service-owned store the Record Service can reconstruct. In-memory is enough to prove the semantics and nothing more | `AGENTS.md` State and execution |
| Repository verification | The MCP surface appends an `OBSERVATION` for `scripts/verify.py` | Either a declared operation of this service, or explicitly not an observation of this kind | `bindings/mcp/manifest.json`, `observe_verify` |
| The existing observer script | `scripts/witness_observe.py` still computes digests and predicates outside this boundary | The same work behind `observe-run`, or a stated reason it belongs in scripts | `AGENTS.md` Directory boundaries |
| Settlement | Nothing settles a run anywhere. `tests/test_kernel_parity.py` proves the kernel would accept this service's observation for `settle_run`; no participant performs the transition | `settle_run` consuming a satisfactory observation and refusing `OBSERVATION_MISSING` without one | `SPEC.md` Transition contract |
| Capability map says ACTIVE | `contracts/fixtures/capability-map.reference.json` marks the five built operations `ACTIVE` at `observation:in-process`, and `scripts/sovnode/composition.py` routes no such address. The Record Service shares the pattern | A declaration something measures: either a composed route or a map that says `DECLARED` until one exists | `contracts/capability-offices.json` |
| Two-binding proof | No binding drives this service; the tests call it in-process | A human binding and a model binding passing the same fixtures | PROD-I-3; `AI-NATIVE.md` check 7 |
| Independent observation of itself | Three witness passes by a participant that did not build it observed the thin slice through its declared surface (`witness/observation-service.md`, commit 3087714). No run of this service, or of any service, has been observed by the operations it declares | An observation of a run, made through `observe-run`, by an observer this service inferred independent | C7; the recursion is real and unresolved at the run level |

## Defaults taken while building the thin slice

Reversible choices. Each names where it lives so it can be overturned in one place.

- **Terminal means no longer in flight, and settlement is not required.** `record.py` reads
  a run as terminal once the executor has written `REPORTED` or a terminal receipt refused or
  settled it. `settle_run` needs the observation this service produces, so settlement cannot
  be a precondition; a settled run may still be observed later, which is what
  `counter-observation` exists for. The manifest's `run_terminal` precondition is read this way.
- **A reported, unsettled run is requested as `UNRESOLVED`.** `request-observation` records
  the run's terminal receipt outcome when one exists. When only a report exists, it writes
  `UNRESOLVED`, the one terminal word in the request schema that claims nothing was decided,
  rather than reading the executor's report as `COMMITTED`. Whether the schema should instead
  carry a word for "reported, not settled" is a question for the contract's owner.
- **The record is four payload events.** `ATTEMPTED`, `REPORTED`, `OUTPUT`, and `GRANT` on
  Record Service journal entries are the whole input. A key absent from the attempt payload
  (`lease`, `grant_id`) is unanswerable; a null value is an answer. That is the line between
  `UNDETERMINED` and `INDEPENDENT`.
- **A found edge outranks an unanswerable one.** A record showing the candidate executed the run
  reads `DIRECT` even when another edge could not be examined. Only a record that found nothing
  and could not answer everything reads `UNDETERMINED`. Both refuse; the precedence keeps the
  refusal's name honest (`relation.py`).
- **A candidate whose grant is not in the record is undetermined** when the run itself ran under
  a grant. The walk cannot say whether the candidate's authority descends from the run's, so it
  does not say.
- **Three predicate kinds.** `BYTES_PRESENT`, `DIGEST_EQUALS`, and `JSON_FIELD_EQUALS`, each
  over an address the run reported as durable output. A predicate naming any other address,
  including the report entry, is refused `PREDICATES_UNDECLARED`. This is the smallest language
  that is evaluable without the executor's report; it is not a claim that it is the right one.
- **Predicates are declared before the looking by clock.** `declared_at` must precede
  `observed_at`; the clock is injected and never read from the host.
- **Every attempt leaves exactly one receipt**, admitted or refused, naming the manifest's reason
  code. This is the invariant issue #173 lists first among its defeating cases.
- **A terminal run that reported nothing durable refuses `INCOMPLETE_PROPOSAL`.** The request
  schema requires at least one durable output address, so the proposal is incomplete; the
  manifest declares no better word. Whether it should (witness judgement item J4) is the
  contract owner's.

## Residuals the third witness pass left open

Recorded at 3087714 rather than repaired, so the witnessed bytes stayed the witnessed bytes.
Repaired on 2026-09-05 on the branch, each with the case that fails without its repair. The
bytes a witness observed are therefore no longer the current bytes: `observation_service_status`
reads `WITNESSED` for commit 3087714, and the current code owes a fresh pass.

- R10: an `OUTPUT` entry with no actor now refuses `UNREADABLE` from `malformed()`, because
  an output with no producer leaves `PRODUCED_THE_OUTPUT` unanswerable while looking answered
  (`test_an_output_with_no_producer_is_unreadable`).
- R11: `observe_run` reads `malformed()` on the record it is handed, so a malformed
  substituted record refuses `UNREADABLE` (`test_observe_run_reads_the_record_it_is_handed`).
  A well-formed substituted record is R14's case, below.
- R12: the report-standing, observation-standing, discovery id/inputs shape, settlement
  receipt, discovery-interface, and binding-field rules are pinned one at a time in
  `conformance/tests/test_kernel_predicates.py`. Pass 4 found the first set was the one this
  page had transcribed at 3087714, not pass 3's; the two discovery rules it named are now pinned.
- R13: `test_the_run_id_itself_is_not_a_predicate_address` now reports the run id as an output
  with an `OUTPUT` entry standing on it, so only the own-entry guard refuses; reverting the
  guard fails the case.

## Residuals the fourth witness pass left open

Pass 4 (commit `f8a755f`, `witness/observation-service.md`) re-supported `WITNESSED` on the
repaired bytes and left these for the builder.

- R14, repaired 2026-09-05 and closing F8 from pass 1: an inference now carries
  `record_digest`, sha256 over every entry digest of the record it read, required by
  `relation-inference.schema.json`. `observe_run` recomputes it from the record it is handed and
  refuses `RELATION_UNDETERMINED` when they differ, so a substituted record refuses whether or
  not it is well formed (`WitnessResidualsOnF8a755f`, three cases: the sound path, the observer
  as a second attempter, the observer as the output's producer). The bytes a witness observed
  moved again; the current code owes a fifth pass.
- J5 (a finding about a check, held for the owner): `scripts/sov_standing.py` reads
  `standing_supported` from the first witness block and reads neither the recorded revision nor
  the tree, so it read `SUPPORTED` while every receipt for the subject was `STALE_SUBJECT`.
  The measurement exists in `sov_witness_layer.py records`, which grades staleness as debt.
- `STATUS.yaml` and `contracts/status-claims.json` still cite `3087714` as the witnessed
  commit; pass 4 supports `f8a755f`. Moving a standing citation is the owner's document.

## Where this sits against the AI-native bar

Not yet scored. The assessment record is owed now that `request-observation` and `observe-run`
execute; it was not written in the same change that built them, because the assessment is a
reading someone other than the builder should take. Worth stating: this is the service that
would move check 3 off `UNATTESTABLE` for every other service in the repository, and it has
not done so yet, because being witnessed as code is not the same as observing a run.
