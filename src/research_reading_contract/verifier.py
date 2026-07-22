from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Iterable

from .pdf_reader import extract_pages, normalize_text, pdf_manifest


class ReadingLevel(str, Enum):
    R0 = "R0_DISCOVERED"
    R1 = "R1_ABSTRACT_VERIFIED"
    R2 = "R2_TARGETED_VERIFIED"
    R3 = "R3_FULL_TEXT_VERIFIED"


LEVEL_RANK = {
    ReadingLevel.R0: 0,
    ReadingLevel.R1: 1,
    ReadingLevel.R2: 2,
    ReadingLevel.R3: 3,
}


@dataclass(frozen=True)
class VerificationResult:
    protocol_version: str
    claimed_level: str
    granted_level: str
    source_valid: bool
    ledger_valid: bool
    claim_grounding_passed: bool
    publishable_at_claimed_level: bool
    accessed_pages: list[int]
    missing_pages_for_claimed_level: list[int]
    errors: list[str]
    warnings: list[str]
    disclaimer: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _page_list(value: Any, field: str, errors: list[str], page_count: int) -> list[int]:
    if value is None:
        return []
    if not isinstance(value, list):
        errors.append(f"{field} must be an array of one-based page numbers.")
        return []

    pages: set[int] = set()
    for item in value:
        if not isinstance(item, int) or isinstance(item, bool):
            errors.append(f"{field} contains a non-integer page value.")
            continue
        if item < 1 or (page_count > 0 and item > page_count):
            errors.append(f"{field} contains page {item} outside 1-{page_count}.")
            continue
        pages.add(item)
    return sorted(pages)


def _valid_sha256(value: Any) -> bool:
    return isinstance(value, str) and bool(re.fullmatch(r"[0-9a-f]{64}", value))


def _claim_grounding(
    report: dict[str, Any],
    accessed_pages: set[int],
    page_count: int,
    page_texts: dict[int, str] | None,
) -> tuple[bool, list[str]]:
    errors: list[str] = []
    claims = report.get("claims", [])
    answer_status = report.get("answer_status")

    if answer_status not in {"complete", "provisional", "insufficient_evidence"}:
        errors.append("answer_status must be complete, provisional, or insufficient_evidence.")
    if not isinstance(claims, list):
        return False, ["claims must be an array."]
    if answer_status in {"complete", "provisional"} and not claims:
        errors.append(f"A {answer_status} answer must contain at least one grounded claim.")

    for index, claim in enumerate(claims, start=1):
        label = f"Claim {index}"
        if not isinstance(claim, dict):
            errors.append(f"{label} must be an object.")
            continue
        if not str(claim.get("claim_id", "")).strip():
            errors.append(f"{label} is missing claim_id.")
        if not str(claim.get("claim_text", "")).strip():
            errors.append(f"{label} is missing claim_text.")
        if claim.get("epistemic_status") not in {
            "direct",
            "author_interpretation",
            "inference",
        }:
            errors.append(f"{label} has an invalid epistemic_status.")

        refs = claim.get("evidence_refs", [])
        if not isinstance(refs, list) or not refs:
            errors.append(f"{label} has no evidence references.")
            continue

        for ref_index, ref in enumerate(refs, start=1):
            ref_label = f"{label} evidence {ref_index}"
            if not isinstance(ref, dict):
                errors.append(f"{ref_label} must be an object.")
                continue
            page = ref.get("page")
            if not isinstance(page, int) or isinstance(page, bool):
                errors.append(f"{ref_label} has no valid page number.")
                continue
            if page < 1 or (page_count > 0 and page > page_count):
                errors.append(f"{ref_label} points outside the source page range.")
                continue
            if page not in accessed_pages:
                errors.append(f"{ref_label} points to page {page} without a valid access receipt.")

            quote = str(ref.get("quote", "")).strip()
            if len(normalize_text(quote)) < 8:
                errors.append(f"{ref_label} must contain a source quote of at least 8 characters.")
            elif page_texts is not None and normalize_text(quote) not in page_texts.get(page, ""):
                errors.append(f"{ref_label} quote was not found on page {page}.")

            if ref.get("support_type") not in {
                "supports",
                "contradicts",
                "qualifies",
                "context",
            }:
                errors.append(f"{ref_label} has an invalid support_type.")

    return not errors, errors


def verify_report(
    report: dict[str, Any],
    receipt_events: Iterable[dict[str, Any]],
    *,
    ledger_errors: Iterable[str] = (),
    pdf_path: str | Path | None = None,
) -> VerificationResult:
    receipt_events = list(receipt_events)
    errors: list[str] = []
    warnings: list[str] = []
    source = report.get("source", {})
    reading = report.get("reading", {})
    coverage = report.get("coverage", {})

    if report.get("protocol_version") != "0.1":
        errors.append("protocol_version must be 0.1.")
    if not str(report.get("report_id", "")).strip():
        errors.append("report_id must be a non-empty string.")
    limitations = report.get("limitations")
    if not isinstance(limitations, list) or not all(
        isinstance(item, str) and item.strip() for item in limitations
    ):
        errors.append("limitations must be an array of non-empty strings.")

    if not isinstance(source, dict):
        source = {}
        errors.append("source must be an object.")
    if not isinstance(reading, dict):
        reading = {}
        errors.append("reading must be an object.")
    if not isinstance(coverage, dict):
        coverage = {}
        errors.append("coverage must be an object.")

    source_sha256 = source.get("sha256")
    page_count = source.get("page_count")
    source_valid = _valid_sha256(source_sha256)
    if not source_valid:
        errors.append("source.sha256 must be a lowercase SHA-256 digest.")
    if not isinstance(page_count, int) or isinstance(page_count, bool) or page_count < 1:
        errors.append("source.page_count must be a positive integer.")
        page_count = 0
        source_valid = False
    if not str(source.get("title", "")).strip():
        errors.append("source.title must be a non-empty string.")

    claimed_text = str(reading.get("claimed_level", ""))
    try:
        claimed_level = ReadingLevel(claimed_text)
    except ValueError:
        claimed_level = ReadingLevel.R0
        errors.append("reading.claimed_level is not a recognized RRC level.")

    ledger_error_list = list(ledger_errors)
    ledger_valid = not ledger_error_list
    errors.extend(ledger_error_list)

    accessed_pages = {
        event.get("page_number")
        for event in receipt_events
        if event.get("source_sha256") == source_sha256
        and isinstance(event.get("page_number"), int)
        and not isinstance(event.get("page_number"), bool)
        and event.get("page_number") >= 1
    }
    if page_count:
        out_of_range = sorted(page for page in accessed_pages if page > page_count)
        if out_of_range:
            warnings.append(
                "Ledger contains receipts outside the reported page range: "
                + ", ".join(str(page) for page in out_of_range)
                + "."
            )
            accessed_pages.difference_update(out_of_range)

    page_texts: dict[int, str] | None = None
    if pdf_path is not None:
        try:
            actual_manifest = pdf_manifest(pdf_path)["source"]
            if actual_manifest["sha256"] != source_sha256:
                errors.append("The supplied PDF SHA-256 does not match the report source.")
                source_valid = False
            if actual_manifest["page_count"] != page_count:
                errors.append("The supplied PDF page count does not match the report source.")
                source_valid = False
            if source_valid:
                extracted = extract_pages(pdf_path, sorted(accessed_pages))
                extracted_by_page = {item["page_number"]: item for item in extracted}
                invalid_receipt_pages = {
                    page
                    for page in accessed_pages
                    if not any(
                        event.get("source_sha256") == source_sha256
                        and event.get("page_number") == page
                        and event.get("page_text_sha256")
                        == extracted_by_page[page]["text_sha256"]
                        and event.get("extracted_chars")
                        == extracted_by_page[page]["extracted_chars"]
                        for event in receipt_events
                    )
                }
                if invalid_receipt_pages:
                    errors.append(
                        "Receipt text digest does not match the supplied PDF on pages: "
                        + ", ".join(str(page) for page in sorted(invalid_receipt_pages))
                        + "."
                    )
                    accessed_pages.difference_update(invalid_receipt_pages)
                page_texts = {
                    page: normalize_text(item["text"])
                    for page, item in extracted_by_page.items()
                    if page in accessed_pages
                }
        except Exception as exc:
            errors.append(f"The supplied PDF could not be verified: {exc}")
            source_valid = False

    abstract_pages = _page_list(
        coverage.get("abstract_pages"), "coverage.abstract_pages", errors, page_count
    )
    required_pages = _page_list(
        coverage.get("required_pages"), "coverage.required_pages", errors, page_count
    )
    required_sections = coverage.get("required_sections", [])
    sections_read = coverage.get("sections_read", [])
    if not isinstance(required_sections, list) or not all(
        isinstance(item, str) and item.strip() for item in required_sections
    ):
        errors.append("coverage.required_sections must be an array of non-empty strings.")
        required_sections = []
    if not isinstance(sections_read, list) or not all(
        isinstance(item, str) and item.strip() for item in sections_read
    ):
        errors.append("coverage.sections_read must be an array of non-empty strings.")
        sections_read = []

    granted = ReadingLevel.R0
    if abstract_pages and set(abstract_pages).issubset(accessed_pages):
        granted = ReadingLevel.R1

    target_question = str(reading.get("target_question", "")).strip()
    sections_satisfied = set(required_sections).issubset(set(sections_read))
    if (
        target_question
        and required_pages
        and set(required_pages).issubset(accessed_pages)
        and sections_satisfied
    ):
        granted = ReadingLevel.R2

    all_pages = set(range(1, page_count + 1)) if page_count else set()
    if all_pages and all_pages.issubset(accessed_pages):
        granted = ReadingLevel.R3

    claim_grounding_passed, claim_errors = _claim_grounding(
        report, accessed_pages, page_count, page_texts
    )
    errors.extend(claim_errors)

    missing_pages: list[int] = []
    if claimed_level == ReadingLevel.R1:
        missing_pages = sorted(set(abstract_pages) - accessed_pages)
        if not abstract_pages:
            errors.append("R1 requires coverage.abstract_pages.")
    elif claimed_level == ReadingLevel.R2:
        missing_pages = sorted(set(required_pages) - accessed_pages)
        if not target_question:
            errors.append("R2 requires reading.target_question.")
        if not required_pages:
            errors.append("R2 requires coverage.required_pages.")
        missing_sections = sorted(set(required_sections) - set(sections_read))
        if missing_sections:
            errors.append("R2 is missing required sections: " + ", ".join(missing_sections) + ".")
    elif claimed_level == ReadingLevel.R3:
        missing_pages = sorted(all_pages - accessed_pages)

    if LEVEL_RANK[granted] < LEVEL_RANK[claimed_level]:
        errors.append(
            f"Claimed {claimed_level.value}, but receipts grant only {granted.value}."
        )

    if pdf_path is None:
        warnings.append(
            "No PDF was supplied; source bytes and evidence quote locations were not independently checked."
        )
    warnings.append(
        "A valid receipt proves recorded page exposure inside the harness trust boundary, not comprehension."
    )

    publishable = (
        source_valid
        and ledger_valid
        and claim_grounding_passed
        and LEVEL_RANK[granted] >= LEVEL_RANK[claimed_level]
        and not errors
    )
    return VerificationResult(
        protocol_version="0.1",
        claimed_level=claimed_text,
        granted_level=granted.value,
        source_valid=source_valid,
        ledger_valid=ledger_valid,
        claim_grounding_passed=claim_grounding_passed,
        publishable_at_claimed_level=publishable,
        accessed_pages=sorted(accessed_pages),
        missing_pages_for_claimed_level=missing_pages,
        errors=errors,
        warnings=warnings,
        disclaimer=(
            "RRC verifies recorded source exposure and claim anchors. "
            "It does not prove comprehension, scientific truth, or review completeness."
        ),
    )
