"""What the AI-native standard declares, read from the contract rather than remembered.

`AI-NATIVE.md` is the owning document and `contracts/ai-native-qualifications.json`
compiles it. Nothing in this package restates a rule the table already carries, so
changing what is admissible is a contract change with a fixture behind it.
"""

from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovsession import principals  # noqa: E402

TABLE = ROOT / "contracts" / "ai-native-qualifications.json"
SCHEMA = ROOT / "contracts" / "ai-native-assessment.schema.json"
CORPUS = ROOT / "conformance" / "fixtures" / "ai-native" / "assessment-cases.json"
ASSESSMENTS = ROOT / "conformance" / "assessments"

SCORE_ORDER = ("NONE", "PARTIAL", "FULL")


def read(path: Path) -> object:
    """Read one JSON document."""
    return json.loads(path.read_text(encoding="utf-8"))


def load_table(path: Path = TABLE) -> dict:
    """Read the compiled AI-native standard."""
    record = read(path)
    assert isinstance(record, dict)
    return record


def scenario_status(root: Path, table: dict) -> dict[str, str]:
    """Every founding scenario's id and declared status, read from its own bytes.

    The status is what decides whether a scenario can evidence a qualification, so it is
    taken from the scenario file each time rather than mirrored into the table, where it
    would drift the first day someone made one executable.
    """
    found: dict[str, str] = {}
    for path in sorted((root / table["scenario_root"]).glob("*.yaml")):
        ident = status = ""
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("id:"):
                ident = line.split(":", 1)[1].strip()
            elif line.startswith("status:"):
                status = line.split(":", 1)[1].strip()
        if ident:
            found[ident] = status or "UNDECLARED"
    return found


def context() -> tuple[dict, dict, dict[str, str], dict | None]:
    """The standard, the record shape, what the scenarios can prove, and who is registered."""
    table = load_table()
    schema = read(SCHEMA)
    assert isinstance(schema, dict)
    registry, _ = principals.load(ROOT)
    return table, schema, scenario_status(ROOT, table), registry
