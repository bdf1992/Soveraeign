from __future__ import annotations

from pathlib import Path

helper = Path(__file__).with_name("gap_195_readiness_definition.py")
text = helper.read_text(encoding="utf-8")
old = '''def refresh_clarity() -> None:
    for path in (
        "PRD.md",
        "SPEC.md",
        "contracts/README.md",
        "diagrams/source-reader-recording.md",
        "diagrams/crossing-typology.md",
        "diagrams/requirement-lifecycle.md",
    ):
'''
new = '''def refresh_clarity() -> None:
    for path in (
        "PRD.md",
        "SPEC.md",
        "contracts/README.md",
    ):
'''
if old not in text:
    raise SystemExit("expected refresh_clarity tuple absent")
text = text.replace(old, new, 1)
old_reviews = '    candidates = list(coverage.get("artifacts", coverage).keys())\n'
new_reviews = '    candidates = list(coverage.get("reviews", {}).keys())\n'
if old_reviews not in text:
    raise SystemExit("expected legacy clarity coverage lookup absent")
text = text.replace(old_reviews, new_reviews, 1)
old_refresh = '''def refresh() -> None:
    run("python", "scripts/sov_diagrams.py", "stamp")
    run("python", "scripts/sov_docs.py", "build")
    refresh_clarity()
'''
new_refresh = '''def refresh() -> None:
    # SPEC is an input to the derived participant surface. Rebuild from the
    # changed source before recording any final documentation or snapshot.
    run("python", "scripts/sov_capability.py", "build")
    run("python", "scripts/sov_interface.py", "build")
    run("python", "scripts/sov_surface.py", "render")
    run("python", "scripts/sov_diagrams.py", "stamp")
    run("python", "scripts/sov_docs.py", "build")
    refresh_clarity()
'''
if old_refresh not in text:
    raise SystemExit("expected refresh function absent")
text = text.replace(old_refresh, new_refresh, 1)
helper.write_text(text, encoding="utf-8", newline="\n")

runner = Path("scripts/run_tooling_tests.py")
runner_text = runner.read_text(encoding="utf-8")
old_measurement = '''# Remeasured 2026-08-27 at 89 modules, and the point of remeasuring is that two
# of the three entries had stopped buying anything: test_sov_branch at 10 gave
# its shard 20 peers where dropping the entry also gave 20, and test_sov_docs at
# 10 gave 19 where dropping it gave 17 - actively worse than no weight at all.
# A weight is a measurement against a module population, so it expires when the
# population grows. 20 and 18 give 14 and 16 against unweighted 17 and 20, which
# is a real gap rather than the single peer the smallest working pair buys.
# test_verify_clocks at 7 still works: 22 peers against 27 unweighted.
MODULE_WEIGHTS = {"test_sov_docs.py": 20, "test_verify_clocks.py": 7,
                  "test_sov_branch.py": 18}
'''
new_measurement = '''# Remeasured 2026-08-31 at 97 modules after the commissioning-contract test was
# added. The 89-module weights had expired: docs at 20 and branch at 18 no longer
# bought shorter shards, and clocks at 7 over-weighted a much smaller Linux cost.
# Holding the other two measured weights constant, 24 gives test_sov_docs 15 peers
# instead of 32 unweighted, 32 gives test_sov_branch 8 instead of 30, and 3 gives
# test_verify_clocks 36 instead of 38. The resulting synthetic loads are
# 39/38/38/38. These remain scheduling hints, never evidence or budget changes.
MODULE_WEIGHTS = {"test_sov_docs.py": 24, "test_verify_clocks.py": 3,
                  "test_sov_branch.py": 32}
'''
if old_measurement not in runner_text:
    raise SystemExit("expected 89-module tooling measurement absent")
runner.write_text(runner_text.replace(old_measurement, new_measurement, 1),
                  encoding="utf-8", newline="\n")
