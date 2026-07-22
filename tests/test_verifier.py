import unittest

from research_reading_contract.ledger import build_page_access_event
from research_reading_contract.verifier import verify_report


SOURCE_SHA = "a" * 64


def receipts(*pages):
    events = []
    previous = None
    for page in pages:
        event = build_page_access_event(
            source_sha256=SOURCE_SHA,
            page_number=page,
            page_text_sha256=(f"{page:x}" * 64)[:64],
            extracted_chars=100,
            previous_event_sha256=previous,
            timestamp=f"2026-01-01T00:00:{page:02d}Z",
            event_id=f"event-{page}",
        )
        events.append(event)
        previous = event["event_sha256"]
    return events


def report(level, page_count=4, evidence_page=2, answer_status="provisional"):
    claims = []
    if answer_status != "insufficient_evidence":
        claims = [
            {
                "claim_id": "C1",
                "claim_text": "The source reports the declared result.",
                "epistemic_status": "direct",
                "evidence_refs": [
                    {
                        "page": evidence_page,
                        "quote": "The declared result was observed.",
                        "support_type": "supports",
                    }
                ],
            }
        ]
    return {
        "protocol_version": "0.1",
        "report_id": "test-report",
        "source": {"sha256": SOURCE_SHA, "page_count": page_count, "title": "Test"},
        "reading": {
            "claimed_level": level,
            "target_question": "What result was reported?",
        },
        "coverage": {
            "abstract_pages": [1],
            "required_pages": [1, 2],
            "required_sections": ["Results"],
            "sections_read": ["Abstract", "Results"],
        },
        "claims": claims,
        "answer_status": answer_status,
        "limitations": [],
    }


class VerifierTests(unittest.TestCase):
    def test_self_reported_full_text_is_downgraded(self):
        result = verify_report(
            report("R3_FULL_TEXT_VERIFIED"), receipts(1, 2)
        )

        self.assertEqual("R2_TARGETED_VERIFIED", result.granted_level)
        self.assertEqual([3, 4], result.missing_pages_for_claimed_level)
        self.assertFalse(result.publishable_at_claimed_level)

    def test_all_pages_grant_full_text(self):
        result = verify_report(
            report("R3_FULL_TEXT_VERIFIED"), receipts(1, 2, 3, 4)
        )

        self.assertEqual("R3_FULL_TEXT_VERIFIED", result.granted_level)
        self.assertTrue(result.claim_grounding_passed)
        self.assertTrue(result.publishable_at_claimed_level)

    def test_unread_evidence_page_fails_grounding(self):
        result = verify_report(
            report("R2_TARGETED_VERIFIED", evidence_page=3), receipts(1, 2)
        )

        self.assertEqual("R2_TARGETED_VERIFIED", result.granted_level)
        self.assertFalse(result.claim_grounding_passed)
        self.assertFalse(result.publishable_at_claimed_level)
        self.assertTrue(any("without a valid access receipt" in error for error in result.errors))

    def test_insufficient_evidence_may_have_no_claims(self):
        result = verify_report(
            report("R1_ABSTRACT_VERIFIED", answer_status="insufficient_evidence"),
            receipts(1),
        )

        self.assertEqual("R1_ABSTRACT_VERIFIED", result.granted_level)
        self.assertTrue(result.claim_grounding_passed)
        self.assertTrue(result.publishable_at_claimed_level)


if __name__ == "__main__":
    unittest.main()
