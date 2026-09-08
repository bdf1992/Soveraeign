"""The checks over what one participant says to another.

Split from `checks.py` on the same seam that put the harness surface in `harness.py`:
a crossing is neither a repository artifact nor a participant's own tree. It is the
edge between two seats, and what has to hold there is different in kind - not "is this
file current" but "did the standing, the questions, and the dissent survive the trip".

This is the Communications domain's verification surface. The competence it grades is
declared in `contracts/seat-etiquette.json` and modeled in
`contracts/seat-message.schema.json`: a participant may change how something reads and
may never change what it is worth. Every check here reads the table rather than a list
of cases, so adding an act or a duty is a change to the contract alone.
"""

from __future__ import annotations

import sys

from sovverify.shape import ROOT, Check

CROSSING_CHECKS = (
    Check("seat carriage duties hold",
          [sys.executable, "scripts/witness_seats.py"], ROOT,
          "starts from a positive fixture the checker admits, breaks it in a way "
          "contracts/seat-etiquette.json forbids but no fixture covers, and requires a defect - "
          "so it answers whether the checker reads the table or recognises its fixtures. This "
          "is where a crossing's standing is actually protected: a carried judgement item, "
          "dissent, residual or stall dropped or edited between seats is the failure the whole "
          "contract exists to catch, and until now nothing in the gate ran it",
          ("contracts/seat-etiquette.json", "contracts/seat-message.schema.json",
           "contracts/fixtures/seat-message.fixtures.json",
           "contracts/fixtures/seat-topology.reference.json",
           "scripts/witness_seats.py", "scripts/sovkernel/seat_etiquette.py")),
)
