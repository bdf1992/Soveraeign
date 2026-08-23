# 0027 · Local model adapter as the first Model Binding implementation

Status: `PROPOSED · OWNER RATIFICATION PENDING`

Numbered after `0026-federation-harness.md`, the highest record on this branch.
`0019` and `0020` are absent here because they landed on `main` in parallel and the
records displaced by them were renumbered into `0021`–`0026`.

## Decision

Build `adapters/ollama/` as the first implementation of the Model provider row already
declared in `adapters/README.md`: a Model Adapter translating a Soveraeign `Model
Binding` to a locally hosted Ollama-compatible runtime, with two declared bindings, two
positive invocation records, fourteen defeating fixtures, and a check suite in
`scripts/verify.py`.

The adapter exists to make open decision O12 answerable. O12 asks Bdo to ratify "the
exact BYOM binding fields, data-boundary modes, and two-model Phase-I fixture". Until
now `bindings/` and `adapters/` held README files and a profile skeleton, so the question
had to be answered from prose. Two working bindings over materially different local
models put a concrete object in front of the ruling.

## Why local, and why now

The node owner's machine already runs four models with weights on local disk. That makes
the safest corner of `contracts/model-binding.schema.json` — `provider_kind: LOCAL`,
`data_boundary: LOCAL_ONLY`, `fallback_policy: NONE`, no monetary charge, no external
world effect — reachable without provisioning anything, and it satisfies the `BYOM.md`
personal-local pattern directly rather than by analogy.

The two-binding parity requirement in `bindings/README.md` needs two materially different
configured models. `qwen3:4b` and `gpt-oss:20b` differ by roughly five times in parameter
count, differ in family and context window, and run on one runtime under one host. That
is the cheapest honest parity fixture available.

## What the adapter refuses, and why it reads a record

The recorded runtime inventory holds `gpt-oss:20b` and `gpt-oss:20b-cloud`. Every
declared field a tag exposes — family, parameter size, quantisation, context length,
capabilities — is identical between them. They differ in `remote_host`, which for the
second names a host outside the machine. Both answer on the same loopback port and both
appear in the same listing.

So a binding checked against its tag could declare `LOCAL` custody and a `LOCAL_ONLY`
data boundary while the operation's input left the node. Every check in `adapter.py`
reads `inventory.json`, a rebuildable projection captured by `capture.py`, and refuses
that binding with `DATA_BOUNDARY_REFUSED`. This is the `AGENTS.md` prohibition on silent
provider fallback and the `FOUND-008` defeating case "unavailable model silently falls
back", met at a concrete runtime rather than stated.

Three reasoned-refusal codes are proposed alongside the three `SPEC.md` declares:
`SILENT_FALLBACK_REFUSED`, `PROVENANCE_INCOMPLETE`, and `PROVENANCE_CONTRADICTED`. The
`invoke_model` row admits a reasoned refusal; the exact set is Bdo's to rule on, and it
is queued rather than merged into `contracts/kernel-transitions.json`.

## Consequences

- `byom_status` moves from `OWNER_DIRECTED_CONTRACT_AND_FIXTURE_PROPOSED` to
  `OWNER_DIRECTED_CONTRACT_BUILT_WITNESSED_DISSENTED`. The contract is unchanged and
  unratified; what changed is that an implementation exercises it and an independent
  observer has refused it (see Standing).
- O12 is unaffected as a gate. It gates `model_binding.ratify_contract`, and nothing here
  ratifies a binding. The adapter narrows what Bdo must decide from an open question to a
  reviewable object with five named judgement items in `adapters/ollama/README.md`.
- `invoke_model` still has no implementation (PROD-I-9). This adapter checks declarations
  and records; it sends no request to any model. The invocation records under `fixtures/`
  are declared fixtures, not captured runs.
- The invocation record's field set stays inside `adapter.py` rather than under
  `/contracts`. Minting a kernel contract for it would create a second semantic authority
  ahead of the ruling, which `AGENTS.md` forbids.
- `scripts/verify.py` gains one check reading the recorded inventory. No repository check
  requires a running model server, so the gate behaves identically on a machine with no
  local runtime.
- Nothing external is enabled. `capture.py` reads a loopback port and is attended;
  `no_external_effects_in_phase_i` is untouched.

## Defaults taken

- Refusal code names, and the choice to propose rather than merge them into the kernel
  transition table.
- The invocation record field set, and keeping it adapter-local.
- `cost_meter` recording `monetary_rate: 0` with `wall_clock_seconds` metered separately,
  rather than declaring local compute costless.
- A recorded inventory as the authority for custody checks, rather than a live probe at
  invocation time.
- `urn:soveraeign:host:local-node` as the host identifier, so no machine-specific path or
  name enters repository text.

Each is reversible and each is queued as a question in `adapters/ollama/README.md`.

## Standing

`BUILT`, witnessed, **dissented**. `python scripts/verify.py` and `python scripts/lint.py`
pass, and an independent `sov-witness` reproduced all eight of the builder's literal claims
— but dissented on `BUILT -> WITNESSED` and found ten defects, four of them defeating the
custody refusal the adapter exists to make
(`reports/2026-08-23-local-model-adapter-witness.md`).

The custody check holds only against honest inputs. `inventory.json` has no integrity
binding to the runtime, so deleting one `remote_host` field restores the refused binding to
`ACCEPTED` with the full repository check set still green; `capture.py` does not verify that
the endpoint it read is local; and an invocation record selects its own data boundary rather
than inheriting the binding's, so a record declaring on its face that the input crossed to a
remote host is accepted.

So this record's central argument — that reading a recorded inventory rather than a tag
closes the gap the shared schema leaves open — is only half true as built. Reading a record
is necessary and is not sufficient; the record itself needs provenance the adapter does not
check. The observer's six judgement items are added to the five in
`adapters/ollama/README.md` and are Bdo's.

The witnessable subset today is the two-binding parity fixture, the `validate.py` command
line, and the declaration-consistency checks. Custody enforcement is not witnessable and
stays `OPEN`. Only Bdo ratifies.
