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

Where this reading stops, stated because a reader who does not know will trust
it further than it goes. An independent witness drove each of these:

- `runpy` executes the target's module body and its whole import closure up to
  the parse call, so a target that does work at import does that work on every
  run. The corpus was checked and none currently does; nothing stops the next
  one. "Runs no command body" is true of the body under the entry point, not of
  everything a module does on the way there.
- A CLI that calls `parse_known_args` to peek at one flag and validates strictly
  afterwards is admitted whatever its arguments, because the guard can only see
  a `parse_args` already on the stack, never one about to be entered.
- The declared interpreter is not the one tested: `python3.11 x.py` is probed
  with this process's own interpreter, so a version-specific failure is invisible.
- A target with no parser at all runs to completion, and its own exit code is
  read as its verdict rather than graded.
"""

from __future__ import annotations

from pathlib import Path
import os
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

class _Reached(BaseException):
    """BaseException, not Exception.

    A CLI that wraps its own parse in `try/except Exception` - an ordinary
    defensive shape - swallowed an Exception sentinel, and the shim then ran
    straight into the command body it exists to avoid. A witness proved that
    with a fixture that wrote a file.
    """

# `parse_args` calls `parse_known_args` and then reports leftover arguments, so a
# patch that raises from the inner call skips the outer check and reports an
# unrecognized flag as a clean parse. That is how `--scenario` on a parser with no
# such flag first read as dispatching. The inner call is only allowed to raise when
# nothing outer is going to validate after it.
_inside = []
_built = []
_init = argparse.ArgumentParser.__init__


def _patched_init(self, *a, **kw):
    _built.append(True)
    _init(self, *a, **kw)


argparse.ArgumentParser.__init__ = _patched_init
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
    # which means it dispatched and this reader has no business grading it. That
    # holds for a target with no parser at all: it ran and returned a verdict.
    sys.exit(_REJECTED if exit_.code == 2 else _PARSED)
except (ImportError, ModuleNotFoundError):
    sys.exit(_UNIMPORTABLE)
except BaseException:
    # The body ran and raised: it dispatched, and its verdict is not ours. If no
    # parser was ever built the failure came first, so nothing dispatched.
    sys.exit(_PARSED if _built else _UNIMPORTABLE)
sys.exit(_NO_PARSER)
'''


def probe(root: Path, mode: str, target: str, argv: list[str],
          environment: dict[str, str] | None = None) -> tuple[int, str]:
    """Return the shim's exit code and whatever the attempt wrote to stderr.

    `environment` carries the leading `NAME=value` assignments the expression
    declared. Accepting that shape in the resolver and then dropping it here made
    the repair cosmetic: `PYTHONPATH=services/record/src python -m ...` was
    refused for the exact absence that prefix exists to supply.
    """
    env = dict(os.environ)
    env.update(environment or {})
    try:
        done = subprocess.run(
            [sys.executable, "-c", SHIM, mode, target, *argv],
            cwd=root, capture_output=True, text=True, timeout=TIMEOUT_SECONDS, env=env,
        )
    except subprocess.TimeoutExpired:
        return PARSED, "timed out past the parser; treated as dispatched"
    lines = (done.stderr or "").strip().splitlines()
    return done.returncode, lines[-1] if lines else ""
