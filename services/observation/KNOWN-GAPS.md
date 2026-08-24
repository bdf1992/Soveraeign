# Observation Service Reference Gaps

Observed differences between the chartered boundary and what exists. The service is
`PROPOSED`: a charter, a manifest with ten declared operations, and nothing that runs. Every
row is a gap by construction, not a regression.

Standing under `decisions/0041-the-observation-service.md`.

| Gap | Observed behavior | Required behavior | Contract |
| --- | --- | --- | --- |
| The whole service | Ten operations declared; none implemented | The path from `request-observation` to a recorded observation or a named refusal | `CHARTER.md`; `contracts/service.json` |
| Independence test | Undefined. Nothing says what makes an observer independent of an executor | A stated, checkable relation — different process, actor, grant chain, or stronger | `SPEC.md` `observer_relation`; `AI-NATIVE.md` check 3 |
| Observation and attestation contracts | `contracts/observation.schema.json` exists at the kernel; no service contract or fixtures do | Positive and defeating fixtures for each declared operation | `AGENTS.md` Implementation order |
| Receipt ownership | The manifest owns `observation-receipt` | Either that, or a `terminal-receipt` in the Record Service journal. Four services now own a private receipt type and nothing says how they relate to the journal's | `contracts/receipt.schema.json`; `services/record/contracts/service.json` |
| Predicate language | `declare-predicates` names a precondition that predicates be evaluable without the executor's report; nothing expresses or checks a predicate | A declared predicate form the service can evaluate against durable outputs | `SPEC.md` `predicate_results` |
| The existing observer script | `scripts/witness_observe.py` computes digests and predicates outside any service boundary | The same work behind a declared operation, or a stated reason it belongs in scripts | `AGENTS.md` Directory boundaries |
| Repository verification | The MCP surface appends an `OBSERVATION` for `scripts/verify.py` | Either a declared operation of this service, or explicitly not an observation of this kind | `bindings/mcp/manifest.json`, `observe_verify` |
| Settlement | Nothing settles a run anywhere | `settle_run` consuming a satisfactory observation and refusing `OBSERVATION_MISSING` without one | `SPEC.md` Transition contract |
| Two-binding proof | No binding drives this service | A human binding and a model binding passing the same fixtures | PROD-I-3; `AI-NATIVE.md` check 7 |
| Independent observation of itself | None. The service that owns observation is observed by nothing | An observer independent of this service's builder | C7; the recursion is real and unresolved |

## Where this sits against the AI-native bar

Not scored. There is no implementation to score, and recording `PARTIAL` anywhere would claim
observable evidence that does not exist. The assessment record is owed once
`request-observation` and `observe-run` execute.

Worth stating: this is the service that would move check 3 off `UNATTESTABLE` for every other
service in the repository. It is also the service most exposed to the recursion in the last
row — whatever observes the observer cannot be the observer, and nothing in the charter solves
that. The honest position is that the first observation of this service is Red work by a
different agent, not a self-test.
