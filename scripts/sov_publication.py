#!/usr/bin/env python3
"""Grade indexed repository publication evidence against its declared surface.

Membership and document bytes come from the Git index, never unstaged working-tree
content. The only working-tree reach is a fail-closed check for local modules that
could shadow the grader's permitted imports. Findings held by `sov` fail `check`;
owner-held findings remain visible without becoming delegated authority.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import fnmatch
import json
import os
import subprocess


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = "contracts/publication-surface.json"
SOV = "sov"
OWNER = "owner"
_CONTENT: dict[str, str | None] = {}
PERMITTED_IMPORTS = frozenset({"argparse", "fnmatch", "json", "os", "pathlib", "subprocess"})


class ContractError(Exception):
    """The declaration cannot be read."""


def _git(*argv: str) -> subprocess.CompletedProcess[str]:
    """The grader's only process-spawn boundary."""
    return subprocess.run(["git", *argv], cwd=ROOT, capture_output=True, text=True)


def _document(value: str | Path) -> str:
    path = Path(value)
    if path.is_absolute():
        try:
            path = path.relative_to(ROOT)
        except ValueError as error:
            raise ContractError(f"{path} is outside the repository") from error
    return path.as_posix()


def tracked() -> list[str]:
    result = _git("ls-files")
    if result.returncode != 0:
        raise ContractError("git ls-files failed; this must run inside the repository")
    return [line for line in result.stdout.splitlines() if line]


def content(document: str | Path) -> str | None:
    """Return the blob the index holds for a document."""
    name = _document(document)
    if name not in _CONTENT:
        result = _git("cat-file", "blob", f":{name}")
        _CONTENT[name] = result.stdout if result.returncode == 0 else None
    return _CONTENT[name]


def load(path: str | Path = CONTRACT) -> dict:
    name = _document(path)
    text = content(name)
    if text is None:
        raise ContractError(f"{name} is not in the repository index")
    try:
        return json.loads(text)
    except json.JSONDecodeError as error:
        raise ContractError(f"{name} is not JSON: {error}") from None


def published(target: str, held: set[str]) -> bool:
    return target in held or any(item.startswith(target + "/") for item in held)


def shadowing_modules() -> list[str]:
    """Return working-tree modules that could replace a permitted import."""
    scripts = ROOT / "scripts"
    found: list[str] = []
    for name in sorted(PERMITTED_IMPORTS):
        head = name.split(".")[0]
        for candidate in (scripts / f"{head}.py", scripts / head / "__init__.py"):
            if candidate.exists():
                found.append(candidate.relative_to(ROOT).as_posix())
    return found


def top_level(paths: list[str]) -> set[str]:
    return {path.split("/", 1)[0] for path in paths}


def finding(check: str, holder: str, path: str, detail: str) -> dict[str, str]:
    return {"id": f"{check}:{path}", "check": check, "holder": holder,
            "path": path, "detail": detail}


def coverage(contract: dict, paths: list[str]) -> list[dict[str, str]]:
    declared = {entry["path"].split("/", 1)[0] for entry in contract["paths"]}
    return [finding("UNCLASSIFIED", SOV, name,
                    "tracked and absent from contracts/publication-surface.json")
            for name in sorted(top_level(paths) - declared)]


def surfaces(contract: dict, paths: list[str]) -> list[dict[str, str]]:
    held = set(paths)
    found: list[dict[str, str]] = []
    for entry in contract["paths"]:
        path, surface = entry["path"], entry["surface"]
        if surface == "LOCAL":
            leaked = sorted(item for item in held if item == path or item.startswith(path + "/"))
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
                elif not published(target, held):
                    found.append(finding("DERIVED_UNCHECKED", SOV, path,
                                         f"declares {role} {target}, which the repository index "
                                         "does not hold"))
        if surface == "SCRATCH" and not entry.get("until"):
            found.append(finding("SCRATCH_OPEN_ENDED", SOV, path,
                                 "kept in the tree with nothing declared that retires it"))
        if surface == "HOST" and not entry.get("host"):
            found.append(finding("HOST_UNDECLARED", SOV, path,
                                 "one host's harness that does not name its host"))
    return found


def reaches(text: str, document: str, required: str) -> bool:
    here = os.path.dirname(document)
    relative = os.path.relpath(required, here).replace(os.sep, "/") if here else required
    return required in text or relative in text


def routes(contract: dict) -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    for route in contract["routes"]:
        document = route["document"]
        text = content(document)
        if text is None:
            found.append(finding("ROUTE_MISSING", SOV, document,
                                 f"the {route['audience']} route has no indexed entry document"))
            continue
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
    declared = contract.get("entrypoint_index")
    if not declared:
        return []
    text = content(declared["index"])
    if text is None:
        return [finding("INDEX_MISSING", SOV, declared["index"],
                        "no indexed entrypoint index exists for the node's command-line surface")]
    names = sorted({Path(item).name for item in paths
                    if fnmatch.fnmatch(Path(item).name, declared["pattern"])})
    return [finding("ENTRYPOINT_UNINDEXED", SOV, name,
                    f"an entrypoint absent from {declared['index']}")
            for name in names if name not in text]


def retired(contract: dict) -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    for entry in contract.get("retired", ()):
        text = content(entry["document"])
        if text is None:
            continue
        if not any(entry["marker"] in line for line in text.split("\n", 12)[:12]):
            found.append(finding("STALE_UNMARKED", entry.get("holder", SOV), entry["document"],
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
    """Prove each declared refusal still discriminates."""
    cases = (
        ("unclassified path", lambda: coverage({"paths": []}, ["strange/thing.md"]), "UNCLASSIFIED"),
        ("classified path", lambda: coverage({"paths": [{"path": "strange"}]},
                                              ["strange/thing.md"]), None),
        ("LOCAL tracked", lambda: surfaces({"paths": [{"path": "scripts", "surface": "LOCAL"}]},
                                            ["scripts/lint.py"]), "LOCAL_TRACKED"),
        ("LOCAL absent", lambda: surfaces({"paths": [{"path": ".local", "surface": "LOCAL"}]},
                                           ["scripts/lint.py"]), None),
        ("DERIVED no builder", lambda: surfaces(
            {"paths": [{"path": "docs/x.html", "surface": "DERIVED", "check": "scripts/lint.py"}]},
            ["scripts/lint.py"]), "DERIVED_UNCHECKED"),
        ("DERIVED missing check", lambda: surfaces(
            {"paths": [{"path": "docs/x.html", "surface": "DERIVED",
                        "builder": "scripts/lint.py", "check": "scripts/nope.py"}]},
            ["scripts/lint.py"]), "DERIVED_UNCHECKED"),
        ("SCRATCH open", lambda: surfaces(
            {"paths": [{"path": "experiments", "surface": "SCRATCH"}]}, []), "SCRATCH_OPEN_ENDED"),
        ("HOST unnamed", lambda: surfaces(
            {"paths": [{"path": ".claude", "surface": "HOST"}]}, []), "HOST_UNDECLARED"),
        ("route missing", lambda: routes(
            {"routes": [{"audience": "x", "document": "NOPE.md",
                         "must_name": [], "must_not_name": []}]}), "ROUTE_MISSING"),
        ("route gap", lambda: routes(
            {"routes": [{"audience": "x", "document": "CONTRACT.md",
                         "must_name": ["zzz-not-present"], "must_not_name": []}]}), "ROUTE_GAP"),
        ("relative route", lambda: routes(
            {"routes": [{"audience": "x", "document": "bindings/README.md",
                         "must_name": ["bindings/INTEGRATING.md"], "must_not_name": []}]}), None),
        ("stale route", lambda: routes(
            {"routes": [{"audience": "x", "document": "README.md",
                         "must_name": [], "must_not_name": ["AGENTS.md"]}]}), "ROUTE_STALE"),
        ("index missing", lambda: entrypoints(
            {"entrypoint_index": {"index": "scripts/NOPE.md", "pattern": "sov_*.py"}}, []),
         "INDEX_MISSING"),
        ("entrypoint missing", lambda: entrypoints(
            {"entrypoint_index": {"index": "CONTRACT.md", "pattern": "sov_*.py"}},
            ["scripts/sov_nowhere.py"]), "ENTRYPOINT_UNINDEXED"),
        ("retired unmarked", lambda: retired(
            {"retired": [{"document": "CONTRACT.md", "marker": "RETIRED",
                          "completed": "2026-01-01"}]}), "STALE_UNMARKED"),
        ("retired absent", lambda: retired(
            {"retired": [{"document": "GONE.md", "marker": "RETIRED",
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
    shadows = shadowing_modules()
    if shadows:
        print("FAIL: publication grader import boundary is shadowed by " + ", ".join(shadows))
        return 1
    try:
        contract, paths = load(), tracked()
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
    return 1 if args.command == "check" and held else 0


if __name__ == "__main__":
    raise SystemExit(main())
