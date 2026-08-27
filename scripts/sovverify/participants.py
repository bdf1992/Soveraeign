"""Checks that run inside a participant's own tree, against that participant's own tests.

These establish `BUILT` evidence about local mechanics and are explicitly NOT
independent of the code they exercise (`AGENTS.md`, Evidence and standing). Each
entry still states its `relation`, because a self-test that does not say it is a
self-test is the claim this repository refuses.

Split out of `checks.py` when that file reached the 300-line module ceiling. The
seam is real rather than arithmetic: the working directory is what tells a reader
whether a check speaks for the repository or for one participant.
"""

from __future__ import annotations

import sys

from sovverify.shape import ROOT, Check

PARTICIPANT_CHECKS = (
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
    Check("Host Service reference tests",
          [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
          ROOT / "services" / "host",
          "the participant's own positive and defeating cases; they establish BUILT evidence for read-health mechanics only and never witness the adapter or host effect",
          ("services/host/tests", "services/host/contracts", "adapters/host")),
    Check("MCP gateway binding",
          [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
          ROOT / "bindings" / "mcp",
          "drives the gateway through its declared JSON-RPC surface rather than calling the "
          "services behind it, and reads its evidence back out of the Record Service journal "
          "instead of trusting the gateway's return value",
          ("bindings/mcp", "bindings/mcp/manifest.json")),
)
