# Crossing topology

```text
source          SPEC.md · services/console/CHARTER.md · STATUS.yaml ·
                CONTRACT.md
source_digest   108497d370c0fd8d · 7dec971f8b6d04d8 · c141d6f181709311 · 896e59ba90828ad7
reader          hand-authored · v1
fidelity        LOSSY
omissions       the class definitions and shared obligations, held by
                crossing-typology.md;
                service internals and component structure, held by service-map.md;
                transition preconditions and reason codes, held by SPEC.md;
                every requirement predicate's positive and defeating fixture pair
```

Which crossings exist, and where. The classes `C1`–`C4` are fixed in
`crossing-typology.md`; this view places them. No edge here is built on both
ends, so every crossing is drawn in pencil.

```mermaid
flowchart TB
    subgraph nd["Soveraeign Node — personal profile"]
        direction TB

        subgraph surf["Operator surfaces"]
            direction LR
            HB["Human Binding"]
            MB["Model Binding"]
        end

        REC["<b>one record</b><br/>one thread, both actor kinds<br/>attributed posts"]
        K["<b>Shared kernel</b><br/>gates · typed authority · transitions<br/>observation · settlement · receipts"]

        subgraph svc["Sibling services"]
            direction LR
            A["<b>Asset</b><br/>built, not witnessed"]
            RC["<b>Record</b><br/>built, not witnessed"]
            C["<b>Console</b><br/>continuity path built"]
            P["<b>Proofing</b><br/>chartered"]
        end

        W["Workers<br/><i>report, never settle</i>"]
        PJ["Projections<br/><i>rebuildable, never authoritative</i>"]
    end

    MA["Model Adapter<br/><i>data_boundary gate</i>"]
    PV["Provider runtime<br/>LOCAL or REMOTE"]
    N2["Second node"]

    HB   -- "C1" --> REC
    MB   -- "C1" --> REC
    REC          --> K
    A    --> K
    RC   --> K
    P    --> K
    C    --> K
    K    --> W
    W    -. "C3 · report only" .-> K
    K    --> PJ
    PJ   -. "C3 · edits return<br/>as proposals" .-> K
    C    -- "C2 · reads the journal<br/>by package import" --> RC
    C    -. "C2 · reads events<br/>and receipts" .-> A
    C    -. "C2" .-> P
    P    -. "C2 · pins versions" .-> A
    MB   -- "C3" --> MA
    MA   -. "refuses on<br/>boundary violation" .-> PV
    nd   -. "C4 · deferred" .-> N2

    classDef pen stroke-width:2px
    classDef pencil stroke-dasharray:5 4,stroke-width:1px
    class K,REC,A,RC pen
    class HB,MB,P,C,W,PJ,MA,PV,N2 pencil
```

## What it shows

Every arrow reaching authoritative state passes **through** the kernel. That is
`CONTRACT.md` C1, and on this canvas it is the only structural rule that holds
without exception: no binding, adapter, worker, projection, or sibling service
has an edge that reaches around it. A surface that bypasses the kernel fails
Phase I outright (`PRD.md`, binding parity).

Three edges are drawn dotted **back** toward the kernel rather than into it,
and the direction is the point:

- a worker **reports**; independent observation and kernel settlement decide
  whether the run committed;
- a projection-originated edit **returns as a proposal**, it is not a write;
- an adapter that fails its data boundary **refuses**, and the refusal carries
  a receipt like any other terminal outcome.

C1 is the only class where two edges land on the same object. A human post and
a model post in one thread are one crossing through one record
(`services/console/CHARTER.md`), which is exactly what `PRD.md` PROD-I-3 asks
for: a fact deposited by one is retrieved and used by the other, with origin and
projection visible, and the crossing returns a receipt.

## Where the far side is a third party

Only `C3` egress leaves the node. `MB → MA → PV` is the sole path on this
canvas that can put bytes in front of someone else, and it is the only path
carrying a `data_boundary` — `LOCAL_ONLY`, `REDACTED_REMOTE`, or
`REMOTE_ALLOWED`.

Two obligations land there and nowhere else. Provider loss must leave
authoritative custody and non-model local operation intact, so `PV` vanishing
may not disturb anything inside the node boundary. And fallback to another
model is never silent — an `EXPLICIT` fallback requires a **new** attributed
invocation and receipt naming the replacement binding (`SPEC.md`
`ModelBinding`).

`C4` is drawn from the node boundary rather than from any component inside it.
A federation crossing is between nodes, not between a service here and a
service there. It is a Phase-I non-goal and stays a stub until
`ENGINEERING.md`'s growth trigger fires — two nodes actually needing to exchange
governed records, at which point identity, policy, and receipt contracts are
owed before the edge is drawn solid.

## Pencil, and why

`Asset`, `Record`, the kernel, and the shared record are pen, and even that is
generous: `STATUS.yaml` records both services as
`BUILT_SELF_TESTED_NOT_WITNESSED`, and built is not witnessed.

One crossing edge is now solid. `Console → Record` is the only passage on this
canvas with a live reader and a live writer: `services/console/` imports
`soveraeign_record_service` and reads the journal through it. It is drawn solid
because it runs, and it is the edge that should worry a reader most — a package
import has no place to check a grant and no place to leave a receipt, so a
crossing that owes four obligations is currently paying none of them. Closing
that is what `services/gateway/CHARTER.md` exists for.

Every other edge is still dashed, but the reasons have changed. `C3` egress has
run: `adapters/ollama/invoke.py` executes a model against the local runtime. Its
data boundary is `LOCAL_ONLY`, so `PV` has never been a third party and the risk
this class exists to govern is contracted and untested. `C1` has no human-facing
binding — `bindings/console/interface.json` declares one and holds no code — so
the two actor kinds have never met in one record. Proofing is a charter.
Federation is contracted with no transport.

## Open

The conformance oracle grades `C1` against the reference participant, and
`services/asset/conformance/BASELINE.md` records the result: `PROD-I-3` fails
because no second binding exists and the crossing does not declare its source,
version, projection, omissions, or destination. That is a participant gap, not
an unbound oracle. No crossing on this canvas has yet been performed by two
materially different bindings, which is what `C1` ultimately owes.
