# Diagrams

Status: `PROVISIONAL · DERIVED PROJECTION · NO STANDING`

Diagrams-as-code views of the governing corpus. Every file here is a
rebuildable projection under the `SPEC.md` Projection rule: each projected
value resolves to an authoritative source record, and each file declares what
it omitted.

Nothing here holds standing. A diagram is a `LOSSY` reading of a document that
already says the thing. Where a diagram and its source disagree, the source
wins and the diagram is stale.

## Pencil and pen

Most of the corpus is still pencil. `CONTRACT.md`, `SPEC.md`, and
`CLASSIFICATION.md` are proposed; `PRD.md` is a freeze candidate. A diagram
that renders proposed vocabulary the same as settled claim misleads every
reader who was not in the room, so the distinction is drawn, not described.

| Rendering | Meaning |
| --- | --- |
| Solid outline | Settled claim, or a service with an implementation |
| Dashed outline | Proposed, chartered-not-built, or blocked on an open `O` decision |

Carried by `classDef pen` and `classDef pencil` in every diagram. The
convention is deliberately theme-neutral — dash pattern and stroke weight, no
fills — so it survives light and dark rendering on GitHub and in any other
Mermaid host.

## Provenance header

Every file opens with the `Recording` fields from `SPEC.md`, so a stale diagram
is detectable rather than merely suspected:

```text
source          the authoritative file this view reads
source_digest   sha256 prefix of that file at authoring time
reader          who or what produced the view, and its version
fidelity        EXACT | LOSSY  (a diagram is always LOSSY)
omissions       what this view dropped to stay legible
```

A digest that no longer matches its source means the diagram is stale. That
check belongs in `scripts/lint.py` once these views are generated rather than
authored; until then it is a manual read.

## Files

| File | Reads | Why it exists |
| --- | --- | --- |
| `source-reader-recording.md` | `SPEC.md`, `CONTRACT.md` C2 | The substrate move prose is worst at |
| `standing-transition.md` | `CLASSIFICATION.md`, `CONTRACT.md` C4, C9 | Keeps `COUNTERED` out of the standing chain |
| `service-map.md` | `CLASSIFICATION.md`, `STATUS.yaml` | Which services exist, which are drawn in pencil |
| `authority-typing.md` | `PRD.md` PROD-I-5, `CONTRACT.md` C3, C5 | Who may ratify what, and what evidence cannot do |
| `requirement-lifecycle.md` | `PRD.md` requirement lifecycle | Why a build report is not a witness |
| `event-outcomes.md` | `CLASSIFICATION.md`, `SPEC.md` Effects | Outcome and effect class are separate axes |
| `crossing-typology.md` | `SPEC.md` `cross`, `CLASSIFICATION.md` | The four crossing classes, and the obligations all four share |
| `crossing-topology.md` | `SPEC.md`, `services/console/CHARTER.md` | Where each crossing class actually occurs inside the node |

## Corpus-wide omissions

These views drop, everywhere and on purpose:

- full field lists for information objects — `SPEC.md` holds those;
- exact schema shapes — `contracts/*.schema.json` holds those;
- historical source addresses and digests — `lineage/` holds those and is
  unpublished under `PUBLICATION.md`;
- every requirement predicate's positive and defeating fixture pair.

## Standing of this directory

Authored by hand as a first pass, from published canonical documents only. No
generator exists yet, so these views enter as proposals under `CONTRACT.md` C11
and claim no authority. Their permanent home, whether they belong to a chartered
projection boundary, and whether a generator is admitted are open questions for
Bdo.
