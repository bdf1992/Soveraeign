"""Grade every witness probe on whether it can still reach the subject it names.

`witness/probes/` holds the code a witness wrote to take an observation. A probe
that has rotted is dead evidence dressed as live evidence: the receipt it
produced still reads as a measurement, and nothing says the code behind it
stopped working.

Grading a probe is deliberately not running its subject through a gate. A probe
observes and exits 0 whether or not the subject survives, and that boundary is
what makes it a witness rather than a judge. Nothing here reads whether a check
held; it reads only whether the probe can still get to the thing it examines.
`sovwitness/reach.py` reads the source; this module grades what it read.

Two tiers, because reaching is expensive:

- `inspect` is static and lives inside `scripts/verify.py`. It requires the
  repository paths the module's own constants declare as its reach to exist and
  to be used.
- `run` executes each probe and grades the process and the report it produced.
  It is out of the verification budget: the three probes shipped on PR #119 cost
  12.7s together, against a 15s ceiling for the whole suite.

## What this cannot do, stated plainly

A probe is graded here on what it declares about itself, and that is the
repository's recurring defect appearing inside the tool written to catch it. The
limit is real and is recorded rather than papered over:

- The reach constants are read from source. A probe can name a path that exists
  while reaching somewhere else entirely. Requiring every declared constant to be
  referenced kills the cheap decoy; it does not make the declaration true.
- `run` reads the report the probe wrote about its own health. A probe that
  catches its reach failure and reports `{"held": true}` is indistinguishable
  here from one that reached, and no amount of report-reading fixes that, because
  the report is the probe's own testimony. Such a handler is reported as debt,
  which is the most that is decidable from outside.

What catches a probe that lies about its results is not in this module. It is the
receipt digesting the probe under `observed_state_addresses`, so that editing the
probe turns its receipt `STALE_PROBE` (`sovwitness/records.py`), plus a reader who
opens the probe. Neither is automated and neither is claimed to be.

What `run` must not do is judge by exit code alone. Every probe here exits 0 by
design, so a clean exit is not evidence of reaching, while a dirty one is
evidence against it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import ast
import json
import subprocess
import sys

from sovwitness import reach
from sovwitness.records import observations_dir, receipts
from sovwitness.shape import ReceiptError, resolve_address

REACH_TIMEOUT_SECONDS = 300
LIVE, DEAD = "LIVE", "DEAD"
# Verdicts that fail the check. A probe that cannot be reached through is not
# weak evidence; it is evidence that stopped existing without saying so.
FAILING_VERDICTS = frozenset({DEAD})


def probes_dir(root: Path) -> Path:
    return root / "witness" / "probes"


def inspect(path: Path, root: Path) -> dict[str, Any]:
    """Read one probe's source and grade whether its declared reach still exists."""
    result: dict[str, Any] = {"probe": path.name, "verdict": LIVE,
                              "reaches": [], "defects": [], "debts": []}
    try:
        tree = ast.parse(path.read_bytes(), filename=str(path))
    except (SyntaxError, ValueError) as broken:
        result.update(verdict=DEAD, defects=[f"does not parse: {broken}"])
        return result

    targets = reach.reach_targets(tree)
    result["reaches"] = sorted(set(targets.values()))
    if not targets:
        result["defects"].append("declares no reach target, so nothing says what it observes")
    used = reach.used_names(tree)
    for name, target in sorted(targets.items()):
        if not (root / target).exists():
            result["defects"].append(f"declared reach {target} is not in the tree")
        elif name not in used:
            result["defects"].append(
                f"{name} declares reach {target} and is never used, so it stands in "
                "for a reach the probe does not take")

    result["defects"].extend(reach.entry_point_defects(tree))
    defects, debts = reach.handler_defects(tree)
    result["defects"].extend(defects)
    result["debts"].extend(debts)
    if result["defects"]:
        result["verdict"] = DEAD
    return result


def _reach_failures(report: Any) -> list[str]:
    """Every place in a probe's report where it said it could not reach the subject."""
    found: list[str] = []

    def walk(node: Any, trail: str) -> None:
        if isinstance(node, dict):
            if "probe_error" in node:
                found.append(f"{trail or 'report'}: {node['probe_error']}")
            elif node.get("held", False) is None:
                found.append(f"{trail or 'report'}: held is null with no probe_error")
            for key, value in node.items():
                walk(value, f"{trail}.{key}" if trail else str(key))
        elif isinstance(node, list):
            for index, value in enumerate(node):
                walk(value, f"{trail}[{index}]")

    walk(report, "")
    return found


def run(path: Path, root: Path) -> dict[str, Any]:
    """Execute one probe and grade the process and the report it produced."""
    result: dict[str, Any] = {"probe": path.name, "verdict": LIVE, "defects": [], "debts": []}
    try:
        done = subprocess.run([sys.executable, str(path)], capture_output=True, text=True,
                              cwd=str(root), timeout=REACH_TIMEOUT_SECONDS)
    except (subprocess.TimeoutExpired, OSError) as broken:
        result.update(verdict=DEAD, defects=[f"did not run to completion: {broken}"])
        return result
    result["exit_code"] = done.returncode
    if done.returncode != 0:
        result["defects"].append(f"exited {done.returncode}; a probe reports rather than fails")
    try:
        report = json.loads(done.stdout)
    except json.JSONDecodeError:
        result.update(verdict=DEAD, defects=result["defects"] + ["emitted no readable report"])
        return result
    if not isinstance(report, dict) or not report:
        result["defects"].append(f"report is {type(report).__name__} and carries no findings")
    failures = _reach_failures(report)
    result["reach_failures"] = failures
    result["defects"].extend(failures)
    if done.stderr.strip():
        result["debts"].append(f"wrote {len(done.stderr)} byte(s) to stderr")
    if result["defects"]:
        result["verdict"] = DEAD
    return result


def modules(root: Path) -> list[Path]:
    """Every probe under the directory, at any depth, in a stable order.

    The walk is recursive and case-folded because a non-recursive glob let a probe
    hide in a subdirectory, and `Path.glob` is case-insensitive on Windows and not
    on the Linux runner that gates the merge.
    """
    directory = probes_dir(root)
    if not directory.is_dir():
        return []
    return sorted(path for path in directory.rglob("*")
                  if path.is_file() and path.suffix.lower() == ".py"
                  and path.name.lower().startswith("probe_"))


def _strays(root: Path) -> list[str]:
    """Files in either directory that the collectors' name filters skip.

    `modules()` sees only `probe_*.py` and `receipts()` only `*.json`, so a probe
    named `check_thing.py` or a receipt named `obs.yaml` was collected by neither
    and both commands reported a clean zero. The filters are declared in the
    directory READMEs, so a stray is reported rather than failed; what is not
    acceptable is that it went unmentioned.
    """
    seen = {path.resolve() for path in modules(root)} | {p.resolve() for p in receipts(root)}
    strays: list[str] = []
    for directory in (probes_dir(root), observations_dir(root)):
        if not directory.is_dir():
            continue
        for path in sorted(directory.rglob("*")):
            if path.is_file() and path.name != "README.md" and path.resolve() not in seen:
                strays.append(f"{path.relative_to(root).as_posix()} is graded by nothing")
    return strays


def joins(root: Path) -> tuple[list[str], list[str]]:
    """Grade the receipt/probe join both ways. Returns (defects, debts).

    The declared probe address is put through the same containment the receipt's
    own addresses face, because a join that skipped it accepted a path outside the
    repository entirely.

    A receipt must also digest the probe it names. Both halves were already in
    hand here and were never joined, so `STALE_PROBE` was opt-in by the receipt's
    author — the party the rule constrains. A receipt that names a probe and omits
    it from `observed_state_addresses` stayed `CURRENT` no matter how the probe
    was edited, which made the central claim of `decisions/0076` aspirational.
    """
    # Keyed on the RESOLVED path, never the basename. A basename is a string the
    # receipt supplies, so a copy of a probe placed anywhere in the tree satisfied
    # the join: the receipt digested the copy, the real probe was edited, and the
    # run was byte-identical to a clean one. Measuring the path the address
    # actually resolves to is the difference between a check and a declaration.
    present = {path.resolve(): path for path in modules(root)}
    named: set[Path] = set()
    defects: list[str] = []
    for receipt in receipts(root):
        try:
            document = json.loads(receipt.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        telemetry = document.get("telemetry") if isinstance(document, dict) else None
        declared = telemetry.get("probe") if isinstance(telemetry, dict) else None
        if not isinstance(declared, str) or not declared.strip():
            continue
        try:
            target = resolve_address(declared, root)
        except (ReceiptError, OSError, ValueError) as broken:
            defects.append(f"{receipt.name} names probe {declared!r}: {broken}")
            continue
        resolved = target.resolve()
        named.add(resolved)
        if not target.is_file():
            defects.append(f"{receipt.name} names probe {declared}, which is not in the tree")
        elif resolved not in present:
            defects.append(
                f"{receipt.name} names {declared}, which is not a probe module in "
                "witness/probes/")
        observed = document.get("observed") if isinstance(document, dict) else None
        addresses = observed.get("observed_state_addresses") if isinstance(observed, dict) else []
        if declared not in (addresses if isinstance(addresses, list) else []):
            defects.append(
                f"{receipt.name} names probe {declared} and does not digest it, so editing "
                "the probe cannot turn this receipt STALE_PROBE")
    debts = [f"{present[path].name} is named by no receipt"
             for path in sorted(set(present) - named)]
    return defects, debts + _strays(root)
