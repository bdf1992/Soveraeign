# Witness observation · local model adapter

Subject: `adapters/ollama/` in the working tree of `feat/federation-harness-and-hardening`,
uncommitted. Builder's claim: `OPEN -> BUILT`, self-tested, not witnessed
(`decisions/0027-local-model-adapter.md`, `adapters/ollama/README.md`).

Observer: `sov-witness`, launched by Claude in an interactive session, independent of the
agent that built the adapter. The observer edited nothing; `adapters/ollama` content
digest was identical before and after
(`f2acfb300dd9b2e2a6fe6dff51115f64fec1143141345596a810de9e5732df6b`). Attack copies ran
in a scratchpad mirror.

Outcome: **DISSENTED** on `BUILT -> WITNESSED` for the adapter as a whole. A narrower
artifact is supportable; see Standing supported.

## Checks the observer ran

| Command | Exit | Result |
| --- | --- | --- |
| `python scripts/verify.py` | 0 | 12 checks, 1.768 s wall; `local model adapter` 13 tests OK in 0.088 s |
| `python scripts/lint.py` | 0 | one named debt, `core.py` at 341 lines |
| `python scripts/verify.py` with `connect`, `getaddrinfo`, and `create_connection` denied process-tree-wide | 0 | 12 checks pass; the ban was proven live first, `capture.build()` under it raised |
| `python -m unittest discover -s adapters/ollama/tests` under an in-process socket ban with `trace` | 0 | 13 tests OK |
| `validate.py bindings` / `binding <defeating>` / `binding <absent>` / `parity` | 0 / 2 / 1 / 0 | exit codes match the documented contract |
| shared schema alone over 16 fixtures and 2 bindings | — | `defeating-cloud-declared-local.json` returns 0 defects |
| `capture.build()` against the live daemon, in memory, no write | — | `models` block and `response_digest` identical to the committed inventory |

## Claims, as observed

| # | Claim | Verdict |
| --- | --- | --- |
| 1 | Two bindings accepted, `LOCAL`/`LOCAL_ONLY`, materially different models | reproduced |
| 2 | Fourteen fixtures refuse with the declared reason code; none undeclared | reproduced at the level of codes; see D6, D7 |
| 3 | The shared schema alone accepts the cloud binding with zero defects | reproduced |
| 4 | No repository check needs a live model runtime | reproduced empirically, not by reading |
| 5 | Nothing executes `invoke_model` or contacts a model during `verify.py` | reproduced; `urlopen` appears only in `capture.py`, which no check invokes |
| 6 | Grants no authority, settles nothing, writes no authoritative state | reproduced as to code; dissented as to the record it writes (D3) |
| 7 | `inventory.json` is a rebuildable projection | reproduced |
| 8 | 12 checks in budget, lint with one named debt | reproduced, with the attribution caveat below |

Attribution caveat on claim 8: the working tree carries a second uncommitted build
(`lineage/`, five `services/asset/scripts/history_*` modules and their tests, and a change
to `scripts/verify_bootstrap.py`). The green `verify.py` is joint, not the adapter's alone.
The observer isolated the adapter's own check separately.

## Defects

**D1 · high · a one-field edit disables the custody refusal and nothing notices.** Deleting
`remote_host` from a cloud row in a mirrored `inventory.json` made a `LOCAL`/`LOCAL_ONLY`
binding on a cloud-served model return `ACCEPTED`, and the 13-test suite still exited 0.
The only guard is `test_a_tag_cannot_settle_custody`, which hardcodes the
`gpt-oss:20b` / `gpt-oss:20b-cloud` pair; forge any other row and the suite is silent.
`inventory.json` is hand-editable with no integrity binding to the runtime.

**D2 · high · nothing verifies the inventory's own provenance.** `adapter.py` reads
`source.runtime_id`, `source.host_id`, and `source.runtime_version` only. `captured_at`,
`response_digest`, `address`, `capture_kind`, and `effect_class` are read by no check. An
inventory dated 1999 with an all-zeros digest passed every check. There is no freshness
budget, so the window between a model pull or re-tag and the next attended capture is
unbounded and invisible. `capture.py` reproduces `response_digest` exactly, so the digest
is checkable; nothing checks it.

**D3 · high · `capture.py` does not verify that the endpoint it read is local.** A stub
`/api/tags` served at a non-loopback address of the same machine was recorded with
`capture_kind: LOCAL_RUNTIME_READ`, `effect_class: RECORD_LOCAL`, and
`host_id: urn:soveraeign:host:local-node`. The endpoint comes from `argv[1]` unvalidated.
The `# noqa: S310 loopback only` comment and the module docstring assert what the code does
not enforce.

**D4 · high · an invocation record chooses which constraint applies to it.** The boundary
check keys off `record["data_boundary_applied"]`, not the binding's `data_boundary`. A
record bound to a `LOCAL_ONLY` binding, declaring `data_boundary_applied: REMOTE_ALLOWED`
and `executed.remote_host: https://ollama.com:443`, is `ACCEPTED`. The
`defeating-crossed-under-local-only` fixture guards only the case where the record honestly
declares `LOCAL_ONLY`.

**D5 · high · provenance the README requires that the code does not check.** In
`check_invocation`, the `executed` block is tested for non-emptiness and for
`model_id`/`model_version` equality with the binding, nothing more. All of these returned
`ACCEPTED`: a foreign `host_id`, a different `runtime_id`, an unrecorded `runtime_version`,
a third-party `provider_id`, and an `input_projection_id` swapped to an unredacted
projection with empty `omissions`. `AGENTS.md` requires an exact input projection at a
crossing; the record carries one and nothing compares it to the binding's.

**D6 · medium · six refusal raises have no fixture.** `trace` coverage shows these lines
never execute: the schema-defect `MODEL_INCOMPATIBLE`, the binding runtime/host mismatch,
the runtime-version mismatch, the second custody branch, the empty-meter check, and the
duplicate-invocation-id check. `CoverageTests` proves each reason-code *string* has a
fixture, not that each refusal *condition* does.

**D7 · medium · one false positive among the fixtures.** `defeating-meter-absent` refuses at
the generic absent-field loop (`absent fields: usage`), not at the meter check it is named
for. Right code, wrong constraint; the meter-emptiness check is never reached.

**D8 · low · vocabulary drift.** `information_role: "PROJECTION"` is not an information role
in `CLASSIFICATION.md`; the declared near neighbour is **View**. `standing: "PROPOSED"` on
the inventory is in neither the operational standing enum nor the artifact lifecycle. Both
are pinned by a test, so the drift is load-bearing. `information_role` appears nowhere else
in the repository.

**D9 · low · a second remoteness signal is discarded.** The live `/api/tags` also carries
`remote_model`; `project_model` drops it, leaving the custody check resting on one field.

**D10 · low · two incompatible binding shapes.** `conformance/run.py` `check_i9` requires
`operation_id`, `authority_contract_id`, `state_before_digest`, `receipt_id`, `result_id`,
and `result_standing`; `contracts/model-binding.schema.json` sets `additionalProperties:
false` and has none of them. The adapter's bindings cannot be fed to the oracle, so the
first Model provider implementation is bound to no cross-participant case.

## Language that outran the observation

- `capture.py` docstring, "a read of a runtime listening on the loopback interface" — not
  enforced (D3). `README.md`, "reads the loopback runtime" — reads whatever `argv[1]` names.
- The `PROVENANCE_CONTRADICTED` and `PROVENANCE_INCOMPLETE` enumerations in `README.md` list
  conditions no fixture proves and, for the executed block, that no code checks (D5, D6).
- The test docstring, "the suite fails while any refusal code the adapter can raise has no
  fixture exercising it" — true of codes, not of paths (D6).

The observer recorded as not overstated: no secrets, no host paths, LF endings with final
newlines throughout, every module under 300 lines, and `decisions/0027` honestly naming the
recorded-inventory choice as a reversible default and queuing it as judgement item 4.

## Standing supported

None as proposed. The custody claim — the reason the artifact exists — holds only against
honest inputs, and D1, D3, and D4 each defeat it from a different direction. In D1 and D2
the repository's full check set stays green while the check checks nothing.

A narrower artifact is supportable today: the two-binding parity fixture, the `validate.py`
command line, and the declaration-consistency checks. Custody enforcement is not.

Only Bdo ratifies; this observation settles nothing.

## Residuals

- Ruff is not installed on this host; the optional style gate did not run.
- No genuinely remote Ollama daemon was tested, only a stub at a non-loopback address of the
  same machine.
- The working tree carries a second uncommitted build, so the green `verify.py` is joint.

## Judgement queued for Bdo

1. May a custody check rest on a hand-editable file with no integrity binding to the
   runtime? If a recorded inventory stays, does it need a freshness budget, a
   `response_digest` re-verification, and a general rather than model-specific forgery test?
2. Is `data_boundary_applied` a field the record may assert, or must the boundary be read
   from the binding and the record checked against it? D4 turns on this.
3. Must `executed.provider_id`, `runtime_id`, `runtime_version`, `host_id`,
   `input_projection_id`, and `omissions` be reconciled against the binding?
4. Does a socket read of an unvalidated endpoint remain `RECORD_LOCAL`, or must `capture.py`
   refuse a non-loopback endpoint before stamping `LOCAL_RUNTIME_READ`? This sharpens the
   builder's own judgement item 5.
5. Is `information_role: PROJECTION` a role you want, or should the inventory carry the
   declared role **View**? Should an adapter-local record carry a `standing` field at all,
   given `/adapters` must not own standing?
6. Must reason-code coverage prove refusal *paths* rather than refusal *strings* before any
   adapter is witnessable?
