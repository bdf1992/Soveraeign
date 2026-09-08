# Observation Service Reference Gaps

Observed differences between the chartered boundary and what exists. Five of the eight declared
operations run; every row below is either a remaining gap or a default taken while building the
thin slice, so the next reader can overturn it rather than inherit it.

Standing under `decisions/0041-the-observation-service.md`.

## Remaining gaps

| Gap | Observed behavior | Required behavior | Contract |
| --- | --- | --- | --- |
| Three operations | `list-pending-observations`, `counter-observation`, and `attest-observation` are declared, `PROPOSED`, and have no code | The full loop the charter describes, including countering an observation later shown wrong | `contracts/service.json` |
| Direct-edge set | Seven edges implemented in `relation.py` across two axes, context and perspective. Bdo settled the axes and the retirement of grant-descent on 2026-09-07; the edge set itself is still a proposal at `PROPOSED` standing | The set agreed rather than proposed. A missing edge is still a way past the check, and both new context edges read a launcher's declaration where they could not measure | `decisions/0104`; `decisions/0041`, Ruling 2 |
| Out-of-band context | `CONSTRUCTION_CONTEXT_INHERITED` reads what the launcher declared it passed. A launcher that declares a thin context and hands the rest over a shared working tree, an undeclared file, or a prompt the record does not hold reads as independent | A measured context rather than a declared one. The present cross-check is weaker: an observation citing addresses beyond its declared context is evidence the declaration was false, and nothing computes that comparison yet | `decisions/0104`, What would defeat this ruling |
| A witness cannot file its own record | `scripts/sovdocs/facets.py` classifies `witness/*.md` into the documentation corpus, so a new witness record makes `sov_docs check` report the page stale and turns `verify.py` red. Repairing that means regenerating `docs/documentation.html`, which a witness is not permitted to edit. The first pass over the seven-edge walk proved this, removed its file, and its record was filed by the builder instead | Either a witness that can leave its record without breaking the gate, or a page build that does not depend on a witness's own output. Custody of a witness record filed by the party it grades is weaker than one the witness wrote | `witness/independence-context-perspective.md`, filing note; `decisions/0100` |
| Lifecycle walk cost | `PRIOR_STANDING_ACTOR` reads every standing arrow on the subject. At `WITNESSED -> RATIFIED` on a long-lived subject that is every actor that ever moved it | A bound, or evidence that the walk stays small. Unmeasured | `decisions/0104`, Residuals |
| Receipt ownership | The service records its own receipts in memory, one per attempt | Either that, or a `terminal-receipt` in the Record Service journal. Four services own a private receipt type and nothing says how they relate to the journal's | `contracts/receipt.schema.json`; `services/record/contracts/service.json` |
| Durable state | Requests, declarations, inferences, observations, and receipts live in the `ObservationService` instance | A projection over the journal or a service-owned store the Record Service can reconstruct. In-memory is enough to prove the semantics and nothing more | `AGENTS.md` State and execution |
| Repository verification | The MCP surface appends an `OBSERVATION` for `scripts/verify.py` | Either a declared operation of this service, or explicitly not an observation of this kind | `bindings/mcp/manifest.json`, `observe_verify` |
| The existing observer script | `scripts/witness_observe.py` still computes digests and predicates outside this boundary | The same work behind `observe-run`, or a stated reason it belongs in scripts | `AGENTS.md` Directory boundaries |
| Settlement | Nothing settles a run anywhere. `tests/test_kernel_parity.py` proves the kernel would accept this service's observation for `settle_run`; no participant performs the transition | `settle_run` consuming a satisfactory observation and refusing `OBSERVATION_MISSING` without one | `SPEC.md` Transition contract |
| Capability map says ACTIVE | `contracts/fixtures/capability-map.reference.json` marks the five built operations `ACTIVE` at `observation:in-process`, and `scripts/sovnode/composition.py` routes no such address. The Record Service shares the pattern | A declaration something measures: either a composed route or a map that says `DECLARED` until one exists | `contracts/capability-offices.json` |
| Two-binding proof | No binding drives this service; the tests call it in-process | A human binding and a model binding passing the same fixtures | PROD-I-3; `AI-NATIVE.md` check 7 |
| Independent observation of itself | Three witness passes by a participant that did not build it observed the thin slice at commit 3087714 (`witness/observation-service.md`). They read the five-edge walk `decisions/0104` replaced, so they no longer cover the enforcement surface and `STATUS.yaml` is demoted accordingly. No run of this service, or of any service, has been observed by the operations it declares | An observation of the seven-edge walk by a participant that did not build it, and beyond that an observation of a run made through `observe-run` by an observer this service inferred independent | C7; the recursion is real and unresolved at the run level |

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

Recorded rather than repaired, so the witnessed bytes at 3087714 stay the witnessed bytes.

- R10: an `OUTPUT` entry with no actor is not on the run subject, so `malformed()` does not
  refuse it and its producer edge cannot be answered; it should read `UNREADABLE`.
- R11: `observe_run` does not call `malformed()` itself; it relies on the inference having done
  so, which a substituted record could bypass.
- R12: three oracle rules (`kernel_predicates.py` report standing, discovery id/inputs shape,
  and settlement receipt) are not yet pinned one at a time in `test_kernel_predicates.py`.
- R13: the own-entry regression test passes with the repair reverted; it needs a case that
  fails without the guard.

## Where this sits against the AI-native bar

Not yet scored. The assessment record is owed now that `request-observation` and `observe-run`
execute; it was not written in the same change that built them, because the assessment is a
reading someone other than the builder should take. Worth stating: this is the service that
would move check 3 off `UNATTESTABLE` for every other service in the repository, and it has
not done so yet, because being witnessed as code is not the same as observing a run.
