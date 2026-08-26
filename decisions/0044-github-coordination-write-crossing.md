# 0044 · The registrar gains a write half, and the standing axis absorbs the witness axis

Status: `PROPOSED · BDO HAS NOT RULED`

Bdo directed the crossing after the board was surveyed on 2026-08-24: "It's just
a logged crossing, that rule should be updated with the crossing type." This
record covers that update and the label refinement it was asked for in the same
breath.

## What was actually wrong

The label catalogue in `.github/labels.yml` was a design document that never
reached the surface it described. Measured against `bdf1992/Soveraeign`:

| Reading | Count |
| --- | --- |
| Declared labels wearing GitHub's default grey `#ededed` with no description | 25 of 38 |
| Declared labels that do not exist on GitHub at all | 11 |
| GitHub stock labels present and worn by no Soveraeign issue | 10 |
| Duplicated declarations inside `labels.yml` itself | 11 |
| Native containment edges on GitHub, against 48 declared in metadata | 0 |
| `requires` edges declared in metadata and visible on the surface | 197 declared, 0 visible |

`scripts/sov_ticket.py labels` reported no drift throughout, and was right to:
it compares which labels an issue wears against the projection, and every issue
wore the correct set. Nothing in the repository compared the labels' *colour and
description* against the catalogue, and nothing compared GitHub's relationship
graph against the containment tree. The board could be exactly as declared in
the one dimension we checked and unreadable in every dimension we did not.

The cause is structural rather than clerical. `adapters/github/README.md`
declared one crossing, `LOCAL_READ_ONLY`, so there was no lawful path from a
declaration to the surface. Every correction was a hand edit in a browser, which
is why none of them happened.

## Ruling 1 — the registrar declares two crossings

`COORDINATION_CAPTURE` (`export.py`) is unchanged and stays `RECORD_LOCAL`.
`COORDINATION_WRITE` (`apply.py`) is new, is `EXTERNAL_WORLD`, and is bounded by
what it may carry rather than by trust in its caller.

Its data-boundary mode is `DECLARED_PROJECTION_OUTBOUND`: a value may cross only
if it is already derivable from `.github/labels.yml`, `contracts/ticket-label-projection.json`,
or the issue's own metadata block. That is the whole safety argument. The plan is
computed offline in `adapters/github/plan.py` from the export alone, so a fresh
witness regenerates it without touching the network, and an action nobody
declared is a `REGISTRAR_REFUSED` rather than an improvisation.

Three further limits, each enforced in code rather than asked for in prose:

- Writing is opt-in. Without `--apply` the tool prints the plan and exits zero.
- A body is edited only between `<!-- sov:relations:begin -->` and its closing
  delimiter. Every other byte, the contract block above all, is preserved.
  Applying the same plan twice changes nothing the second time.
- A label is deleted only if `labels.yml` names it in a `retire:` entry. A live
  label nobody declared is left alone: deleting what no one declared is not the
  adapter's call.

Before rewriting bodies the run snapshots every current body to
`.local/registrar/bodies-before/`, and it writes `apply.receipt.json` naming the
crossing, the operator, the source export, every action, and each outcome. A
body rewrite is reversible from that snapshot. A label deletion is not, which is
why deletion is the one verb gated on an explicit declaration.

The crossing settles nothing. It writes labels, containment edges, and a
rendered block. It cannot open, close, comment on, assign, or milestone an
issue, and it writes no standing, ratification, or settlement in any form.

**What would defeat this ruling:** an `apply.py` run whose effect is not
derivable from the local declarations at the export's digest; a body rewrite
that changes a byte outside the delimiters; a second run that is not a no-op; or
a label deletion the catalogue never declared.

## Ruling 2 — one standing axis, not two

The `witness:` axis is retired. It encoded the artifact lifecycle a second time,
so a ticket needed two labels to say one thing:

| Old pair | Meaning | Now |
| --- | --- | --- |
| `standing: self-tested` + `witness: pending` | built, witness outstanding | `standing: self-tested` |
| (no standing label) + `witness: witnessed` | independently witnessed | `standing: witnessed` |
| (no standing label) + `witness: demoted` | demoted by a defeating observation | `standing: demoted` |

Worse, `standing: self-tested` and `witness: witnessed` were both `#2DA44E`: the
same green for "we tested it ourselves" and "someone else verified it," which is
the exact distinction `AGENTS.md` exists to hold. That is now amber and green.

`standing_to_label` covers all eight declared values and each projects to at
most one label. `RATIFIED` gains a label for the first time; a ratified ticket
previously looked identical to one opened a minute ago, so the terminal rung of
`OPEN -> BUILT -> WITNESSED -> RATIFIED` was invisible on the board.

The ramp is monotone in how much evidence stands behind the claim, so the board
reads as a lifecycle rather than a palette:

| Label | Colour | Evidence standing behind it |
| --- | --- | --- |
| (none) | — | `OPEN`; the default, omitted like `effect: record-local` |
| `standing: proposed` | `#D4C5F9` | a proposal, nothing built |
| `standing: declared` | `#B6BBC0` | a boundary declared, implementation not begun |
| `standing: chartered` | `#54AEFF` | a contract or charter, implementation incomplete |
| `standing: self-tested` | `#D29922` | built and self-tested; witness outstanding |
| `standing: witnessed` | `#2DA44E` | an independent witness receipt, current and resolvable |
| `standing: ratified` | `#116329` | Bdo accepted the evidenced result |
| `standing: demoted` | `#CF222E` | a fall off the ramp, not a rung on it |

`witness:` stays listed in `unprojected_label_prefixes` and is named in the new
`retired_label_prefixes`, so a surviving `witness:` label reads as drift rather
than passing unseen.

Migration cost was four closed issues (#53 through #56), the only tickets that
wore a `witness:` label. `witness: pending` and `witness: witnessed` were worn
by none.

**What would defeat this ruling:** a standing value that projects to two labels
or to none; a `witness:` label reappearing on the surface without reading as
drift; or a case where the retired axis carried a distinction the ramp cannot.

## Ruling 3 — containment goes native, the dependency DAG stays rendered

`CONTRIBUTING.md` already said containment is the only native relationship and
that `requires` and `parent_bits` never enter GitHub's single-parent tree. That
policy was right and simply unexecuted. It is now executed rather than amended.

Containment becomes real GitHub sub-issues, from `child_issues` on the epic and
`village_issue` on every bit and stub — not `parent`, which the schema lets a
bit point at the epic while its village is the node that contains it. GitHub
permits one parent, so an issue the epic places is never placed again.

The dependency DAG stays metadata-authoritative and gains a rendered block:
`requires`, `parent_bits`, `leans_on`, `asks`, and `holds` as plain issue links,
so GitHub's backlink graph shows them and a reader sees them without parsing
YAML. No closing keyword is used anywhere in the block, because a stub cannot
close its bit by itself.

**What would defeat this ruling:** a containment edge on the surface that no
`village_issue` or `child_issues` entry derives; a rendered block that a reader
can edit into a second authority the metadata does not carry; or a stub closing
its bit because the rendering made GitHub do it.

## What changed

- `.github/labels.yml`: the duplicated eleven-label block removed; `standing:
  witnessed`, `standing: ratified`, and `standing: demoted` added; `standing:
  self-tested` recoloured amber; a `retire:` section added naming the three
  `witness:` labels and ten GitHub stock labels.
- `contracts/ticket-label-projection.json`: `standing_to_label` covers all eight
  values, `standing_to_witness_label` is gone, `retired_label_prefixes` added.
- `scripts/sovticket/labels.py`: the second standing projection removed.
- `adapters/github/catalogue.py`: new, 170 lines. Plans the label surface: the
  catalogue diff and the per-issue label diff, which are different questions.
- `adapters/github/plan.py`: new, 222 lines. Plans the relationship surface:
  containment edges and the rendered block. Both derive everything offline.
- `adapters/github/apply.py`: new, 239 lines. Performs a plan and receipts it.
- `adapters/github/export.py`: captures the label catalogue to a `.labels.json`
  sidecar, so an unworn label no longer reads as absent, and captures GitHub's
  native containment graph, so the plan can report what would actually change.
- `scripts/tests/test_github_apply_plan.py`: 27 cases. `scripts/tests/test_sov_ticket_labels.py`:
  three added, including that a surviving `witness:` label reads as drift.
- `CONTRIBUTING.md` and `adapters/github/README.md` updated alongside, as that
  section requires when label axes or the containment rule change.

## Ruling 4 — the module budget reaches the rest of the production tree

`scripts/lint.py` measured module size only under `scripts/` and packaged `src/`
trees. `adapters/`, `bindings/`, `workers/`, and `conformance/` were unmeasured,
which is how this session's own planner reached 351 lines without the gate
noticing. `PRODUCTION_ROOTS` now covers all of them, and test directories are
excluded rather than counted.

Widening surfaced one existing overrun, `conformance/run.py` at 332 lines. It is
entered as named debt, not fixed: another session holds that file, and the
overrun was already observed in `reports/2026-08-23-stack-certification.md`. The
budget had simply never reached it. Entering it records the debt; the comment
above `KNOWN_MODULE_DEBT` is explicit that entry is not grandfathering.

**What would defeat this ruling:** a production module outside `PRODUCTION_ROOTS`
and outside a `src/` tree; or a debt entry that outlives the split it names.

## Residual

The `retire:` list is a one-way instruction with no positive case proving a
deletion is safe to repeat. Deleting a label that is already gone is a no-op on
GitHub, so the risk is bounded, but the fixture corpus does not cover it.

`sov_ticket.py labels` still checks only which labels an issue wears. Colour and
description drift is caught by `apply.py --only labels` printing a non-empty
plan, which is a tool nobody runs on a schedule. Whether that check belongs in
the ticket-contract workflow's `board` job is open.

Issues #51 and #52 carry no metadata block and no labels, and are the only two
tickets failing `sov_ticket.py validate`. They are the charting-experiment
sidecar pair. Writing a block for them means choosing a kind, village, horizon,
and standing, which is product judgement rather than a projection, so they were
left as they stand and reported rather than invented.

`conformance/run.py` fails the module budget and is carried as named debt. It is
the conformance domain's to split.

## What still waits on Bdo

- Whether to accept the write half at all. It mutates a public repository, so
  every write is an irreversible external effect however narrowly it is gated,
  and direction to add a crossing type is not acceptance of this shape of it.
- Which coordination surface survives. `decisions/0057-board-management-role.md`
  landed on `main` nineteen hours before this record was written, declaring its
  own write path; the claim above that no lawful path existed was true when the
  branch was cut and false by the time it was committed. Both define
  `adapters/github/apply.py` and neither is a superset: `0057-board-management-role.md` writes branch-ref
  deletion, this one writes containment relations and issue bodies. The label
  catalogues differ by 120 lines. Accepting both would admit two write paths to
  one surface.
- A kind, village, horizon, and standing for issues #51 and #52, which is the
  product judgement this record declined to invent.
- Whether the label colour and description drift check belongs in the
  ticket-contract workflow's `board` job, or stays a tool run by hand.
