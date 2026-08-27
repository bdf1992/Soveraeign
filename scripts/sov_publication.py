#!/usr/bin/env python3
"""Grade the tracked tree against the surface each path is declared to occupy.

`PUBLICATION.md` owns what may never be published and stops there. Generated
output, one host's harness, the work journal and scratch were never classified,
so they accumulated in a public repository and a newcomer reads them as product.
`contracts/publication-surface.json` declares a surface for every tracked
top-level path, the routes that must reach a reader, and the entrypoint index.
This performs the reading.

Findings carry a holder. A finding held by `sov` is a defect and fails `check`;
a finding held by `owner` is reported and does not fail, because a declared gate
stops one transition and not the frontier (`AGENTS.md`, Authority). Nothing here
grants authority, changes standing, or decides whether a path should be public:
it reports where the tree and the declaration disagree.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import fnmatch
import json
import os
import subprocess


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "publication-surface.json"
SOV = "sov"
OWNER = "owner"


class ContractError(Exception):
    """The declaration cannot be read, which is a defect and not a finding."""


def load(path: Path = CONTRACT) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ContractError(f"{path.relative_to(ROOT)} is missing") from None
    except json.JSONDecodeError as error:
        raise ContractError(f"{path.relative_to(ROOT)} is not JSON: {error}") from None


def tracked() -> list[str]:
    """Every tracked path, as git reports it, with forward slashes."""
    result = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        raise ContractError("git ls-files failed; this must run inside the repository")
    return [line for line in result.stdout.splitlines() if line]


def top_level(paths: list[str]) -> set[str]:
    return {path.split("/", 1)[0] for path in paths}


def finding(check: str, holder: str, path: str, detail: str) -> dict[str, str]:
    return {"id": f"{check}:{path}", "check": check, "holder": holder,
            "path": path, "detail": detail}


def coverage(contract: dict, paths: list[str]) -> list[dict[str, str]]:
    """Every tracked top-level path must be classified, so the tree cannot grow unclassified."""
    declared = {entry["path"].split("/", 1)[0] for entry in contract["paths"]}
    return [finding("UNCLASSIFIED", SOV, name,
                    "tracked and absent from contracts/publication-surface.json")
            for name in sorted(top_level(paths) - declared)]


def surfaces(contract: dict, paths: list[str]) -> list[dict[str, str]]:
    """Each entry must satisfy the rule its own surface declares."""
    tracked_set = set(paths)
    found: list[dict[str, str]] = []
    for entry in contract["paths"]:
        path, surface = entry["path"], entry["surface"]
        if surface == "LOCAL":
            leaked = sorted(item for item in tracked_set
                            if item == path or item.startswith(path + "/"))
            if leaked:
                found.append(finding("LOCAL_TRACKED", SOV, path,
                                     f"declared operator-machine only, yet {len(leaked)} tracked "
                                     f"file(s) exist, first {leaked[0]}"))
            continue
        if surface == "DERIVED":
            for role in ("builder", "check"):
                target = entry.get(role)
                if not target:
                    found.append(finding("DERIVED_UNCHECKED", SOV, path,
                                         f"generated output declaring no {role}"))
                elif not (ROOT / target).exists():
                    found.append(finding("DERIVED_UNCHECKED", SOV, path,
                                         f"declares {role} {target}, which is not a file"))
        if surface == "SCRATCH" and not entry.get("until"):
            found.append(finding("SCRATCH_OPEN_ENDED", SOV, path,
                                 "kept in the tree with nothing declared that retires it"))
        if surface == "HOST" and not entry.get("host"):
            found.append(finding("HOST_UNDECLARED", SOV, path,
                                 "one host's harness that does not name its host"))
    return found


def reaches(text: str, document: str, required: str) -> bool:
    """Whether the document reaches the required path, repo-relative or relative to itself.

    A link written from inside a directory is a real reference to the file it resolves
    to. Grading only the repository-relative spelling refuses a document for being
    correctly written, which pushes an author toward a spelling that satisfies the
    matcher rather than the reader.
    """
    here = os.path.dirname(document)
    relative = os.path.relpath(required, here).replace(os.sep, "/") if here else required
    return required in text or relative in text


def routes(contract: dict) -> list[dict[str, str]]:
    """An entry document must name what its audience needs and must not name a stale pointer."""
    found: list[dict[str, str]] = []
    for route in contract["routes"]:
        document = route["document"]
        target = ROOT / document
        if not target.is_file():
            found.append(finding("ROUTE_MISSING", SOV, document,
                                 f"the {route['audience']} route has no entry document"))
            continue
        text = target.read_text(encoding="utf-8")
        owner_held = set(route.get("owner_held", ()))
        for required in route["must_name"]:
            if reaches(text, document, required):
                continue
            holder = OWNER if required in owner_held else SOV
            found.append(finding("ROUTE_GAP", holder, f"{document}->{required}",
                                 f"the {route['audience']} route does not name {required}"))
        for refused in route["must_not_name"]:
            if refused in text:
                found.append(finding("ROUTE_STALE", SOV, f"{document}->{refused}",
                                     f"the {route['audience']} route still points at {refused}"))
    return found


def entrypoints(contract: dict, paths: list[str]) -> list[dict[str, str]]:
    """Every command-line entrypoint must appear in the index, or nobody else can reach it."""
    declared = contract.get("entrypoint_index")
    if not declared:
        return []
    index = ROOT / declared["index"]
    if not index.is_file():
        return [finding("INDEX_MISSING", SOV, declared["index"],
                        "no index exists for the node's command-line surface")]
    text = index.read_text(encoding="utf-8")
    pattern = declared["pattern"]
    names = sorted({Path(item).name for item in paths
                    if fnmatch.fnmatch(Path(item).name, pattern)})
    return [finding("ENTRYPOINT_UNINDEXED", SOV, name,
                    f"an entrypoint absent from {declared['index']}")
            for name in names if name not in text]


def retired(contract: dict) -> list[dict[str, str]]:
    """A document describing a completed operation must be marked, or it reads as current."""
    found: list[dict[str, str]] = []
    for entry in contract.get("retired", ()):
        document = entry["document"]
        target = ROOT / document
        if not target.is_file():
            continue
        head = target.read_text(encoding="utf-8").split("\n", 12)[:12]
        if not any(entry["marker"] in line for line in head):
            found.append(finding("STALE_UNMARKED", entry.get("holder", SOV), document,
                                 f"describes an operation completed {entry['completed']} and "
                                 f"carries no {entry['marker']} marker in its opening lines"))
    return found


def audit(contract: dict, paths: list[str]) -> list[dict[str, str]]:
    return (coverage(contract, paths) + surfaces(contract, paths)
            + routes(contract) + entrypoints(contract, paths) + retired(contract))


def render(found: list[dict[str, str]]) -> None:
    for item in sorted(found, key=lambda entry: (entry["holder"], entry["check"], entry["path"])):
        print(f"{item['holder']:6} {item['check']:20} {item['path']}")
        print(f"       {item['detail']}")


def selfcheck() -> int:
    """Prove every declared refusal fires, so an empty finding list means something."""
    cases = (
        ("an unclassified tracked path is refused",
         lambda: coverage({"paths": []}, ["strange/thing.md"]), "UNCLASSIFIED"),
        ("a classified tracked path is admitted",
         lambda: coverage({"paths": [{"path": "strange"}]}, ["strange/thing.md"]), None),
        ("a LOCAL path with tracked files is refused",
         lambda: surfaces({"paths": [{"path": "scripts", "surface": "LOCAL"}]},
                          ["scripts/lint.py"]), "LOCAL_TRACKED"),
        ("a LOCAL path with no tracked files is admitted",
         lambda: surfaces({"paths": [{"path": ".local", "surface": "LOCAL"}]},
                          ["scripts/lint.py"]), None),
        ("DERIVED output with no builder is refused",
         lambda: surfaces({"paths": [{"path": "docs/x.html", "surface": "DERIVED",
                                      "check": "scripts/lint.py"}]}, []), "DERIVED_UNCHECKED"),
        ("DERIVED output whose check is not a file is refused",
         lambda: surfaces({"paths": [{"path": "docs/x.html", "surface": "DERIVED",
                                      "builder": "scripts/lint.py",
                                      "check": "scripts/nope.py"}]}, []), "DERIVED_UNCHECKED"),
        ("SCRATCH with nothing that retires it is refused",
         lambda: surfaces({"paths": [{"path": "experiments", "surface": "SCRATCH"}]}, []),
         "SCRATCH_OPEN_ENDED"),
        ("a HOST path naming no host is refused",
         lambda: surfaces({"paths": [{"path": ".claude", "surface": "HOST"}]}, []),
         "HOST_UNDECLARED"),
        ("a route with no entry document is refused",
         lambda: routes({"routes": [{"audience": "x", "document": "NOPE.md",
                                     "must_name": [], "must_not_name": []}]}), "ROUTE_MISSING"),
        ("a route that does not name what it must is refused",
         lambda: routes({"routes": [{"audience": "x", "document": "CONTRACT.md",
                                     "must_name": ["zzz-not-present"],
                                     "must_not_name": []}]}), "ROUTE_GAP"),
        ("a link relative to the document's own directory reaches its target",
         lambda: routes({"routes": [{"audience": "x", "document": "bindings/README.md",
                                     "must_name": ["bindings/INTEGRATING.md"],
                                     "must_not_name": []}]}), None),
        ("a route still pointing at a stale document is refused",
         lambda: routes({"routes": [{"audience": "x", "document": "README.md",
                                     "must_name": [],
                                     "must_not_name": ["AGENTS.md"]}]}), "ROUTE_STALE"),
        ("a missing entrypoint index is refused",
         lambda: entrypoints({"entrypoint_index": {"index": "scripts/NOPE.md",
                                                   "pattern": "sov_*.py"}}, []), "INDEX_MISSING"),
        ("an entrypoint absent from the index is refused",
         lambda: entrypoints({"entrypoint_index": {"index": "CONTRACT.md",
                                                   "pattern": "sov_*.py"}},
                             ["scripts/sov_nowhere.py"]), "ENTRYPOINT_UNINDEXED"),
        ("a retired document with no marker is refused",
         lambda: retired({"retired": [{"document": "CONTRACT.md", "marker": "RETIRED",
                                       "completed": "2026-01-01"}]}), "STALE_UNMARKED"),
        ("a retired document that no longer exists is admitted",
         lambda: retired({"retired": [{"document": "GONE.md", "marker": "RETIRED",
                                       "completed": "2026-01-01"}]}), None),
    )
    failures = 0
    for name, run, expected in cases:
        found = run()
        actual = found[0]["check"] if found else None
        ok = actual == expected
        failures += not ok
        print(f"{'PASS' if ok else 'FAIL'}: {name} "
              f"(expected {expected or 'no finding'}, read {actual or 'no finding'})")
    print(f"{'PASS' if not failures else 'FAIL'}: publication surface selfcheck, "
          f"{len(cases) - failures}/{len(cases)} declared cases")
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("command", nargs="?", default="audit",
                        choices=("audit", "check", "queue", "selfcheck"))
    args = parser.parse_args()
    if args.command == "selfcheck":
        return selfcheck()
    try:
        contract = load()
        paths = tracked()
    except ContractError as error:
        print(f"FAIL: {error}")
        return 1
    found = audit(contract, paths)
    held = [item for item in found if item["holder"] == SOV]
    owned = [item for item in found if item["holder"] == OWNER]
    if args.command == "queue":
        print(json.dumps(sorted(found, key=lambda item: item["id"]), indent=2, sort_keys=True))
        return 0
    render(found)
    verdict = "FAIL" if held else "PASS"
    print(f"{verdict}: {len(contract['paths'])} declared path(s), {len(found)} finding(s), "
          f"{len(held)} held by sov, {len(owned)} held by the owner")
    if args.command == "check":
        return 1 if held else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
