"""What an independent observation recorded, and how it reads back.

`AGENTS.md` holds that a build cannot witness itself and that a test may establish
`BUILT` but never `WITNESSED`. A findings log is therefore deliberately not a
verdict: it says what was looked at and what happened, and the standing note it
prints says out loud that it settles nothing.

Known residual: `scripts/witness_console.py` and `scripts/witness_seats.py` each
carry their own copy of this class. They predate this module and belong to the
console and governance domains; converting them is that domain's change, not a
side effect of adding a third witness.
"""

from __future__ import annotations


class Observation:
    """What was looked at, and what it did. Never a verdict about standing."""

    def __init__(self) -> None:
        self.findings: list[tuple[bool, str, str]] = []

    def note(self, held: bool, claim: str, detail: str = "") -> None:
        """Record one thing that was checked and whether it held."""
        self.findings.append((held, claim, detail))

    def failed(self) -> list[tuple[bool, str, str]]:
        """The findings that did not hold."""
        return [finding for finding in self.findings if not finding[0]]

    def report(self) -> int:
        """Print every finding and return a process exit code."""
        width = max(len(claim) for _, claim, _ in self.findings)
        for held, claim, detail in self.findings:
            print(("PASS" if held else "FAIL") + "  " + claim.ljust(width) + "  " + detail)
        failed = self.failed()
        print("\n" + str(len(self.findings) - len(failed)) + "/" + str(len(self.findings))
              + " independent observations held")
        print("Standing note: an observation independent of the builder. It proposes at most "
              "BUILT -> WITNESSED and settles nothing.")
        return 1 if failed else 0
