"""Turn one markdown document into the html the page carries.

Rendering is not a function of the document alone: a link becomes an anchor only
when the page also carries its target, so the corpus the document was rendered
against is part of what identifies a rendering. `sov_docs` owns what the corpus
is and how the page is assembled; this module owns how one document becomes html.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path, PurePosixPath
import posixpath
import re

from sovdocs.markdown import render as render_markdown


ROOT = Path(__file__).resolve().parents[2]
# The searchable excerpt kept per document; the whole corpus ships in one page.
SEARCH_BUDGET = 4000


# Joined with a newline only so the corpus key is stable and readable in a digest.
NEWLINE = chr(10)

def _resolver(path: str, known: dict[str, str]):
    """Turn a link written relative to one document into an anchor inside this page.

    A document links to a sibling the way the repository stores it - `AGENTS.md`,
    `../SPEC.md`, `decisions/0001-founding-boundary.md`. On one page those targets
    are anchors, not files, so each is resolved against the linking document's own
    directory. A target this page does not carry resolves to nothing and renders
    as text rather than a link that goes nowhere.
    """
    base = PurePosixPath(path).parent

    def resolve(target: str) -> str | None:
        address, _, fragment = target.partition("#")
        if not address:
            return "#" + fragment if fragment else None
        # Relative to the citing document, then from the repository root, then by
        # a basename only one document answers to. A name two documents share is
        # ambiguous and stays unresolved rather than guessing at one of them.
        # posixpath.normpath, never os.path.normpath: the latter returns backslashes
        # on Windows, which match no corpus key, and the page then differs by host.
        candidates = [posixpath.normpath(str(base / address)), address]
        for candidate in candidates:
            if candidate in known:
                return f"#{known[candidate]}"
        if "/" not in address:
            matches = [value for key, value in known.items()
                       if key.rsplit("/", 1)[-1] == address]
            if len(matches) == 1:
                return f"#{matches[0]}"
        return None

    return resolve


_RENDERED: dict[tuple[str, str, str], tuple[str, str, str, str, list]] = {}


def _rendered(source: Path, resolve=None, corpus: str = "") -> tuple[str, str, str, str, list]:
    """Render one document, keyed by its bytes so a repeat costs a dictionary lookup.

    The check rebuilds the whole page to compare bytes, and the tests build it
    several times over. Rendering 156 documents each time was the only slow part
    of either.

    `corpus` is part of the key because the rendered body is not a function of the
    document alone: a link resolves to an anchor only when this page carries its
    target, so the same bytes render differently against a different corpus. Keyed
    on the document alone, one build over a subset served its body back to the next
    build over the whole set, and the page went stale against itself.
    """
    raw = source.read_bytes()
    digest = sha256(raw).hexdigest()
    key = (digest, source.relative_to(ROOT).as_posix(), corpus)
    cached = _RENDERED.get(key)
    if cached is not None:
        return cached
    text = raw.decode("utf-8", errors="replace")
    body, headings = render_markdown(text, resolve)
    built = (digest, text, body, re.sub(r"\s+", " ", text.lower())[:SEARCH_BUDGET], headings)
    _RENDERED[key] = built
    return built
