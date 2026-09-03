"""The checks that grade what this repository says about itself.

Split from `checks.py` on the pressure that split `participants.py` out of it,
and along the same kind of seam. A check over a contract, a schema, or a
participant's code grades something the repository builds. These grade the
record it keeps: standing, traps, status claims, the owner queue, phase floors,
declared closures, signposts, diagrams, and the witness receipts behind them. A
defect here is the repository describing itself wrongly, which is the failure no
amount of passing code catches.

`checks.py` splices this group back in at the position it held, so the order a
run prints is unchanged.
"""

from __future__ import annotations

import sys

from sovverify.shape import ROOT, Check

RECORD_CHECKS = (
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
    Check("diagram provenance", [sys.executable, "scripts/sov_diagrams.py"], ROOT,
          "recomputes each declared source digest from the file's bytes at the moment of "
          "the check; it never reads a diagram's own claim about being current",
          ("diagrams",)),
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
)
