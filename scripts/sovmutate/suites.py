"""Test-suite ownership for mutation targets.

A mutation score is meaningful only when the command actually exercises the
file being mutated. Specific owners precede the broad scripts fallback; an
unclaimed production file is refused by the caller rather than scored against
an unrelated suite.
"""

from __future__ import annotations

from pathlib import Path
import sys


def declarations(root: Path) -> tuple[tuple[str, tuple[str, ...], Path], ...]:
    """Ordered path-prefix to test-command ownership declarations."""
    return (
        ("conformance", ("-m", "unittest", "discover", "-s", "conformance/tests", "-q"), root),
        (str(Path("bindings/sov")),
         ("-m", "unittest", "discover", "-s", "bindings/sov/tests", "-q"), root),
        (str(Path("services/asset")),
         ("-m", "unittest", "discover", "-s", "tests", "-q"), root / "services" / "asset"),
        (str(Path("services/console")),
         ("-m", "unittest", "discover", "-s", "tests", "-q"), root / "services" / "console"),
        (str(Path("services/host")),
         ("-m", "unittest", "discover", "-s", "tests", "-q"), root / "services" / "host"),
        (str(Path("adapters/host")),
         ("-m", "unittest", "discover", "-s", "tests", "-q"), root / "services" / "host"),
        (str(Path("services/registry")),
         ("-m", "unittest", "scripts.tests.test_registry_horizontal", "-q"), root),
        (str(Path("scripts/sov_mutate.py")), ("scripts/sov_mutate.py", "selfcheck"), root),
        (str(Path("scripts/sovmutate")), ("scripts/sov_mutate.py", "selfcheck"), root),
        (str(Path("scripts/sov_capability.py")),
         ("-m", "unittest", "scripts.tests.test_capability_map", "-q"), root),
        (str(Path("scripts/sovkernel/capability_map.py")),
         ("-m", "unittest", "scripts.tests.test_capability_map", "-q"), root),
        (str(Path("scripts/sovschedule")), (
            "-m", "unittest",
            "scripts.tests.test_automation_authoring",
            "scripts.tests.test_automation_control",
            "scripts.tests.test_automation_health",
            "scripts.tests.test_automation_intent", "-q"), root),
        (str(Path("scripts/sov_clarity.py")),
         ("-m", "unittest", "scripts.tests.test_sov_clarity", "-q"), root),
        (str(Path("scripts/sovclarity")),
         ("-m", "unittest", "scripts.tests.test_sov_clarity", "-q"), root),
        (str(Path("scripts/sovcustody/lifecycle.py")),
         ("-m", "unittest", "scripts.tests.test_sov_custody_lifecycle", "-q"), root),
        (str(Path("scripts/sovcustody")),
         ("-m", "unittest", "scripts.tests.test_custody_boards", "-q"), root),
        (str(Path("scripts/sov_custody.py")), (
            "-m", "unittest",
            "scripts.tests.test_custody_boards",
            "scripts.tests.test_sov_custody_lifecycle", "-q"), root),
        ("scripts", ("-m", "unittest", "discover", "-s", "scripts/tests", "-q"), root),
    )


def suite_for(path: Path, root: Path) -> tuple[tuple[str, ...], Path] | None:
    """The command and cwd that exercise ``path``, or None if unclaimed."""
    try:
        relative = str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return None
    for prefix, argv, cwd in declarations(root):
        if relative == prefix or relative.startswith(prefix + ("\\" if "\\" in relative else "/")):
            return (sys.executable,) + argv, cwd
    return None
