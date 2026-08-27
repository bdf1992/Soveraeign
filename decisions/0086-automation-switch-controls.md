# 0086 — Controls you can reach, and an authority you cannot reach around

Status: `PROPOSED · BDO HAS NOT RULED`
Date: 2026-08-27
Seat: `seat:session-control`
Extends `decisions/0083-automation-health-read.md`, which built the read this puts
controls on. Extends `decisions/0015-scheduled-runs.md`, which declared the schedules.

## What was true before this

`decisions/0083` landed a read-only health surface: a command, a rendered page under
`docs/`, nine health rules in a contract, and a fixture corpus defeating them. The
ticket that opened that work said step two — switching — waited on Bdo saying the read
was right, and gave the reason: a switch over a read you have not confirmed is how you
end up able to change things you cannot see.

Bdo looked at the page and said it needs controls. That is his call and it is product
intent, which is the one kind of thing this repository has never let a participant
settle. This record does not relitigate the sequencing; it records what was built when
he asked for it, and what the building had to decide.

## Rulings

**1. Controls on a page require a process, so this adds HTTP over loopback.** A file
opened from disk has nothing behind it to write with. `AGENTS.md` and `ENGINEERING.md`
both say HTTP waits for a conformance case that requires it, and the owner requiring a
page with working switches is that case. It is written into
`conformance/fixtures/automation-control/` and `scripts/tests/test_automation_control.py`
rather than asserted here.

The listening socket binds `127.0.0.1` and `build_server` refuses any other address
rather than trusting a flag — the refusal lives in the module that opens the socket,
because a configuration that says loopback and a socket that binds elsewhere is exactly
the gap worth closing where it can actually be closed. A token is minted per run and
printed once, so a page you happen to be visiting cannot post into your console. That
is origin separation, not authentication, and the contract says so.

Effect class is `RESOURCE_CONSUMPTION`: a process on the owner's machine. Nothing
crosses a data boundary and no third party is reachable, so this is not the
`EXTERNAL_WORLD` effect Phase I refuses. Reading it as one would be wrong in the
direction of uselessness; reading a socket bound to `0.0.0.0` as this would be wrong in
the direction that matters, which is why that one refuses.

**2. One operation, two bindings, and the authority check inside the operation.** The
page's button and the command line both call `control.set_switch` and nothing else. A
control merely hidden from a page is not an authority check — the command line reaches
the same function, and so does anything that imports the module. The test that matters
drives a model actor through both bindings and requires the same recorded proposal from
each.

**3. The two directions are not symmetric, and typing them the same would be the
mistake.** Arming a schedule commits tokens and wall clock that will be spent with
nobody watching. That is `RESOURCE_COMMITMENT`, one of the seven reasons
`contracts/acceptance-policy.json` admits for holding something on the owner, and Bdo
had already reserved it for himself in the ticket. Switching one off consumes nothing,
reverses in a keystroke, and reduces effect; `AGENTS.md` refuses a request for
permission to do reversible record-local work by name.

So: a model operator may switch a schedule off and may only propose arming one. The
proposal is recorded and the switch does not move. A surface that made an operator wait
for the owner before switching something off would be unusable during the exact
incident it exists for, and a surface that let a model arm one would let any session on
this box spend the owner's money while he slept.

**4. Refused attempts are recorded, and the no-op is not.** Every path through the
operation appends one line to `.claude/schedules/change-log.ndjson`, including the
refusals, because a log of only what succeeded cannot answer the question an operator
asks after an incident, which is who tried. The exception is setting a switch to the
state it already holds: that writes nothing and records nothing, because two operators
clicking the same button is one transition. Reporting it as `EFFECTED` would make the
record claim a change that never happened, so it is its own outcome, `UNCHANGED`.

**5. The log is committed; the run ledger stays local.** A run is a local event and its
ledger is gitignored. A switch is a decision about the repository, and if its provenance
lived under `.local/` then cloning this repository would produce a node whose
automations are armed with no record of who armed them.

**6. The static page keeps no buttons.** `docs/automation.html` renders with controls
off and says where the working ones are. A button that silently does nothing is worse
than no button, and the staleness check from `decisions/0083` still grades a file the
console never serves — a running console does not move the committed bytes, which is a
test rather than a claim.

**7. Creating and editing are the same authority question as arming.** Bdo asked next
for the definitions themselves to be editable, which opens two holes that would have made
the switch rule theatre. A model that may not arm `nightly-qa` can create `nightly-qa-2`
with `enabled: true`; or it can leave an armed schedule's switch alone and repoint it at
a different workflow, or raise its budget. Both commit the owner's resources by another
route.

One sentence closes both, and it is the sentence already there: a change to what runs
unattended is the owner's. So creating a declaration already armed needs the owner, and
editing an armed one needs the owner. Creating a switched-off declaration and editing a
switched-off one are reversible record-local work and need nobody. Switching it off
first is the route, and anyone may do that. Cases `D-002` and `D-008`.

`name` and `enabled` are not editable through that path. `name` is the file stem, so
changing it creates a second declaration and removes this one, which is not an edit.
`enabled` has its own operation, because two doors to one transition means two authority
checks to keep in step and one of them will drift.

**8. A form must not be able to write a document the runner would refuse.** The operation
writes the declaration, asks the ordinary loader to load it, and reports the loader's own
complaint — one opinion about validity rather than two that drift. A rejected write is
rolled back to the exact prior bytes: bytes rather than a re-serialised equivalent,
because rewriting through a text write normalises line endings and a rollback on this
host would silently convert a CRLF file to LF while reporting it changed nothing. The
target dropdown is read off `.claude/` the same way the loader's target check reads it,
so it cannot offer something the save refuses.

Deleting a declaration is not offered. An uncommitted one has no copy anywhere and the
operator who typed it is the only thing that ever knew it existed. Switching it off is
the reversible answer.

**9. The declaration diff is one line.** The operation patches the `enabled` line and
verifies the result by re-parsing rather than reserialising the document, because these
declarations are hand-written and hold formatting `json.dumps` does not reproduce. A
switch that reformatted the whole file would bury its own changed field in a diff nobody
reviews.

## Defaults taken

- One log for all three changes, `.claude/schedules/change-log.ndjson`, rather than one
  per operation. An operator asking what happened to a schedule should read one file, not
  merge two by timestamp.
- The log lives beside the declarations rather than in a new service. Moving both onto
  Console surface 3 is one move; the seam is `history.py` plus `changelog.py`.
- The command line records a model actor unless `--as-owner` is passed, because a session
  running the CLI is not Bdo and must not be able to arm a schedule by claiming to be.
- The console opens a browser on start. `--no-open` turns it off.
- The port defaults to 0, so the OS picks a free one and two consoles do not collide.

## What this does not do

It does not run anything, register anything with the Windows scheduler, or bring an
occurrence forward. It does not commit: a flipped switch sits in the working tree until
someone lands it. It does not authenticate — anyone at this machine is the owner as far
as the console can tell, and the record says that rather than naming a person. And it
arms nothing: every declaration on this node still reads `enabled: false`, because
arming one is Bdo's and he has not done it.

## Residuals

The console cannot tell operators apart. A switch flipped and never committed is a
decision this repository loses on the next clean checkout. The page and the command can
disagree, because the served page reads the working tree and the committed page reads
`HEAD`; both say which. And `armed` is not `running`: nothing on this node ticks a
schedule, so a reader who takes a switch reading `on` as evidence that something is
happening would be wrong.

The AI-native reading is `conformance/assessments/automation-switch.json`. It scores
`FULL` on reachability and commitment, `PARTIAL` on provenance and retraction, and its
`earn_it` judgement is `OPEN` — which caps the verdict regardless of the arithmetic,
because whether a model path here is substantive or an accessory beside the real control
surface is a human judgement and it is Bdo's. Four of the nine Soveraeign checks are
`UNPROVEN` or `PARTIAL` and are left visible.

## What still waits on Bdo

1. `earn_it`: is the model path to this operation substantive, or an accessory beside
   the page? `OPEN` is not a favourable result and only he closes it.
2. Whether adding HTTP, even bound to loopback, is a boundary he wants crossed in Phase
   I. The alternative was a page whose buttons do nothing, which he rejected.
3. What you meant by "create with a list of services, adapters, and connections". A
   schedule says *when* to run one workflow or skill, with what arguments and under what
   budget. It does not compose services — that is what the workflow itself does, and a
   workflow is JavaScript. The form creates schedules over things that already exist. If
   what you want is to define the composed thing from a surface, that is a separate and
   much larger concern and nothing here starts it.
4. Arming any schedule. That was his before this work and it still is; what changed is
   that there is now a control for it and a record of it.

## Standing

`PROPOSED`. The tests establish `BUILT` and witness nothing. The corpus caught one real
defect during construction that no reading had found: a schedule whose workflow file had
been deleted could not be switched off, because loading the declaration failed on the
missing target before the switch logic ran — so the surface trapped on exactly the
schedule an operator most needs to stop. `require_target` on the loader is the repair and
`C-012` is the case that holds it.

Independent observation is owed and not held. The observation on `decisions/0083` covers
commit `11c3f1a` and nothing in this record.
