from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"expected repair text absent in {path.relative_to(ROOT)}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")


model = ROOT / "scripts/sovcustody/model.py"
replace_once(
    model,
    "from sovcustody import circuit as circuitmod  # noqa: E402\n",
    "from sovcustody import circuit as circuitmod  # noqa: E402\n"
    "from sovcustody import collections as collectionmod  # noqa: E402\n",
)
text = model.read_text(encoding="utf-8")
start = text.index("def collection_paths() -> tuple[Path, ...]:")
end = text.index("def by_id(custody_id: str)", start)
replacement = '''def collection_paths() -> tuple[Path, ...]:\n    return collectionmod.paths(COLLECTION, COLLECTION_DIR)\n\n\ndef collections() -> list[dict[str, Any]]:\n    return collectionmod.documents(COLLECTION, COLLECTION_DIR)\n\n\ndef custodies(phase: str | None = None) -> list[dict[str, Any]]:\n    return collectionmod.records(COLLECTION, COLLECTION_DIR, phase)\n\n\n'''
model.write_text(text[:start] + replacement + text[end:], encoding="utf-8", newline="\n")

progress = ROOT / "scripts/sov_phase_progress.py"
replace_once(
    progress,
    "import subprocess\nimport re\n\nimport sov_f2_gate\nfrom sovcustody import circuit as custody_circuit\n",
    "import subprocess\n\nimport sov_f2_gate\n"
    "from sov_active_phase_progress import grade_active_phase, phase_record, status_phase\n",
)
text = progress.read_text(encoding="utf-8")
start = text.index("def status_phase() -> str:")
end = text.index("def grade(report: dict, contract: dict)", start)
progress.write_text(text[:start] + text[end:], encoding="utf-8", newline="\n")

commands = ROOT / "scripts/sovcustody/commands.py"
replace_once(
    commands,
    '''def command_reconcile(args: argparse.Namespace) -> int:\n    """Every phase exit clause against the custody that holds it.\n\n    The clauses are read from contracts/phases.json, which pins the defining\n    documents by digest. Restating them here would be a second copy of the exit,\n    and a second copy is where a narrowed definition enters.\n    """\n''',
    '''def command_reconcile(args: argparse.Namespace) -> int:\n    """Read phase exit clauses against their phase-scoped custody."""\n''',
)

checks = ROOT / "scripts/sovverify/checks.py"
replace_once(
    checks,
    '''           "contracts/custodies.json", "contracts/custodies",\n           "scripts/sov_f2_gate.py", "scripts/sov_phase_progress.py", "scripts/sovcustody")),\n''',
    '''           "contracts/custodies.json", "contracts/custodies", "scripts/sov_f2_gate.py",\n           "scripts/sov_phase_progress.py", "scripts/sovcustody")),\n''',
)
# The check table was exactly one line over after expanding the phase-progress
# evidence closure. Keep normal two-line top-level spacing while dropping one
# redundant empty line before the table itself.
replace_once(checks, "from sovverify.shape import ROOT, Check\n\n\nREPOSITORY_CHECKS", 
             "from sovverify.shape import ROOT, Check\n\nREPOSITORY_CHECKS")
