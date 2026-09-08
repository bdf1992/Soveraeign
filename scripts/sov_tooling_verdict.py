#!/usr/bin/env python3
"""Grade the tooling runner's verdict path from outside the tooling suite."""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parent.parent
RUNNER = ROOT / "scripts" / "run_tooling_tests.py"
DRIVER = ROOT / "scripts" / "sovtooling"
GRADED_CHECK = "repository tooling tests"
GRADED_COMMAND = "scripts/run_tooling_tests.py"

PASSING = (
    "import unittest\n\n"
    "class Ok(unittest.TestCase):\n"
    "    def test_true(self):\n"
    "        self.assertTrue(True)\n"
)
SWALLOWING = (
    "import sys\n\n"
    "sys.exit(0)   # exits at import and takes the rest of its shard with it\n"
)
FAILING = (
    "import unittest\n\n"
    "class Bad(unittest.TestCase):\n"
    "    def test_false(self):\n"
    "        self.fail('deliberate; the runner must refuse')\n"
)


def miniature(root: Path, modules: dict[str, str]) -> Path:
    tests = root / "scripts" / "tests"
    tests.mkdir(parents=True)
    shutil.copy(RUNNER, root / "scripts" / "run_tooling_tests.py")
    # The runner reads per-module costs from the driver, so a miniature tree without
    # it grades a runner that cannot start. This copy is what makes these trees a
    # reading of the real runner rather than of a decapitated one.
    shutil.copytree(DRIVER, root / "scripts" / "sovtooling")
    for name, body in modules.items():
        (tests / f"{name}.py").write_text(body, encoding="utf-8", newline="\n")
    return root / "scripts" / "run_tooling_tests.py"


def invoke(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=str(script.parents[1]),
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )


def run_case(
    modules: dict[str, str], args: tuple[str, ...], expect_zero: bool, what: str
) -> str | None:
    with tempfile.TemporaryDirectory() as raw:
        result = invoke(miniature(Path(raw), modules), *args)
    if (result.returncode == 0) == expect_zero:
        return None
    wanted = "exit 0" if expect_zero else "a non-zero exit"
    output = (result.stdout + result.stderr).strip()[:400] or "(nothing)"
    return f"{what}: exit {result.returncode}; expected {wanted}. Output: {output}"


def verdict_defects() -> list[str]:
    cases = (
        ({"test_ok": PASSING, "test_bad": FAILING}, (), False, "one failing module"),
        # This slot held `--failfast`, which the runner never implemented: argv was
        # ignored, so the flag did nothing and the case graded the runner by accident.
        # Once the runner grew a real parser the same case began grading argparse's
        # usage error instead, before any module loaded. Both halves are now named.
        ({"test_ok": PASSING, "test_bad": FAILING}, ("--weights",), False,
         "failing module under a flag the runner does implement"),
        ({"test_ok": PASSING}, ("--no-such-flag",), False,
         "an unrecognized flag is refused rather than ignored"),
        ({"test_ok": PASSING}, (), True, "one passing module"),
        ({}, (), False, "no test modules"),
        # A module that exits at import kills its shard, which then returns 0 and
        # simply omits its modules. Until the runner reported per-module costs there
        # was nothing to compare against the discovered population, and this tree
        # reported PASS over tests that never executed. Base b1448ee exits 0 here.
        ({"test_ok": PASSING, "test_gone": SWALLOWING}, (), False,
         "a module that exits at import is not silently dropped"),
    )
    return [
        defect
        for defect in (
            run_case(modules, args, expect_zero, what)
            for modules, args, expect_zero, what in cases
        )
        if defect is not None
    ]


def identity_defects() -> list[str]:
    """Require the named repository check to still invoke the real tooling runner."""
    from sovverify.checks import CHECKS

    named = [check for check in CHECKS if check.name == GRADED_CHECK]
    if len(named) != 1:
        return [
            f"check table holds {len(named)} checks named {GRADED_CHECK!r}; exactly one is required"
        ]
    command = [str(part).replace("\\", "/") for part in named[0].command]
    if GRADED_COMMAND not in command:
        return [
            f"{GRADED_CHECK!r} runs {command}, not {GRADED_COMMAND}; the suite can be bypassed without changing check count"
        ]
    return []


def main() -> int:
    defects = identity_defects() + verdict_defects()
    if defects:
        for defect in defects:
            print(f"  {defect}")
        print("FAIL: tooling verdict path cannot be trusted")
        return 1
    print("PASS: tooling verdict (broken trees refuse, clean tree passes, empty tree refuses, check identity bound)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
