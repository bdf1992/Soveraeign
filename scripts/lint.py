#!/usr/bin/env python3
"""Fast dependency-free repository hygiene checks."""

from __future__ import annotations

from pathlib import Path
import ast
import os
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".md", ".py", ".json", ".yaml", ".yml", ".toml"}
TEXT_NAMES = {".cursorrules", ".env.example", ".gitattributes", ".gitignore"}
# .local/ is gitignored runtime state (scheduled-run ledger and captures); it is never
# repository text and may legitimately contain local paths from captured tool output.
SKIP_PARTS = {".git", ".venv", "__pycache__", "lineage", ".local"}
MAX_PRODUCTION_LINES = 300
# The module budget reached only `scripts/` and packaged `src/` trees, so an adapter,
# binding, worker, or the oracle itself could grow past the limit unseen. Adding a root
# here surfaces existing overruns; each is entered as named debt below, never grandfathered.
PRODUCTION_ROOTS = ("scripts/", "adapters/", "bindings/", "workers/", "conformance/")
# Retired 2026-08-23: core.py was split into store.py (custody and receipts),
# authority.py (grants and sessions), runs.py (leased derivation), and
# projections.py (rebuildable views). Re-entering a module here records debt; it
# does not grandfather it.
KNOWN_MODULE_DEBT: dict[str, str] = {
    "scripts/verify.py": (
        "the CHECKS table has grown to 24 entries and is now most of the file; the split is "
        "the table into its own module, leaving the runner behind. Entered 2026-08-24 while "
        "the landing branch was frozen, because refactoring the verification harness during "
        "a landing freeze risks the gate every session depends on. Owed to the verification "
        "domain, not paid"
    ),
    "conformance/run.py": (
        "the oracle grew past the limit before the budget reached conformance/ at all, so "
        "this is an overrun the gate had never seen rather than a new one. Observed in "
        "reports/2026-08-23-stack-certification.md and entered 2026-08-24 when the budget "
        "was widened to adapters/, bindings/, workers/, and conformance/. Owed to the "
        "conformance domain, which holds the file, not paid"
    ),
}
SECRET_PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "OpenAI-style token": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
}
LOCAL_PATH_PATTERNS = (
    re.compile(r"(?:^|[\s'\"])/Users/[^/\s]+/"),
    re.compile(r"(?:^|[\s'\"])/home/[^/\s]+/"),
    re.compile(r"(?:^|[\s'\"])[A-Za-z]:\\Users\\[^\\\s]+\\"),
)


def repository_text_files() -> list[Path]:
    """Return lintable repository text without descending into excluded trees."""
    paths: list[Path] = []
    for raw_root, dirs, files in os.walk(ROOT, topdown=True):
        # Pruning here matters: filtering paths after Path.rglob() still traverses
        # .git object storage, virtualenvs and local runtime captures before throwing
        # their entries away. The hygiene population is unchanged; the excluded trees
        # simply never become I/O work.
        dirs[:] = sorted(name for name in dirs if name not in SKIP_PARTS)
        root = Path(raw_root)
        for name in sorted(files):
            path = root / name
            if path.suffix in TEXT_SUFFIXES or path.name in TEXT_NAMES:
                paths.append(path)
    return sorted(paths)


def check_text(path: Path, text: str) -> list[str]:
    relative = path.relative_to(ROOT)
    defects = []
    if "\r" in text:
        defects.append(f"{relative}: CRLF line endings")
    if text and not text.endswith("\n"):
        defects.append(f"{relative}: missing final newline")
    for number, line in enumerate(text.splitlines(), 1):
        if line.endswith((" ", "\t")):
            defects.append(f"{relative}:{number}: trailing whitespace")
        if "\t" in line and path.suffix == ".py":
            defects.append(f"{relative}:{number}: tab in Python source")
    for name, pattern in SECRET_PATTERNS.items():
        if pattern.search(text):
            defects.append(f"{relative}: possible {name}")
    for pattern in LOCAL_PATH_PATTERNS:
        if pattern.search(text):
            defects.append(f"{relative}: local absolute user path")
            break
    return defects


def check_python(path: Path, text: str) -> tuple[list[str], list[str]]:
    relative = path.relative_to(ROOT).as_posix()
    defects = []
    warnings = []
    try:
        tree = ast.parse(text, filename=relative)
    except SyntaxError as error:
        return [f"{relative}:{error.lineno}: syntax error: {error.msg}"], warnings
    if path.name != "__init__.py":
        has_future = any(
            isinstance(node, ast.ImportFrom)
            and node.module == "__future__"
            and any(alias.name == "annotations" for alias in node.names)
            for node in tree.body
        )
        if not has_future:
            defects.append(f"{relative}: missing future annotations import")
    lines = len(text.splitlines())
    is_production = (
        "/src/" in f"/{relative}"
        or relative.startswith(PRODUCTION_ROOTS)
    ) and "/tests/" not in f"/{relative}"
    if is_production and lines > MAX_PRODUCTION_LINES:
        if relative in KNOWN_MODULE_DEBT:
            warnings.append(
                f"KNOWN DEBT: {relative} has {lines} lines; {KNOWN_MODULE_DEBT[relative]}"
            )
        else:
            defects.append(
                f"{relative}: {lines} lines exceeds production limit {MAX_PRODUCTION_LINES}"
            )
    return defects, warnings


def main() -> int:
    defects = []
    warnings = []
    paths = repository_text_files()
    if not paths:
        print("FAIL: repository text population is empty")
        return 1
    python_count = 0
    for path in paths:
        # Read bytes, never Path.read_text: universal-newline translation silently
        # rewrites CR and CRLF to LF, which made the check_text CRLF rule unreachable
        # on every platform. Decoding here keeps the line endings the file really has.
        data = path.read_bytes()
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as error:
            relative = path.relative_to(ROOT).as_posix()
            defects.append(f"{relative}: not valid UTF-8 at byte {error.start}")
            continue
        defects.extend(check_text(path, text))
        if path.suffix == ".py":
            python_count += 1
            python_defects, python_warnings = check_python(path, text)
            defects.extend(python_defects)
            warnings.extend(python_warnings)
    for warning in warnings:
        print(f"WARN: {warning}")
    if defects:
        for defect in defects:
            print(f"FAIL: {defect}")
        return 1
    print(
        f"PASS: repository hygiene ({len(paths)} text files, {python_count} Python modules, "
        f"{len(warnings)} named debt)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
