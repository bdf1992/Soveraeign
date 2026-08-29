"""Read ``ROADMAP.md``: which subjects are graded, and where each lane's prose ends.

This module knows Markdown and knows nothing about refusals. It answers what the
document says; ``roadmap_lanes`` decides what the contract requires of that. The
split is why a Markdown rule can be repaired without touching a refusal, and the
reverse.

Three of its rules were earned by witnesses defeating earlier drafts, and each
names a class rather than the instance that found it. A lane's prose ends at the
blank line *or* at the next line that starts a block, because bounding on the
next bold paragraph let a lane swallow an italic follower and bounding on the
blank line alone let it swallow one placed on the very next line. A lane opening
twice is reported as two occurrences rather than resolved last-wins, which had
let a duplicate mask an emptied original. And a declared extra subject reports
every heading that answers to it, because skipping a missing one silently is
what let a rename stop grading the recursion while the gate stayed green.
"""

from __future__ import annotations

import re

#: A phase heading. Multi-digit and optional backticks, so a `P10` section and a
#: mistyped backtick are both visible; the first draft matched one digit and a
#: required backtick, and a new phase or a typo went unread by the grader while
#: staying visible to ``sov_next``.
#:
#: `P` only. The archived `F0`-`F6` ladder carries no lanes and must not be made
#: to: ``ROADMAP-F0-F6.md`` is pinned byte-for-byte in ``contracts/phases.json``
#: as the definition the closed `phase:i` was graded against, so a check that
#: demanded lanes there would demand editing a closed phase's definition.
PHASE_HEADING = re.compile(r"^#{2,3} `?(P\d+)`? ·[^\n]*$", re.M)

#: A row of the phase table: ``| `P0` Ground and govern | ... |``.
PHASE_TABLE_ROW = re.compile(r"^\| `(P\d+)` ", re.M)

#: A lane opener at the head of its own paragraph: ``**Never.** ...``.
LANE_OPENER = re.compile(r"^\*\*([A-Z][a-z]+)\.\*\*(?=[ \n])", re.M)

#: Blockquote markers, stripped before parsing a subject that declares them.
BLOCKQUOTE = re.compile(r"^> ?", re.M)

#: A fenced code block. Blanked before lanes are scanned: a lane that exists only
#: inside a fence shows a reader an example of a lane rather than being one.
CODE_FENCE = re.compile(r"^```.*?^```", re.S | re.M)

#: A line that starts a new block and therefore ends a lane: emphasis, heading,
#: table, fence. A lane ends here as well as at the blank line, because Markdown
#: lazy continuation makes ``**Never.** .`` and a following italic line one
#: paragraph, and the emptied lane then borrowed the follower's words.
#:
#: ``-`` and ``>`` are deliberately absent. A Never written as a bullet list or a
#: quoted passage is a well-stated edge, and terminating on those graded it as an
#: abandoned lane - reporting a good edge under the code for an empty one. The
#: cost of leaving them out is that a bullet list following a lane is read as part
#: of it; this document uses ``-`` for bullets and opens none after a lane.
BLOCK_START = re.compile(r"^(?:\*|#|\||`{3})", re.M)

#: HTML comments, removed before words are counted. A comment renders as nothing,
#: so its words are not a stated edge however many of them there are.
HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)


def body(text: str, start: int) -> str:
    """The text from ``start`` up to the next heading of any level."""
    rest = text[start:]
    stop = re.search(r"^#{1,6} ", rest, re.M)
    return rest[:stop.start()] if stop else rest


def phase_sections(roadmap_text: str) -> dict[str, str]:
    """Phase id -> the body under its heading, for the `P` ladder only."""
    return {match.group(1): body(roadmap_text, match.end())
            for match in PHASE_HEADING.finditer(roadmap_text)}


def table_phases(roadmap_text: str) -> list[str]:
    """Phase ids the roadmap's tables name, first mention first.

    The name crosswalk keys its rows onto the same ladder, so a phase is named
    more than once. Deduplicated rather than filtered by section: a phase in
    either table with no graded heading is the same defect.
    """
    seen: dict[str, None] = {}
    for match in PHASE_TABLE_ROW.finditer(roadmap_text):
        seen.setdefault(match.group(1), None)
    return list(seen)


def extras(roadmap_text: str, contract: dict) -> list[tuple[dict, list]]:
    """Each declared extra subject, with every heading that answers to it.

    Zero and many are both defects the caller names. Skipping a missing heading
    silently is what let a rename stop grading the recursion while the gate the
    document advertises stayed green.
    """
    pairs = []
    for extra in (contract.get("graded_subjects") or {}).get("extra") or []:
        pattern = rf"^#{{2,4}} {re.escape(str(extra.get('heading')))}\s*$"
        pairs.append((extra, list(re.finditer(pattern, roadmap_text, re.M))))
    return pairs


def graded_subjects(roadmap_text: str, contract: dict) -> dict[str, str]:
    """Subject label -> the body graded for lanes.

    Every phase heading, plus the extra headings the contract names. The extras
    are how the recursion gets graded at all: the roadmap's own lanes and the
    worked child are declared by the same contract to carry the same shape, and
    a check that read only phase sections would grade one level of a rule that
    claims to hold at every level.

    A heading that answers to no declared subject, or to two, is left out here
    and named by the caller. Quietly taking the first is what a rename hid behind.
    """
    subjects = phase_sections(roadmap_text)
    for extra, found in extras(roadmap_text, contract):
        if len(found) != 1:
            continue
        section = body(roadmap_text, found[0].end())
        subjects[str(extra.get("subject") or extra.get("heading"))] = (
            BLOCKQUOTE.sub("", section) if extra.get("strip_blockquote") else section)
    return subjects


def lanes_in(section: str) -> dict[str, list[str]]:
    """Lane name -> the prose of every paragraph that opens it.

    A lane's prose ends at the blank line or at the next line that starts a
    block, whichever comes first. Bounding on the next *bold* paragraph let a
    lane swallow an italic follower; bounding on the blank line alone still let
    it swallow one placed on the very next line, because Markdown treats that as
    the same paragraph. Both shapes appear in the document this grades.

    Only the first paragraph of a lane is read. The contract declares a lane to
    be one paragraph, so a lane that spans two is graded on the first and its
    continuation is not counted.

    Fenced code is blanked first, so a lane that exists only inside a fence does
    not satisfy the shape. A fence shows a reader an example of a lane, not one.

    The value is a list because a lane opening twice is a defect the caller
    refuses. Returning the last one silently is what let a duplicate mask an
    emptied original.
    """
    found: dict[str, list[str]] = {}
    section = CODE_FENCE.sub(lambda match: "\n" * match.group().count("\n"), section)
    for match in LANE_OPENER.finditer(section):
        rest = section[match.end():]
        bounds = [len(rest)]
        blank = rest.find("\n\n")
        if blank >= 0:
            bounds.append(blank)
        block = BLOCK_START.search(rest, 1)
        if block:
            bounds.append(block.start())
        found.setdefault(match.group(1), []).append(rest[:min(bounds)].strip())
    return found


def words(prose: str) -> int:
    """Words of substance, so a lone full stop does not read as a stated edge.

    What renders as nothing is removed first and does not count: HTML comments,
    and the target of a link or image, which is why ``[](http://a-b-c)`` read as
    five words of stated edge. A link's visible label survives, because a reader
    sees it. Whoever sets the threshold should keep it low - it exists to refuse a
    lane opened and abandoned, never to grade how well an edge is written, which
    is a reading.
    """
    visible = HTML_COMMENT.sub("", prose)
    visible = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", visible)
    return len(re.findall(r"[0-9A-Za-z][0-9A-Za-z'-]*", visible))


#: A whole small roadmap in the shape this module reads, for a caller to mutate.
#: It lives here rather than beside the refusals because it is Markdown, and the
#: grader claimed to know none: a control that encodes the heading grammar a
#: second time diverges silently from PHASE_HEADING and then proves a syntax the
#: parser no longer reads.
CONTROL = """## The phases

| Phase | Product result | Estimate |
| --- | --- | ---: |
| `P0` Control | A product result | 50% |

### `P0` · Control

**Result.** A product result.

{lanes}

*Repository reading.* A reading that follows the lanes.

**Exits when** it does.

### The shape recurses

Prose about the recursion.

> **A worked child.**
>
{quoted}

### The roadmap's own lanes

{lanes}
"""


def control(lane_names: list[str], sentence: str = "A sentence of four words.") -> str:
    """A control roadmap carrying every graded subject a caller could declare.

    Including the blockquoted child: without it the strip_blockquote path has no
    controlled case and is exercised only against the live document. The phase
    also ends on an italic paragraph, which is the follower shape that defeated
    the first two drafts of the empty-Never rule.
    """
    lanes = [f"**{name}.** {sentence}" for name in lane_names]
    return CONTROL.format(lanes="\n\n".join(lanes),
                          quoted="\n>\n".join(f"> {lane}" for lane in lanes))
