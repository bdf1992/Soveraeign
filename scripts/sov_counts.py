#!/usr/bin/env python3
"""Grade every hand-written count in live prose against a deterministic counter.

`scripts/sov_snapshot.py` does this for ten numbers on one page, because that page
went stale inside a day and every launched agent reads it as current
(`LESSONS.md` L-0001). The same failure is not confined to that page. When this
check was first run, `CLAUDE.md` was the only file in the repository whose counts
were graded, and it was correct; eight numbers elsewhere had drifted, four of them
in documents that govern - a product requirement in `PRD.md`, an owner-accepted
ratio in `GROUND.md`, a service's own legal-transition count, and the harness
count in the file that describes the harness.

The generalisation is a contract rather than more patterns.
`contracts/counted-populations.json` declares a population, how to count it, and
the wording that claims it. Prose is then searched for that wording anywhere,
which is what makes this different from ten regexes: a count written into a file
that did not exist when this was built is graded on the day it is written, and a
service added tomorrow brings its own population with it through the template.

What this settles is narrow and stated so it is not read as more: whether a number
matches the population its wording names. Not whether the sentence around it is
true, not whether the population is the right one to cite, and never anything
about standing. `debt` prints the count-shaped sentences no population declares,
so coverage is a list a reader can act on rather than an inference from silence.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sovcounts import grading  # noqa: E402
from sovcounts import populations as pops  # noqa: E402
from sovcounts import scan  # noqa: E402
from sovcounts import selfcheck  # noqa: E402


def _read() -> tuple[list, list, dict, dict, dict]:
    """Everything a verdict needs: claims, candidates, derived values, and why not."""
    declared = pops.contract()
    populations, paths = pops.load()
    values: dict[str, int] = {}
    reasons: dict[str, str] = {}
    for population in populations:
        try:
            values[population.id] = pops.derive(population.derivation, paths)
        except pops.Underivable as absent:
            reasons[population.id] = str(absent)
    files = scan.live_files(paths, tuple(declared["frozen_paths"]["paths"]))
    guard = tuple(declared["subset_qualifiers"]["words"])
    claims, candidates = scan.scan(pops.ROOT, files, populations, guard)
    return claims, candidates, values, reasons, declared


def cmd_selfcheck(_args=None) -> int:
    """Prove the grader fires and every population still counts something."""
    return selfcheck.run()


def cmd_check(_args=None) -> int:
    """Grade the repository's live prose, after proving the grader still works."""
    if cmd_selfcheck() != 0:
        print("\nREFUSED: the check itself is broken, so its verdict about the "
              "repository means nothing. Nothing was graded.")
        return 1
    claims, candidates, values, reasons, declared = _read()
    exemptions = declared["historical_claims"]["claims"]
    findings = grading.grade(claims, values, reasons, exemptions)

    for finding in findings:
        if finding.kind == grading.HISTORICAL:
            print(f"HISTORICAL {finding.path}:{finding.line} states {finding.stated} "
                  f"{finding.anchor} - {finding.detail}")
        elif finding.kind == grading.UNDERIVABLE:
            print(f"NOT CHECKED HERE {finding.path}:{finding.line} - "
                  f"{finding.population}: {finding.detail}")
    print(f"NOT CHECKED: {len(candidates)} count-shaped sentences no population "
          "declares. Run `debt` to read them; silence about them is coverage, "
          "not confirmation.")

    drifted = grading.drifted(findings)
    if drifted:
        for finding in drifted:
            print(f"FAIL {finding.path}:{finding.line}: states {finding.stated} "
                  f"{finding.anchor}, the record holds {finding.actual} "
                  f"({finding.population})")
        print("\nA number written by hand disagrees with the record it names. Correct "
              "the prose, or land the sources it already describes. If the number is "
              "a dated statement of past state, record it under `historical_claims` in "
              "contracts/counted-populations.json with the reason; if it counts part "
              "of a population, the sentence needs wording the subset guard reads. "
              "Never widen a population to make a number fit.")
        return 1

    graded = len([f for f in findings if f.kind == grading.MATCH])
    print(f"PASS: {graded} stated count(s) match the record, across "
          f"{len(values)} declared population(s)")
    return 0


def cmd_debt(_args=None) -> int:
    """Print the count-shaped sentences no population declares."""
    _, candidates, _, _, _ = _read()
    by_noun: dict[str, list] = {}
    for candidate in candidates:
        by_noun.setdefault(candidate.noun, []).append(candidate)
    for noun in sorted(by_noun, key=lambda n: len(by_noun[n]), reverse=True):
        found = by_noun[noun]
        print(f"\n{len(found):3}  {noun}")
        for candidate in found[:4]:
            print(f"       {candidate.path}:{candidate.line}  {candidate.stated}")
        if len(found) > 4:
            print(f"       ... and {len(found) - 4} more")
    print(f"\n{len(candidates)} ungraded count-shaped sentence(s) over "
          f"{len(by_noun)} distinct nouns. Most are ordinary prose. A noun that "
          "names a repository population and recurs is a population worth declaring "
          "in contracts/counted-populations.json.")
    return 0


def cmd_populations(_args=None) -> int:
    """Print every declared population and what it currently holds."""
    populations, paths = pops.load()
    for population in populations:
        try:
            value: object = pops.derive(population.derivation, paths)
        except pops.Underivable as absent:
            value = f"not derivable here ({absent})"
        print(f"{population.id:34} {value}")
        print(f"{'':34} counts {population.counts}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("check", help="grade every bound count in live prose")
    sub.add_parser("debt", help="list count-shaped sentences no population declares")
    sub.add_parser("populations", help="show every declared population and its value")
    sub.add_parser("selfcheck", help="prove the grader fires and does not over-fire")
    args = parser.parse_args(argv)
    commands = {"check": cmd_check, "debt": cmd_debt,
                "populations": cmd_populations, "selfcheck": cmd_selfcheck}
    return commands.get(args.command or "check", cmd_check)(args)


if __name__ == "__main__":
    raise SystemExit(main())
