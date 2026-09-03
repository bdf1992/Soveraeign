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
| Two-binding proof | No binding drives this service; the tests call it in-process | A human binding and a model binding passing the same fixtures | PROD-I-3; `AI-NATIVE.md` check 7 |
| Independent observation of itself | None. The service that owns observation has been observed by nothing but its own tests | An observer independent of this service's builder | C7; the recursion is real and unresolved |

## Defaults taken while building the thin slice

Reversible choices. Each names where it lives so it can be overturned in one place.

- **Terminal means reported or refused, not settled.** `record.py` reads a run as terminal once
  the executor has written `REPORTED` or a terminal receipt refused the run. `settle_run` needs
  the observation this service produces, so a run could never be observed if terminal meant
  settled. The manifest's `run_terminal` precondition is read this way.
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

## Where this sits against the AI-native bar

Not yet scored. The assessment record is owed now that `request-observation` and `observe-run`
execute; it was not written in the same change that built them, because the assessment is a
reading someone other than the builder should take. Worth stating: this is the service that
would move check 3 off `UNATTESTABLE` for every other service in the repository, and the honest
position is unchanged: the first observation of this service is Red work by a different agent,
not a self-test.
