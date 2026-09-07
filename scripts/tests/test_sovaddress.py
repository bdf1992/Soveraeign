"""Cases for the address below the file: each fragment kind resolves to the bytes it
means, a sibling's change leaves the addressed digest alone, and every refusal names
itself. Every case builds its own files under a temporary directory."""

from __future__ import annotations

from pathlib import Path
import json
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import sovaddress  # noqa: E402

COLLECTION = {
    "custodies": [
        {"custody_id": "custody:a", "members": [
            {"address": "x.py", "stage": "VERTICAL_SLICE", "note": "one"},
            {"address": "y.py", "stage": "ROOT_POINT", "note": "two"}]},
        {"custody_id": "custody:b", "members": []},
    ],
    "a/b": {"~key": 1},
}

STATUS = """schema_version: 1
# introduces phase
phase: phase:1-5
owner_holds:
  - id: O1
    reason: PUBLICATION

# introduces the next key
owner_accepted:
  - id: A1
"""

RECORD = """# Title

intro

## Pass 2: commit b

body two

### Detail

deeper

## Pass 1: commit a

body one
"""


class Case(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.addCleanup(self._temp.cleanup)
        self.root = Path(self._temp.name)
        (self.root / "c.json").write_text(json.dumps(COLLECTION, indent=2), encoding="utf-8")
        (self.root / "STATUS.yaml").write_text(STATUS, encoding="utf-8")
        (self.root / "r.md").write_text(RECORD, encoding="utf-8")
        (self.root / "p.py").write_text("print()\n", encoding="utf-8")


class WholeFile(Case):
    def test_a_bare_path_means_the_exact_bytes(self) -> None:
        self.assertEqual(sovaddress.resolve(self.root, "p.py"), b"print()\n")
        self.assertEqual(sovaddress.split("p.py"), ("p.py", None))
        self.assertEqual(sovaddress.split("c.json#/a"), ("c.json", "/a"))


class JsonFragments(Case):
    def test_pointer_with_selectors_reaches_a_member_field(self) -> None:
        address = "c.json#/custodies[custody_id=custody:a]/members[address=x.py]/note"
        self.assertEqual(sovaddress.resolve(self.root, address), b'"one"')

    def test_a_sibling_change_leaves_the_addressed_digest_alone(self) -> None:
        address = "c.json#/custodies[custody_id=custody:a]/members[address=x.py]"
        before = sovaddress.digest(self.root, address)
        document = json.loads((self.root / "c.json").read_text(encoding="utf-8"))
        document["custodies"][0]["members"][1]["note"] = "moved"
        document["custodies"].append({"custody_id": "custody:c", "members": []})
        (self.root / "c.json").write_text(json.dumps(document), encoding="utf-8")
        self.assertEqual(sovaddress.digest(self.root, address), before)
        self.assertNotEqual(sovaddress.digest(self.root, "c.json"), before)
        document["custodies"][0]["members"][0]["note"] = "moved too"
        (self.root / "c.json").write_text(json.dumps(document), encoding="utf-8")
        self.assertNotEqual(sovaddress.digest(self.root, address), before)

    def test_canonical_form_ignores_indentation_and_key_order(self) -> None:
        one = sovaddress.digest(self.root, "c.json#/custodies[custody_id=custody:b]")
        document = json.loads((self.root / "c.json").read_text(encoding="utf-8"))
        document["custodies"][1] = {"members": [], "custody_id": "custody:b"}
        (self.root / "c.json").write_text(json.dumps(document, indent=4), encoding="utf-8")
        self.assertEqual(sovaddress.digest(self.root, "c.json#/custodies[custody_id=custody:b]"),
                         one)

    def test_a_selector_value_may_hold_a_slash(self) -> None:
        document = json.loads((self.root / "c.json").read_text(encoding="utf-8"))
        document["custodies"][0]["custody_id"] = "custody:phase/a"
        (self.root / "c.json").write_text(json.dumps(document), encoding="utf-8")
        address = "c.json#/custodies[custody_id=custody:phase/a]/members/0/note"
        self.assertEqual(sovaddress.resolve(self.root, address), b'"one"')

    def test_escapes_and_indexes(self) -> None:
        self.assertEqual(sovaddress.resolve(self.root, "c.json#/a~1b/~0key"), b"1")
        self.assertEqual(sovaddress.resolve(self.root, "c.json#/custodies/1/custody_id"),
                         b'"custody:b"')
        self.assertEqual(sovaddress.resolve(self.root, "c.json#"),
                         sovaddress.canonical(COLLECTION))

    def test_refusals_name_themselves(self) -> None:
        for address, code in (
            ("c.json#/custodies[custody_id=custody:z]", "FRAGMENT_NOT_FOUND"),
            ("c.json#/nope", "FRAGMENT_NOT_FOUND"),
            ("c.json#/custodies/9", "FRAGMENT_NOT_FOUND"),
            ("c.json#custodies", "FRAGMENT_MALFORMED"),
            ("c.json#/custodies[bad", "FRAGMENT_MALFORMED"),
            ("p.py#anything", "FRAGMENT_UNSUPPORTED"),
        ):
            with self.assertRaises(sovaddress.AddressError) as refused:
                sovaddress.resolve(self.root, address)
            self.assertEqual(refused.exception.code, code, address)

    def test_two_matching_elements_are_ambiguous(self) -> None:
        document = json.loads((self.root / "c.json").read_text(encoding="utf-8"))
        document["custodies"].append({"custody_id": "custody:a", "members": []})
        (self.root / "c.json").write_text(json.dumps(document), encoding="utf-8")
        with self.assertRaises(sovaddress.AddressError) as refused:
            sovaddress.resolve(self.root, "c.json#/custodies[custody_id=custody:a]")
        self.assertEqual(refused.exception.code, "SELECTOR_AMBIGUOUS")


class RefusalsAndEdges(Case):
    def test_a_selector_never_matches_an_element_lacking_the_key(self) -> None:
        document = json.loads((self.root / "c.json").read_text(encoding="utf-8"))
        document["custodies"].append({"members": []})
        (self.root / "c.json").write_text(json.dumps(document), encoding="utf-8")
        with self.assertRaises(sovaddress.AddressError) as refused:
            sovaddress.resolve(self.root, "c.json#/custodies[custody_id=None]")
        self.assertEqual(refused.exception.code, "FRAGMENT_NOT_FOUND")

    def test_undecodable_bytes_refuse_by_name(self) -> None:
        (self.root / "b.md").write_bytes(b"# T\n\xff\xfe\n")
        (self.root / "b.yaml").write_bytes(b"k: 1\n\xff\n")
        for address in ("b.md#T", "b.yaml#k"):
            with self.assertRaises(sovaddress.AddressError) as refused:
                sovaddress.resolve(self.root, address)
            self.assertEqual(refused.exception.code, "FRAGMENT_MALFORMED", address)

    def test_a_duplicate_top_level_key_is_ambiguous(self) -> None:
        (self.root / "STATUS.yaml").write_text(STATUS + "phase: again\n", encoding="utf-8")
        with self.assertRaises(sovaddress.AddressError) as refused:
            sovaddress.resolve(self.root, "STATUS.yaml#phase")
        self.assertEqual(refused.exception.code, "SELECTOR_AMBIGUOUS")

    def test_closing_marks_and_fenced_blocks_do_not_make_headings(self) -> None:
        text = "# Top ##\n\n```\n# not a heading\n```\n\nafter\n\n# Next\n"
        (self.root / "f.md").write_text(text, encoding="utf-8")
        self.assertEqual(sovaddress.resolve(self.root, "f.md#Top"),
                         b"# Top ##\n\n```\n# not a heading\n```\n\nafter\n")
        with self.assertRaises(sovaddress.AddressError):
            sovaddress.resolve(self.root, "f.md#not a heading")


class YamlBlocks(Case):
    def test_a_top_level_block_stops_before_the_next_keys_comment(self) -> None:
        block = sovaddress.resolve(self.root, "STATUS.yaml#owner_holds")
        self.assertEqual(block, b"owner_holds:\n  - id: O1\n    reason: PUBLICATION")

    def test_a_sibling_block_change_leaves_the_digest_alone(self) -> None:
        before = sovaddress.digest(self.root, "STATUS.yaml#owner_holds")
        text = STATUS.replace("  - id: A1\n", "  - id: A24\n  - id: A1\n")
        (self.root / "STATUS.yaml").write_text(text, encoding="utf-8")
        self.assertEqual(sovaddress.digest(self.root, "STATUS.yaml#owner_holds"), before)
        self.assertNotEqual(sovaddress.digest(self.root, "STATUS.yaml#owner_accepted"),
                            sovaddress.DIGEST_PREFIX + "x")

    def test_last_key_runs_to_the_end_and_missing_keys_refuse(self) -> None:
        self.assertEqual(sovaddress.resolve(self.root, "STATUS.yaml#owner_accepted"),
                         b"owner_accepted:\n  - id: A1")
        with self.assertRaises(sovaddress.AddressError) as refused:
            sovaddress.resolve(self.root, "STATUS.yaml#nothing")
        self.assertEqual(refused.exception.code, "FRAGMENT_NOT_FOUND")


class MarkdownSections(Case):
    def test_a_section_runs_to_the_next_heading_at_its_level_or_above(self) -> None:
        section = sovaddress.resolve(self.root, "r.md#Pass 2: commit b")
        self.assertEqual(section, b"## Pass 2: commit b\n\nbody two\n\n### Detail\n\ndeeper\n")
        self.assertEqual(sovaddress.resolve(self.root, "r.md#Pass 1: commit a"),
                         b"## Pass 1: commit a\n\nbody one\n")

    def test_an_edit_to_another_section_leaves_the_digest_alone(self) -> None:
        before = sovaddress.digest(self.root, "r.md#Pass 1: commit a")
        (self.root / "r.md").write_text(RECORD.replace("body two", "body two, revised"),
                                        encoding="utf-8")
        self.assertEqual(sovaddress.digest(self.root, "r.md#Pass 1: commit a"), before)

    def test_missing_and_duplicate_headings_refuse(self) -> None:
        with self.assertRaises(sovaddress.AddressError) as refused:
            sovaddress.resolve(self.root, "r.md#Pass 9")
        self.assertEqual(refused.exception.code, "FRAGMENT_NOT_FOUND")
        (self.root / "r.md").write_text(RECORD + "\n## Detail\n", encoding="utf-8")
        with self.assertRaises(sovaddress.AddressError) as refused:
            sovaddress.resolve(self.root, "r.md#Detail")
        self.assertEqual(refused.exception.code, "SELECTOR_AMBIGUOUS")


if __name__ == "__main__":
    unittest.main()
