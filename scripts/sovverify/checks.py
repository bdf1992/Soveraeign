"""The repository-owned half of the check table, and the `Check` every entry is.

Every entry states in `relation` how the check avoids relying on the thing it
checks. That sentence is the check's warrant; an entry without one is a command,
not evidence.

The table lives apart from the runner so it can grow without dragging the runner
past its line budget, and it is now split again on the same pressure and along a
real seam: a check whose working directory is a participant's own tree is running
that participant's own tests, which is a different kind of evidence from a check
the repository owns over its contracts. Those live in `participants.py`. `CHECKS`
is both, and `scripts/verify.py` reads only `CHECKS`.
"""

from __future__ import annotations

import sys

from sovverify.participants import PARTICIPANT_CHECKS
from sovverify.record import RECORD_CHECKS
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
) + RECORD_CHECKS + (
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
    Check("active phase closure checks",
          [sys.executable, "scripts/sov_custody.py", "closures", "--phase", "active", "--run"],
          ROOT,
          "runs the closure check every exit custody of the active phase declares and refuses "
          "one that prints nothing. Two Phase 1.5 exit custodies opened naming Python modules "
          "with no entry point, so the declared check exited 0 in silence and a participant "
          "reading it would call the custody closed. The static screen in sovcustody/closures.py "
          "grades every declared command in the repository including closed-phase history, but "
          "it grades a declaration and `if __name__ == \"__main__\": pass` satisfies it; only "
          "running the command measures whether it reports. The scope is the active phase "
          "because that is the set somebody is asked to close today, and running every declared "
          "command reaches history nobody is carrying. A non-zero exit from a closure check is "
          "not a defect here: refusing loudly is the check working",
          ("contracts/custodies", "contracts/custody.schema.json", "STATUS.yaml",
           "scripts/sovcustody/closures.py", "scripts/sov_custody.py")),
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
    Check("Node Interface projection",
          [sys.executable, "scripts/sov_interface.py", "check"], ROOT,
          "rebuilds from current source digests and compares the checked projection byte-for-byte; the projection cannot make itself reachable or observed",
          ("contracts/fixtures/node-interface.reference.json", "contracts/node-interface.schema.json", "scripts/sovnode")),
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
    Check("automation health",
          [sys.executable, "scripts/sov_schedule.py", "health-check"], ROOT,
          "reads the schedule declarations and the run ledger at the moment of the check "
          "and re-derives every reading, rather than believing the rendered page; the page "
          "is then compared byte for byte against that derivation so it cannot go stale "
          "silently, and where this machine holds no ledger the check says the run-history "
          "half is UNCHECKED and names the absent source instead of grading it green. An "
          "UNHEALTHY reading refuses here, which is the only alert Phase I admits",
          ("contracts/automation-health.json", ".claude/schedules", "docs/automation.html",
           "conformance/fixtures/automation-health/cases.json", "scripts/sovschedule")),
    Check("repository tooling tests", [sys.executable, "scripts/run_tooling_tests.py"], ROOT,
          "the harness's own tests; independent of the repository content they check, but "
          "not of the harness itself; the runner partitions the complete discovered module "
          "population and fails if any shard fails",
          ("scripts/tests", "scripts/run_tooling_tests.py")),
)

#: Every check, in the order a run prints them: what the repository owns, then
#: what each participant says about itself.
CHECKS = REPOSITORY_CHECKS + PARTICIPANT_CHECKS
