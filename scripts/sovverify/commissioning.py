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
)
