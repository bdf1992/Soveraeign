from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/gap-195-readiness-definition.yml"
SELF = Path(__file__).resolve()


def replace(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"expected block absent in {path}: {old[:120]!r}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")


def run(*args: str, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        capture_output=capture,
        check=not capture,
    )


def write_json(path: str, value: object) -> None:
    (ROOT / path).parent.mkdir(parents=True, exist_ok=True)
    (ROOT / path).write_text(
        json.dumps(value, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def assert_closed_boundary() -> tuple[dict, dict]:
    status = (ROOT / "STATUS.yaml").read_text(encoding="utf-8")
    if "\nphase: NONE_ACTIVE\n" not in "\n" + status:
        raise SystemExit("readiness work refuses unless STATUS.yaml remains NONE_ACTIVE")
    phases = json.loads((ROOT / "contracts/phases.json").read_text(encoding="utf-8"))
    if len(phases.get("phases", [])) != 1:
        raise SystemExit("readiness work expected exactly the closed phase:i record")
    phase_i = phases["phases"][0]
    if (
        phase_i.get("phase_id") != "phase:i"
        or phase_i.get("terminal") != "CLOSED_INCOMPLETE"
        or phase_i.get("succeeded_by") is not None
    ):
        raise SystemExit("readiness work refuses to alter the closed phase boundary")
    return phases, phase_i


def apply_spec_and_profile() -> None:
    phases, phase_i = assert_closed_boundary()
    spec_path = ROOT / "SPEC.md"
    spec_bytes = spec_path.read_bytes()
    current_digest = "sha256:" + sha256(spec_bytes).hexdigest()
    spec_pin = next(
        (item for item in phase_i["definition"] if item.get("document") == "SPEC.md"),
        None,
    )
    if spec_pin is None:
        raise SystemExit("phase:i no longer pins live SPEC.md as expected")
    if spec_pin["digest"] != current_digest:
        raise SystemExit(
            f"Phase-I SPEC pin does not match current bytes: "
            f"{spec_pin['digest']} != {current_digest}"
        )

    archive = ROOT / "archives/SPEC-PHASE-I-TERMINAL.txt"
    archive.write_bytes(spec_bytes)
    spec_pin["document"] = "archives/SPEC-PHASE-I-TERMINAL.txt"
    write_json("contracts/phases.json", phases)

    replace(
        "SPEC.md",
        """# Phase-I Logical Specification

Status: `PROPOSED · STACK-NEUTRAL · OWNER FREEZE PENDING`

This specification implements the Phase-I requirements in `PRD.md`. It fixes
logical objects, roles, states, transitions, predicates, receipts, and refusal
behavior. It does not select storage, encoding, language, transport, process,
container, graph, model provider, or repository layout.
""",
        """# Soveraeign Logical Specification

Status: `PROPOSED · STACK-NEUTRAL`

This specification fixes Soveraeign's shared logical objects, roles, states,
transitions, predicates, receipts, and refusal behavior. Qualification profiles
in `PRD.md` select which predicates a campaign must prove; changing the live
specification does not rewrite a closed campaign.

The exact Phase-I bytes are preserved at
`archives/SPEC-PHASE-I-TERMINAL.txt` and pinned by `contracts/phases.json`.
The Phase-I predicates below remain readable historical profile content while
later commissioning predicates may extend the live grammar. This specification
does not select storage, encoding, language, transport, process, container,
graph, model provider, or repository layout.
""",
    )

    replace(
        "SPEC.md",
        """A recording never replaces or mutates its source.

#### `Proposal`
""",
        """A recording never replaces or mutates its source.

#### `RecordProjection`

```text
projection_id, subject_addresses, recipient_principal, recipient_relation,
purpose, record_head, as_of,
included_records: [{address, digest}],
omissions: [{record_class, reason}],
projection_digest, created_at
```

A Record projection is a bounded, reconstructable reading of the common
append-preserving Record for one subject, recipient relation, purpose, and
cutoff. `included_records` names the exact evidence delivered; `omissions`
declares what classes were intentionally withheld and why. An empty omission
list is an explicit claim that no class was withheld.

A projection is not Record, standing, authority, settlement, or private memory.
It grants nothing by existing, and every projected value resolves back to its
included Record addresses and digests. Independent evaluators freeze the
projection cutoff before reading one another's conclusions, so a later reader
can reconstruct what evidence was available when a finding was formed.

#### `Finding`

```text
finding_id,
subject: {kind, address},
evaluator: {principal_id, relation},
scope, record_projection_id,
claims: [{claim_id, verdict, detail}],
evidence_addresses, counterevidence_addresses,
input_finding_ids, created_at, frozen_at | null,
authority_effect: NONE, settlement_effect: NONE,
supersedes: []
```

A Finding is an attributable interpretation of a named subject against cited
evidence. It is not an Observation: an Observation records independently seen
state, while a Finding says what an evaluator concludes from a declared evidence
projection. It is not authority and cannot settle itself.

`WORK` and `PARTICIPANT_IN_WORK` are distinct subjects. A work result may fail
while the participant carried its assignment correctly, or the result may pass
while participant conduct exceeded scope or authority. A comparison is itself a
Finding over frozen input Findings; it preserves their citations and dissent and
cannot manufacture evidence absent from their projections.

#### `Proposal`
""",
    )

    replace(
        "SPEC.md",
        "## Interface parity\n",
        """## Phase 1.5 commissioning predicates

These predicates prepare the `Phase 1.5 · Operational Commissioning`
qualification profile in `PRD.md`. They carry no phase standing while
`STATUS.yaml` remains `NONE_ACTIVE`. Controller, Orchestrator, Worker, and
Witness are one proving arrangement of these primitives, not privileged Kernel
roles.

### P15-Q1 · Fresh participation

- `P15-Q1.1` A fresh participant can resolve its principal, isolated session,
  current phase state, accepted work, capabilities, required authority, effect
  envelope, relevant governance, and assigned Record projection from the
  artifact without oral history.
- `P15-Q1.2` Accepted work has a durable address, custody or lease, closure
  condition, defeating condition, and cleanup obligations that survive the
  session carrying it.
- `P15-Q1.3` Principal identity, session continuity, grant authority, and
  interface binding remain distinct; a cross-principal or cross-session mismatch
  refuses rather than borrowing authority from a valid neighboring fact.

### P15-Q2 · Evidenced and fairly judged work

- `P15-Q2.1` Consequential operational history reaches the append-preserving
  Record and can be reconstructed without treating participant-private state as
  authoritative history.
- `P15-Q2.2` Every evaluative context uses a `RecordProjection` that names its
  subject, recipient relation, cutoff, included evidence, declared omissions,
  and digest, and the projection grants no authority.
- `P15-Q2.3` Findings about `WORK` and `PARTICIPANT_IN_WORK` remain separate,
  name evaluator and scope, and cite evidence available through the declared
  Record projection.
- `P15-Q2.4` Independent evaluative projections are frozen before their
  conclusions are shared; comparison preserves the frozen findings, citations,
  counterevidence, and dissent, distinguishes evidence differences from
  interpretation or subject defects, and cannot settle missing evidence by
  preference.

### P15-Q3 · Discovery, continuity, and reuse

- `P15-Q3.1` Settlement follows current state plus required independent
  observation, and closure retires declared leases, branches, worktrees,
  projections, claims, and other temporary coordination inventory rather than
  leaving successful work operationally unfinished.
- `P15-Q3.2` Another fresh participant can discover an accepted result, its
  standing, basis, receipts, and usable capability and can use it without oral
  history from the builder or prior session.

### P15-Q4 · Definition recurrence and institution-neutral composition

- `P15-Q4.1` Settled Records, scoped Findings, observations, and receipts may be
  cited into a later `Proposal` or candidate Definition while preserving the
  exact evidence addresses from which the candidate was synthesized.
- `P15-Q4.2` A generated, agreed, demonstrated, or repeatedly successful
  candidate Definition gains no standing or authority merely from that evidence;
  policy and phase transitions still require their governing authority.
- `P15-Q4.3` Identity, session, authority, work, custody, Record projection,
  observation, finding, settlement, and discovery semantics do not depend on
  fixed Controller/Orchestrator/Worker/Witness names, so later citizens may
  compose different institutions from the same governed primitives.

## Interface parity
""",
    )

    replace(
        "PRD.md",
        """### Later profiles

Each roadmap phase past `P0` earns its own profile, and none exists yet. The
shape is set here: named criteria with predicates in `SPEC.md` and fixtures in
`conformance/`, addressed by identifier, never advanced by the document that
declares them.
""",
        """## Prepared Phase 1.5 qualification profile

**`Phase 1.5 · Operational Commissioning`.** Working name: **Participant
Delivery Substrate**. This is a prepared successor profile, not an active phase.
`STATUS.yaml` remains the authority for whether a campaign is open, and merely
writing, testing, or agreeing with this profile grants it no standing.

Its purpose is to commission the participation and learning substrate that a
later Phase II can use rather than to prebuild what those citizens will do with
it. Phase II participants may compose teams, offices, councils, workflows,
institutions, sovereign nodes, federation arrangements, or other structures
from the same identity, authority, work, custody, Record, observation,
settlement, and discovery primitives. Those institutional forms are deliberately
not Phase 1.5 requirements.

### P15-Q1 · Fresh participation

A participant with no private history can enter from the artifact, establish an
attributable principal and isolated session, discover the current campaign and a
bounded unit of work, resolve capability and authority separately, and receive
the relevant governance and Record context needed to act. The work's custody,
closure, defeating condition, and cleanup obligations survive the participant's
session.

### P15-Q2 · Evidenced and fairly judged work

Consequential work converges on the common append-preserving Record. Different
legitimate evaluators receive scoped, reconstructable Record projections and
form separately cited Findings. Work quality and participant conduct are judged
as different subjects; independent readings freeze before comparison; a
comparator preserves citations and dissent and attributes a defect to work,
participant, orchestration, witnessing, Record, or policy rather than averaging
opinions into a score.

### P15-Q3 · Discovery, continuity, and reuse

Work settles only after required independent observation and explicit cleanup.
Another fresh participant can then discover the accepted result, reconstruct why
it stands, reach the capability it produced, and use it without builder-private
state or oral history.

### P15-Q4 · Definition recurrence and institution-neutral composition

Settled experience can become cited input to a new Proposal or candidate
Definition. The candidate preserves its evidence basis and gains no authority or
standing merely because participants generated, agreed with, or successfully
demonstrated it. The mechanics are expressed through generic governed
primitives rather than hardcoded Controller, Orchestrator, Worker, or Witness
species, so Phase II citizens can compose institutions the founder did not need
to predict.

### Commissioning terminal

Technical qualification is one witnessed Definition-to-Value-to-Definition
circuit on an exact revision: fresh participants enter without oral history,
carry bounded work under explicit authority, leave reconstructable operational
history, independently judge both the work and its carrying, compare and repair
those findings, settle and clean temporary state, hand a discoverable result to
another fresh participant, and synthesize a cited candidate next Definition
that remains unprivileged. Root operational acceptance remains a separate act
after these technical criteria are evidenced.

This profile exists **for Phase II**. Phase 1.5 commissions the ability to
self-organize and learn under governed evidence; Phase II decides what citizens
actually accomplish with it. A future Phase III requirement may therefore be a
product of Phase II's recorded experience without Phase II acquiring the power
to open or ratify that future phase itself.

### Later profiles

Later campaigns may derive new profiles from settled experience without
rewriting earlier ones. The shape remains named criteria with predicates in
`SPEC.md` and fixtures in `conformance/`, addressed by identifier and never
advanced by the document that declares them.
""",
    )


def write_contracts() -> None:
    projection_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://soveraeign.local/contracts/record-projection.schema.json",
        "title": "Soveraeign RecordProjection (PROPOSED)",
        "description": "A bounded, reconstructable, non-authoritative reading of the common Record for one subject, recipient relation, purpose, and cutoff.",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "record_projection_schema", "projection_id", "subject_addresses",
            "recipient_principal", "recipient_relation", "purpose", "record_head",
            "as_of", "included_records", "omissions", "projection_digest",
            "authority_effect", "created_at",
        ],
        "properties": {
            "record_projection_schema": {"const": "soveraeign-record-projection/v1"},
            "projection_id": {"type": "string", "minLength": 1},
            "subject_addresses": {
                "type": "array", "minItems": 1, "uniqueItems": True,
                "items": {"type": "string", "minLength": 1},
            },
            "recipient_principal": {"type": "string", "minLength": 1},
            "recipient_relation": {"type": "string", "minLength": 1},
            "purpose": {"type": "string", "minLength": 1},
            "record_head": {"type": "string", "minLength": 1},
            "as_of": {"type": "string", "minLength": 1},
            "included_records": {
                "type": "array", "minItems": 1,
                "items": {"$ref": "#/$defs/addressed"},
            },
            "omissions": {"type": "array", "items": {"$ref": "#/$defs/omission"}},
            "projection_digest": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
            "authority_effect": {"const": "NONE"},
            "created_at": {"type": "string", "minLength": 1},
        },
        "$defs": {
            "addressed": {
                "type": "object", "additionalProperties": False,
                "required": ["address", "digest"],
                "properties": {
                    "address": {"type": "string", "minLength": 1},
                    "digest": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"},
                },
            },
            "omission": {
                "type": "object", "additionalProperties": False,
                "required": ["record_class", "reason"],
                "properties": {
                    "record_class": {"type": "string", "minLength": 1},
                    "reason": {"type": "string", "minLength": 1},
                },
            },
        },
    }
    write_json("contracts/record-projection.schema.json", projection_schema)

    finding_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://soveraeign.local/contracts/finding.schema.json",
        "title": "Soveraeign Finding (PROPOSED)",
        "description": "An attributable interpretation of a named subject against cited evidence. A Finding is not Observation, authority, or settlement.",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "finding_schema", "finding_id", "subject", "evaluator", "scope",
            "record_projection_id", "claims", "evidence_addresses",
            "counterevidence_addresses", "input_finding_ids", "created_at",
            "frozen_at", "authority_effect", "settlement_effect", "supersedes",
        ],
        "properties": {
            "finding_schema": {"const": "soveraeign-finding/v1"},
            "finding_id": {"type": "string", "minLength": 1},
            "subject": {"$ref": "#/$defs/subject"},
            "evaluator": {"$ref": "#/$defs/evaluator"},
            "scope": {"type": "object"},
            "record_projection_id": {"type": "string", "minLength": 1},
            "claims": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/claim"}},
            "evidence_addresses": {
                "type": "array", "minItems": 1, "uniqueItems": True,
                "items": {"type": "string", "minLength": 1},
            },
            "counterevidence_addresses": {
                "type": "array", "uniqueItems": True,
                "items": {"type": "string", "minLength": 1},
            },
            "input_finding_ids": {
                "type": "array", "uniqueItems": True,
                "items": {"type": "string", "minLength": 1},
            },
            "created_at": {"type": "string", "minLength": 1},
            "frozen_at": {"type": ["string", "null"]},
            "authority_effect": {"const": "NONE"},
            "settlement_effect": {"const": "NONE"},
            "supersedes": {
                "type": "array", "uniqueItems": True,
                "items": {"type": "string", "minLength": 1},
            },
        },
        "$defs": {
            "subject": {
                "type": "object", "additionalProperties": False,
                "required": ["kind", "address"],
                "properties": {
                    "kind": {"enum": [
                        "WORK", "PARTICIPANT_IN_WORK", "FINDING_SET",
                        "CAPABILITY", "INSTITUTION", "NODE", "OTHER",
                    ]},
                    "address": {"type": "string", "minLength": 1},
                },
            },
            "evaluator": {
                "type": "object", "additionalProperties": False,
                "required": ["principal_id", "relation"],
                "properties": {
                    "principal_id": {"type": "string", "minLength": 1},
                    "relation": {"type": "string", "minLength": 1},
                },
            },
            "claim": {
                "type": "object", "additionalProperties": False,
                "required": ["claim_id", "verdict", "detail"],
                "properties": {
                    "claim_id": {"type": "string", "minLength": 1},
                    "verdict": {"enum": [
                        "CONFIRMED", "DISSENTED", "UNATTESTABLE",
                        "UNRESOLVED", "CLASSIFIED",
                    ]},
                    "detail": {"type": "string", "minLength": 1},
                },
            },
        },
    }
    write_json("contracts/finding.schema.json", finding_schema)

    replace(
        "contracts/README.md",
        "| `observation.schema.json` | records independent evidence of what occurred: what an observer looked at, how it avoided relying solely on the executor's report, and which predicates held (`SPEC.md` `Observation`) |\n",
        "| `observation.schema.json` | records independent evidence of what occurred: what an observer looked at, how it avoided relying solely on the executor's report, and which predicates held (`SPEC.md` `Observation`) |\n"
        "| `record-projection.schema.json` | prepares a bounded, reconstructable view of common Record evidence for one subject, recipient relation, purpose, and cutoff; it declares omissions and grants no authority (`SPEC.md` `RecordProjection`) |\n"
        "| `finding.schema.json` | records an evaluator's scoped, cited interpretation of a named subject; work, participant conduct, and comparison findings share one shape without becoming observations, authority, or settlement (`SPEC.md` `Finding`) |\n",
    )
    replace(
        "contracts/README.md",
        """The direction of authority is intentionally one-way:

`governing sources -> paradigm index -> service manifest bindings -> derived closure`

The arrow never reverses. Editing or passing the closure cannot change a service
manifest, grant authority, promote standing, or alter a governing Kernel source.
""",
        """The direction of authority is intentionally one-way:

`governing sources -> paradigm index -> service manifest bindings -> derived closure`

Operational evidence has the same one-way rule:

`Record -> RecordProjection -> Finding -> comparison Finding`

Neither arrow reverses. Editing or passing a closure, projection, or Finding
cannot change its source Record, grant authority, promote standing, settle a
claim, or alter a governing Kernel source.
""",
    )
    replace(
        "contracts/custody.schema.json",
        "Exactly one of the two routes must be available, the same rule contracts/work-item.schema.json applies to a single item.",
        "Exactly one of the two routes must be available, matching the bounded closure carried by contracts/work-lease.schema.json and the handoff rules in contracts/closure-ownership.json.",
    )


def update_diagram_readings() -> None:
    replace(
        "diagrams/source-reader-recording.md",
        """omissions       full field lists for Source, Reader, and Recording;
                payload custody and addressing mechanics;
                the Proposal object, which enters this flow separately
""",
        """omissions       full field lists for Source, Reader, and Recording;
                payload custody and addressing mechanics;
                Proposal, RecordProjection, and Finding, which branch from this flow
""",
    )
    replace(
        "diagrams/crossing-typology.md",
        "                federation identity and policy contracts, which do not exist\n",
        """                RecordProjection and Finding composition, outside this typology;
                federation identity and policy contracts, which do not exist
""",
    )
    replace(
        "diagrams/requirement-lifecycle.md",
        """omissions       the nine PROD-I requirement texts and their defeating cases;
                per-operation evidence, held by service tests and observation records
""",
        """omissions       campaign-specific qualification texts and defeating cases;
                per-operation evidence, held by service tests and observation records
""",
    )


def write_fixture_and_test() -> None:
    projection = {
        "record_projection_schema": "soveraeign-record-projection/v1",
        "projection_id": "projection:work-81:witness",
        "subject_addresses": ["work:81"],
        "recipient_principal": "principal:witness-9",
        "recipient_relation": "witness",
        "purpose": "independent work review",
        "record_head": "record:head:44",
        "as_of": "2026-08-31T17:00:00Z",
        "included_records": [{
            "address": "record:412",
            "digest": "sha256:" + "a" * 64,
        }],
        "omissions": [{
            "record_class": "EVALUATIVE_FINDING",
            "reason": "freeze independent reading before prior conclusions are disclosed",
        }],
        "projection_digest": "sha256:" + "b" * 64,
        "authority_effect": "NONE",
        "created_at": "2026-08-31T17:00:00Z",
    }
    finding = {
        "finding_schema": "soveraeign-finding/v1",
        "finding_id": "finding:witness:81",
        "subject": {"kind": "WORK", "address": "work:81"},
        "evaluator": {"principal_id": "principal:witness-9", "relation": "witness"},
        "scope": {"revision": "abc123", "operation": "asset.ingest-asset"},
        "record_projection_id": "projection:work-81:witness",
        "claims": [{
            "claim_id": "requested-result",
            "verdict": "DISSENTED",
            "detail": "restart fixture defeats the result",
        }],
        "evidence_addresses": ["record:412", "observation:14"],
        "counterevidence_addresses": [],
        "input_finding_ids": [],
        "created_at": "2026-08-31T17:05:00Z",
        "frozen_at": "2026-08-31T17:06:00Z",
        "authority_effect": "NONE",
        "settlement_effect": "NONE",
        "supersedes": [],
    }
    cases = [
        {"case_id": "record-projection-positive", "schema": "record-projection.schema.json", "valid": True, "record": projection},
        {"case_id": "record-projection-missing-omissions", "schema": "record-projection.schema.json", "valid": False, "remove": "omissions"},
        {"case_id": "record-projection-missing-cutoff", "schema": "record-projection.schema.json", "valid": False, "remove": "as_of"},
        {"case_id": "record-projection-no-evidence", "schema": "record-projection.schema.json", "valid": False, "set": {"included_records": []}},
        {"case_id": "finding-work-positive", "schema": "finding.schema.json", "valid": True, "record": finding},
        {"case_id": "finding-participant-positive", "schema": "finding.schema.json", "valid": True, "mutate_subject_kind": "PARTICIPANT_IN_WORK"},
        {"case_id": "finding-missing-projection", "schema": "finding.schema.json", "valid": False, "remove": "record_projection_id"},
        {"case_id": "finding-no-evidence", "schema": "finding.schema.json", "valid": False, "set": {"evidence_addresses": []}},
        {"case_id": "finding-cannot-claim-standing", "schema": "finding.schema.json", "valid": False, "set": {"standing": "RATIFIED"}},
        {"case_id": "finding-unknown-subject", "schema": "finding.schema.json", "valid": False, "mutate_subject_kind": "WORKER_REPUTATION"},
    ]
    write_json("conformance/fixtures/commissioning/evidence-contract-cases.json", {"cases": cases})

    test_text = '''"""Positive and defeating cases for prepared commissioning evidence contracts."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovkernel.jsonschema import validate  # noqa: E402


class CommissioningEvidenceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        corpus = ROOT / "conformance/fixtures/commissioning/evidence-contract-cases.json"
        cls.cases = json.loads(corpus.read_text(encoding="utf-8"))["cases"]
        cls.schemas = {
            name: json.loads((ROOT / "contracts" / name).read_text(encoding="utf-8"))
            for name in {case["schema"] for case in cls.cases}
        }
        cls.positive = {
            case["schema"]: case["record"]
            for case in cls.cases if case.get("record") is not None
        }

    def case_record(self, case: dict) -> dict:
        record = deepcopy(case.get("record") or self.positive[case["schema"]])
        if case.get("mutate_subject_kind"):
            record["subject"]["kind"] = case["mutate_subject_kind"]
        if case.get("remove"):
            record.pop(case["remove"], None)
        for key, value in (case.get("set") or {}).items():
            record[key] = value
        return record

    def test_declared_cases(self) -> None:
        for case in self.cases:
            with self.subTest(case=case["case_id"]):
                defects = validate(self.case_record(case), self.schemas[case["schema"]])
                self.assertEqual(not defects, case["valid"], defects)

    def test_both_subjects_share_one_finding_contract(self) -> None:
        kinds = {
            self.case_record(case)["subject"]["kind"]
            for case in self.cases
            if case["case_id"] in {"finding-work-positive", "finding-participant-positive"}
        }
        self.assertEqual(kinds, {"WORK", "PARTICIPANT_IN_WORK"})

    def test_phase_i_spec_archive_is_exact_and_successor_remains_unopened(self) -> None:
        phases = json.loads((ROOT / "contracts/phases.json").read_text(encoding="utf-8"))
        self.assertEqual(len(phases["phases"]), 1)
        phase_i = phases["phases"][0]
        pin = next(item for item in phase_i["definition"]
                   if item["document"] == "archives/SPEC-PHASE-I-TERMINAL.txt")
        actual = "sha256:" + sha256((ROOT / pin["document"]).read_bytes()).hexdigest()
        self.assertEqual(actual, pin["digest"])
        self.assertEqual(phase_i["terminal"], "CLOSED_INCOMPLETE")
        self.assertIsNone(phase_i["succeeded_by"])
        self.assertIn("phase: NONE_ACTIVE", (ROOT / "STATUS.yaml").read_text(encoding="utf-8"))

    def test_prepared_profile_is_non_authoritative_and_recurrent(self) -> None:
        prd = (ROOT / "PRD.md").read_text(encoding="utf-8")
        spec = (ROOT / "SPEC.md").read_text(encoding="utf-8")
        self.assertIn("Prepared Phase 1.5 qualification profile", prd)
        self.assertIn("This is a prepared successor profile, not an active phase", prd)
        for criterion in ("P15-Q1", "P15-Q2", "P15-Q3", "P15-Q4"):
            self.assertIn(criterion, prd)
            self.assertIn(criterion, spec)
        self.assertIn("candidate next Definition", prd)
        self.assertIn("gains no standing or authority", spec)


if __name__ == "__main__":
    unittest.main()
'''
    target = ROOT / "scripts/tests/test_commissioning_evidence_contracts.py"
    target.write_text(test_text, encoding="utf-8", newline="\n")


def apply() -> None:
    apply_spec_and_profile()
    write_contracts()
    update_diagram_readings()
    write_fixture_and_test()


def refresh_clarity() -> None:
    for path in (
        "PRD.md",
        "SPEC.md",
        "contracts/README.md",
        "diagrams/source-reader-recording.md",
        "diagrams/crossing-typology.md",
        "diagrams/requirement-lifecycle.md",
    ):
        run("python", "scripts/sov_clarity.py", "record", path, "--changed")

    coverage = json.loads((ROOT / ".clarity/coverage.json").read_text(encoding="utf-8"))
    candidates = list(coverage.get("artifacts", coverage).keys())
    for _ in range(4):
        result = run("python", "scripts/sov_clarity.py", "check", capture=True)
        output = result.stdout + "\n" + result.stderr
        stale: list[str] = []
        for line in output.splitlines():
            if "BASIS_STALE" not in line and "TEXT_STALE" not in line:
                continue
            for path in candidates:
                if path in line and path not in stale:
                    stale.append(path)
        if not stale:
            if result.returncode != 0:
                print(output)
                raise SystemExit(result.returncode)
            return
        for path in stale:
            run("python", "scripts/sov_clarity.py", "record", path, "--changed")
    run("python", "scripts/sov_clarity.py", "check")


def refresh() -> None:
    run("python", "scripts/sov_diagrams.py", "stamp")
    run("python", "scripts/sov_docs.py", "build")
    refresh_clarity()


def refresh_snapshot() -> None:
    sys.path.insert(0, str((ROOT / "scripts").resolve()))
    from sovsnapshot import claims

    path = ROOT / "CLAUDE.md"
    text = path.read_text(encoding="utf-8")
    derived = claims.derive_all()
    missing = [claim.name for claim in claims.CLAIMS if claim.name not in derived.values]
    if missing:
        raise SystemExit(f"cannot refresh snapshot; underivable claims: {missing}")
    for claim in claims.CLAIMS:
        value = derived.values[claim.name] + (1 if claim.name == "commits" else 0)
        match = re.search(claim.pattern, text)
        if not match:
            raise SystemExit(f"snapshot pattern absent for {claim.name}")
        start, end = match.span(1)
        text = text[:start] + str(value) + text[end:]
    path.write_text(text, encoding="utf-8", newline="\n")


def finalize() -> None:
    assert_closed_boundary()
    WORKFLOW.unlink()
    SELF.unlink()
    refresh_snapshot()
    run("python", "scripts/sov_clarity.py", "record", "CLAUDE.md", "--changed")
    run("python", "scripts/sov_clarity.py", "check")
    run("python", "scripts/sov_docs.py", "build")


COMMANDS = {"apply": apply, "refresh": refresh, "finalize": finalize}


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in COMMANDS:
        raise SystemExit("usage: gap_195_readiness_definition.py apply|refresh|finalize")
    COMMANDS[sys.argv[1]]()
