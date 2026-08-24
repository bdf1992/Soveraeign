"""A small CommonMark subset, rendered to HTML with the standard library only.

It covers what this repository's 157 documents actually use: ATX headings,
fenced code, pipe tables, nested bullet and ordered lists, blockquotes, thematic
breaks, YAML front matter, and inline code, links, bold and italic.

Raw HTML in a source document is escaped rather than passed through. A viewer
that renders whatever a document contains would let a document decide how the
viewer behaves, and 44 of these documents contain angle brackets in prose that
were never meant as markup.

Unsupported constructs degrade to text rather than disappearing, so a document
is never silently shown as less than it is.
"""

from __future__ import annotations

from typing import Iterator
import html
import re


FENCE = re.compile(r"^(```|~~~)\s*([\w-]*)\s*$")
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*$")
BULLET = re.compile(r"^(\s*)[-*+]\s+(.*)$")
ORDERED = re.compile(r"^(\s*)(\d+)[.)]\s+(.*)$")
QUOTE = re.compile(r"^>\s?(.*)$")
RULE = re.compile(r"^\s{0,3}([-*_])(\s*\1){2,}\s*$")
ROW = re.compile(r"^\s*\|(.+)\|\s*$")
DIVIDER = re.compile(r"^\s*\|?[\s:-]*-[\s|:-]*\|?\s*$")

CODE_SPAN = re.compile(r"(`+)(.+?)\1", re.S)
LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
BOLD = re.compile(r"\*\*(\S(?:.*?\S)?)\*\*")
ITALIC = re.compile(r"(?<![*\w])\*(\S(?:[^*]*?\S)?)\*(?!\*)")
AUTOLINK = re.compile(r"<(https?://[^>\s]+)>")

SAFE_SCHEMES = ("http://", "https://", "mailto:", "#")


def slug(text: str) -> str:
    """A stable anchor for a heading, so a table of contents can point at it."""
    cleaned = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    return re.sub(r"[\s_]+", "-", cleaned) or "section"


def _href(target: str) -> str:
    """Keep a link inert unless its scheme is one a document may safely name."""
    if target.startswith(SAFE_SCHEMES) or not re.match(r"^[a-zA-Z][\w+.-]*:", target):
        return html.escape(target, quote=True)
    return "#"


def inline(text: str) -> str:
    """Render inline markup. Code spans are rendered first and never re-scanned."""
    parts: list[str] = []
    position = 0
    for match in CODE_SPAN.finditer(text):
        parts.append(_inline_rest(text[position:match.start()]))
        parts.append(f"<code>{html.escape(match.group(2).strip(), quote=True)}</code>")
        position = match.end()
    parts.append(_inline_rest(text[position:]))
    return "".join(parts)


def _inline_rest(text: str) -> str:
    escaped = html.escape(text, quote=True)
    escaped = AUTOLINK.sub(lambda m: f'<a href="{_href(m.group(1))}">{m.group(1)}</a>', escaped)
    escaped = LINK.sub(
        lambda m: f'<a href="{_href(html.unescape(m.group(2)))}">{m.group(1)}</a>', escaped)
    escaped = BOLD.sub(r"<strong>\1</strong>", escaped)
    escaped = ITALIC.sub(r"<em>\1</em>", escaped)
    return escaped


def strip_front_matter(lines: list[str]) -> list[str]:
    """Drop a leading YAML block. It is metadata about the document, not its text."""
    if lines and lines[0].strip() == "---":
        for index in range(1, len(lines)):
            if lines[index].strip() == "---":
                return lines[index + 1:]
    return lines


class Renderer:
    """One document. `headings` collects the outline as a side effect of rendering."""

    def __init__(self, text: str) -> None:
        self.lines = strip_front_matter(text.replace("\r\n", "\n").split("\n"))
        self.headings: list[tuple[int, str, str]] = []

    def html(self) -> str:
        return "".join(self._blocks())

    def _blocks(self) -> Iterator[str]:
        index = 0
        lines = self.lines
        while index < len(lines):
            line = lines[index]
            if not line.strip():
                index += 1
                continue
            fence = FENCE.match(line)
            if fence:
                index, block = self._fence(index, fence.group(1))
                yield block
                continue
            heading = HEADING.match(line)
            if heading:
                yield self._heading(len(heading.group(1)), heading.group(2))
                index += 1
                continue
            if RULE.match(line):
                yield "<hr>"
                index += 1
                continue
            if ROW.match(line) and index + 1 < len(lines) and DIVIDER.match(lines[index + 1]):
                index, block = self._table(index)
                yield block
                continue
            if QUOTE.match(line):
                index, block = self._quote(index)
                yield block
                continue
            if BULLET.match(line) or ORDERED.match(line):
                index, block = self._list(index, 0)
                yield block
                continue
            index, block = self._paragraph(index)
            yield block

    def _heading(self, level: int, text: str) -> str:
        anchor = slug(text)
        self.headings.append((level, text, anchor))
        return f'<h{level} id="{anchor}">{inline(text)}</h{level}>'

    def _fence(self, index: int, marker: str) -> tuple[int, str]:
        language = FENCE.match(self.lines[index]).group(2)
        body: list[str] = []
        index += 1
        while index < len(self.lines) and not self.lines[index].startswith(marker):
            body.append(self.lines[index])
            index += 1
        attribute = f' data-lang="{html.escape(language, quote=True)}"' if language else ""
        code = html.escape("\n".join(body), quote=True)
        return index + 1, f"<pre{attribute}><code>{code}</code></pre>"

    def _quote(self, index: int) -> tuple[int, str]:
        body: list[str] = []
        while index < len(self.lines):
            match = QUOTE.match(self.lines[index])
            if not match:
                break
            body.append(match.group(1))
            index += 1
        inner = Renderer("\n".join(body)).html()
        return index, f"<blockquote>{inner}</blockquote>"

    def _table(self, index: int) -> tuple[int, str]:
        def cells(line: str) -> list[str]:
            return [cell.strip() for cell in ROW.match(line).group(1).split("|")]

        header = cells(self.lines[index])
        index += 2
        rows: list[list[str]] = []
        while index < len(self.lines) and ROW.match(self.lines[index]):
            rows.append(cells(self.lines[index]))
            index += 1
        head = "".join(f"<th>{inline(cell)}</th>" for cell in header)
        body = "".join(
            "<tr>" + "".join(f"<td>{inline(cell)}</td>" for cell in row) + "</tr>"
            for row in rows)
        return index, ("<div class=\"scroll\"><table><thead><tr>" + head
                       + f"</tr></thead><tbody>{body}</tbody></table></div>")

    def _list(self, index: int, depth: int) -> tuple[int, str]:
        """One list level. A deeper indent recurses; a shallower one ends this level."""
        ordered = bool(ORDERED.match(self.lines[index]))
        items: list[str] = []
        while index < len(self.lines):
            line = self.lines[index]
            if not line.strip():
                if index + 1 < len(self.lines) and (BULLET.match(self.lines[index + 1])
                                                    or ORDERED.match(self.lines[index + 1])):
                    index += 1
                    continue
                break
            match = ORDERED.match(line) or BULLET.match(line)
            if not match:
                if items and line.startswith(" " * (depth + 2)):
                    items[-1] += " " + inline(line.strip())
                    index += 1
                    continue
                break
            indent = len(match.group(1))
            if indent < depth:
                break
            if indent > depth:
                index, nested = self._list(index, indent)
                items[-1] = items[-1] + nested if items else nested
                continue
            content = match.group(3) if ORDERED.match(line) else match.group(2)
            items.append(inline(content))
            index += 1
        tag = "ol" if ordered else "ul"
        body = "".join(f"<li>{item}</li>" for item in items)
        return index, f"<{tag}>{body}</{tag}>"

    def _paragraph(self, index: int) -> tuple[int, str]:
        body: list[str] = []
        while index < len(self.lines):
            line = self.lines[index]
            if (not line.strip() or HEADING.match(line) or FENCE.match(line)
                    or RULE.match(line) or QUOTE.match(line)
                    or BULLET.match(line) or ORDERED.match(line) or ROW.match(line)):
                break
            body.append(line.strip())
            index += 1
        return index, f"<p>{inline(' '.join(body))}</p>"


def render(text: str) -> tuple[str, list[tuple[int, str, str]]]:
    """Render one document, returning its HTML and its heading outline."""
    renderer = Renderer(text)
    return renderer.html(), renderer.headings
