#!/usr/bin/env python3
"""Grade every diagram against the sources it declares it read.

`diagrams/README.md` specifies a `source_digest` per view "so a stale diagram is
detectable rather than merely suspected", and then defers the check to whenever
the views are generated rather than authored. Until then it was a manual read,
and a manual read that nobody performs reports every view as current. This
performs it.

A diagram holds no standing. Grading one settles nothing: it reports whether the
view still reads the bytes it claims to have read, and nothing about whether the
drawing was ever right.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import argparse
import json
import sys


ROOT = Path(__file__).resolve().parents[1]
DIAGRAMS = ROOT / "diagrams"
# The provenance block is the `Recording` shape from SPEC.md. Only these two fields
# are graded; `reader`, `fidelity`, and `omissions` are read by people, not by this.
FIELDS = ("source", "source_digest", "reader", "fidelity", "omissions")
DIGEST_CHARACTERS = 16
SEPARATOR = "·"
NEWLINE = chr(10)


class ProvenanceError(Exception):
    """The view cannot be graded at all, which is a defect and not a stale digest."""


def digest_of(path: Path) -> str:
    """The recorded digest shape: a sha256 prefix over the file's exact bytes."""
    return sha256(path.read_bytes()).hexdigest()[:DIGEST_CHARACTERS]


def provenance(text: str) -> dict[str, str]:
    """The provenance header fields, with wrapped continuation lines rejoined."""
    lines = text.split("\n")
    try:
        opening = next(index for index, line in enumerate(lines) if line.strip() == "```text")
    except StopIteration:
        raise ProvenanceError("no provenance block") from None
    fields: dict[str, list[str]] = {}
    current: str | None = None
    for line in lines[opening + 1:]:
        if line.strip() == "```":
            break
        name = line.split(" ", 1)[0].strip()
        if name in FIELDS:
            current = name
            fields[current] = [line[len(name):].strip()]
        elif current is not None:
            fields[current].append(line.strip())
    for required in ("source", "source_digest"):
        if not fields.get(required):
            raise ProvenanceError(f"provenance block has no {required}")
    return {name: " ".join(part for part in parts if part) for name, parts in fields.items()}


def readings(header: dict[str, str]) -> list[tuple[str, str]]:
    """Pair each declared source with the digest declared beside it, in order."""
    sources = [part.strip() for part in header["source"].split(SEPARATOR) if part.strip()]
    digests = [part.strip() for part in header["source_digest"].split(SEPARATOR) if part.strip()]
    if len(sources) != len(digests):
        raise ProvenanceError(
            f"{len(sources)} source(s) declared against {len(digests)} digest(s)")
    return list(zip(sources, digests))


def grade(path: Path) -> dict[str, object]:
    """One view's verdict: CURRENT, STALE, or INVALID, with the readings that decided it."""
    try:
        pairs = readings(provenance(path.read_text(encoding="utf-8")))
    except ProvenanceError as error:
        return {"view": path.name, "verdict": "INVALID", "defects": [str(error)], "readings": []}
    defects: list[str] = []
    graded: list[dict[str, str]] = []
    for source, declared in pairs:
        target = ROOT / source
        if not target.is_file():
            defects.append(f"declares {source}, which is not a file")
            graded.append({"source": source, "declared": declared, "actual": "MISSING"})
            continue
        actual = digest_of(target)
        graded.append({"source": source, "declared": declared, "actual": actual})
        if actual != declared:
            defects.append(f"{source} moved: declared {declared}, actual {actual}")
    verdict = "INVALID" if any(item["actual"] == "MISSING" for item in graded) else (
        "STALE" if defects else "CURRENT")
    return {"view": path.name, "verdict": verdict, "defects": defects, "readings": graded}


def stamp(path: Path) -> list[str]:
    """Rewrite a view's declared digests to the sources as they stand now.

    This records a re-reading; it cannot perform one. Running it over a view whose
    drawing was never corrected launders a stale diagram into a current-looking one,
    which is the exact failure the digest exists to prevent. Correct the view first,
    stamp second, and let `grade` be the gate.
    """
    text = path.read_text(encoding="utf-8")
    header = provenance(text)
    sources = [part.strip() for part in header["source"].split(SEPARATOR) if part.strip()]
    fresh = [digest_of(ROOT / source) for source in sources]
    changed = [f"{source}: {old} -> {new}"
               for (source, old), new in zip(readings(header), fresh) if old != new]
    if not changed:
        return []
    # The block is fixed-width and may wrap, so the field is rewritten as one line.
    lines = text.split(NEWLINE)
    opening = next(index for index, line in enumerate(lines) if line.strip() == "```text")
    closing = next(index for index, line in enumerate(lines[opening + 1:], opening + 1)
                   if line.strip() == "```")
    body = lines[opening + 1:closing]
    rebuilt: list[str] = []
    skipping = False
    for line in body:
        name = line.split(" ", 1)[0].strip()
        if name == "source_digest":
            rebuilt.append(f"source_digest   {f' {SEPARATOR} '.join(fresh)}")
            skipping = True
            continue
        if skipping and name not in FIELDS:
            continue
        skipping = False
        rebuilt.append(line)
    # The repository pins LF in .gitattributes and scripts/lint.py reads working-tree
    # bytes, so the newline is stated rather than left to the platform default.
    path.write_text(NEWLINE.join(lines[:opening + 1] + rebuilt + lines[closing:]),
                    encoding="utf-8", newline=NEWLINE)
    return changed


def views() -> list[Path]:
    return sorted(path for path in DIAGRAMS.glob("*.md") if path.name != "README.md")


def selfcheck() -> int:
    """Prove the grader detects a moved source, an unreadable header, and a count mismatch."""
    cases = (
        ("a matching digest reads CURRENT",
         "```text\nsource          CONTRACT.md\nsource_digest   {live}\n```\n", "CURRENT"),
        ("a moved source reads STALE",
         "```text\nsource          CONTRACT.md\nsource_digest   0000000000000000\n```\n", "STALE"),
        ("a source that does not exist reads INVALID",
         "```text\nsource          NOPE.md\nsource_digest   0000000000000000\n```\n", "INVALID"),
        ("a header with no digest reads INVALID",
         "```text\nsource          CONTRACT.md\n```\n", "INVALID"),
        ("more sources than digests reads INVALID",
         "```text\nsource          CONTRACT.md " + SEPARATOR + " SPEC.md\n"
         "source_digest   {live}\n```\n", "INVALID"),
        ("no provenance block at all reads INVALID", "# just a title\n", "INVALID"),
    )
    live = digest_of(ROOT / "CONTRACT.md")
    scratch = DIAGRAMS / ".selfcheck.md"
    failures = 0
    try:
        for name, body, expected in cases:
            scratch.write_text(body.replace("{live}", live), encoding="utf-8",
                               newline=NEWLINE)
            actual = grade(scratch)["verdict"]
            ok = actual == expected
            failures += not ok
            print(f"{'PASS' if ok else 'FAIL'}: {name} (expected {expected}, read {actual})")
    finally:
        scratch.unlink(missing_ok=True)
    print(f"{'PASS' if not failures else 'FAIL'}: diagram grader selfcheck, "
          f"{len(cases) - failures}/{len(cases)} declared cases")
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("command", nargs="?", default="grade",
                        choices=("grade", "stamp", "selfcheck"))
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    if args.command == "selfcheck":
        return selfcheck()
    if args.command == "stamp":
        total = 0
        for path in views():
            for change in stamp(path):
                print(f"{path.name}: {change}")
                total += 1
        print(f"PASS: restamped {total} declared reading(s)")
        return 0

    results = [grade(path) for path in views()]
    if not results:
        print("FAIL: no diagrams to grade")
        return 1
    stale = [item for item in results if item["verdict"] != "CURRENT"]
    if args.as_json:
        print(json.dumps({"views": results, "stale": len(stale)}, indent=2, sort_keys=True))
        return 1 if stale else 0
    for item in results:
        print(f"{item['verdict']:8} {item['view']}")
        for defect in item["defects"]:
            print(f"         {defect}")
    verdict = "FAIL" if stale else "PASS"
    print(f"{verdict}: {len(results)} diagram(s) graded, {len(stale)} stale or invalid")
    return 1 if stale else 0


if __name__ == "__main__":
    raise SystemExit(main())
