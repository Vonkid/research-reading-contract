import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from pypdf import PdfWriter

from research_reading_contract.cli import main
from research_reading_contract.ledger import build_page_access_event
from research_reading_contract.pdf_reader import pdf_manifest
from research_reading_contract.verifier import verify_report


class CliTests(unittest.TestCase):
    def test_setup_and_doctor_project_scope(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            setup_output = io.StringIO()
            with contextlib.redirect_stdout(setup_output):
                setup_code = main(
                    [
                        "setup",
                        "--agent",
                        "both",
                        "--scope",
                        "project",
                        "--project",
                        str(project),
                    ]
                )
            setup_result = json.loads(setup_output.getvalue())

            doctor_output = io.StringIO()
            with contextlib.redirect_stdout(doctor_output):
                doctor_code = main(
                    [
                        "doctor",
                        "--agent",
                        "both",
                        "--scope",
                        "project",
                        "--project",
                        str(project),
                    ]
                )
            doctor_result = json.loads(doctor_output.getvalue())

        self.assertEqual(0, setup_code)
        self.assertEqual(2, len(setup_result["installed"]))
        self.assertEqual(0, doctor_code)
        self.assertTrue(doctor_result["ready"])

    def test_end_to_end_blank_pdf_receipts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pdf = root / "sample.pdf"
            writer = PdfWriter()
            writer.add_blank_page(width=200, height=200)
            writer.add_blank_page(width=200, height=200)
            with pdf.open("wb") as handle:
                writer.write(handle)

            ledger = root / "access.jsonl"
            read_output = io.StringIO()
            with contextlib.redirect_stdout(read_output):
                read_code = main(
                    ["read", str(pdf), "--pages", "1-2", "--ledger", str(ledger)]
                )
            self.assertEqual(0, read_code)
            self.assertEqual(
                [1, 2],
                [p["page_number"] for p in json.loads(read_output.getvalue())["pages"]],
            )

            source = pdf_manifest(pdf)["source"]
            report = {
                "protocol_version": "0.1",
                "report_id": "cli-test",
                "source": {**source, "title": "Blank fixture"},
                "reading": {"claimed_level": "R3_FULL_TEXT_VERIFIED"},
                "coverage": {
                    "abstract_pages": [],
                    "required_pages": [],
                    "required_sections": [],
                    "sections_read": [],
                },
                "claims": [],
                "answer_status": "insufficient_evidence",
                "limitations": ["Blank test fixture."],
            }
            report_path = root / "report.json"
            report_path.write_text(json.dumps(report), encoding="utf-8")

            verify_output = io.StringIO()
            with contextlib.redirect_stdout(verify_output):
                verify_code = main(
                    [
                        "verify",
                        str(report_path),
                        "--ledger",
                        str(ledger),
                        "--pdf",
                        str(pdf),
                    ]
                )
            result = json.loads(verify_output.getvalue())

        self.assertEqual(0, verify_code)
        self.assertEqual("R3_FULL_TEXT_VERIFIED", result["granted_level"])
        self.assertTrue(result["publishable_at_claimed_level"])

    def test_pdf_rejects_forged_page_text_digest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pdf = root / "sample.pdf"
            writer = PdfWriter()
            writer.add_blank_page(width=200, height=200)
            with pdf.open("wb") as handle:
                writer.write(handle)

            source = pdf_manifest(pdf)["source"]
            forged_receipt = build_page_access_event(
                source_sha256=source["sha256"],
                page_number=1,
                page_text_sha256="f" * 64,
                extracted_chars=999,
                previous_event_sha256=None,
                timestamp="2026-01-01T00:00:00Z",
                event_id="forged-event",
            )
            report = {
                "protocol_version": "0.1",
                "report_id": "forged-test",
                "source": {**source, "title": "Blank fixture"},
                "reading": {"claimed_level": "R1_ABSTRACT_VERIFIED"},
                "coverage": {
                    "abstract_pages": [1],
                    "required_pages": [],
                    "required_sections": [],
                    "sections_read": ["Abstract"],
                },
                "claims": [],
                "answer_status": "insufficient_evidence",
                "limitations": ["Blank test fixture."],
            }

            result = verify_report(report, [forged_receipt], pdf_path=pdf)

        self.assertEqual("R0_DISCOVERED", result.granted_level)
        self.assertFalse(result.publishable_at_claimed_level)
        self.assertTrue(any("Receipt text digest" in error for error in result.errors))


if __name__ == "__main__":
    unittest.main()
