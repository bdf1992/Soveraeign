# 0088 — The model fills the form; a person saves it

Status: `PROPOSED · BDO HAS NOT RULED`
Date: 2026-08-27
Seat: `seat:session-control`
Extends `decisions/0086-automation-switch-controls.md`, which built the controls this
puts a sentence in front of. First use of `adapters/ollama` by anything but its own
tests.

## What was asked

Bdo, looking at the console: "I also need a communication service here so we can request
edit in natural language." Alongside it, a question about storage — whether the
declarations should come from a database, and which service is ready for that.

## Rulings

**1. The declarations stay as committed JSON files, and that is not a performance
decision.** Seven files of about a kilobyte cost microseconds to read; SQLite would be
slower and would add a projection to keep in sync. What it would cost is the property
the rest of this design rests on: the declarations are committed, so git diffs them, a
clone carries them, and a switch flip is a one-line diff a reviewer can read. The change
log is a committed file for the same reason.

The run history is the half that should move. `.local/schedules/ledger.ndjson` is
gitignored machine-local state and the Record Service already owns an append-preserving
journal. `services/automation/KNOWN-GAPS.md` names this as "the schedule lift" and names
what it waits on: a `SYSTEM` principal, a verified identity, a live grant, and the
Capability Broker (epic `#15`). None of those is code this concern could write. The
Automation Service boundary is acceptance packet A7, presented and not accepted.

**2. The model proposes and never writes.** A model that could call
`automation.update_schedule` would walk straight through the authority split
`decisions/0086` exists to state. So the operation is `automation.propose_edit`: it reads
a declaration, asks what a sentence means to change, checks the answer, and hands back a
proposal that fills the form. A person reads what moved and clicks save, and the save is
a separate request with its own grant check.

This is not caution about model quality. It is the same shape the switch already has,
where a model operator holding no seat gets a recorded proposal rather than an effect.
The proposal is data and holds no callable; a test asserts that rather than trusting it.

**3. `enabled` and `name` never reach the model, and are refused if they come back.** The
declaration the prompt quotes is filtered to the editable fields, so the model is not
shown the switch. If it proposes `enabled` anyway — case `P-002` — that is `NOT_EDITABLE`
and the field never reaches the form. Without this, a model could arm a schedule by
proposing it into a form the owner then saves, which routes around the authority by
making the owner the one who clicks.

**4. Local model, `LOCAL_ONLY`, no fallback.** The invocation goes through
`adapters/ollama` and its declared binding. No bytes reach a third party, so this is not
the `EXTERNAL_WORLD` effect Phase I refuses, and it costs Bdo's own hardware rather than
API spend. An unreachable model is `MODEL_UNAVAILABLE`; substituting another model or
provider is forbidden and does not happen. Every answer is shown with the model that
produced it, the seconds it took, and the boundary it ran under — an unattributed
suggestion is the thing this avoids.

**5. What the model gets wrong is bounded by what is checked afterwards.** A field
outside the editable set, a value of the wrong kind, and an unparseable answer are
refusals. Prose wrapping and code fences are tolerated, because models do that however
they are asked not to and refusing it would make the feature useless while proving
nothing — what is inside the braces is still checked strictly. The worst outcome is a
proposal a person reads and rejects.

**6. A partial nested object is completed before anyone sees it.** Asked to raise a
budget, the real model answered `{"limits": {"max_budget_usd": 8}}`, which read literally
drops `timeout_seconds`. The schema requires both, so applying it would have been refused
and rolled back — safe, but the person asked to change one number and would have read a
schema complaint. Case `P-008` is that first real answer.

## Defaults taken

- `qwen3:4b` is the default binding. It answered correctly on every request tried and
  takes six to sixteen seconds. `gpt-oss:20b` is also bound and available.
- The ask box lives in the row that is already open, not at the top of the page.
- The proposal highlights the fields it changed rather than saving and showing a diff
  afterwards, so the review happens before the write and not after it.

## What this does not do

It does not write, commit, arm, or run anything. It does not reach any network beyond
`127.0.0.1`. It does not create schedules — only edits to one that exists — because a
creation is mostly a name and a target and the form asks for those directly.

## Residuals

`scripts/sovschedule/intent.py` bootstraps `sys.path` to import `adapters/ollama`, which
`AGENTS.md` forbids in production code. The adapter is not packaged and its modules are
not importable by project path. The alternative was a second, undeclared model crossing,
which is worse; the fix is packaging the adapter, and this is named rather than left for
a reader to find.

A proposal names its model, its time, and its boundary, and it is still a suggestion from
a four-billion-parameter model on a desktop. Nobody has measured how often it is right.
The surface shows the fields it changed rather than applying them, which is the answer to
not knowing.

The tests never invoke a model. Its output is not deterministic and pinning it would be
pinning a model's mood; what is pinned is the boundary around it. So nothing here proves
the model is useful — only that a wrong answer cannot become a write.

## What still waits on Bdo

1. Whether a local model in the console is a boundary he wants crossed at all. It is
   `LOCAL_ONLY` and costs only his own hardware, and it is still a model in the loop of
   an operating surface.
2. The storage question above: whether the Automation Service lift is worth unblocking,
   which means epic `#15` and packet A7, not this concern.
3. `earn_it` on `conformance/assessments/automation-switch.json`, still `OPEN`. This
   makes the case for `SUBSTANTIVE` stronger and does not settle it.

## Standing

`PROPOSED`. The tests establish `BUILT` and witness nothing. Independent observation is
owed for everything in `decisions/0086` and this record too.
