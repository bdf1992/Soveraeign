# Console Service

Status: `CONTINUITY PATH BUILT AND SELF-TESTED · REMAINDER CHARTERED`

One slice of this service is built. `src/soveraeign_console_service/` implements
the operator continuity record path and `cli.py` is the only way in;
`tests/` holds thirty-one cases, and `KNOWN-GAPS.md` says exactly what is not
built. The rest of this directory remains contract and boundary.

The service boundary, owned records, proving narrative, and defeating cases are
in `CHARTER.md`; `contracts/` holds the manifest and record schemas;
`conformance/` holds declarative seed fixtures a participant must satisfy.

The threaded operator interface that renders this service is a Human Binding
under `bindings/`, not part of this directory. A Model Binding reads the same
records as typed structure.

## Built slice: operator continuity

Channels, threads, posts, operator sessions and authority grants, appended to the
Record Service journal, with a read path rebuilt from that journal on every call.
Its purpose is the thing a session cannot do for itself: carry work across a
boundary where all context is lost, and let a human operator and a model operator
reach the same thread through one transition.

```
PYTHONPATH=services/console/src;services/record/src python -m soveraeign_console_service.cli --root .local/console operations --operator sov
```

`operations` is the discovery command - `AI-NATIVE.md` gates on whether a fresh
model instance can find out what may be done without a person explaining it.
Every command returns one JSON object, refusals included.

The operator is required, and so is a live grant. Every BUILT operation here
checks the authority `contracts/capability-offices.json` declares for it: nine
of them declared one and checked nothing until Bdo ruled on 2026-08-25 to guard
them, `grant` and `revoke` among them, so anyone reaching the service could
write itself a grant. What a fresh instance can now find out without a person
explaining it is what may be done and what each operation costs; running one
still needs the permit. `services/console/tests/test_enforced_authority.py`
drives all nine from both sides.

`.claude/hooks/console_session.py` binds a Claude Code session to an operator
session: it briefs a starting session with what landed while the operator was
away, and closes the session afterwards so the read position advances. That hook
is host plumbing and holds no standing; everything consequential it does, it does
through the CLI above. The `sov-continuity` skill is the operating guide.

Why this slice came before the judgement surface named below, and what Bdo has
not yet ruled on, are in
`decisions/0036-operator-continuity-before-the-screen.md`.

## Judgement surface (proposed, not built)

The slice this README originally declared first is the owner's judgement
surface: the path through which the owner receives a judgement request, answers it, and has the answer land as a
judgement-resolution record that can carry `RATIFIED` standing (`CHARTER.md`,
"First slice: the owner's judgement surface"). Its target is a local CLI over
the Python API, the Local surface row of `ENGINEERING.md`: no HTTP, no UI
framework, and not a GUI claim. In the manifest,
`list-pending-judgement-requests` is the pending-list read the human and model
bindings invoke to list `QUEUED` judgement requests from judgement-request
records, receipted; `resolve-judgement` is realized as the `SPEC.md` `ratify`
transition with the request's question as the Proposal being ratified. The
Human Binding it runs through is declared under `bindings/console/` as an
interface only. `conformance/008-judgement-request-reaches-owner.yaml`
(CONS-008, reach) and `conformance/009-owner-resolution-lands-ratified.yaml`
(CONS-009, land) are its seed fixtures. Nothing in the slice is implemented;
every entry in it is a proposal until the gates below hold.

The judgement surface begins only after:

1. the classification and logical specification are frozen or explicitly
   authorized as provisional build targets;
2. console-specific positive and defeating fixtures are executable;
3. the Asset Service and Proofing Service event and receipt read paths are
   stable enough to project without direct database access;
4. Bdo authorizes a provisional Human Binding target (`decisions/0014`).
   Ratifying the boundary itself gates only the standing word.

No placeholder implementation is treated as progress toward those gates. The
continuity slice above does not close any of them: it built a service, not a
binding, and reads no sibling service.
