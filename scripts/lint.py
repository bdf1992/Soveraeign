#!/usr/bin/env python3
"""Fast dependency-free repository hygiene checks."""

from __future__ import annotations

from pathlib import Path
import ast
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".md", ".py", ".json", ".yaml", ".yml", ".toml"}
TEXT_NAMES = {".cursorrules", ".env.example", ".gitignore"}
SKIP_PARTS = {".git", ".venv", "__pycache__", "lineage"}
MAX_PRODUCTION_LINES = 300
KNOWN_MODULE_DEBT = {
    "services/asset/src/soveraeign_asset_service/core.py":
        "split storage, receipts/authority, and asset lifecycle before adding behavior",
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


def _git_population() -> list[Path] | None:
    """Return Git-admittable files, including force-added ignored paths."""
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    if result.returncode:
        return None
    return [ROOT / item.decode("utf-8", errors="surrogateescape")
            for item in result.stdout.split(b"\0") if item]


def repository_text_files() -> list[Path]:
    candidates = _git_population()
    if candidates is None:
        candidates = [path for path in ROOT.rglob("*") if path.is_file()]
    paths = []
    for path in candidates:
        if not path.is_file() or any(part in SKIP_PARTS for part in path.relative_to(ROOT).parts):
            continue
        try:
            path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        paths.append(path)
    return sorted(set(paths))


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
    is_production = "/src/" in f"/{relative}" or relative.startswith("scripts/")
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
        text = path.read_text(encoding="utf-8")
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
