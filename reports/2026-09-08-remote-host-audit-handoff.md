# Remote host audit handoff, 2026-09-08

Written for a fresh agent picking this up on Bdo's Windows workstation, and for
the root seat. The session that produced it ran in the Claude Code web container
and could not finish the diagnostic that matters most, because that host refused
to spawn the process the experiment needs.

Nothing here ratifies anything. Standing is marked per finding, and the
distinction that carried the whole audit is kept throughout: **a file on disk is
not a loaded configuration, and a missing effect is not a proven non-invocation.**

## Read this before you act

You are almost certainly in a different environment from the one that made these
findings. Every environment-scoped claim below is tagged with where it was
observed. Do not carry a `remote-linux-container` finding onto the workstation
without re-observing it.

| | remote container (where this was found) | workstation (where you probably are) |
| --- | --- | --- |
| Working directory at start | `/home/user`, **above** the repository | expected to be the repository root |
| Settings passed to the CLI | `--settings /root/.claude/launcher-settings.json` | expected: normal hierarchy, no flag |
| Repositories | four, via `--add-dir` multi-root | expected: one |
| `PowerShell` tool | absent | present, and `&&` / `||` do not chain |
| Local `main` | frozen at the image-build commit | expected to track normally |
| Project hooks | produced no observable effect | **unknown — this is the open question** |

## The one thing to check first

**No session in the remote container registers itself, and the repository's own
session-hygiene layer produced no observable effect there.**

Established: `.git/sov-sessions/sessions.ndjson` held two records, both from the
image build at `13:41:57/58`, and none after the container booted at `21:01:02`,
despite ~14 Bash calls that each reach `_ensure_registered`. No hook-typed
attachment appears anywhere in the session transcript. `sov_session.py console`
reported `principal: unidentified` and no register event.

Not established, and do not let anyone shorten this: **why**. Three causes all
produce that identical record, because every project hook runs inside
`except BaseException: pass` and exits 0.

- **H-cwd** — settings discovery is anchored to the working directory, which was
  one level above the repository, so `.claude/settings.json` never entered the
  effective configuration.
- **H-settings-flag** — `--settings <file>` displaces the project settings
  hierarchy. Confounded with H-cwd: both were true of every launch.
- **H-fail** — hooks were invoked and died silently on import.

**H-unsupported is excluded.** The launcher's own log shows it runs
`claude --init-only` per repository with cwd set to that repository, explicitly
"for session start hooks", and the Soveraeign run took 1966 ms against 371–436 ms
for the three repos with no project hooks — and a `register` + `end` pair lands in
the store inside that window. Project hooks do run in that image, from that cwd.

Narrowed by commit comparison (`48a0f57` → `64fe985`): the three SessionStart
hook scripts and the whole imported registration package (`sov_session.py`,
`sovsession/`) are **byte-identical** between image build and audited HEAD.
`.claude/settings.json` is **not** — the diff is the added `UserPromptSubmit`
entry and `"outputStyle": "Communications"`. So the historical success establishes
the SessionStart path only, and says nothing about `UserPromptSubmit`, the output
style, or `PreToolUse`/`PostToolUse`.

## The experiment, prepared and unrun

Blocked in the container: the auto-mode classifier refused to spawn `claude`. It
is a host permission, not a repository rule, and on the workstation it may simply
work. Paired runs, cwd as the only intended variable. Run the **parent-directory
case first**, so that if it invokes nothing it leaves no console grants to skew
the second run.

```
# same binary, same args, same settings file, same revision, same env but the label
cd <parent of the repo>
SOV_SESSION=audit-initonly-parent claude --init-only \
  --settings <the launcher settings file, if this host uses one> \
  --add-dir <repo> --debug --debug-to-stderr

cd <repo>
SOV_SESSION=audit-initonly-repo   claude --init-only \
  --settings <same file> \
  --add-dir <repo> --debug --debug-to-stderr
```

Observable: new lines in `$(git rev-parse --git-common-dir)/sov-sessions/sessions.ndjson`,
attributable by the `SOV_SESSION` label. Capture stdout, stderr and exit status
per run, and the pre/post digest of that file.

| Outcome | Establishes | Does **not** establish |
| --- | --- | --- |
| repo registers, parent does not | a cwd-dependent difference in whether the hook set is invoked under `--init-only`, with everything else held | which mechanism; anything about interactive sessions |
| both register | initialization can register from both cwds under these conditions; the cause lies elsewhere | any cause — it relocates the question |
| neither registers | nothing. A shared negative is uninformative | — |

`--init-only` fires SessionStart **and** SessionEnd. Per run that means: one
console session opened and closed in the append-preserving journal, possibly a
few grant records, one rewrite of `.local/console/host-sessions.json`, and a
register + end pair in the session store. All under `.local/` and
`.git/sov-sessions/`, all gitignored, none touching the tracked tree. Effect class
`RECORD_LOCAL` plus `RESOURCE_CONSUMPTION`. The journal is append-preserving, so
those records can be counter-recorded but not erased — small, and worth saying
out loud before you run it.

## Two findings the owner asked to be carried

### The frozen trunk reference

**Established, remote container.** Local `main` was pinned at `48a0f576`, the
commit the container image was built from, while `origin/main` had moved to
`64fe9856` eight hours later. Nothing refreshed it, and nothing said so.

The consequence was a briefing that read `58 ahead of main` for a branch one
commit ahead of the actual trunk. `_position` in `scripts/sovsession/brief.py`
compared against a bare `main` and never named which `main` it meant, so there
was nothing to check the number against.

Fixed in `a976227` (below): prefer `origin/main` when the ref resolves, name the
ref in the reading, and declare a local trunk that trails the remote one. **The
environment fact is not fixed** — a fresh remote container will still freeze local
`main` at image build. That belongs in `contracts/harness-hosts.json`, which
currently records no such property, and it is why any measurement of "unlanded
work" taken in that host is wrong by default.

### The phase records

**Corrected here.** An earlier reading of this audit suspected a conflict because
`contracts/phases.json` and `contracts/custodies/phase-1-5.json` both carry
`"status": "PROPOSED"` while `STATUS.yaml:10` declares `phase: phase:1-5`. On
inspection that is not a conflict: the collection-level `status` is the standing
of the **contract**, and the phase entry itself reads
`execution_status: OPEN`, `acceptance_status: NOT_EARNED`, `terminal: IN_FLIGHT`.
Those agree with `STATUS.yaml`. The suspicion is withdrawn.

Two things did survive the check, and both are questions rather than defects:

- `phase:1-5` carries **`opened_at: None`**. CLAUDE.md states the phase opened
  2026-09-03 and cites `decisions/0102`, so the opening date exists only in prose
  and in the decision record, not in the machine-readable phase entry. A reader
  that needs the date has no field to read.
- All **six** exit custodies under `contracts/custodies/phase-1-5.json` are
  `PROPOSED`. Whether the exit custodies of an already-open phase are meant to
  sit at `PROPOSED` is a governance question, not something this session should
  settle. `contracts/custody.schema.json` and `decisions/0102` own it.

Both belong to the governance domain. Neither is urgent.

## What landed

Branch `claude/context-audit-baseline-oie84r`, pushed. One commit ahead of
`origin/main` per fix; the branch's other 57 commits are already on the trunk and
are an artifact of the frozen local `main`, not unlanded work.

| Commit | Change | Evidence |
| --- | --- | --- |
| `ac0e765` | `intent: (not registered)` meant *no intent recorded*, not *no register event* — a registered session with no intent printed the same line. The store already sets `registered`; it never reached the briefing. An unregistered session is now told it holds no path claims, is invisible to peers, and gets no refusal from the shared-tree guard. | 6 tests, defeating case included; `lint` PASS, `verify` exit 0 |
| `a976227` | Position read against `origin/main` when it resolves, the ref named in the output, a stale local trunk declared. Trees with no remote keep the old reading under its own name. | 4 more tests; `lint` PASS, `verify` exit 0 |

One repair made in place: `test_session_phase_context` asserted the old intent
line from a fixture omitting `registered`. Its own name says its subject is a
registered session, so the fixture now says so. The strict default — a missing
key reads as **unregistered** — was kept, not loosened to make a test pass.

Both are `BUILT`. Neither is witnessed; the session that wrote them cannot
witness them.

## The queue, for the workstation

| | Work | Scope | Notes |
| --- | --- | --- | --- |
| **P1b** | A `harness` reading: cwd vs repo root, which settings files exist and which are plausibly in scope, whether any SessionStart trace exists for this session | `scripts/` — in grant scope | The durable form of this whole audit. Without it the next session repeats six hours of it. Intended shape: a subcommand on `sov_session.py`, since it reads the same store and the same session identity |
| **P2** | `contracts/harness-hosts.json` — the `remote-linux-container` entry is `OBSERVED` and misdescribes the invocation it was observed in | `contracts/` — in grant scope | Lists `Task` where the invocation has `Agent`; omits `ToolSearch`, `Artifact`, `Monitor`, `SendUserFile`, `ScheduleWakeup`; has no concept of a deferred tool, and several it lists were deferred rather than resident. Add the frozen-`main` property and a field for "project hooks not observed to load". Also: confirm the `workstation-windows` entry from an actual invocation and move it `RECORDED` → `OBSERVED` — **you will be the first session able to do that** |
| **P3** | A CLAUDE.md trap: the hooks this repository declares may not be running, and `.claude/settings.json` on disk is not evidence that this session loaded it | CLAUDE.md — **outside** the standing grant | Draft and present; do not land it under the grant. Points at whatever P1b builds |
| **P4** | Gateway standing disagrees with itself | `STATUS.yaml` — **outside** the grant | `STATUS.yaml:34` `gateway_service_status: CHARTERED_BOUNDARY_NOT_IMPLEMENTED` against `services/README.md:15` "first IN_PROCESS route pattern built and self-tested". CLAUDE.md's snapshot follows the README. One of the three is wrong; governance domain settles it |
| **P5** | The paired `--init-only` experiment above | — | Held on host permission in the container. Should be runnable on the workstation |
| **P6** | The two phase-record questions above | `contracts/`, governance | Low. The conflict I first suspected is withdrawn |

`reports/` is outside `grant:standing-landing-loop`'s path scope, so this file
reaching `main` needs a route other than the standing grant. It is committed to
the topic branch, which is where the host directed this session's work.

## What this session got wrong, kept because it is the finding

The audit's own measured failure was one pattern with three instances: reporting
*"no evidence of X in my context"* as *"X does not exist"* — for hooks, for the
output style, and for the concern address. The baseline was correctly scoped and
shallow: it labelled its bases, used UNKNOWN honestly, and never noticed that an
entire configuration layer sat outside its window.

A first scoring pass then made the mirror-image error, re-reading those hedged
claims as unhedged and charging the baseline for its own stated unknowns. The
corrected delta is 45 MATCHED / 0 DRIFTED / 0 INVENTED / 2 MISSED / 8 UNVERIFIED.
Do not read that total as fidelity — nearly all of it is claims about the
session's own window, where it is the primary source and can barely be wrong.
The distribution is the finding; the number is not.

The practical residue for you: the guard that refuses a write to a path another
live session holds — the one written after three files were clobbered on
2026-08-23 — is designed to fail silently when the registry is unreachable. A
session running with it inert looks exactly like a session running with it live.
That is what `ac0e765` makes visible and what P1b would make checkable.
