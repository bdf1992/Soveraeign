# Narrative Layer

Status: proposed projection. Holds no standing, routes nothing, owns no issue.

`tree.json` is the technical map of the epic-of-epics (`#1`): villages, bits,
stubs, `requires` edges. This file is the same 49 issues told a second way:
by where an actor meets the system (**front office**) and by what holds
that meeting up (**back office**). `villages.json` still routes dispatch;
`offices.json` carries this grouping in machine shape.

Use this layer to talk about what an actor walks in wanting, which
counter they go to, what that counter quietly leans on, and what they leave
holding. Use `tree.json` when you need to know what is blocked on what.

Exact terms stay exact. Every story ends with a **Today** line read from the
tree (`ready` / `held` / `unrouted`) and the repository snapshot in
`CLAUDE.md`. Nothing below is `WITNESSED` or `RATIFIED`; that is the accurate
reading of a founding-phase node, not a shortfall.

## The cast

A story's teller is named in the kernel's own terms: an `actor_kind`
(`HUMAN`, `MODEL`, `WORKER`, `SYSTEM`, from `SPEC.md`) holding a
participation or boundary `role` from `CLASSIFICATION.md`. No word here is
new; the table only says who shows up at a counter.

| Teller | `actor_kind` / `role` | Who they are |
| --- | --- | --- |
| **Human operator** | `HUMAN` / `operator` | A person working inside the node through a Human Binding. |
| **Model operator** | `MODEL` / `operator` | A model working inside the node through a Model Binding. Sov when the portable profile is loaded; Claude in an interactive session. Same world, same record. |
| **Agent** | `HUMAN` or `MODEL` / `agent` | An operator selecting or requesting actions within granted authority. |
| **Worker** | `WORKER` / `worker` | Leased hands. One job per lease. Reports; never settles its own work. |
| **Witness** | `HUMAN` or `MODEL` / `witness` | Independent eyes. Observes through a path the builder did not control. |
| **External system** | `SYSTEM` / `operator` | An enterprise system or remote provider reached through a declared adapter. It has no expectations of its own; its story is told on its behalf by the operator who integrated it. |
| **Peer node** | `SYSTEM` / `node` | A second Soveraeign Node on the far side of a federation crossing. Horizon (`#24`), not Phase I. |

**Owner is not in the table.** Owner is the context Bdo walks up in, not a
role Bdo holds: it sets which Binding Bdo comes through and which Projection
Bdo sees, over whatever role Bdo is holding at that moment. Bdo at the
Operator Desk is a `HUMAN` / `operator`; Owner is what shapes the desk for
them, the way the Sov profile shapes a model's seat. On a ticket it travels
in `authority`, never in `role`. The Console charter already calls its
realized form operator settings and dashboard projections.

## The shape of a story

A story is told from the actor's side of the counter: what they
expected, where the floor was not there, and what they ask of the ground
underneath. The scenario says what the system promised; the story says what
the actor found; the gap is the ask.

Filed stories use `kind: story` (`CONTRIBUTING.md`, decision 0022). The
prose in this file and any story added to it use the same lines, in the
ticket's own field names:

```text
Teller:        actor_kind / role, from the cast
Counter:       the front-office bit the teller walks up to (parent)
Expected:      what they expected to be able to do, in their words
Found:         where the realization fell short
Leans on:      the back-office supports the crossing cannot work without
Asks:          what the substrate should do differently, addressed to the
               issue that owns it
Scenario:      the conformance/scenarios.json id that walks it, once bound
Today:         what the tree and the working tree actually say
```

The walk reads each filed story as **told** (no scenario), **walkable**
(bound, every support at least `BUILT`), or **walked** (`WITNESSED`). A
story is never taken as work; its asks point at the bits and stubs that are.
The counter stories below are composite and predate the kind. The first
filed story is `#67` at the Operator Desk (told, `HUMAN` / `operator`), and
its first finding is that the desk itself has no bit in the tree - the
Console is a charter and a closing stub, not an owned obligation. That
containment defect stands as a queued judgement, not a bug.

---

## Front office: where actors meet the system

### The Operator Desk: `#30`, `#45`

**Who walks in:** a human operator or a model operator.
**What they want:** to sit down in the node and work: see what is going on,
talk in threads, be told when something needs them, and ask the owner for a
call when one is needed.
**Counter:** Operator bindings (`#30`) prove a human and a model get the same
desk: same record, same authority, same history. The Sov profile (`#45`) is
the model operator's seat at that desk. The Console Service owns the desk
itself: sessions, threads, posts, notifications, judgement requests, operator
settings, dashboard projections.
**Leans on:** The Record (`#6`, `#7`), The Permits Office (`#11`, `#12`,
`#13`), The Model Counter (`#19`, `#29`), The Inspectorate (`#23`, `#26`),
The Door (`#16`).
**What they leave with:** one attributable event per consequential thing
they did, and a judgement request that lands on the owner's desk instead of
being decided for them.
**Today:** the Console boundary and its name are accepted; the service is not
built. The Sov profile validates and its fixtures pass; it is accepted as the
operating shape and is not live. `#30` is `held` on nine issues, `#45` on two.
The story is fully told (`services/console/CHARTER.md`, `SOV.md`); no actor can
walk it, because the contract and its defeating fixtures do not exist yet.

### The Door: `#16`, `#17`

**Who walks in:** an external system, a remote operator, or later a peer
node.
**What they want:** to get something in, get something out, or have a
message carried, and to be told plainly when the answer is no.
**Counter:** The Gateway Service (`#16`) is governed ingress and egress: who
may cross, in which data-boundary mode, with what exact projection of the
input. The Relay Service (`#17`) carries messages once they are inside.
**Leans on:** The Permits Office (`#11`, `#12`, `#13`, `#14`, `#15`), The
Record (`#6`, `#7`).
**What they leave with:** a receipt for the crossing, including the
refusals. Silent fallback is forbidden, so a closed door is a recorded door.
**Today:** nothing is built and no harness domain claims either issue;
both are `unrouted`. This is on purpose for now: `no_external_effects_in_phase_i`
stands, so the Door is locked and the story is about what the lock looks like.

### The Model Counter: `#19`, `#29`

**Who walks in:** an owner or operator bringing a model; a team connecting an
enterprise system.
**What they want:** to plug in their own model or their own system and have
it treated as an operator, not as an authority.
**Counter:** Bindings and Adapters (`#19`) declare the interface on the
inside; Adapters (`#29`) translate to the named thing on the outside. BYOM is
the practice, not a service. No provider SDK type passes the counter.
**Leans on:** The Permits Office (`#13`, `#14`, `#15`), The Door (`#16`),
The Job Window (`#18`), The Record (`#25`).
**What they leave with:** a declared binding with a data-boundary mode, and a
receipt for every call, with only an opaque credential reference on it.
**Today:** the binding contract exists (`contracts/model-binding.schema.json`)
and two scenarios wait for it (`006`, `008`). The binding contract is
accepted; the kernel has no `invoke_model` implementation (PROD-I-9), and the
Ollama adapter grades declared bindings against a recorded inventory rather than
executing one. Nothing waits on the owner here. `#19` and `#29` are `held`.

### The Job Window: `#18`, `#20`, `#21`, `#31`

**Who walks in:** an operator with work to hand in; later, a schedule with
nobody present.
**What they want:** the work done by someone else, and to know whether it
actually landed rather than whether somebody said it did.
**Counter:** an operation plan goes in. Runtime and Workers (`#18`) lease it
to a worker (`#31`); the worker reports; a witness observes; the kernel
settles. The Workflow Service (`#20`) strings operations together and keeps
them; the Automation Service (`#21`) lets schedules and machine triggers open
the window unattended.
**Leans on:** The Record (`#6`, `#7`), The Permits Office (`#13`, `#14`),
The Door (`#17`), The Inspectorate (`#9`).
**What they leave with:** first a report, clearly labelled as the worker's
own word; then a settlement, which is someone else's.
**Today:** this story already runs, but in the harness, not in the product.
Controller, Orchestrator, Worker, and Witness exist as `.claude/` plumbing;
thirteen workflows and a scheduled-run tick exist; every shipped schedule is
disabled. There is no kernel-level append-preserving journal to settle into
(PROD-I-8). All four issues are `unrouted`.

### The Review Desk: `#22`, `#28`

**Who walks in:** an operator who needs a decision on a specific version of
something.
**What they want:** a review that cannot drift: annotations pinned to exact
asset versions, rounds that close, and a decision that stays attached to what
was actually looked at.
**Counter:** The Proofing Service (`#22`) owns sessions, rounds,
version-pinned annotations, and the decision lifecycle; `#28` is its
reference participant.
**Leans on:** The Record (`#8`, `#10`), The Permits Office (`#11`, `#12`,
`#13`, `#14`), The Job Window (`#18`, `#20`), The Model Counter (`#19`).
**What they leave with:** a decision record pinned to the versions reviewed.
**Today:** the boundary is accepted and the service is not built
(`services/proofing/CHARTER.md`, two schemas, a defeating fixture). What is
missing is the contract and its fixtures, not permission. `#22` is
`held` on ten issues. The longest "Leans on" line in the front office: this
desk opens last.

### The Drafting Window: `#42`, `#50`

**Who walks in:** an operator who wants to see and shape the map of who can do
what.
**What they want:** to look at charts and skill forests, configure a view,
and not accidentally change what anything means.
**Counter:** Chart compiler bindings (`#42`) lower a governed chart into a
human or model operator environment; the Skill graph UI projection (`#50`)
shows the forest without owning it.
**Leans on:** The Pattern Room (`#40`, `#41`, `#47`), The Permits Office
(`#14`), The Door (`#16`), The Model Counter (`#19`), The Operator Desk
(`#30`), The Inspectorate (`#49`).
**What they leave with:** a view. Projections are rebuildable and never
become authoritative by convenience.
**Today:** the newest and least settled line. Both issues are `unrouted`; the
experimental QA sidecar (`#51`) is closed and its cleanup (`#52`) waits on an
ownership decision (`#47`); a RED engagement (`#57`) is open against the
foundation underneath. Nothing to walk yet.

---

## Back office: what holds the counters up

### The Record: `#6`, `#7`, `#8`, `#10`, `#25`, `#27`

What it does for the front: every counter writes here and nothing is ever
erased; a correction is written under the original. The Shared Kernel (`#6`)
says which moves are legal; the System of Record (`#7`) keeps the
append-preserving history; the Asset Service (`#8`, `#27`) turns bytes into
governed identities with version history; the Graph Service (`#10`) keeps the
typed map of entities, assets, and operations; shared contracts (`#25`)
validate every boundary record.

**Today:** `#6` is the one `ready` issue in the whole tree, and everything
else queues behind it. The Asset Service is built and self-tested, not
witnessed. Six kernel schemas exist; `contracts/kernel-transitions.json` is in
the working tree, uncommitted. No kernel journal (PROD-I-8).

### The Permits Office: `#11`, `#12`, `#13`, `#14`, `#15`

What it does for the front: says who is standing at the counter (Identity,
`#11`), what they are allowed to do right now (Authority, `#12`), refuses at
every consequential boundary (Security and Gates, `#13`), knows what exists
and which version (Registry, `#14`), and hands machines short-lived,
attenuated tokens (Capability Broker, `#15`).

**Today:** the office is half-built and half-undomained. Identity (`#11`) and
Registry (`#14`) route to the `trust` domain on the artifacts already in
`services/identity/` and `services/registry/`, and both are `held` behind the
Asset Service (`#8`). Authority (`#12`), Security and Gates (`#13`), and the
Capability Broker (`#15`) have no artifact and stay `unrouted`. This is still
the widest gap between front and back: every counter's "Leans on" line passes
through here, and no counter can know who is standing at it.

### The Inspectorate: `#9`, `#23`, `#26`, `#32`, `#49`, `#57`

What it does for the front: the independent eyes that turn a report into an
observation. Observation and Attestation (`#9`); the conformance harness
binding observations to defeating fixtures (`#26`); Phase-I Qualification,
the full human/model crossing (`#23`); the Day-0 engineering harness (`#32`);
the Capability resolution witness (`#49`); and the first RED engagement
(`#57`). A build cannot witness itself anywhere in this file.

**Today:** the oracle is executable with 20 controlled cases and every
defeating fixture fails as declared; `scripts/verify.py` passes in about
1.3 s. Participant binding is still open. Nothing in the repository is
`WITNESSED` yet.

### The Ground: `#37`, `#39`

What it does for the front: the place the node physically lives. A
reproducible local custody ground (`#37`) first; a bridge from that node to a
customer-owned Kubernetes topology (`#39`) later.

**Today:** both `unrouted`. The node runs as local process calls and a CLI;
that is the baseline, not a gap.

### The Pattern Room: `#40`, `#41`, `#47`, `#48`

What it does for the front: the typed map of competence that The Drafting
Window shows. The Charting contract (`#40`), the Skill and capability graph
(`#41`), where skill declarations canonically live (`#47`), and the relation
schema that validates them (`#48`).

**Today:** `#40` `held`, the rest `unrouted`; `#57` is actively trying to
defeat this room. Under adversarial review by design.

### Beyond the Node: `#24`

What it does for the front: the Door's far side. Two sovereign nodes, one
governed crossing.

**Today:** horizon. Requires Qualification (`#23`) and most of The Permits
Office. Not Phase I.

---

## Outside both offices

- `#1` to `#5`: the epic and its four villages. Structure, not a counter.
- `#52`: housekeeping; remove the experimental sidecar after `#47` decides.
- `#51`, `#53` to `#56`: closed. Noise in the tree, nothing in the story.

## What the two layers say together

Read front to back, the queue has one shape: every counter leans on The
Permits Office, The Permits Office leans on The Record, and The Record
starts at `#6`. The technical tree says this as "two ready, fourteen held,
twenty unrouted". The narrative says it as: nobody can be told who they
are yet, so no counter can open; the ledger has to exist before the permits
office can, and the ledger's first page is the kernel's list of legal moves.

## Decisions this layer queues for the owner

None of these are decided here.

1. **Where the layer lives.** It sits under `.claude/epic/` as a projection
   beside `villages.json`. If Bdo wants it to carry standing, it moves out of
   `.claude/` and into the governing set, and `AGENTS.md` says which document
   owns it.
2. **Office assignment of the ambiguous issues.** The Job Window (`#18`,
   `#20`, `#21`, `#31`) could be read as back office; it was placed front
   because an actor hands work in there. The Review Desk is front for
   the same reason. Either could be moved.
3. **The story kind itself.** `kind: story` is accepted
   (`decisions/0022-story-ticket-kind.md`, ruled by
   `decisions/0033-close-the-founding-docket.md`). It is defeated by a story
   that dispatches work, or by an Owner reading that needs a new role value in
   `CLASSIFICATION.md`.
4. **The rest of the Permits Office.** Identity and Registry now route to the
   `trust` domain on the artifacts under `services/identity/` and
   `services/registry/`. Authority (`#12`), Security and Gates (`#13`), and the
   Capability Broker (`#15`) have no such artifact, so they stay `unrouted`.
   That is not a decision queued here: writing the charter, contract, or tests
   that would evidence a domain is ordinary work at this tier, and this item is
   listed only because the office it describes is half-covered.

## How to add a story

Pick one teller and one counter. Say what they expected and where it
fell short before saying what to change; an ask with no `found` behind it is
a feature request wearing a story's clothes. List only the supports the
crossing genuinely cannot work without, and address each ask to the issue
that owns the substrate. Write the **Today** line from
`python scripts/sov_epic.py status` plus the working tree, never from
memory. File it as `kind: story` with the counter as `parent`; do not give
it a `requires` edge. Add any new counter or support to one office in
`offices.json`, never two.
