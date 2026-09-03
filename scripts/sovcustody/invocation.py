"""What a declared command would actually run, read without running it.

Split from `sovcustody.closures` on the module ceiling and along a real seam:
reading a command expression is its own responsibility, and it is the half that
consumes nothing. `closures` decides what a custody's closure declaration means;
this decides what the words in it name.

Both answers are approximations by construction. `script_of` declines any
expression that is not an interpreter plus a file, because `-m` names an import
target and a non-Python command is somebody else's vocabulary. `has_entry_point`
grades whether running a module would execute anything, which is not whether it
would say anything. `closures.grade_live` is what measures that.
"""

from __future__ import annotations

from pathlib import Path
import ast
import re
import shlex

#: `python`, `python3`, `python3.12`, `pythonw`, and the Windows launcher `py`.
INTERPRETER = re.compile(r"^(?:python|py)[0-9.]*w?(?:\.exe)?$", re.IGNORECASE)

#: Interpreter options that consume the token after them, so it is not the script.
VALUED_OPTIONS = frozenset({"-W", "-X", "--check-hash-based-pycs"})

Defect = tuple[str, str]


def script_of(expression: str) -> str | None:
    """The repository-relative script a `python ...` expression would run, if any.

    `None` means the expression is not a plain interpreter-plus-file invocation
    and this module declines to judge it statically: `-m` and `-c` name an
    import target or a literal rather than a file, and a non-Python command is
    somebody else's vocabulary. `grade_live` asks those the only way that works,
    which is to run them.
    """
    try:
        argv = shlex.split(expression)
    except ValueError:
        return None
    # A `NAME=value` prefix is environment, not the interpreter. Without this,
    # `PYTHONPATH=scripts python foo.py` reads `pythonpath=scripts` as an
    # interpreter and returns `python` as the script.
    while argv and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", argv[0]):
        argv = argv[1:]
    if len(argv) < 2 or not INTERPRETER.match(Path(argv[0]).name):
        return None

    rest = iter(argv[1:])
    for token in rest:
        if token in ("-m", "-c"):
            return None
        if token in VALUED_OPTIONS:
            next(rest, None)
            continue
        if token.startswith("-"):
            continue
        return token
    return None


def _names_main(test: ast.expr) -> bool:
    """True for `__name__ == "__main__"` and its `in (...)` spelling, only."""
    if not isinstance(test, ast.Compare) or len(test.ops) != 1:
        return False
    operator = test.ops[0]
    left, right = test.left, test.comparators[0]
    if isinstance(right, ast.Name) and right.id == "__name__":
        # `if "__main__" == __name__:` is the same guard written backwards.
        left, right = right, left
    if not isinstance(left, ast.Name) or left.id != "__name__":
        return False
    if isinstance(operator, ast.Eq):
        return isinstance(right, ast.Constant) and right.value == "__main__"
    if isinstance(operator, ast.In) and isinstance(right, (ast.Tuple, ast.List)):
        return any(isinstance(item, ast.Constant) and item.value == "__main__"
                   for item in right.elts)
    return False


def _does_something(body: list[ast.stmt]) -> bool:
    """False for a guard body that is only `pass`, `...`, or a docstring."""
    for statement in body:
        if isinstance(statement, ast.Pass):
            continue
        if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant):
            continue
        return True
    return False


def _is_entry_call(node: ast.stmt) -> bool:
    """True for an unguarded top-level call that runs the module, not one that sets it up."""
    if isinstance(node, ast.Raise):
        exception = node.exc
        return (isinstance(exception, ast.Call) and isinstance(exception.func, ast.Name)
                and exception.func.id == "SystemExit")
    if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
        return False
    function = node.value.func
    if isinstance(function, ast.Name):
        return True
    return (isinstance(function, ast.Attribute) and function.attr == "exit"
            and isinstance(function.value, ast.Name) and function.value.id == "sys")


def has_entry_point(source: str) -> bool:
    """True when running the module as a command would execute something.

    A `__main__` guard is the ordinary spelling and decides on its own: a guard
    whose body is `pass` reports False, because it declares an entry point and
    executes nothing. A guard anywhere in the module settles the answer, so a
    top-level call earlier in the file cannot vote first.

    Only when no guard exists does a bare top-level call count, and only the
    shapes that are an entry point rather than import-time setup: a plain
    `main()`, or exiting on one. `logging.getLogger(__name__)` at module level
    is setup, and an attribute call is how it is spelled.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    for node in tree.body:
        if isinstance(node, ast.If) and _names_main(node.test):
            return _does_something(node.body)
    return any(_is_entry_call(node) for node in tree.body)
