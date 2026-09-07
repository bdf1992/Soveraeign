#!/usr/bin/env python3
"""Run named tooling test modules in one process and time each one.

The suite's cost has always been reported as one number per shard. A shard
number cannot name the module that grew, so every weight in
``scripts/run_tooling_tests.py`` was set by a separate hand campaign that
measured every module alone and then discarded the measurements, keeping only
prose. Three such campaigns each found the previous table inverted.

This driver keeps unittest as the oracle and the existing one-process-per-shard
isolation, and adds the reading that was being thrown away: the wall cost of
each module, on the same run that proves the modules pass.

Load order does change, and the docstring said otherwise until a witness read it:
`python -m unittest a b c` imports every module before running any test, while this
runs each module's tests before importing the next. No module in the population
depends on that today. A module that comes to depend on it would be relying on a
neighbour's import side effect, which is worth failing over rather than preserving.
"""

from __future__ import annotations

import argparse
import io
import time
import unittest

COST_PREFIX = "COST_MODULE"


def run_module(name: str) -> tuple[bool, float, str]:
    """Run one test module. Return whether it passed, its wall cost, and its output."""
    stream = io.StringIO()
    started = time.perf_counter()
    try:
        suite = unittest.defaultTestLoader.loadTestsFromName(f"scripts.tests.{name}")
        result = unittest.TextTestRunner(stream=stream, verbosity=1).run(suite)
        passed = result.wasSuccessful()
    except Exception as error:  # a module that cannot even load is a failure, not a crash
        passed = False
        stream.write(f"{name}: could not be loaded: {error!r}\n")
    return passed, time.perf_counter() - started, stream.getvalue()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("modules", nargs="+", help="module stems under scripts/tests/")
    args = parser.parse_args(argv)
    failed = False
    for name in args.modules:
        passed, seconds, output = run_module(name)
        print(f"{COST_PREFIX} {name} {seconds:.3f} {'PASS' if passed else 'FAIL'}", flush=True)
        if not passed:
            failed = True
            if output.rstrip():
                print(output.rstrip(), flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
