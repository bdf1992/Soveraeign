"""Checks that read the active phase's exit custodies through their own closure commands.

A commissioning check is neither repository hygiene nor a participant's self-test: it
drives the live participation layers as a fresh participant would and grades the result
through the independent instrument in `conformance/`. The group is kept apart so the
repository table does not absorb every clause the open phase adds, and so a reader can
see which checks the phase exit itself leans on.
"""

from __future__ import annotations

import sys

from sovverify.shape import ROOT, Check

COMMISSIONING_CHECKS = (
    Check("fresh participation slice", [sys.executable, "scripts/sov_fresh.py", "selfcheck"],
          ROOT,
          "drives the live session, lease, node-interface, authority and Record layers in a "
          "temporary store as a declared fixture principal and grades what they resolved "
          "through conformance/commissioning.py, which imports none of them; the three "
          "defeating variants prove the grade can fail",
          ("scripts/sov_fresh.py", "scripts/sovfresh", "conformance/commissioning.py",
           "contracts/custodies/phase-1-5.json")),
    Check("discovery and reuse slice", [sys.executable, "scripts/sov_reuse.py", "selfcheck"],
          ROOT,
          "reads a fixture result the way a second fresh participant would - custody member, "
          "witness record, receipts, landed bytes, restored journal - and grades P15-Q3 "
          "through conformance/commissioning.py; nine defeating variants each fail the "
          "predicates they declare. The clause's own closure command, which until now "
          "nothing in the suite ran",
          ("scripts/sov_reuse.py", "scripts/sovreuse", "conformance/commissioning.py",
           "contracts/custodies/phase-1-5.json")),
    Check("definition recurrence slice", [sys.executable, "scripts/sov_recurrence.py",
                                          "selfcheck"], ROOT,
          "synthesizes a candidate Definition from settled experience under a fixture root, "
          "grades P15-Q4 through conformance/commissioning.py, and proves the candidate takes "
          "no standing and the primitives compose under an institution the founder did not "
          "predict; nine defeating variants each fail the predicates they declare, and the "
          "positive variant is checked for citing no member nobody witnessed. This grades the "
          "instrument, not the clause: the fixture root is temporary and the live reading "
          "against this repository is run by no check here",
          ("scripts/sov_recurrence.py", "scripts/sovrecurrence", "conformance/commissioning.py")),
    Check("node journal custody", [sys.executable, "scripts/sov_node.py", "journals"], ROOT,
          "replays every journal export under nodes/ with the Record Service's own verifier, "
          "which recomputes each entry digest from its contents, and resolves every "
          "self-report citation into the export it names by address, head and entry id; "
          "the head held outside an export stays the witness's, so a truncation is caught "
          "there, not here",
          ("nodes", "reports/observations", "scripts/sovnode/journal.py", "scripts/sov_node.py",
           "services/record/src/soveraeign_record_service/custody.py")),
)
