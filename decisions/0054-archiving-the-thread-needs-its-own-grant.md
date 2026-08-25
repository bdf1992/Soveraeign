# 0054 · Archiving the thread needs its own grant

Status: `OWNER-RULED · BUILT · SELF-TESTED · NOT WITNESSED`

`decisions/0053` left one question with Bdo: `console.archive-thread` declared
`archive:thread` in the office table and enforced `open:thread` in code, and either
reading was defensible. Bdo ruled on 2026-08-24:

> Archiving a thread for yourself does not, archiving THE thread would.

## The distinction, and which one is built

Two different acts wear the same English word.

| Act | What it changes | Grant |
| --- | --- | --- |
| Archive **the** thread | a lifecycle record lands in the shared journal; no operator may post into it afterwards | its own, `archive:thread` |
| Archive it **for yourself** | one operator stops seeing it in their own continuity read; everyone else is unaffected | none of its own |

`console.archive-thread` is the first one. `core.archive_thread` appends a
`thread-lifecycle` entry with `lifecycle: ARCHIVED`, and `reads.thread` folds it into the
thread's current state for every reader, which is why a post from any operator is refused
afterwards. It reaches past the archiver, so it needs a grant the archiver has to be given
rather than one they already hold for opening threads.

**The second act does not exist and is not being built here.** It is named only so that a
later per-operator hide cannot arrive under the bare word `archive` and inherit this
ruling by accident. If it is built it needs its own capability identifier.

## What changed

`ENFORCED_AUTHORITY["console.archive-thread"]` in
`services/console/src/soveraeign_console_service/authority.py` moved from `open:thread` to
`archive:thread`. That is one line, and it deliberately narrows an ability: an operator
holding `open:thread` today could archive and now cannot.

The narrowing is what `decisions/0053` refused to do on its own authority, because
removing an ability from whoever holds a grant is a policy act rather than a rename. Bdo
made it.

Three consequences follow from that one line.

**The last declared/enforced divergence is closed.** Six console capabilities were
diverging when discovery was built; five were renames and were aligned then, and this was
the sixth. `KNOWN_DIVERGENCE` in `services/console/tests/test_discovery.py` is now an
empty set rather than a deleted one, so a new divergence fails there instead of quietly
making a capability's authority unanswerable.

**The `UNDETERMINABLE` authority reading has no instance on this node.** It is still a
real reading and still tested, now from an invented divergence rather than a real one -
the node has none today and the reading has to keep working for the day it grows one.

**A participant can now learn what archiving costs.** The row previously read
`UNDETERMINABLE`, which told a caller only that nobody could answer. It now reads
`NOT_HELD` against a grant name that exists and can be asked for.

## Evidence

`services/console/tests/test_operator_continuity.py` gained
`test_opening_a_thread_does_not_carry_the_right_to_archive_it`: the fixture operator holds
`open:thread`, opened the thread under it, and is refused with
`Bdo holds no live archive:thread grant scoped to <channel>`. The thread is still `OPEN`
afterwards, so the refusal stopped the transition rather than being raised after it. The
positive case grants `archive:thread` explicitly.

`services/console/tests/test_discovery.py` gained
`test_archiving_the_thread_is_answered_for_rather_than_undeterminable`, which reads the
ruling back out of the discovery surface.

29 discovery cases, 22 continuity cases, 31 contract-shape cases.

## The adversarial pass, and the channel that was not reading this service

Asked where discovery had been attacked, the answer was worse than expected and is now
better than it was.

`scripts/sov_mutate.py` is the repository's red channel: it mutates a module and reports
what the suite fails to notice, and it exists because
`decisions/0025` names the GitHub red lane as a known defect - it requires a secret nobody
set and reports **pass** when unconfigured, so a refusal and a real screening look alike.
Mutation scoring needs no key and cannot fail open.

Pointed at discovery, it said:

```text
UNSCORED: no suite in SUITES claims .../discovery.py; not counted in the channel
```

**`SUITES` claimed `conformance`, `bindings/sov`, `services/asset` and `scripts`, and
nothing else.** The Console Service, the Record Service and the MCP binding had never been
mutation-scored - not scored badly, not scored at all - while the channel reported a
number that read as if it covered the repository. `services/console` is now registered,
which is one line and makes 84 console cases count toward the channel that claims to
measure them.

The first real score found four behaviours nothing asserted:

| Mutant | What could have shipped |
| --- | --- |
| `reachable` tally `1 -> 2` | a participant told the node reaches 68 operations when it reaches 34 |
| `discover(...)` returns `None` | the function the CLI and MCP binding actually call was exercised by no case; every test drove `operations` underneath it |
| `operator_id is not None` inverted | grants read for exactly the participants they should not be read for |
| `check(...)` returns `None` | a receipt naming no grant - or the revoked one - while the operation still committed |

Discovery scores **96.8%** (30 of 31 mutants killed), `authority.py` **93.3%** (14 of
15). Both were unscorable an hour earlier.

Two survivors are left deliberately. One is `return None` mutated to `return None`,
which no test can kill. `authority.py:59` shortens a grant id from 16 hex
characters to 17; pinning an id length would raise the number without asserting a
behaviour, and padding a score is the failure this tool exists to detect.

Mutation scoring is not part of `scripts/verify.py` - it runs the suite once per mutant,
which the fifteen-second budget cannot hold - so it has to be run deliberately:

```text
python scripts/sov_mutate.py run --target services/console/src/soveraeign_console_service/discovery.py
```

Three services still sit outside `SUITES`: `services/record`, `services/observation`, and
`bindings/`. Registering them is not this record's work, but the channel percentage should
not be read as repository-wide until they are in it.

## Reading the surface's own output found a worse one

The row for `console.discover-operations` said:

```text
"reading": "NOT_KNOWN_HERE",
"because": "this operation is declared and this service enforces no authority for it,
            because it is not built"
```

False twice. It is built, and the reason a grant does not decide it is that no check
exists - not that nobody could answer. `NOT_KNOWN_HERE` means *this console cannot speak
for that capability*, which is a refusal to guess. Reporting an unguarded operation under
it makes an open door read like a locked one somebody else holds the key to.

**Nine built console operations declare an authority and check none:**
`close-session`, `discover-operations`, `grant`, `list-grants`, `list-publications`,
`open-session`, `read-thread`, `revoke`, `session-context`. `console.grant` declares
`grant:authority` and checks nothing, so anyone reaching the service can write themselves
a grant; `console.revoke` is the same in the other direction. Both also declare a
precondition, `issuer_holds_authority`, that nothing checks. All nine were reported as
unanswerable rather than as unguarded.

**How far that reaches, exactly.** Seven of the nine are `IN_PROCESS` only, `grant` and
`revoke` among them, so calling them means already holding the `ConsoleService` object -
code inside the node, not a caller across a transport. Two are wider:
`console.discover-operations` is on CLI and MCP, and `console.list-publications` is on the
CLI. Both are reads. So this is a hole in what the service enforces about its own
callers, not an unauthenticated path to writing grants, and it should not be reported as
one.

A fourth reading now names it:

| Reading | Means |
| --- | --- |
| `HELD` | a live grant in this journal names this authority |
| `NOT_HELD` | a check exists and this participant fails it |
| `NOT_ENFORCED` | built and callable, declares an authority, checks none; any caller is admitted |
| `NOT_KNOWN_HERE` | another service's store governs it, or nothing is built yet to enforce anything |
| `UNDETERMINABLE` | declares one name and checks another, so no grant can be matched |

The omission line names all nine capabilities rather than counting them, because a number
is not something a reader can act on.

**Nothing was guarded.** Adding a check to nine built operations is the same class of act
as narrowing `archive-thread` - it removes an ability from whoever can currently call
them, and it is Bdo's. What changed is that the surface now says so out loud. Anyone
reading `python -m soveraeign_console_service.cli operations` sees it in the first screen.

`test_every_built_console_capability_is_either_checked_or_named_unenforced` asserts the
partition: every built console capability is in `ENFORCED_AUTHORITY` or named in the
unenforced set, so a tenth cannot appear silently.

## The observation was retaken

`bindings/mcp/observations/journey-02-discovery.json` recorded
`{NOT_HELD: 5, NOT_KNOWN_HERE: 96, UNDETERMINABLE: 1}` and an omission line counting the
divergence. That was true when it was taken and is not true now, so
`python bindings/mcp/observe_journey_02.py` was run again and both artifacts were
rewritten. The current walk records `{NOT_ENFORCED: 9, NOT_HELD: 6, NOT_KNOWN_HERE: 87}`,
no divergence omission, and the nine unguarded operations named.

These two files are script output beside the binding rather than journal records, so
retaking overwrites rather than appends. Nothing here preserves the earlier observation; the
counts it held are quoted above so the change is readable, and a durable answer needs the
Observation Service (`GROUND-010`), which is a charter.

## Defaults taken

- The per-operator hide is named and not built. Building it now would be inventing a
  product experience the ruling did not ask for.
- `contracts/capability-offices.json` was not touched. It already declared
  `archive:thread`; the code moved to policy rather than policy moving to the code.
- No existing grant was migrated. There is no live journal outside test fixtures whose
  operators would need re-granting, and inventing a migration for a journal that does not
  exist would be worse than leaving the narrowing to bite where it is observed.
- `services/console` was added to `SUITES` and the other unscored services were not.
  Registering a suite that then scores badly is a finding somebody has to work; taking one
  service at a time keeps each finding attached to whoever can act on it.

## What this does not establish

Not witnessed. The tests were written beside the code they check, and the observation was
taken by calling the gateway it observes.

It settles the authority *name* for archiving. It does not settle who should hold
`archive:thread`, which is a grant-issuing question and belongs to whoever administers the
node.
