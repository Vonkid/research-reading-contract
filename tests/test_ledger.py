import json
import tempfile
import unittest
from pathlib import Path

from research_reading_contract.ledger import (
    build_page_access_event,
    canonical_json,
    validate_ledger,
)


class LedgerTests(unittest.TestCase):
    def test_valid_chain_is_accepted(self):
        first = build_page_access_event(
            source_sha256="a" * 64,
            page_number=1,
            page_text_sha256="b" * 64,
            extracted_chars=100,
            previous_event_sha256=None,
            timestamp="2026-01-01T00:00:00Z",
            event_id="event-1",
        )
        second = build_page_access_event(
            source_sha256="a" * 64,
            page_number=2,
            page_text_sha256="c" * 64,
            extracted_chars=120,
            previous_event_sha256=first["event_sha256"],
            timestamp="2026-01-01T00:00:01Z",
            event_id="event-2",
        )
        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / "access.jsonl"
            ledger.write_text(canonical_json(first) + "\n" + canonical_json(second) + "\n")
            events, errors = validate_ledger(ledger)

        self.assertEqual(2, len(events))
        self.assertEqual([], errors)

    def test_tampered_event_stops_chain(self):
        event = build_page_access_event(
            source_sha256="a" * 64,
            page_number=1,
            page_text_sha256="b" * 64,
            extracted_chars=100,
            previous_event_sha256=None,
            timestamp="2026-01-01T00:00:00Z",
            event_id="event-1",
        )
        event["page_number"] = 2
        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / "access.jsonl"
            ledger.write_text(json.dumps(event) + "\n")
            events, errors = validate_ledger(ledger)

        self.assertEqual([], events)
        self.assertIn("invalid event digest", errors[0])


if __name__ == "__main__":
    unittest.main()
