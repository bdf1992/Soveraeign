"""What a contract declares about itself, as opposed to what it says about itself.

This half of the P15-Q4.3 reading answers one question: does the contract a primitive is
paired with declare the paired term? Only structure counts. A contract's identity is read
at its root, the names it defines are read from its schema keywords, and prose is not read
anywhere - not a description, not a note, not a comment, and not a title.

Three revisions of this rule were refused by three separate readers, each for reading
something that was not a declaration. The first searched the whole JSON dump, so `authority`
matched the sentence "it grants no authority" in 49 of 78 contracts. The second stopped
reading descriptions and kept reading `title`, which is free prose in a structural field, so
one pairing resolved on a title sentence and another failed for having no title at all. The
third harvested a `properties` dict out of an `examples` array, which is instance data. What
survives is deliberately small.
"""

from __future__ import annotations

from typing import Any

DECLARED_NAME_KEYS = ("$defs", "definitions", "properties", "patternProperties")
"""Where a contract declares names rather than describing itself."""

PROSE_KEYS = ("description", "note", "$comment", "warrant", "title", "name", "enum")
"""Keys whose values a contract uses to describe itself rather than to declare anything.

Named here so the self-check's mispaired variant can be pinned against the list instead of
carrying its own copy. `enum` is in it because an enum value is data the contract admits,
not a name it declares."""

EXAMPLE_KEYS = ("examples", "example", "fixtures")
"""Instance data, not declaration. Identity is read at the root for exactly this reason, and
a fifth witness showed the names half did not follow the same line: a `properties` dict
inside an `examples` array was harvested as though the contract had declared it."""


def identity_names(document: Any) -> set[str]:
    """A contract's own declared identity, read at the document root only.

    `$id` for a JSON Schema, and a root-level `_id` or `_schema` value for the policy and
    circuit files that carry no `$id`. Root only, because a contract's identity is declared
    where the contract begins; an identifier nested in example data belongs to the example.

    A value carrying whitespace is not an identifier and is skipped, so a root key that
    happens to end in `_id` cannot smuggle a sentence in. A fifth witness pointed out that
    without this the rule would admit prose again through a differently named door.
    """
    if not isinstance(document, dict):
        return set()
    names = set()
    for key, value in document.items():
        if not isinstance(value, str) or not value or any(c.isspace() for c in value):
            continue
        if key == "$id" or key.endswith("_id") or key.endswith("_schema"):
            names.add(value)
    return names


def structural_names(document: Any) -> set[str]:
    """The names a contract declares: its own identity, and the names it defines.

    Prose is excluded on purpose, and `title` and `name` are prose. An earlier revision read
    them as structure, which let a title sentence stand in for a declaration in both
    directions - one pairing resolved because a title happened to contain its term, another
    failed because its file had no title - and a witness flipped both with an edit that
    changed nothing structural.
    """
    names: set[str] = identity_names(document)

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key in EXAMPLE_KEYS:
                    continue
                if key in DECLARED_NAME_KEYS and isinstance(value, dict):
                    names.update(value)
                    walk(value)
                elif key not in PROSE_KEYS:
                    walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(document)
    return {str(name).lower().replace("_", "").replace("-", "").replace(" ", "")
            for name in names}


def declares(document: Any, primitive: str) -> bool:
    """True when the contract declares the primitive structurally, not merely mentions it."""
    wanted = primitive.replace("_", "")
    return any(wanted in name for name in structural_names(document))
