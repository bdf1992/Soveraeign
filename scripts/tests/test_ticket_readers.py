"""Unit tests for the two readers of the ``soveraeign-ticket/v1`` metadata block.

``sovticket.yamlblock`` serves the ticket contract commands and ``sovepic.metadata``
serves the epic walk. Both read the same block, so both are tested here together: a
subset one admits and the other refuses is how issue #67 came to walk in the tree while
failing the contract check. The end-to-end cases live in
``conformance/fixtures/tickets/body-cases.json`` and run through
``scripts/sov_ticket.py selfcheck``; these cover local mechanics and reader parity.
"""

from __future__ import annotations

from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovepic.metadata import MetadataError, parse_body  # noqa: E402
from sovticket.yamlblock import TicketBlockError, load_ticket, parse_block  # noqa: E402

BODY = """# Title — bounded outcome

```yaml
issue_schema: soveraeign-ticket/v1
tags:
  - "kind:bit"
  - "village:ground-and-evidence"
  - "horizon:now"
kind: bit
bit_id: BIT-GROUND-KERNEL
village: ground-and-evidence
parent: "#1"
standing: OPEN
horizon: NOW
authority: Bdo/phase-gate
effect_class: RECORD_LOCAL
evidence_pointer: contracts/
last_observed_at: null
requires: ["#25", "#26"]
dependency_channels:
  produces: [kernel-transitions]
  consumes: [receipts]
```

## Obligation

Body prose.
"""

class YamlBlockTests(unittest.TestCase):
    """The bounded YAML subset admits what the contract uses and refuses the rest."""

    def test_block_may_sit_under_a_heading(self) -> None:
        self.assertEqual(load_ticket(BODY)["kind"], "bit")

    def test_prose_before_the_block_is_refused(self) -> None:
        with self.assertRaises(TicketBlockError):
            load_ticket("Some narrative first.\n\n```yaml\nkind: bit\n```\n")

    def test_unclosed_fence_is_refused(self) -> None:
        with self.assertRaises(TicketBlockError):
            load_ticket("```yaml\nkind: bit\n")

    def test_null_literal_becomes_none(self) -> None:
        self.assertIsNone(load_ticket(BODY)["last_observed_at"])

    def test_quoted_empty_string_is_not_null(self) -> None:
        self.assertEqual(parse_block('walker_receipt: ""'), {"walker_receipt": ""})

    def test_block_sequence_and_flow_sequence(self) -> None:
        metadata = load_ticket(BODY)
        self.assertEqual(metadata["tags"][0], "kind:bit")
        self.assertEqual(metadata["requires"], ["#25", "#26"])

    def test_nested_mapping_is_admitted_one_level(self) -> None:
        channels = load_ticket(BODY)["dependency_channels"]
        self.assertEqual(channels, {"produces": ["kernel-transitions"], "consumes": ["receipts"]})

    def test_flow_sequence_keeps_quoted_separators(self) -> None:
        self.assertEqual(parse_block('a: ["x,y", z]'), {"a": ["x,y", "z"]})

    def test_duplicate_key_is_refused(self) -> None:
        with self.assertRaises(TicketBlockError):
            parse_block("kind: bit\nkind: village")

    def test_tab_indentation_is_refused(self) -> None:
        with self.assertRaises(TicketBlockError):
            parse_block("a:\n\t- b")

    def test_anchor_and_alias_are_refused(self) -> None:
        for text in ("&anchor value", "*alias"):
            with self.assertRaises(TicketBlockError):
                parse_block(text)

    def test_multi_line_scalar_is_refused(self) -> None:
        with self.assertRaises(TicketBlockError):
            parse_block("summary: |\n  folded text")

    def test_flow_mapping_is_refused(self) -> None:
        with self.assertRaises(TicketBlockError):
            parse_block("a: {b: c}")

    def test_a_sequence_item_may_be_a_mapping(self) -> None:
        parsed = parse_block('asks:\n  - of: "#11"\n    adjustment: "exist"\n')
        self.assertEqual(parsed, {"asks": [{"of": "#11", "adjustment": "exist"}]})

    def test_sequence_item_mappings_stay_separate(self) -> None:
        text = 'asks:\n  - of: "#11"\n    adjustment: "one"\n  - of: "#30"\n    adjustment: "two"\n'
        self.assertEqual(
            parse_block(text),
            {"asks": [{"of": "#11", "adjustment": "one"}, {"of": "#30", "adjustment": "two"}]},
        )

    def test_a_top_level_key_closes_the_open_sequence_item(self) -> None:
        """A continuation key belongs to the item above it, never to a later top-level key."""
        text = 'asks:\n  - of: "#11"\n    adjustment: "one"\nstanding: OPEN\n'
        parsed = parse_block(text)
        self.assertEqual(parsed["standing"], "OPEN")
        self.assertEqual(parsed["asks"], [{"of": "#11", "adjustment": "one"}])

    def test_a_sequence_item_mapping_may_carry_a_flow_sequence(self) -> None:
        parsed = parse_block('asks:\n  - of: "#11"\n    also: ["#12", "#13"]\n')
        self.assertEqual(parsed, {"asks": [{"of": "#11", "also": ["#12", "#13"]}]})

    def test_a_quoted_scalar_item_containing_a_colon_stays_a_scalar(self) -> None:
        """Tags read as scalars: the mapping shape is opened by an unquoted key, not by a colon."""
        self.assertEqual(parse_block('tags:\n  - "kind:story"\n'), {"tags": ["kind:story"]})

    def test_a_sequence_may_not_mix_item_shapes(self) -> None:
        for text in (
            'asks:\n  - of: "#11"\n    adjustment: "one"\n  - "#30 should do the rest"\n',
            'asks:\n  - "#30 should do the rest"\n  - of: "#11"\n    adjustment: "one"\n',
        ):
            with self.assertRaises(TicketBlockError):
                parse_block(text)

    def test_a_sequence_item_may_not_repeat_a_key(self) -> None:
        with self.assertRaises(TicketBlockError):
            parse_block('asks:\n  - of: "#11"\n    of: "#30"\n')

    def test_a_sequence_item_admits_one_level_only(self) -> None:
        with self.assertRaises(TicketBlockError):
            parse_block('asks:\n  - of: "#11"\n    adjustment: "one"\n      note: "deeper"\n')


class ReaderParityTests(unittest.TestCase):
    """One ticket contract is read by two parsers; they must not drift apart.

    ``sovticket.yamlblock`` serves the ticket contract commands and
    ``sovepic.metadata`` serves the epic walk. Both read the same
    ``soveraeign-ticket/v1`` block. When decision 0022 added a story's ``asks``, only
    the epic reader was extended, so issue #67 walked in the tree and failed the
    contract check. This case makes that class of divergence fail here instead of on
    the live board.
    """

    def setUp(self) -> None:
        corpus = ROOT / "conformance" / "fixtures" / "tickets" / "body-cases.json"
        self.cases = json.loads(corpus.read_text(encoding="utf-8"))["cases"]

    def test_both_readers_parse_every_positive_body_identically(self) -> None:
        for case in (c for c in self.cases if c["expect"] == "VALID"):
            with self.subTest(case=case["case_id"]):
                self.assertEqual(load_ticket(case["body"]), parse_body(case["body"]))

    def test_both_readers_refuse_every_defeating_body(self) -> None:
        """Wording may differ between the two readers; admitting the body may not."""
        for case in (c for c in self.cases if c["expect"] == "REFUSED"):
            with self.subTest(case=case["case_id"]):
                with self.assertRaises(TicketBlockError):
                    load_ticket(case["body"])
                with self.assertRaises(MetadataError):
                    parse_body(case["body"])

if __name__ == "__main__":
    unittest.main()
