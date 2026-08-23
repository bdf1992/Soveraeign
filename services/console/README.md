# Console Service

Status: `CHARTERED · NOT IMPLEMENTED`

This directory is reserved for the Console Service contract and future
reference participant. The service boundary, owned records, proving narrative,
and defeating cases are in `CHARTER.md`; `contracts/` holds the manifest and
proposed record schemas; `conformance/` holds declarative seed fixtures a
future participant must satisfy.

The threaded operator interface that renders this service is a Human Binding
under `bindings/`, not part of this directory. A Model Binding reads the same
records as typed structure.

## First slice (proposed)

The first slice is the owner's judgement surface: the path through which the
owner receives a judgement request, answers it, and has the answer land as a
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
every entry in it is a proposal until O18 is ruled and the gates below hold.

Implementation begins only after:

1. the classification and logical specification are frozen or explicitly
   authorized as provisional build targets;
2. console-specific positive and defeating fixtures are executable;
3. the Asset Service and Proofing Service event and receipt read paths are
   stable enough to project without direct database access;
4. Bdo authorizes a provisional Human Binding target or O10 closes
   (`decisions/0014`; `STATUS.yaml` O18).
   Ratifying the boundary itself gates only the standing word.

No placeholder implementation is treated as progress toward those gates.
