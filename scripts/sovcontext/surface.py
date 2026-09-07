"""Measure what it costs to become oriented in this repository.

Four readings, each a count of something a reader actually has to traverse:

    volume      how much text each surface holds
    reach       entrypoints nothing names, and names pointing at nothing
    redundancy  facts stated by more than one producer
    routes      how many other governing documents each one sends a reader to

None of it is a quality judgement. A large surface is not a defective surface,
and an orphan script is not a bad script. What these numbers establish is the
size of the traversal, so a compression pass can be graded on the tree rather
than on how the pass describes itself.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import re

from sovcontext.probes import PROBES

SKIP_DIRS = (".git", "lineage", "archives", "node_modules", ".local", "experiments")

# Each surface is (name, glob, whether its lines are counted).
SURFACES: tuple[tuple[str, str], ...] = (
    ("root-docs", "*.md"),
    ("agents", ".claude/agents/*.md"),
    ("skills", ".claude/skills/*/SKILL.md"),
    ("workflows", ".claude/workflows/*.js"),
    ("scripts", "scripts/*.py"),
    ("script-packages", "scripts/*/*.py"),
    ("decisions", "decisions/*.md"),
    ("service-docs", "services/*/*.md"),
    ("contracts", "contracts/**/*.json"),
    ("reports", "reports/**/*.md"),
)

# Surfaces a participant may have to read before it can act at all. The rest are
# reached only once a concern has already been named.
ORIENTATION = ("root-docs", "agents", "skills", "workflows")


def _lines(path: Path) -> int:
    try:
        return len(path.read_text(encoding="utf-8", errors="replace").splitlines())
    except OSError:
        return 0


def volume(root: Path) -> dict[str, Any]:
    """Count files and lines per surface, and the orientation subtotal."""
    surfaces: list[dict[str, Any]] = []
    for name, pattern in SURFACES:
        paths = sorted(p for p in root.glob(pattern) if p.is_file())
        surfaces.append({
            "surface": name,
            "files": len(paths),
            "lines": sum(_lines(p) for p in paths),
        })
    orientation = [s for s in surfaces if s["surface"] in ORIENTATION]
    return {
        "surfaces": surfaces,
        "orientation_files": sum(s["files"] for s in orientation),
        "orientation_lines": sum(s["lines"] for s in orientation),
        "total_files": sum(s["files"] for s in surfaces),
        "total_lines": sum(s["lines"] for s in surfaces),
    }


def _prose(root: Path) -> list[Path]:
    """Every file that could name an entrypoint to a reader."""
    found: list[Path] = []
    for pattern in ("*.md", ".claude/**/*.md", ".claude/**/*.js", "services/*/*.md",
                    "scripts/README.md", "docs/*.md"):
        found.extend(p for p in root.glob(pattern) if p.is_file())
    return sorted(set(found))


def reach(root: Path) -> dict[str, Any]:
    """Entrypoints nothing names, and named entrypoints that do not exist."""
    named: set[str] = set()
    for path in _prose(root):
        text = path.read_text(encoding="utf-8", errors="replace")
        named.update(re.findall(r"[A-Za-z0-9_]+\.py", text))
    present = {p.name for p in root.glob("scripts/*.py")}
    orphans = sorted(present - named)
    # A name in prose that resolves to no script under scripts/ is a dead route
    # only if it looks like one of ours; a stdlib or third-party filename is not.
    dangling = sorted(n for n in named - present
                      if n.startswith(("sov_", "sov", "verify", "lint")) and "/" not in n)
    return {
        "entrypoints": len(present),
        "unnamed": orphans,
        "unnamed_count": len(orphans),
        "dangling": dangling,
        "dangling_count": len(dangling),
    }


def redundancy(root: Path) -> dict[str, Any]:
    """For each declared fact, how many files state it."""
    corpus = _prose(root)
    facts: list[dict[str, Any]] = []
    for fact_id, owner, name, pattern in PROBES:
        rx = re.compile(pattern, re.IGNORECASE)
        producers = sorted(
            str(p.relative_to(root)).replace("\\", "/")
            for p in corpus
            if rx.search(p.read_text(encoding="utf-8", errors="replace"))
        )
        facts.append({
            "fact": fact_id,
            "name": name,
            "owner": owner,
            "producers": len(producers),
            "restatements": max(0, len(producers) - 1),
            "files": producers,
        })
    facts.sort(key=lambda f: -f["producers"])
    return {
        "facts": facts,
        "total_restatements": sum(f["restatements"] for f in facts),
        "worst": facts[0]["fact"] if facts else None,
    }


DOC_REF = re.compile(r"\b([A-Z][A-Z0-9-]*\.md|STATUS\.yaml)\b")


def routes(root: Path) -> dict[str, Any]:
    """How many other governing documents each root document sends a reader to."""
    docs = sorted(p for p in root.glob("*.md") if p.is_file())
    names = {p.name for p in docs} | {"STATUS.yaml"}
    edges: list[dict[str, Any]] = []
    for path in docs:
        text = path.read_text(encoding="utf-8", errors="replace")
        targets = sorted({m for m in DOC_REF.findall(text)
                          if m in names and m != path.name})
        edges.append({"doc": path.name, "out": len(targets), "targets": targets})
    edges.sort(key=lambda e: -e["out"])
    total = sum(e["out"] for e in edges)
    return {
        "documents": len(docs),
        "edges": total,
        "mean_fanout": round(total / len(docs), 1) if docs else 0.0,
        "by_document": edges,
    }


def checkpoint(root: Path) -> dict[str, Any]:
    """One reading of the whole context surface."""
    vol = volume(root)
    rch = reach(root)
    red = redundancy(root)
    rte = routes(root)
    return {
        "reading": "soveraeign-context-surface/v1",
        "volume": vol,
        "reach": rch,
        "redundancy": red,
        "routes": rte,
        "headline": {
            "orientation_lines": vol["orientation_lines"],
            "orientation_files": vol["orientation_files"],
            "entrypoints": rch["entrypoints"],
            "unreachable_entrypoints": rch["unnamed_count"],
            "duplicated_facts": sum(1 for f in red["facts"] if f["producers"] > 1),
            "total_restatements": red["total_restatements"],
            "route_edges": rte["edges"],
            "mean_fanout": rte["mean_fanout"],
        },
    }
