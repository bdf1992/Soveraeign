# Fresh participation: the first P15-X1 slice

Session `session-651746`, branch `claude/phase-2-citizen-mechanics-inrozu`, 2026-09-06.
Concern: move `custody:phase-1-5/fresh-participation` (exit clause P15-X1) off its opening
point with work whose closure a command demonstrates. Effect class `RECORD_LOCAL`
throughout. No phase state, standing field, or floor moved.

## Terminal

Presented on the branch for acceptance, in nine commits: the slice, the repairs each
witness pass asked for, the standing the fourth pass supports, the office opened at Bdo's
direction, and the node's journal separated from the report. Not landed on `main`: the change touches `CLAUDE.md`, which
the ratified standing grant excludes, so `scripts/sov_land.py` is not the path and Bdo's
review of the branch is.

## What was built, and the command that proves it

| Part | Proof | Reading at the second commit |
| --- | --- | --- |
| A fresh participant enters from the artifact and resolves principal, host session, phase, work, node session, grant, one admitted crossing and a Record projection | `python scripts/sov_fresh.py run --principal principal:claude-fable-5 --issuer principal:bdo` | `PASS`; P15-Q1.1, Q1.2, Q1.3 hold |
| The same run in a node nobody has granted anything in | `python scripts/sov_fresh.py run --principal principal:claude-fable-5` | `FAIL`; Q1.1 and Q1.2 hold, Q1.3 reads `identity separation missing grant_id` and the crossing is refused `SESSION_IDENTITY_REQUIRED` |
| The probe can fail | `python scripts/sov_fresh.py selfcheck` | positive variant passes; `unregistered-principal` fails Q1.1 and Q1.3, `work-dies-with-session` fails Q1.2, `no-grant` fails Q1.3, nothing else fails |
| The layers are the product's own | `scripts/sovfresh/layers.py`, `scripts/sovfresh/node.py` | session registry, lease store, custody model, Node Interface, `LocalActionPath` (Console, Gateway, Record, Registry services); the grade comes from `conformance/commissioning.py`, which imports none of them |
| Unit cases | `python -m unittest scripts.tests.test_sov_fresh` | 15 cases |
| Custody board | `python scripts/sov_custody.py board custody:phase-1-5/fresh-participation` | one `ITEM` member at `VERTICAL_SLICE`, standing `WITNESSED`, observed by the pass 4 witness at `0cf5a57` |
| Progress floor | `python scripts/sov_active_phase_progress.py` | `custody:phase-1-5/fresh-participation` floor raised `ROOT_POINT` to `VERTICAL_SLICE`; the reader refuses a fall below it |
| Repository gate | `python scripts/verify.py`; `python scripts/lint.py` | 51 checks PASS; hygiene PASS |

The heading's "second commit" reads "latest commit" for rows that changed under later passes:
the foreign-session refusal, the issuer gate, and the environment handling below.

The closed path: host session registered; principal resolved from the registry as the
participant declares it; campaign read from `STATUS.yaml` and `contracts/phases.json` by
digest; work read from the custody collection; a lease taken under it, held by the run's
instance principal with the declared principal as controller; a node opened with empty
stores; when an issuer exists, the Console Service records `open:session` and the
operation's required authority for the actor and opens the actor's session; `registry.resolve`
bound to that session and dispatched through the Gateway; three more crossings the node must
refuse; the run's facts appended to the node's Record and projected back; the host session
ended; the lease read back as orphaned inventory and the console session as still open; the
three predicates graded. The last layer is a check whose result is derived from the run.

What the node refuses, each read from a Gateway receipt with its stage:

- a request bound to a session this node never opened: `ACTOR_ATTRIBUTION_MISMATCH` at the
  attribution stage;
- another actor presenting this actor's session: `ACTOR_ATTRIBUTION_MISMATCH` at the
  attribution stage;
- another actor on its own session without the grant: `AuthorityRefused` at the authority
  stage.

`cross_principal_session_mismatch` reads `REFUSED` only when all three refuse for the reason
named and the owner's own crossing committed. A refusal for another reason is reported as
`REFUSED_FOR_ANOTHER_REASON` and fails the predicate.

## Independent witness

Pass 1 observed commit `d40d61f` through the declared surfaces. Verdict `NOT-YET`; standing
supported `BUILT`, unchanged. Record: `witness/fresh-participation.md`, receipt under
`witness/observations/`. Seven defects, each repaired in the second commit:

1. The Q1.3 mismatch was derived from `AUTHORITY_REFUSED` for an actor no grant names, which
   is absence of a grant, not a refused mismatch; the `borrowed-authority` variant defeated the
   probe's own derivation, not the product. Now every identity and refusal is read from the
   node's Console and Gateway records, and the Q1.3 defeating variant is `no-grant`, a state
   this node is actually in.
2. `grant_id` was the standing grant that had refused the participant. Now it is the grant the
   issuer recorded for the actor, or `None`, which fails the predicate.
3. `unregistered-principal` was not implemented inside the probe; through the CLI it passed.
   Now the variant substitutes an unregistered principal itself, whatever was declared.
4. `oral_history_used` was a constant. Now it is true when a resolver input the caller did not
   declare is set in the environment, and the input is named.
5. Cleanup obligations were composed by the probe. Now they are the custody's own list plus
   what the stores read back: the lease the store reports orphaned, and the console session
   still `OPEN`.
6. `interface_binding_id` fell back to a probe constant on refusal. Now it is `None`.
7. The cross-session reading compared verdicts, not codes. Now each refusal must carry the
   reason it declares.

Pass 2 observed commit `161d559`. Verdict `NOT-YET`; standing supported `BUILT`. F1 to F7
read repaired except one leg of F1, and four new defects, each repaired in the third commit:

- F18: `selfcheck` failed when `SOV_PRINCIPAL` was inherited from the environment although
  the run overrides it, and the fixture registry was read through the same override. Now
  only the registry variable counts as an undeclared input, and only when no registry was
  passed; the fixture registry is read from the repository path directly.
- F19: the foreign-session leg was refused by the scripts-layer binding, never by the node.
  Now the request is bound to a session the node never opened and the Gateway refuses it
  with a receipt at its attribution stage.
- F20: any string passed as `--issuer` opened the temporary node's permits office and made
  itself that node's root. Now only the registry's `root_principal` may issue; any other
  name, including an empty one (F21), issues nothing and Q1.3 reads unmet.

Pass 2 residuals recorded: the committed receipt names no grant (F22); the host session and
the node session are two sessions, so the Q1.1 observation now carries `node_session_id`
beside `session_id` (F23); the check ran over its ceiling once under load (F24); the Console
and Gateway commit a crossing for a null `principal_id` (F25, a product question). Pass 2's
J4 asks whether P15-X1 may be observed against a temporary node whose root grant the run
seeded under the registry's root name, or wants a persisted node whose office the root seat
opened; `--issuer` shows the mechanism and is not evidence the seat acted.

Pass 3 observed commit `8fd7716`, scoped to the pass 2 repairs. Verdict
`RATIFIABLE-WITH-CONDITIONS`; standing supported `BUILT`, with `BUILT -> WITNESSED` supported
for the instrument claim once two low defects are discharged. Both repaired in the fourth
commit:

- F26: the issuer gate read the checked-in registry while the resolver honoured
  `SOV_PRINCIPAL_REGISTRY`, so the two could read different registries. Now the gate reads
  the registry the resolver reads, and the Q1.1 observation records which registry that was.
- F27: the issuer gate is the probe's rule, not the node's, and was described as the node's.
  The Console makes a fresh node's first issuer its root and reads no registry. The rule is
  now named `PROBE_ISSUER_GATE`, its refusal is reported as the probe's, and the module
  docstring says so.

Pass 3 residuals recorded: the committed receipt names no grant (F22); host and node
sessions remain two sessions (F23); the check reads over its ceiling under load (F24); the
node commits a crossing for a null principal (F25); a host-preset `SOV_PRINCIPAL` is accepted
as the declaration channel and not flagged as oral history (F28, J6); pass 2's record first
entered history in the builder's commit (F30, as pass 1's did and this pass's will). Pass 3
adds J5: the custody closes on `selfcheck`, which is environment-blind by design, while its
`defeated_by` names oral history that only `run` observes.

Pass 4 observed commit `0cf5a57`, scoped to F26 and F27. Verdict `REPRODUCED`; standing
supported `BUILT -> WITNESSED` for the instrument claim at that revision, with the words for
the member's `stage_observed_by` field given by the witness and carried verbatim. The
witness attached a scope, not a precondition: the standing says the probe is what it says
and grades what it says. It is not evidence that P15-X1 holds for this node, whose permits
office no seat has opened (J4). Pass 4 found one low defect, F31: reverting either repair
left the unit suite green. Two cases now pin them, in the fifth commit, after the witnessed
bytes; the standing binds to `0cf5a57`. Pass 4 adds J7: the custody schema says
`stage_observed_by` names who "settled" the stage, and a witness settles nothing.

Pass 5 observed commit `219686d` and the persisted node. Verdict `REPRODUCED` for the run
and the extended instrument; dissent from any reading that the root seat acted (F35, above).
Four defects, each repaired in the sixth commit: the office and persisted-entry surface had
no tests (F33); two refusals surfaced as tracebacks (F34); the office receipt was overwritten
on repeat and named no registry (F36, now an append-only act line with the registry digest
and the journal heads); and the custody note asserted the direction as fact (F37). The
participant now closes its own console session, which retires F38. Residuals: the third
refusal leg changed under the pass 4 standing (F39, it is now the actor reaching past its
own grant, so both node modes read the same three); the packet's head sits inside the file
it checks and the witness holds an outside head (F40); the committed receipt's subject names
the resolved name rather than the operation (F41, product); this witness was launched from
the session the direction names (F42). Pass 5 adds J8, whether a custody note may assert
a direction before its acceptance, and J9, whether the packet wants a gate with an outside
head.

Pass 1 residuals recorded rather than changed: `--json` now works after the subcommand (F8);
the declared verify/lint evidence in the old authority request is gone with that request
(F9); `SOV_PRINCIPAL_REGISTRY` is now an explicit argument and, when set undeclared, is
reported as oral history (F10); `survives_session` now requires the store to read the lease as
orphaned after the session ended (F11); the custody schema has no evidence field and
`sovcustody/model.py` never calls `judge_advance`, so a member stage is a declaration
nothing measures (F12, pre-existing); `COMMISSIONING_CHECKS` is now spliced in one place,
the package `__init__` (F13); the custody closure command and the verify `Check` are two
declarations nothing ties together (F14, same as every other custody); the work the
participant accepts is the custody that lists the probe (F16); an `UNIDENTIFIED` principal can
still take a lease with `controller_principal: null` (F17, a lease-contract question).

## The office, opened

After the fourth pass Bdo directed, in his own words in this session: "Open the office on my
behalf me and rerun it as evidence and level with me." This session performed the act with
`python scripts/sov_fresh.py open-office` against the node whose stores live at
`.local/node-interface` on this host, twice under the same direction: the first act seated
`principal:bdo` as that node's root issuer and granted `principal:claude-fable-5`
`open:session` and `read:registry`; the second added `close:session` so the participant can
retire its own session. Every grant carries `granted_by: principal:bdo` in the node's
journal. The command refuses any issuer but the registry's root, and an act line naming the
registry by digest and the journal head before and after is appended beside the state.

Then `python scripts/sov_fresh.py run --principal principal:claude-fable-5 --node-state
.local/node-interface`: the participant entered that node as itself, seeded nothing, opened
its session under the grant it held, crossed once, was refused three times for the reasons
the node declares, closed its own console session, and all three predicates hold. The acts,
the runs, and the node's journal export are one packet,
`reports/observations/2026-09-06-fresh-participation-live-node.json`, which a reader
verifies against its record head with the Record Service.

What this is and is not. Witness pass 5 reproduced the run against the node and read the
export back entry by entry. It also read that the node's root is whatever non-empty name
the first caller passes, that the probe's gate is a string comparison against a registry
the caller may replace, that the registry's own `principal:bdo` entry is `UNVERIFIED`, and
that the direction lives in a transcript and a file this session wrote. So the record shows
the predicates holding on a persisted node whose journal names `principal:bdo` as root; it
cannot show that the root seat acted. That is the product residual F35, and the reason the
witness split J4: if Bdo accepts this packet with his quoted words, the acceptance is itself
the record that the seat acted; otherwise the question is what channel authenticates the
seat's issuance. The node state is runtime state on one host and leaves with it; the packet
is what stays.

## The journal, separated from the report

Bdo asked whether the packet should be separated from the node, and then said yes to an
operational node's journal living in this repository. The packet had been three things in
one file: the node's journal, this session's self-report, and the head that vouches for
the journal. They are now three artifacts.

- The journal is the node's own export, `nodes/node-local/journal/23d3b48086be.json`,
  written by `python scripts/sov_node.py export-journal` and named by the head it replays
  to. `nodes/README.md` says how to read it and how to bring the node back on another host
  with `restore-journal`, into an empty state, so the office is opened once and the history
  stays one chain. `selfcheck` now proves that path: export, restore, enter as the granted
  operator, all three predicates hold, and no grant is issued on the way; a truncated export
  is refused as soon as the head held outside it is supplied.
- The self-report is `reports/observations/2026-09-06-fresh-participation-live-node-2.json`.
  It names the export by address and head and the nine entries it relies on by id, and
  carries nothing the journal carries. The first packet is kept as the bytes pass 5 read.
- The outside head stays the witness's. `python scripts/sov_node.py journals` runs inside
  verify and refuses a misnamed export or a citation that does not resolve; it does not
  and cannot detect truncation, and says so.

Pass 6 observed commit `571e936` and the node, scoped to journal custody. Verdict
`REPRODUCED`. The witness read the node's head with sqlite from its own byte copy of the
store, independently of every committed file, and the committed export replays to exactly
that head; it recorded that head as the outside head, and refused pass 5's older head
against the same export. It dissented on one of the three artifacts and found six defects,
each repaired in the ninth commit: the first packet had been rewritten at `ed6a4f4` and
still embedded the journal, so it is restored to the bytes pass 5 read (F43); the gate read
only `cited_entries`, and now every `entry_id` or `receipt_id` a self-report mentions must
resolve, as must its cited entry count (F44); two exports of one node both passed, and now
a node has one head (F45); a fabricated entry crashed the gate rather than failing it
(F46); nothing tied the directory to the node the entries name or to the node registry
(F47); a refused restore left an empty store behind (F48). Residuals: the Record CLI's own
restore has no outside-head option and one of its refusal branches is unreachable (F49,
product); the slice check runs over its ceiling now that it restores a node (F50, ceiling
reset from measurement); the second office act reused the first act's quoted direction and
left duplicate grants in the journal (F52). Pass 6 adds J10, whether a head held in
`witness/` on the builder's branch and read from the builder's host is the custody the
clause wants, and J11, whether accepting the packet also accepts `nodes/` on the
publication surface.

## Standing changes

- `custody:phase-1-5/fresh-participation` member `scripts/sov_fresh.py`: `BUILT` to
  `WITNESSED` at `0cf5a57`, on the pass 4 record by a participant that built nothing here.
- `contracts/phase-progress.json`: the custody's floor `ROOT_POINT` to `VERTICAL_SLICE`,
  the progress record the opening note reserves for a witnessed member.
- No `STATUS.yaml` field, phase state, or clause verdict moved. P15-X1 stays `NOT_EARNED`.

## Defaults taken

Reversible; each can be overturned in one place.

- The custody's closure check moves from `python scripts/sov_session.py brief` to
  `python scripts/sov_fresh.py selfcheck`. `decisions/0102` recorded the first as "the reader
  that exists today"; the brief cannot detect the clause's defeating condition and the probe
  is built to.
- Member kind `ITEM`, work state `PRESENTED`. The floor in `contracts/phase-progress.json`
  stays `ROOT_POINT`: the opening note raises a floor where a witnessed member exists, and
  this member is a build claim.
- The check joins verify under a new group, `scripts/sovverify/commissioning.py`, spliced in
  by the package `__init__` beside the integrity checks. Named ceiling 1.5 seconds against
  0.62 measured alone.
- `selfcheck` uses a temporary registry copy whose root is a fixture, `principal:fixture-root`,
  with one fixture principal under it, so the self-check never issues in the real root's
  name. Neither exists outside the run. `run` without `--issuer` reports what a fresh node
  holds; `--issuer` must name the registry's root principal, and the run then shows the
  mechanism under that name without proving the seat acted (J4).
- The crossing is `registry.resolve` on `sov://asset/ingest-asset`, scope `registry:any`:
  reachable, `RECORD_LOCAL`, deterministic.

## Residuals

- The model serving this session is `claude-fable-5-1`. The registry names
  `principal:claude-fable-5`, and the live run declared that. Whether the version drift wants
  a new registry entry is identity naming, so it is recorded rather than done (witness J3).
- A fresh node has recorded no grant for any actor, so P15-Q1.3 is unmet there until an
  issuer opens the permits office. Whether the clause may be observed with the root seat
  issuing for the run, or wants a standing grant to a fresh principal, is the witness's J1.
- Re-pointing an exit custody's closure check is taken as a reversible default; whether it
  wants a decision-record note is the witness's J2.
- `python scripts/sov_active_phase_progress.py` prints nothing on a passing read.
- Two counts on `CLAUDE.md` moved: 50 to 51 verification checks and 30 to 31 reports. The page
  was corrected, not the tolerance, and its clarity receipt re-recorded after a read against
  `AGENTS.md`, `SOV.md`, and `STATUS.yaml`.

## Next bounded operation

Under the same custody: a second vertical that shares the boundary with this one so the
custody can reach `HORIZONTAL_SURFACE`, its declared target. The natural candidate is the
discovery side of P15-X3: a second fresh participant finds this run's lease, console session,
and projection from the stores alone. Under P15-X1 itself, the remaining gap is a session
whose principal is verified rather than `UNVERIFIED`, which waits on the Identity Service
challenge lifecycle.
