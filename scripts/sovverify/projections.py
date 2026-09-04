"""Checks that rebuild a published projection from its sources and compare the bytes.

A projection is rebuildable or it is not a projection (`AGENTS.md`, State and
execution). Each check here re-derives a rendered artifact - a diagram, the node
interface, the documentation page, the operation surface, the automation page -
from the bytes it declares as sources at the moment of the check, and refuses
when the checked-in artifact does not match. None of them reads the artifact's
own claim about being current, which is the property that makes the reading
evidence rather than a restatement.

Split out of `checks.py` when that file reached the 300-line module ceiling a
second time. The seam is the same kind the first split used and is real rather
than arithmetic: these checks grade drift between a derivation and its record,
where the rest of the repository table grades a contract or the current state
against a rule. A drift check fails for a reason no contract edit can express -
somebody changed a source and did not rebuild - and that is a different finding
to hand a reader.
"""

from __future__ import annotations

import sys

from sovverify.shape import ROOT, Check

PROJECTION_CHECKS = (
    Check("diagram provenance", [sys.executable, "scripts/sov_diagrams.py"], ROOT,
          "recomputes each declared source digest from the file's bytes at the moment of "
          "the check; it never reads a diagram's own claim about being current",
          ("diagrams",)),
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
)
