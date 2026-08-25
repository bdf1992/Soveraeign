# Requirement lifecycle

```text
source          PRD.md · SPEC.md · CONTRACT.md · STATUS.yaml
source_digest   f1157f2f1ebad6aa · 108497d370c0fd8d · 896e59ba90828ad7 · c141d6f181709311
reader          hand-authored · v1
fidelity        LOSSY
omissions       the nine PROD-I requirement texts and their defeating cases;
                per-requirement current standing, which STATUS.yaml does not
                yet record requirement by requirement
```

```mermaid
flowchart LR
    O["<b>OPEN</b>"]
    B["<b>BUILT</b><br/>implementation claim"]
    W["<b>WITNESSED</b><br/>independent evidence"]
    R["<b>RATIFIED</b><br/>declared right"]

    O -- "positive and defeating<br/>fixture for every<br/>normative predicate" --> B
    B -- "independent run,<br/>different actor" --> W
    W -- "Bdo's recorded decision" --> R

    SELF["Builder's own<br/>success report"]
    SELF -- "cannot advance a requirement — C7" --x W

    classDef pen stroke-width:2px
    classDef pencil stroke-dasharray:5 4,stroke-width:1px
    class O,B,W,R,SELF pen
```

## What it shows

`BUILT` is a claim, not a result. Passing self-authored unit tests gets a
requirement to `BUILT` and no further. `WITNESSED` needs an independent run;
`RATIFIED` needs the declared right. No agent advances a requirement on its own
report.

The blocked arrow is `CONTRACT.md` C7 — an executor's success report is not
evidence that the world changed. Settlement uses an observer that can inspect
world state without relying on the executor's account. In this repository's
harness that is enforced structurally: the agent that builds and the agent that
witnesses are never the same agent.

## Where the work actually sits

`STATUS.yaml` records `asset_service_status`, `record_service_status`,
`local_model_adapter_status`, `service_manifest_contract_status`,
`coordination_registrar_status`, and `lineage_corpus_status` all as
`BUILT_SELF_TESTED_NOT_WITNESSED`. Six claims parked at exactly the
`BUILT → WITNESSED` seam, which is the seam this diagram exists to make
unmissable. Nothing in this repository has reached `WITNESSED`.

Phase I exits only when every normative predicate has both fixtures, the
applicable fixtures run through **one human-facing binding and two materially
different model bindings** — three in total, not two — independent observation
can reconstruct the receipts, open judgement calls are visible, and Bdo ratifies
operational acceptance (`PRD.md`, Phase-I exit).
