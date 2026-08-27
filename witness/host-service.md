# Witness record — Host Service (issue #108)

```witness
standing_supported  none
```

**Verdict: NOT-YET.**

**Standing supported: none for the subject as a whole.** The refusal half of the
`read-health` vertical is independently observed and holds under attack. The
success half was not reached, and today it cannot be reached by any participant
that refuses to import the implementation. `host_service_status` stays
`BUILT_READ_HEALTH_SELF_TESTED_REMAINDER_DECLARED_NOT_WITNESSED` and was not
edited.

- **Commit witnessed:** `4b96ba19df210f148bc41e4e4c2d8166bec72091`, in an
  isolated worktree (`CLAUDE.md` trap T6).
- **Observed:** 2026-08-26T17:06:10Z.
- **Receipt:** `witness/observations/issue-108-host-read-health.json`.
- **Reproduce:** `python witness/probes/probe_host_interface.py`.

## What independence rests on

This session did not build `services/host` or `adapters/host` and did not edit
either. The probe imports neither `soveraeign_host_service` nor
`local_host_adapter`; it reaches the vertical only as a subprocess through
`scripts/sov_interface.py` and the Console Service CLI.

The participant's own suite was deliberately not re-run as evidence.
`services/host/tests/test_host_service.py` imports the implementation directly
and substitutes a fake adapter in nine of its eleven tests. Running it would
have been the build checking itself.

## Correction to the premise this subject was prioritized on

**The Host Service does not cross a process boundary.** A grep for `subprocess`,
`os.system`, `popen`, `Popen`, `os.exec`, and `shell=True` across
`services/host/` and `adapters/host/` returns zero matches.

The adapter's entire host reading is three `pathlib.read_text` calls against
`/proc/meminfo`, `/proc/uptime`, and `/proc/sys/kernel/random/boot_id`, plus
`os.getloadavg`, `os.cpu_count`, and three `platform` calls — all in-process.
`services/host/contracts/service.json` forbids
`arbitrary-shell-or-command-execution`, and the code matches the manifest.

On this Windows host all three `/proc` reads and `os.getloadavg` fail, so the
real adapter would return nulls with six declared limitations. That is the
adapter behaving as documented, not a fault.

The consequence for this lane is that no external-world effect was ever at stake
here, which lowers the subject's consequence relative to the journal.

## What was reproduced, and what happened

Eight attacks through declared surfaces only. Six held.

| # | Attack | Result |
| --- | --- | --- |
| 1 | Project the operation under both bindings, compare digests | Held — both carry `031838d42233…`; both report `observed=no` |
| 2 | Invoke the built operation with no grant recorded anywhere | Held — `AUTHORITY_REFUSED`, `GOVERNED_REFUSAL`, at stage `check-authority`, journaled as a `RECEIPT` |
| 3 | Invoke with a foreign scope, a wildcard scope, an empty scope | Held — all three `AUTHORITY_REFUSED` (see the caveat below) |
| 4 | Invoke all seven declared mutating host operations | Held — all `OPERATION_NOT_REACHABLE`, none committed |
| 5 | Scan every declared surface for this machine's identity | Held — no node name, user name, or home path disclosed |
| 6 | Run the interface's own parity proof and read which adapter it used | Held, with a caveat — see F3 |
| 7 | Reach the success path through declared surfaces | **Failed** |
| 8 | Read the process exit status of a refusal | **Failed** |

Caveat on attack 3: with no live grant reachable, a *correct* scope refuses too.
This shows no scope slips through. It does not show that scope was the reason
any given call was refused. Isolating that needs a granted call, which F1 is
about.

## Findings

### F1 · MATERIAL TO WITNESSING · no declared path issues the grant this operation needs

`services/host/CHARTER.md`:

> every call requires a live SOV grant for its exact capability and scope

That is the right rule and it fires correctly. The problem is what it costs an
outside observer.

The Console Service CLI is the only declared surface that records a live grant,
and it records one successfully — exit 0, grant written — at every state-root
placement its declared arguments allow. Its journal always lands at
`<console_root>/journal/record-service.sqlite3`
(`services/console/src/soveraeign_console_service/cli.py:46`). The Node
Interface reads authority from `RecordService(<state_root>/record)`
(`scripts/sovnode/composition.py:133`).

Three placements were tried — console root equal to the state root, to
`<state_root>/console`, and to `<state_root>/record` — and all three left
`invoke` at `AUTHORITY_REFUSED`. There is no combination of declared arguments
that puts a Console-issued grant in the store the Node Interface reads.

Consequence: the success path of the Host Service's only `BUILT` operation
cannot be reached without importing the implementation. The health snapshot, its
conformance to `services/host/contracts/host-health.schema.json`, its
limitations list, and the adapter diagnostic non-leakage that commits `33c7b98`
and `bbad5a6` were written to defend are all unobserved, and unobservable by
this path.

This is not a defect in the service's behaviour. It is a gap in its
reachability, which `AI-NATIVE.md` gates on. Any one of three things would close
it: a `grant` subcommand on `scripts/sov_interface.py`, a `--journal` argument on
the Console CLI, or a documented state-root layout that composes the two.

### F2 · MINOR · a governed refusal is invisible in the exit status

Both `AUTHORITY_REFUSED` on `host.read-health` and `OPERATION_NOT_REACHABLE` on
`host.power-off` return process exit 0 from `scripts/sov_interface.py`. The
Record Service CLI answers the same class of refusal with exit 2 and documents
the mapping in its module docstring.

A caller that reads exit status rather than parsing stdout cannot tell a
governed refusal from a committed call. On a surface whose refusals are the
governance, that is worth a look by whoever owns the interface.

### F3 · INFORMATIONAL · the interface's own proof substitutes the adapter

`sov_interface.py prove` drives `host.read-health` under both bindings to
terminal outcome `COMMITTED`, `standing_effect` `NONE`, boundary
`PROCESS_EXECUTION_HOST`, `same_host_semantics` true. It uses adapter
`urn:soveraeign:adapter:node-interface-proof-host:v1` — not
`adapters/host/local_host_adapter.py`.

So it proves the service, gateway, and binding path, and it does not touch the
adapter that reads the host. `prove` labels its own output
`BUILT_EVIDENCE_SETTLES_NOTHING`, which is accurate and is why this is recorded
rather than raised as a defect.

## Conditions that would discharge the verdict

1. Close F1 by any of the three routes named above, then re-run this probe with
   a granted call so the snapshot, the schema conformance, and the diagnostic
   non-leakage can actually be observed; and
2. Either fix F2 or document that this surface reports outcome in stdout only.

Both are repairs. A witness may not make either
(`AGENTS.md`; `witness/README.md`).

## Verified

```
$ python witness/probes/probe_host_interface.py
exit 0 — 8 checks, 6 held, 2 failed
    success_path_reachable_through_declared_surfaces: false
    refusal_is_visible_in_the_exit_status: false

$ grep -rn "subprocess|os\.system|popen|Popen|os\.exec|shell=True" services/host adapters/host
NO MATCHES

$ python scripts/sov_interface.py show host.read-health --binding HUMAN
host.read-health  [031838d42233]
declared=yes  bound=yes  policy_active=yes  reachable=yes  observed=no
authority  read:host-health
exit 0

$ python scripts/sov_interface.py invoke host.power-off --actor operator \
      --scope host:local --binding MODEL --state-root <tmp>
REFUSED OPERATION_NOT_REACHABLE: host.power-off
exit 0

$ python scripts/verify.py
PASS: 39 checks in 12.058s wall — GRADE SILVER
exit 0

$ python scripts/lint.py
PASS: repository hygiene
exit 0
```

`CLAUDE.md` trap T2 applies to `verify.py`: exit 0 means unchanged, not
conformant.

## Uncovered

- **The health snapshot itself** — content, schema conformance, limitations.
  Blocked by F1.
- **Adapter diagnostic non-leakage.** The tests defend it with a fabricated
  credential string; this observation could not reach the code path that would
  leak it.
- **The snapshot-defect refusal path**, which does persist a service-authored
  diagnostic string. Read, not exercised.
- **Linux behaviour.** Only the Windows degradation path was seen, and only by
  reading the adapter, not by running it through the service.
- **The other 14 `PROPOSED` operations**, beyond confirming seven are
  unreachable.
- **Issue #108 is absent from `.claude/epic/tree.json`**, which synced
  2026-08-25T00:18:23Z. The subject was identified from `services/host/` and
  `STATUS.yaml` instead, so the epic projection is behind the tree.
