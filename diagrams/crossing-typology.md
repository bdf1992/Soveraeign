# Crossing typology

```text
source          SPEC.md · CLASSIFICATION.md · PRD.md · CONTRACT.md
source_digest   4ef61f91044a584e · b034a56c7cf90000 · 81f09529b5679d78 · f95acd076c4977d7
reader          hand-authored · v1
fidelity        LOSSY
omissions       the receipt and event-envelope field lists, held by SPEC.md and
                contracts/*.schema.json;
                per-class refusal reason codes beyond the four named below;
                the topology of where each class occurs, held by
                crossing-topology.md;
                federation identity and policy contracts, which do not exist
```

`receipts_for_crossings` is a settled source claim. Which passages count as
crossings, and what each owes, is proposed, so the classes are drawn in pencil.

```mermaid
flowchart TB
    X["<b>Crossing</b><br/>a governed passage between<br/>two custody domains"]

    X --> C1["<b>C1 · Operator</b><br/>human ↔ model<br/>through one record"]
    X --> C2["<b>C2 · Service</b><br/>sibling ↔ sibling<br/>inside one node"]
    X --> C3["<b>C3 · Boundary</b><br/>surface ↔ kernel<br/>node ↔ provider"]
    X --> C4["<b>C4 · Federation</b><br/>node ↔ node"]

    subgraph owes["What every class owes — identically"]
        direction LR
        O1["named<br/>authoritative<br/>source"]
        O2["declared<br/>projection +<br/>omissions"]
        O3["live typed<br/>authority<br/>check"]
        O4["terminal<br/>receipt"]
    end

    C1 --> owes
    C2 --> owes
    C3 --> owes
    C4 --> owes

    classDef pen stroke-width:2px
    classDef pencil stroke-dasharray:5 4,stroke-width:1px
    class X,O1,O2,O3,O4 pen
    class C1,C2,C3,C4 pencil
```

## What it shows

The four classes differ in **what sits on the far side**. They do not differ in
**what the passage owes**. That is the whole claim of this view, and it is why
one typology is worth drawing rather than four unrelated pictures.

A crossing is not merely a call. It is a passage where a fact leaves one
custody domain and arrives in another, and the arrival must be reconstructable
from the record alone. `SPEC.md` gives the `cross` transition exactly one
precondition set — declared source, reader or projection, omissions, authority,
destination — and exactly one commit: a destination record **and** a receipt.

## The four classes

| Class | Traverses | Far side | Phase-I standing |
| --- | --- | --- | --- |
| **C1 · Operator** | one record, two actor kinds | a `HUMAN` or `MODEL` operator | required — `PRD.md` PROD-I-3; no second binding exists |
| **C2 · Service** | a declared service contract | a sibling service in the same node | executes as a package import, not as a declared crossing |
| **C3 · Boundary** | a binding, adapter, worker, or projection | the kernel, or a named external runtime | executes against a local runtime only |
| **C4 · Federation** | a governed node-to-node crossing | a second sovereign node | contracted, no transport, Phase-I non-goal |

`Subsystem` is the generic architectural class and is not a level between
service and component (`CLASSIFICATION.md`). None of these classes creates a
new authority path; each is a passage **through** the kernel, never around it.

## What every crossing owes

Four obligations, and they are the same four in every class:

| Obligation | Where it is fixed | Defeating case |
| --- | --- | --- |
| Name the authoritative source and version | `SPEC.md` `cross` preconditions | the crossing cannot name its source |
| Declare the reader or projection, and its omissions | `SPEC.md` Projection rule | a projected value resolves to nothing |
| Check a live typed, scoped, budgeted grant | `PRD.md` PROD-I-5 | a machine right ratifies judgement |
| Return one terminal receipt | `PRD.md` PROD-I-4 | an unmarked entry is admitted |

The receipt is owed **even when the crossing refuses**. `SPEC.md` is explicit
that a receipt is attributable and addressable on refusal, failure, unresolved
judgement, dissent, and counteraction. A silent crossing is a defect regardless
of class.

## What differs between classes

Only two things, and both are about loss:

**What can be lost.** C1 loses nothing outside the node. C3 is the only class
that can put bytes in front of a third party, which is why it is the only class
carrying a `data_boundary` — `LOCAL_ONLY`, `REDACTED_REMOTE`, or
`REMOTE_ALLOWED` (`SPEC.md` `ModelBinding`). C4 would be the second such class
if it existed.

**What survives the far side vanishing.** `PRD.md` PROD-I-9 requires that
provider loss leaves authoritative custody and non-model local operation
intact. That obligation lands entirely on C3. C1 and C2 have no far side to
lose — both are inside one node, and losing the node is not a crossing failure.

## Pencil, and why

Every class is still dashed, but not for the reasons it was when this view was
first drawn. Each class now has code on at least one end, and none of them is a
declared crossing end to end.

C1 has a model binding and no human-facing binding: `bindings/console/interface.json`
declares one and holds no code, so the two actor kinds have never met in one
record. `services/asset/conformance/BASELINE.md` records `PROD-I-3` failing for
exactly that reason.

C2 executes. `services/console/` imports `soveraeign_record_service` directly and
reads the journal through it. That is a Python import, not a passage through a
declared service contract — which is the gap `services/gateway/CHARTER.md` was
chartered to close. A crossing that works by importing the far side has no place
to check authority and no place to leave a receipt.

C3 executes too. `adapters/ollama/invoke.py` runs a model against the local
runtime, applies the binding's declared omissions before sending, and grades the
outcome from the runtime's own `done_reason`. Its data boundary is `LOCAL_ONLY`;
no bytes have ever gone in front of a third party, so the class's distinguishing
risk is contracted and untested.

C4 is contracted with no transport (`STATUS.yaml`,
`federation_crossing_status: PROPOSED_CONTRACT_BUILT_SELF_TESTED_NO_TRANSPORT`),
a Phase-I non-goal, and a `ROADMAP.md` deferral.

The four obligations are drawn in pen. They are downstream of settled source
claims — `receipts_for_crossings`, `typed_scoped_revocable_authority`,
`evidence_does_not_grant_authority` — not of any proposed class boundary. A
future class would inherit them unchanged; that is the point of fixing them
once here.
