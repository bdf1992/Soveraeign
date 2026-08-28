"""Read a witness record: what it declares, and whether it declares anything.

Split from `scripts/sov_standing.py` when five rounds of repair took that module
past the 300-line ceiling. The split is by owned responsibility rather than by
line count: this module reads `witness/`, and the module it left reads
`STATUS.yaml`. The two sides deliberately fail in opposite directions - see
`claimed_standing()` there - so keeping them apart makes that easier to hold on
to, not harder.
"""

from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
WITNESS_DIR = ROOT / "witness"


NOT_A_RECORD = {"readme", "index"}

# A witness record carries a subject at most to WITNESSED. `AGENTS.md` reserves
# ratification for a seat that settles JUDGEMENT, and `witness/README.md` says
# the same: depositing a record makes advancing standing possible and never
# performs it. A record declaring RATIFIED has over-reached, and the gate names
# that rather than quietly declining to count it.
WITNESS_MAY_SUPPORT = "WITNESSED"

# The field is read from a declared position, never searched for in the document.
#
# The previous repair stripped fenced blocks, inline spans and HTML comments and
# then searched what remained. A fourth reading walked four quotation forms past
# it: a nested four-backtick fence, an unterminated fence, a blockquoted label,
# and an indented one. That was the correct finding and the general one - there
# is no finite list of ways markdown can quote, so stripping what looks like
# quotation is enumeration wearing structure's clothes. It is the same mistake
# the value half of this gate had already been repaired for, made again on the
# other axis in the same commit.
#
# A position has no such tail. The block must be the first content in the file,
# after an optional heading, and nothing after it is read at all. A record may
# then quote anything, in any nesting, terminated or not, without touching what
# it declares - which matters, because the most likely record to quote this gate
# is a record about this gate.
BLOCK_OPEN = "```witness"
BLOCK_CLOSE = "```"
STANDING_FIELD = "standing_supported"

# A block holds field lines and nothing else. This is the bound on the body,
# so it is what refuses a run-on block rather than a line count would.
FIELD_LINE = re.compile(r"^[a-z][a-z0-9_]*[ \t]+\S")

# The second half of the bound, and the honest half. A field line is a weak shape
# - "some prose here" matches it - so shape alone would not stop a run-on block
# from swallowing a document. A declaration is a handful of fields; past this it
# is not a declaration and the gate stops rather than guessing.
MAX_BLOCK_LINES = 8

# The whole value must BE a standing. Scanning a value for one is what three
# readings each defeated in a new way: `SELF_WITNESSED` splits into SELF and
# WITNESSED under any tokeniser, so a scan reads a self-witness - the one
# inversion `AGENTS.md` exists to forbid - as support for it. `PRE-WITNESSED`,
# `WITNESSED subject to conditions` and `WITNESSED (retracted)` each defeated a
# different hand-written denial list, and such a list has no end. Inside a plain
# text block there is no emphasis to strip either, so `WITNESSED*` and its
# footnote are simply not this word.
SUPPORTED_VALUES = {"WITNESSED": "WITNESSED", "RATIFIED": "RATIFIED"}


def declared_block(text: str) -> list[str] | None:
    """The record's declaration block, or None if it does not open with one.

    Two bounds, and the second is the one a fifth reading had to supply. The open
    is a position: the block is the first content in the file, after blank lines
    and at most the title heading. An unbounded run of headings was admitted
    before, so `## Example only:` above a quoted block promoted over the record's
    own declaration further down.

    The close was an unbounded forward search, which is the same defect wearing
    the other shoe: an opening fence the author never closed ran on until some
    later fence, swallowing everything between and reading a quoted value as the
    record's own. Proved on a shipped record, from a verbatim quotation of the
    page that tells authors to quote it.

    So the body is bounded by shape rather than by distance: every line in it must
    be a field line. A run-on block picks up prose, a heading, or a fence, none of
    which is a field, and the record declares nothing. That is the right answer
    for an unterminated fence anyway - it is malformed, and guessing where the
    author meant it to end is the guess this gate keeps being defeated by.
    """
    lines = text.split("\n")
    index = 0
    while index < len(lines) and not lines[index].strip():
        index += 1
    if index < len(lines) and lines[index].startswith("#"):
        index += 1
    while index < len(lines) and not lines[index].strip():
        index += 1
    if index >= len(lines) or lines[index].strip() != BLOCK_OPEN:
        return None
    index += 1
    body: list[str] = []
    while index < len(lines) and lines[index].strip() != BLOCK_CLOSE:
        if not FIELD_LINE.match(lines[index]) or len(body) >= MAX_BLOCK_LINES:
            return None
        body.append(lines[index])
        index += 1
    return body if index < len(lines) else None


def declared_field(text: str) -> str | None:
    """The one `standing_supported` value the record's own block states.

    Stated twice is stated ambiguously and counts as not stated: a record says
    this once or it says nothing.
    """
    body = declared_block(text)
    if body is None:
        return None
    found = [line.split(None, 1)[1] if len(line.split(None, 1)) > 1 else ""
             for line in body if line.split(None, 1)[:1] == [STANDING_FIELD]]
    return found[0] if len(found) == 1 else None


def supported_standing(record: Path) -> str | None:
    """The standing this record declares, or None if it declares none.

    A filename is a declaration; what the record says is the artifact. This reads
    one field from one declared position and compares its whole value against a
    closed set. It does not read English and does not search the document.

    Non-ASCII is refused before the comparison. Case folding is not identity -
    the Turkish dotless i upper-cases to `I`, so a lookalike spelling would walk
    straight through an exact match.
    """
    try:
        text = record.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    value = declared_field(text)
    if value is None:
        return None
    value = value.strip()
    if not value.isascii():
        return None
    return SUPPORTED_VALUES.get(value.upper())


def witness_records(witness_dir: Path = WITNESS_DIR) -> dict[str, str]:
    """Subject to the standing its record declares, for records that declare one.

    The directory's own documentation is not an observation of anything. Counting
    it would let the file that explains the convention satisfy a claim made under
    that convention.
    """
    if not witness_dir.is_dir():
        return {}
    declared = {}
    for path in sorted(witness_dir.glob("*.md")):
        stem = path.stem.lower()
        if stem in NOT_A_RECORD:
            continue
        standing = supported_standing(path)
        if standing is not None:
            declared[stem] = standing
    return declared
