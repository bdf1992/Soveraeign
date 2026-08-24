#!/usr/bin/env python3
"""Read this node's documentation, rendered, with its custody visible.

`ingest` puts every document through the Asset Service, so each one becomes an
addressed source with a version, a content digest, and a receipt. `build`
renders those documents into one browsable page and shows that custody beside
each. `check` refuses when the page no longer matches the documents it claims to
show.

Ingestion is what makes this the node's own reader rather than a static site
generator that happens to live here: the page states, per document, the version
the Asset Service holds and whether the bytes on disk have moved since.

Full-text search is built here, not fetched. The Asset Service's search
projection indexes an asset's label and its ratified descriptions, not the bytes
of the payload, so searching it finds documents by title and never by content.
Indexing payload text is the Projection Service's declared job (`configure-text`,
`search-text`), and that service stands PROPOSED and unbuilt. This page carries
its own index in the meantime and says so; nothing here pretends to call a
service that does not exist.

Every read is local. `ingest` writes only the asset store it is given and the
record under `docs/`.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any
import argparse
import json
import os
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "services" / "asset" / "src"))

from sovdocs.markdown import render as render_markdown  # noqa: E402
from sovdocs.site import render as render_site  # noqa: E402

SKIP_PARTS = {".git", ".venv", "__pycache__", ".local", "node_modules", "lineage", "docs"}
PAGE = ROOT / "docs" / "documentation.html"
LEDGER = ROOT / "docs" / "ingest.json"
STORE = ROOT / ".local" / "docs-assets"
SEARCH_BUDGET = 4000

GROUPS = (
    ("Governing set", lambda path: "/" not in path),
    ("Decisions", lambda path: path.startswith("decisions/")),
    ("Services", lambda path: path.startswith("services/")),
    ("Contracts and bindings", lambda path: path.startswith(("contracts/", "bindings/",
                                                             "adapters/", "conformance/"))),
    ("Reports", lambda path: path.startswith("reports/")),
    ("Diagrams", lambda path: path.startswith("diagrams/")),
    ("Harness", lambda path: path.startswith(".claude/")),
)


def sources() -> list[Path]:
    """Every markdown document this node publishes to its own readers, in a stable order."""
    found: list[Path] = []
    for raw_root, dirs, files in os.walk(ROOT, topdown=True):
        # The published-document population excludes these trees. Prune them before
        # descent so a documentation check never pays to walk Git objects, local
        # runtime state, generated docs, or dependency trees it will discard anyway.
        dirs[:] = sorted(name for name in dirs if name not in SKIP_PARTS)
        root = Path(raw_root)
        found.extend(root / name for name in sorted(files) if name.endswith(".md"))
    return sorted(found, key=lambda path: path.relative_to(ROOT).as_posix())


def _title(text: str, path: str) -> str:
    match = re.search(r"^#\s+(.+?)\s*$", text, re.M)
    return match.group(1) if match else Path(path).stem


def _identifier(path: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", path.lower().removesuffix(".md")).strip("-")


def documents(ledger: dict[str, Any]) -> list[dict[str, Any]]:
    """Render every document once, joined to whatever the Asset Service recorded for it."""
    built = []
    for source in sources():
        path = source.relative_to(ROOT).as_posix()
        raw = source.read_bytes()
        text = raw.decode("utf-8", errors="replace")
        body, _ = render_markdown(text)
        built.append({
            "id": _identifier(path),
            "path": path,
            "title": _title(text, path),
            "digest": sha256(raw).hexdigest(),
            "html": body,
            "search": re.sub(r"\s+", " ", text.lower())[:SEARCH_BUDGET],
            "asset": ledger.get(path),
        })
    return built


def grouped(built: list[dict[str, Any]]) -> list[tuple[str, list[dict[str, Any]]]]:
    """Group for the sidebar. A document lands in the first group that claims it."""
    remaining = list(built)
    groups: list[tuple[str, list[dict[str, Any]]]] = []
    for label, claims in GROUPS:
        taken = [document for document in remaining if claims(document["path"])]
        if taken:
            groups.append((label, taken))
        remaining = [document for document in remaining if document not in taken]
    if remaining:
        groups.append(("Elsewhere", remaining))
    return groups


def read_ledger() -> dict[str, Any]:
    if LEDGER.exists():
        return json.loads(LEDGER.read_text(encoding="utf-8"))["documents"]
    return {}


def build() -> str:
    ledger = read_ledger()
    built = documents(ledger)
    ingested = sum(1 for document in built if document["asset"])
    return render_site(built, grouped(built), ingested)


def cmd_ingest(args: argparse.Namespace) -> int:
    """Put every document through the Asset Service and record what it returned."""
    from soveraeign_asset_service import AssetService  # noqa: PLC0415

    service = AssetService(Path(args.store) if args.store else STORE)
    recorded: dict[str, Any] = {}
    try:
        for source in sources():
            path = source.relative_to(ROOT).as_posix()
            result = service.ingest(source, _title(source.read_text(encoding="utf-8",
                                                                   errors="replace"), path),
                                    args.actor, locator=f"repo:{path}")
            recorded[path] = {key: result[key] for key in
                              ("asset_id", "version_id", "digest", "receipt_id")}
        service.rebuild_projections()
    finally:
        service.close()
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(
        json.dumps({"ledger_schema": "soveraeign-doc-ingest/v1",
                    "note": "What the Asset Service holds for each document. A projection of "
                            "its receipts, not a second record: the service store is the "
                            "original and this is rebuilt by re-running ingest.",
                    "documents": dict(sorted(recorded.items()))}, indent=2) + "\n",
        encoding="utf-8", newline="\n")
    print(f"PASS: ingested {len(recorded)} documents, recorded in "
          f"{LEDGER.relative_to(ROOT).as_posix()}")
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    out = Path(args.out) if args.out else PAGE
    out.parent.mkdir(parents=True, exist_ok=True)
    page = build()
    out.write_text(page, encoding="utf-8", newline="\n")
    ledger = read_ledger()
    built = documents(ledger)
    drifted = sum(1 for document in built
                  if document["asset"] and document["asset"]["digest"] != document["digest"])
    print(f"PASS: {out.relative_to(ROOT).as_posix()} ({len(built)} documents, "
          f"{sum(1 for d in built if d['asset'])} ingested, {drifted} changed since ingest, "
          f"{len(page) // 1024} KiB)")
    return 0


def cmd_check(_: argparse.Namespace) -> int:
    """Refuse a page that no longer matches the documents it claims to show."""
    if not PAGE.exists():
        print(f"FAIL: {PAGE.relative_to(ROOT).as_posix()} has not been built")
        return 1
    if PAGE.read_text(encoding="utf-8") != build():
        print(f"FAIL: {PAGE.relative_to(ROOT).as_posix()} is stale; "
              "run `python scripts/sov_docs.py build`")
        return 1
    print(f"PASS: documentation page matches {len(sources())} documents")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sov_docs")
    sub = parser.add_subparsers(dest="command", required=True)
    ingest = sub.add_parser("ingest", help="put every document through the Asset Service")
    ingest.add_argument("--actor", default="Bdo")
    ingest.add_argument("--store")
    ingest.set_defaults(handler=cmd_ingest)
    build_cmd = sub.add_parser("build", help="render the documentation page")
    build_cmd.add_argument("--out")
    build_cmd.set_defaults(handler=cmd_build)
    sub.add_parser("check", help="refuse a stale page").set_defaults(handler=cmd_check)
    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
