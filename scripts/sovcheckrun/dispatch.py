"""Run a declared command as far as its argument parser and no further.

Executing a closure check is not this reader's business: several declared checks
read live inventory, and one of them is an admission. But refusing to execute
anything is what let five commands that exit 2 be reported as runnable. The
middle is real and is what this module does - drive the target up to the moment
its parser accepts or rejects the declared arguments, then stop before the body.

The shim patches `argparse.ArgumentParser.parse_args` to raise a sentinel the
instant a parse succeeds, then runs the target under `runpy` with the declared
argv. A target that parses raises the sentinel and its command body never runs.
A target that rejects the arguments raises `SystemExit(2)` from inside argparse.
A target that cannot be imported raises before either.
"""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys

#: Exit codes the shim uses; distinct from anything argparse or the target emits.
PARSED = 40
REJECTED = 41
UNIMPORTABLE = 42
NO_PARSER = 43

TIMEOUT_SECONDS = 20

SHIM = '''
import argparse, os, runpy, sys
_PARSED, _REJECTED, _UNIMPORTABLE, _NO_PARSER = 40, 41, 42, 43
mode, target = sys.argv[1], sys.argv[2]
# argparse reads sys.argv[1:], so the target keeps its own program-name slot.
sys.argv = [target] + sys.argv[3:]
# `python a/b.py` puts a/ on sys.path[0] and `python -m x` puts the cwd there.
# Without this the shim reports an import failure for every script that imports
# a sibling module, which is most of them.
sys.path.insert(0, os.path.dirname(os.path.abspath(target)) if mode == "path" else os.getcwd())

class _Reached(Exception):
    pass

# `parse_args` calls `parse_known_args` and then reports leftover arguments, so a
# patch that raises from the inner call skips the outer check and reports an
# unrecognized flag as a clean parse. That is how `--scenario` on a parser with no
# such flag first read as dispatching. The inner call is only allowed to raise when
# nothing outer is going to validate after it.
_inside = []
_parse_args = argparse.ArgumentParser.parse_args
_parse_known = argparse.ArgumentParser.parse_known_args


def _patched_parse_args(self, *a, **kw):
    _inside.append(True)
    try:
        _parse_args(self, *a, **kw)
    finally:
        _inside.pop()
    raise _Reached()


def _patched_parse_known(self, *a, **kw):
    result = _parse_known(self, *a, **kw)
    if _inside:
        return result
    raise _Reached()


argparse.ArgumentParser.parse_args = _patched_parse_args
argparse.ArgumentParser.parse_known_args = _patched_parse_known

try:
    if mode == "module":
        runpy.run_module(target, run_name="__main__", alter_sys=True)
    else:
        runpy.run_path(target, run_name="__main__")
except _Reached:
    sys.exit(_PARSED)
except SystemExit as exit_:
    # argparse exits 2 on a usage error; anything else is the target's own verdict,
    # which means it dispatched and this reader has no business grading it.
    sys.exit(_REJECTED if exit_.code == 2 else _PARSED)
except (ImportError, ModuleNotFoundError):
    sys.exit(_UNIMPORTABLE)
except BaseException:
    # The body ran and raised. It dispatched; its verdict is not ours.
    sys.exit(_PARSED)
sys.exit(_NO_PARSER)
'''


def probe(root: Path, mode: str, target: str, argv: list[str]) -> tuple[int, str]:
    """Return the shim's exit code and whatever the attempt wrote to stderr."""
    try:
        done = subprocess.run(
            [sys.executable, "-c", SHIM, mode, target, *argv],
            cwd=root, capture_output=True, text=True, timeout=TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return PARSED, "timed out past the parser; treated as dispatched"
    lines = (done.stderr or "").strip().splitlines()
    return done.returncode, lines[-1] if lines else ""
