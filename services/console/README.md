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

Implementation begins only after:

1. the classification and logical specification are frozen or explicitly
   authorized as provisional build targets;
2. console-specific positive and defeating fixtures are executable;
3. the Asset Service and Proofing Service event and receipt read paths are
   stable enough to project without direct database access;
4. Bdo accepts the Console Service boundary (`decisions/0014`).

No placeholder implementation is treated as progress toward those gates.
