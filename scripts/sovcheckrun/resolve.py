"""Turn a declared closure expression into the thing a shell would actually run.

Every refusal here is one an independent witness drove against the first version
of this reader, which took the first token ending in `.py` and looked for the
substring `__name__ == "__main__"`. That admitted `python a.py && python mute.py`,
admitted a file whose only occurrence of the substring was inside its docstring,
refused a real guard written with single quotes, and refused the `PYTHONPATH=`
form that is the one shape that repairs `custody:record-custody`.
"""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple
import ast
import shlex

#: Tokens that mean the expression is more than one command. A reader that takes
#: the first `.py` token cannot say which stage it graded, so it grades none.
SHELL_OPERATORS = frozenset({"&&", "||", ";", "|", ">", ">>", "<", "&"})

INTERPRETERS = ("python", "python3")


class Target(NamedTuple):
    """What a closure expression resolves to, or why it does not resolve."""

    mode: str            # "path", "module", or "" when unresolved
    target: str          # the file path or the dotted module name
    argv: list[str]      # the tokens after the target
    path: Path | None    # the file on disk, when one is known
    refusal: str         # a refusal code, or "" when resolved


def _interpreter(token: str) -> bool:
    name = Path(token).name
    return name in INTERPRETERS or name.startswith("python3.")


def has_entry_point(path: Path) -> bool:
    """True when the module has a real top-level `if __name__ == "__main__":`.

    Parsed rather than searched. The substring appears in docstrings and comments
    across this repository, and a real guard may be written with either quote
    style, so a text match is wrong in both directions.
    """
    try:
        tree = ast.parse(path.read_bytes().decode("utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return False
    for node in tree.body:
        if not isinstance(node, ast.If):
            continue
        for side in ast.walk(node.test):
            if isinstance(side, ast.Name) and side.id == "__name__":
                return True
    return False


def module_paths(root: Path, dotted: str) -> list[Path]:
    """Every file in the tree that could serve `python -m <dotted>`, sorted.

    More than one match is reported rather than silently resolved: taking the
    first sorted candidate picked `charting/model.py` for `model`, which is not
    a decision a reader of a contract should make on the contract's behalf.
    """
    relative = Path(*dotted.split("."))
    found: list[Path] = []
    for pattern in (f"**/{relative}.py", f"**/{relative}/__main__.py"):
        for candidate in sorted(root.glob(pattern)):
            if ".git" in candidate.parts or "__pycache__" in candidate.parts:
                continue
            found.append(candidate)
    return found


def resolve(root: Path, expression: str) -> Target:
    """Resolve one closure expression, or name the refusal that stops it."""
    try:
        tokens = shlex.split(expression)
    except ValueError:
        return Target("", "", [], None, "CLOSURE_CHECK_UNPARSEABLE")
    if not tokens:
        return Target("", "", [], None, "CLOSURE_CHECK_UNPARSEABLE")
    if any(token in SHELL_OPERATORS for token in tokens):
        return Target("", "", [], None, "CLOSURE_CHECK_COMPOUND")

    # Leading NAME=value assignments are part of the invocation, not arguments.
    while tokens and "=" in tokens[0] and not tokens[0].startswith("-") \
            and not tokens[0].endswith(".py"):
        tokens = tokens[1:]
    if tokens[:1] == ["env"]:
        tokens = tokens[1:]
        while tokens and "=" in tokens[0] and not tokens[0].startswith("-"):
            tokens = tokens[1:]
    if not tokens or not _interpreter(tokens[0]):
        return Target("", "", [], None, "CLOSURE_CHECK_NOT_PYTHON")

    rest = tokens[1:]
    if rest[:1] == ["-m"]:
        if len(rest) < 2:
            return Target("", "", [], None, "CLOSURE_CHECK_UNPARSEABLE")
        dotted, argv = rest[1], rest[2:]
        candidates = module_paths(root, dotted)
        if not candidates:
            return Target("module", dotted, argv, None, "CLOSURE_CHECK_TARGET_MISSING")
        if len(candidates) > 1:
            return Target("module", dotted, argv, candidates[0], "CLOSURE_CHECK_AMBIGUOUS")
        return Target("module", dotted, argv, candidates[0], "")

    script = next((token for token in rest if token.endswith(".py")), None)
    if script is None:
        return Target("", "", [], None, "CLOSURE_CHECK_NOT_PYTHON")
    path = (root / script).resolve()
    if not path.is_file():
        return Target("path", script, [], None, "CLOSURE_CHECK_TARGET_MISSING")
    return Target("path", script, [t for t in rest if t != script], path, "")
