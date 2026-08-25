"""The declared check table: what `scripts/verify.py` runs, and why each one is independent.

Every entry states in `relation` how the check avoids relying on the thing it
checks. That sentence is the check's warrant; an entry without one is a command,
not evidence. The table lives apart from the runner so it can grow without
dragging the runner past its line budget with it.
"""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple
import sys


ROOT = Path(__file__).resolve().parents[2]


class Check(NamedTuple):
    name: str
    command: list[str]
    cwd: Path
    relation: str
    observes: tuple[str, ...]


CHECKS = (
    Check("repository hygiene", [sys.executable, "scripts/lint.py"], ROOT,
          "reads repository bytes directly with read_bytes, never a build report, and never "
          "Path.read_text whose newline translation would hide the defect it looks for",
          (".gitattributes", "scripts/lint.py")),
    Check("recorded traps still hold", [sys.executable, "scripts/sov_traps.py"], ROOT,
          "re-derives every recorded trap from the repository at check time, so a trap that "
          "has stopped being true fails here instead of going stale in prose",
          ("CLAUDE.md", "scripts/sov_traps.py")),
    Check("standing claims carry a witness", [sys.executable, "scripts/sov_standing.py"], ROOT,
          "reads STATUS.yaml and the witness records by separate paths and grades one against "
          "the other, so a standing claim cannot supply the record that would support it",
          ("STATUS.yaml", "scripts/sov_standing.py")),
    Check("owner queue", [sys.executable, "scripts/sov_accept.py", "audit"], ROOT,
          "fails when anything sits on the owner without a complete packet, reading the "
          "declared acceptance contract rather than any claim that a result is ready",
          ("contracts/acceptance-policy.json", "scripts/sov_accept.py")),
    Check("acceptance routing", [sys.executable, "scripts/sov_docket.py", "check"], ROOT,
          "reads the decision records and the two declared contracts and proves the crosswalk "
          "is total, no routing names a record that does not exist, and every claim that "
          "STATUS.yaml already answers a record is true of the file; it grades no decision as "
          "right and settles none of them",
          ("contracts/decision-standing.json", "contracts/acceptance-routing.json",
           "decisions", "STATUS.yaml")),
    Check("charting derivation tests",
          [sys.executable, "-m", "unittest", "discover", "-s", "charting/tests", "-v"], ROOT,
          "re-derives the whole chart from SDLC.md and the checked-in skill bindings at the "
          "moment of the check, so a binding that has stopped matching the tier it implements "
          "fails here rather than going stale in a recorded derivation",
          ("charting", "SDLC.md")),
    Check("bootstrap and locked evidence", [sys.executable, "scripts/verify_bootstrap.py"], ROOT,
          "re-digests locked evidence from disk rather than trusting a recorded digest",
          ("scripts/verify_bootstrap.py",)),
    Check("signpost reconciliation", [sys.executable, "scripts/sov_next.py", "--strict"], ROOT,
          "re-reads STATUS.yaml, ROADMAP.md and the epic projection at the moment of the "
          "check; it does not consult any prior reconciliation",
          ("ROADMAP.md", "STATUS.yaml", ".claude/epic/tree.json")),
    Check("diagram provenance", [sys.executable, "scripts/sov_diagrams.py"], ROOT,
          "recomputes each declared source digest from the file's bytes at the moment of "
          "the check; it never reads a diagram's own claim about being current",
          ("diagrams",)),
    Check("conformance oracle controls", [sys.executable, "conformance/run.py"], ROOT,
          "the oracle derives every defect from observation records and never reads a "
          "participant verdict field, and never imports participant implementation code",
          ("conformance/oracle-controls.json", "conformance/run.py",
           "conformance/requirements.py")),
    Check("conformance oracle tests",
          [sys.executable, "-m", "unittest", "discover", "-s", "conformance/tests", "-v"], ROOT,
          "tests the oracle from outside itself, including cases proving it refuses reports "
          "it cannot read",
          ("conformance/tests",)),
    Check("kernel transition contract", [sys.executable, "scripts/sov_kernel.py", "selfcheck"],
          ROOT,
          "judges a declared corpus of positive and defeating requests against the "
          "authored table; it reads no participant verdict and asks the table nothing "
          "about whether it is correct, only what it admits",
          ("contracts/kernel-transitions.json",
           "conformance/fixtures/kernel/transition-cases.json")),
    Check("kernel contract against SPEC.md", [sys.executable, "scripts/sov_kernel.py", "drift"],
          ROOT,
          "re-reads SPEC.md bytes and derives the transition set and refusal codes from "
          "the governing document rather than trusting the authored table it is checking",
          ("SPEC.md", "contracts/kernel-transitions.json")),
    Check("kernel participant parity", [sys.executable, "scripts/sov_kernel.py", "parity"],
          ROOT,
          "compares each participant's declared refusal vocabulary against the kernel "
          "contract, so a participant cannot vouch for its own correspondence",
          ("contracts/kernel-parity.json", "contracts/kernel-transitions.json")),
    Check("service manifest contract", [sys.executable, "scripts/sov_service.py", "check"],
          ROOT,
          "derives the refusal vocabulary and transition ids from the kernel table and the "
          "requirement ids from PRD.md at check time, and rebuilds each logical endpoint from "
          "the manifest's own service and operation id rather than trusting the address it "
          "declares",
          ("contracts/service-manifest.schema.json",
           "contracts/fixtures/service-manifest.fixtures.json")),
    Check("product ground and canon joins",
          [sys.executable, "scripts/sov_canon.py", "check"], ROOT,
          "resolves every capability the canon names against the capability map rather than "
          "against the canon's own word for it, refuses a promise deriving from no product "
          "ground and a ground claim no promise carries, refuses a promise that is "
          "canonical only because something was built that way, and reads GROUND.md and "
          "CANON.md at check time so an identifier declared in a record and absent from the "
          "document that owns its wording fails here rather than drifting",
          ("GROUND.md", "CANON.md", "contracts/product-ground.json",
           "contracts/product-canon.json",
           "contracts/fixtures/capability-map.reference.json")),
    Check("receipt event vocabulary",
          [sys.executable, "scripts/sov_capability.py", "events"], ROOT,
          "parses each service's own modules and reads the event names its source passes to "
          "its journal, rather than asking the service or a table what it emits; an event "
          "must then be a capability the map declares or an entry the manifest states a "
          "reason for, and an excuse the service stopped emitting fails too",
          ("scripts/sovkernel/receipt_events.py", "services/asset/src", "services/console/src",
           "contracts/fixtures/capability-map.reference.json")),
    Check("specification traceability", [sys.executable, "scripts/sov_spec.py", "trace"], ROOT,
          "walks from SPEC.md requirements to the evidence records that claim them and "
          "refuses a standing whose predecessor standing is unreached",
          ("SPEC.md", "PRD.md")),
    Check("semantic cold-start task", [sys.executable, "scripts/sov_witness.py", "semantic"],
          ROOT,
          "judges the custody round trip by digests the witness computes itself rather than "
          "by any value the participant reported",
          ("conformance/founding-scenarios/010-semantic-custody-round-trip.yaml",)),
    Check("participant against its baseline", [sys.executable, "scripts/sov_baseline.py"], ROOT,
          "runs the participant in a separate process and grades it through the frozen "
          "oracle, which never imports participant code; the participant does not report its "
          "own verdict",
          ("services/asset/conformance/BASELINE.md", "conformance/scenarios.json")),
    Check("ticket contract corpora", [sys.executable, "scripts/sov_ticket.py", "selfcheck"],
          ROOT,
          "reads checked-in transition, metadata, and issue-body corpora and never contacts the "
          "coordination surface it describes; the issue-body cases start from bytes a person could "
          "paste into GitHub, so a shape the schema admits but no ticket body can express fails here",
          ("contracts/ticket-transitions.json", "conformance/fixtures/tickets/body-cases.json")),
    Check("closure ownership", [sys.executable, "scripts/sov_closure.py", "selfcheck"], ROOT,
          "grades declared handoff claims against the table rather than against the judgement of "
          "the participant that wrote them, and refuses a contract that declares a refusal no case "
          "proves fires; the evaluator holds no copy of the table, so admitting a new seam or "
          "raising the work-in-progress ceiling is a contract change with a case behind it",
          ("contracts/closure-ownership.json",
           "conformance/fixtures/closure/handoff-cases.json")),
    Check("standing authority grants", [sys.executable, "scripts/sov_grant.py", "selfcheck"],
          ROOT,
          "grades a declared corpus of requests against grants the corpus itself carries, so "
          "the evaluator is never asked whether the issued registry is correct, only what it "
          "admits; it also validates every issued grant against the schema and refuses a "
          "corpus that leaves any reachable refusal code unproven, which is what stops a "
          "grant sitting in the registry looking authoritative while no case can exercise it",
          ("contracts/authority-grant.schema.json", "contracts/standing-grants.json",
           "conformance/fixtures/authority/grant-cases.json")),
    Check("node registry", [sys.executable, "scripts/sov_node.py", "validate"], ROOT,
          "reads the checked-in registry and the seat topology and grades one against the "
          "other; it contacts no peer and opens no socket, so the check cannot pass or fail "
          "because of what another node happened to be doing",
          ("contracts/fixtures/node-registry.reference.json",
           "contracts/node-identity.schema.json")),
    Check("Sov context profile",
          [sys.executable, "-m", "unittest", "discover", "-s", "bindings/sov/tests", "-v"], ROOT,
          "invokes the profile checker over declared fixtures, including one defeating "
          "declaration, rather than asking the profile whether it is valid",
          ("bindings/sov",)),
    Check("local model adapter",
          [sys.executable, "-m", "unittest", "discover", "-s", "adapters/ollama/tests", "-v"],
          ROOT,
          "grades declared bindings and invocation records against a recorded runtime "
          "inventory rather than a live daemon, so the result cannot depend on whether a "
          "model server happens to be running on the checking machine",
          ("adapters/ollama", "contracts/model-binding.schema.json")),
    Check("Identity component tests",
          [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
          ROOT / "services" / "identity",
          "the component's own tests; these establish BUILT evidence about the challenge and "
          "recovery mechanics and are explicitly NOT independent of the code they exercise. "
          "The refusal cases are the exception worth naming: they drive the lifecycle against "
          "the refusal table services/identity/CHARTER.md declared before the code existed",
          ("services/identity/tests", "services/identity/CHARTER.md")),
    Check("Record Service reference tests",
          [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
          ROOT / "services" / "record",
          "the participant's own tests; these establish BUILT evidence about local mechanics "
          "and are explicitly NOT independent of the code they exercise",
          ("services/record/tests",)),
    Check("Record Service independent witness",
          [sys.executable, "scripts/witness_record.py"], ROOT,
          "performs the witness walk declared on issue #7 without importing the participant: "
          "the service is reached only as a subprocess through its CLI, every digest is "
          "recomputed from the chain rule the charter states, and the interrupt is staged "
          "against the store from outside the service",
          ("scripts/witness_record.py",
           "services/record/src/soveraeign_record_service/cli.py")),
    Check("Console Service reference tests",
          [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
          ROOT / "services" / "console",
          "the participant's own tests; these establish BUILT evidence about local mechanics "
          "and are explicitly NOT independent of the code they exercise. The contract-shape "
          "cases are the exception worth naming: they validate the records the service emits "
          "against the schema files in services/console/contracts/, which were written before "
          "the implementation existed and are not edited to accommodate it",
          ("services/console/tests", "services/console/contracts")),
    Check("Observation Service contracts",
          [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
          ROOT / "services" / "observation",
          "no implementation exists to exercise, so these cases judge the contracts alone: a "
          "declared defeat must be refused, a record labelled schema-valid but semantically "
          "wrong must still validate so the gap stays recorded rather than passing as "
          "coverage, and the direct-edge vocabulary is read out of CHARTER.md at check time",
          ("services/observation/contracts", "services/observation/CHARTER.md")),
    Check("Asset Service reference tests",
          [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
          ROOT / "services" / "asset",
          "the participant's own tests; these establish BUILT evidence about local mechanics "
          "and are explicitly NOT independent of the code they exercise",
          ("services/asset/tests",)),
    Check("documentation reader",
          [sys.executable, "scripts/sov_docs.py", "check"], ROOT,
          "re-renders every published document from its bytes on disk and compares the page "
          "byte for byte, so a document that changed without a rebuild fails here rather than "
          "being shown under a receipt for an older version",
          ("docs/documentation.html", "docs/ingest.json", "scripts/sovdocs")),
    Check("operation surface page",
          [sys.executable, "scripts/sov_surface.py", "check"], ROOT,
          "rebuilds the page from the capability map, the service manifests and the gateway "
          "manifest at the moment of the check and compares bytes, so a page edited by hand "
          "or left behind by a manifest change fails rather than misinforming a reader",
          ("docs/surface.html", "contracts/fixtures/capability-map.reference.json",
           "bindings/mcp/manifest.json")),
    Check("MCP gateway binding",
          [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
          ROOT / "bindings" / "mcp",
          "drives the gateway through its declared JSON-RPC surface rather than calling the "
          "services behind it, and reads its evidence back out of the Record Service journal "
          "instead of trusting the gateway's return value",
          ("bindings/mcp", "bindings/mcp/manifest.json")),
    Check("repository tooling tests",
          [sys.executable, "-m", "unittest", "discover", "-s", "scripts/tests", "-v"], ROOT,
          "the harness's own tests; independent of the repository content they check, but "
          "not of the harness itself",
          ("scripts/tests",)),
)
