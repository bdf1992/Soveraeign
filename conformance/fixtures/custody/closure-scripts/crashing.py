"""A module that prints one line of reading and then dies with a traceback.

Exit code alone cannot separate this from a closure check refusing loudly,
because refusing loudly is what a closure check is for. The traceback on stderr
is the discriminator, and this fixture is why `run` keeps it.
"""

from __future__ import annotations


def main() -> int:
    """Report, then break."""
    print("reading: partial")
    raise RuntimeError("the reader broke after reporting")


if __name__ == "__main__":
    raise SystemExit(main())
