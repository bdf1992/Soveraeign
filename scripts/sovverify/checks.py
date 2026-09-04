"""The repository-owned half of the check table, and the `Check` every entry is.

Every entry states in `relation` how the check avoids relying on the thing it
checks. That sentence is the check's warrant; an entry without one is a command,
not evidence.

The table lives apart from the runner so it can grow without dragging the runner
past its line budget, and it has now split twice on that pressure, each time
along a real seam rather than an arithmetic one. A check whose working directory
is a participant's own tree is running that participant's own tests, which is a
different kind of evidence from a check the repository owns over its contracts;
those live in `participants.py`. A check that rebuilds a published projection and
compares the bytes fails for a reason no contract edit can express - somebody
changed a source and did not rebuild - so it hands a reader a different finding;
those live in `projections.py`. What is left here is the repository grading its
own contracts and current state. `CHECKS` is all three, assembled in
`sovverify/__init__.py`, and `scripts/verify.py` reads only `CHECKS`.
"""

from __future__ import annotations

import sys

from sovverify.participants import PARTICIPANT_CHECKS
from sovverify.projections import PROJECTION_CHECKS
from sovverify.shape import ROOT, Check

REPOSITORY_CHECKS = (
    Check("repository hygiene", [sys.executable, "scripts/lint.py"], ROOT,
          "reads repository bytes directly with read_bytes, never a build report, and never "
          "Path.read_text whose newline translation would hide the defect it looks for",
          (".gitattributes", "scripts/lint.py")),
    Check("orientation snapshot", [sys.executable, "scripts/sov_snapshot.py", "check"],
          ROOT,
          "re-derives every number at the moment of the check - git ls-tree for the "
          "counted directories and git rev-list for the history, both of the commit at "
          "HEAD, and the working tree for the two counts the repository already "
          "computes, the check table and the capability projection - and never reads "
          "the page's own claim about being current; the page is orientation for every "
          "launched agent, which does not carry the interactive session's context to "
          "correct it (LESSONS.md L-0001). Reading the commit for the counted "
          "directories is Bdo's ruling on acceptance packet A5, and it is what stops "
          "another session's untracked file from reporting a correct page as drifted; "
          "the same ruling left the other two where they were, and the run prints which "
          "half each number belongs to",
          # The derivation moved into scripts/sovsnapshot/ and this tuple did not
          # follow it, so the emitted observation digested neither the code that
          # produces the verdict nor the check table one of the claims counts.
          ("CLAUDE.md", "scripts/sov_snapshot.py", "scripts/sovsnapshot",
           "scripts/sovverify/checks.py")),
    Check("recorded traps still hold", [sys.executable, "scripts/sov_traps.py"], ROOT,
          "re-derives every recorded trap from the repository at check time, so a trap that "
          "has stopped being true fails here instead of going stale in prose",
          ("CLAUDE.md", "scripts/sov_traps.py")),
    Check("standing claims carry a witness", [sys.executable, "scripts/sov_standing.py"], ROOT,
          "reads STATUS.yaml and the witness records by separate paths and grades one against "
          "the other, so a standing claim cannot supply the record that would support it",
          ("STATUS.yaml", "scripts/sov_standing.py")),
    Check("status claims are typed",
          [sys.executable, "scripts/sov_status_claims.py", "check"], ROOT,
          "reads STATUS.yaml line by line, not through a YAML parser that would collapse the "
          "duplicated keys, and grades it against a crosswalk holding no copy of it; an "
          "untyped field and a stale entry both fail",
          ("STATUS.yaml", "contracts/status-claims.json")),
    Check("status claim refusals fire",
          [sys.executable, "scripts/sov_status_claims.py", "selfcheck"], ROOT,
          "grades cases the oracle carries itself and never reads STATUS.yaml, so repairing the "
          "live record cannot stop a refusal being proved; a refusal no case fires is a defect",
          ("contracts/status-claims.json", "conformance/fixtures/status-claims/cases.json")),
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
    Check("witness receipts against the tree",
          [sys.executable, "scripts/sov_witness_layer.py", "records"], ROOT,
          "recomputes every digest a witness receipt declares from the subject's bytes at "
          "the moment of the check; it reads no field in which a receipt states its own "
          "freshness and never asks a subject whether it changed. Subject drift is reported "
          "as debt because a receipt observes a named commit and never claimed to describe "
          "the present; a receipt that digests nothing, or whose own probe moved, fails",
          ("witness/observations", "scripts/sovwitness/records.py")),
    Check("witness probes still reach",
          [sys.executable, "scripts/sov_witness_layer.py", "probes"], ROOT,
          "parses each probe and requires the repository paths its own source declares as "
          "its reach to exist and to be used, so a probe aimed at a deleted subject fails "
          "here rather than going on producing receipts. It grades no check the probe makes, "
          "because a probe observes and never settles. The reach is the probe's own "
          "declaration and this check says so: a probe naming a path it does not take is "
          "caught by the receipt digesting the probe, not here. Executing the probes is "
          "`sov_witness_layer.py run`, out of this budget at 12.7s",
          ("witness/probes", "scripts/sovwitness/probes.py")),
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
    Check("asset object cases",
          [sys.executable, "scripts/sov_asset_objects.py", "selfcheck"], ROOT,
          "judges a declared corpus of lawful and defeating worlds against predicates that "
          "import no participant code, so an invariant is graded before any implementation "
          "carries the objects and a defeating case that stops defeating fails the run",
          ("SPEC.md", "conformance/asset_objects.py",
           "conformance/fixtures/asset/object-cases.json")),
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
    Check("lessons loop", [sys.executable, "scripts/sov_lessons.py", "check"], ROOT,
          "parses LESSONS.md and grades each standing against the tree rather than against "
          "the page's own summary of itself, and reads what counts as EFFECTIVE out of the "
          "check table it is an entry in, so a lesson cannot assert a check that is not "
          "running. The drain count does not refuse: decisions/0029 declined that on the "
          "reasoning that failing on an eighth lesson makes capture costly exactly when "
          "capture matters, and this closes the half of that residual which taxes nobody",
          ("LESSONS.md", "contracts/lessons-loop.json", "decisions/0029-lessons-loop.md",
           "scripts/sov_lessons.py")),
    Check("phase progress floor", [sys.executable, "scripts/sov_phase_progress.py", "check"],
          ROOT,
          "re-reads SPEC.md and the conformance corpus at check time and grades the distance "
          "between them against the preserved Phase-I floor, and when STATUS names a later "
          "active phase it also requires every unearned exit custody to have an initialized "
          "stage floor and refuses regression below it. It never reads a stored board or prior "
          "gate report. The F2 gate itself is deliberately not the check: registering it would "
          "refuse every run until the phase exit is earned, which teaches a reader to ignore "
          "it. A fall refuses because a fall is attributable to the edit that caused it; a "
          "stall is printed and recorded as debt, on the reasoning decisions/0081 used to take "
          "the wall clock out of the exit code (reports/2026-08-27-phase-i-retro.md, finding 1)",
          ("SPEC.md", "STATUS.yaml", "contracts/phases.json",
           "conformance/oracle-controls.json", "contracts/phase-progress.json",
           "contracts/custodies.json", "scripts/sov_f2_gate.py",
           "scripts/sov_phase_progress.py", "scripts/sovcustody")),
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
          "raising the work-in-progress ceiling is a contract change with a case behind it. It "
          "also refuses a refusal that leaves nothing reachable: every code must name an "
          "operation that clears it, and at least one the refused participant can take alone",
          ("contracts/closure-ownership.json",
           "conformance/fixtures/closure/handoff-cases.json",
           "conformance/fixtures/closure/reachable-operations-cases.json")),
    Check("closure checks reach their parser",
          [sys.executable, "scripts/sov_closure_checks.py", "check"], ROOT,
          "drives the command each custody declares as far as its argument parser and stops "
          "before the body, rather than trusting the schema that only validated the string's "
          "shape. Resolving the path was the first version and was wrong where it mattered: "
          "it called twenty-one closure checks runnable while seven exited 2 into a usage "
          "message, so the gate was itself the defect it named. Driving the parser catches a "
          "renamed subcommand, a removed flag, and a package that is not importable as "
          "declared, and still runs no check's body - one declared check names an admission. "
          "The seven already broken are carried in contracts/closure-checks.json as attributed "
          "debt, and an entry there that starts dispatching fails, so the list cannot outlive "
          "the breakage it records. PASS means the gate can speak, never that it said yes",
          ("contracts/custody.schema.json", "contracts/custodies.json",
           "contracts/custodies", "contracts/closure-checks.json",
           "scripts/sov_closure_checks.py", "scripts/sovcheckrun")),
    Check("closure check refusals fire",
          [sys.executable, "scripts/sov_closure_checks.py", "selfcheck"], ROOT,
          "drives one fixture per declared refusal through the same grader the check above "
          "runs and fails when a refusal admits its fixture, so a refusal cannot be declared "
          "and left unwired; a declared code no fixture exercises also fails. The mute fixture is a file this package owns whose only job is "
          "to look runnable and not be: it carries the entry-point text inside its docstring, "
          "the case that defeated the first reader's substring test",
          ("scripts/sov_closure_checks.py", "scripts/sovcheckrun")),
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
    Check("Record Service independent witness",
          [sys.executable, "scripts/witness_record.py"], ROOT,
          "performs the witness walk declared on issue #7 without importing the participant: "
          "the service is reached only as a subprocess through its CLI, every digest is "
          "recomputed from the chain rule the charter states, and the interrupt is staged "
          "against the store from outside the service",
          ("scripts/witness_record.py",
           "services/record/src/soveraeign_record_service/cli.py")),
    Check("Kernel binding closure",
          [sys.executable, "scripts/sov_kernel.py", "binding-check"], ROOT,
          "rebuilds cross-service binding facts from manifests, paradigms, and Kernel transitions; it does not ask service implementations whether their declarations are coherent",
          ("services", "contracts/kernel-paradigms.json", "contracts/kernel-transitions.json")),
    Check("repository tooling tests", [sys.executable, "scripts/run_tooling_tests.py"], ROOT,
          "the harness's own tests; independent of the repository content they check, but "
          "not of the harness itself; the runner partitions the complete discovered module "
          "population and fails if any shard fails",
          ("scripts/tests", "scripts/run_tooling_tests.py")),
)

#: Every check, in the order a run prints them: what the repository owns over its
#: contracts, then the projections it must be able to rebuild, then what each
#: participant says about itself.
CHECKS = REPOSITORY_CHECKS + PROJECTION_CHECKS + PARTICIPANT_CHECKS
