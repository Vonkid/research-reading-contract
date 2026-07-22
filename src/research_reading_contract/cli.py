from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from . import __version__
from .ledger import append_page_access_events, validate_ledger
from .pdf_reader import extract_pages, parse_page_spec, pdf_manifest
from .verifier import verify_report


def _print_json(value: Any) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True))


def _load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rrc",
        description="Verify scientific PDF reading coverage and claim anchors.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    manifest_parser = subparsers.add_parser("manifest", help="Fingerprint a PDF source.")
    manifest_parser.add_argument("pdf", help="Path to the PDF.")

    read_parser = subparsers.add_parser(
        "read", help="Extract pages and append page-access receipts."
    )
    read_parser.add_argument("pdf", help="Path to the PDF.")
    read_parser.add_argument(
        "--pages", required=True, help="One-based page list, for example 1-3,7,10."
    )
    read_parser.add_argument(
        "--ledger", required=True, help="Path to the local JSONL receipt ledger."
    )

    verify_parser = subparsers.add_parser(
        "verify", help="Verify a reading report against a receipt ledger."
    )
    verify_parser.add_argument("report", help="Path to the reading report JSON.")
    verify_parser.add_argument("--ledger", required=True, help="Path to the receipt ledger.")
    verify_parser.add_argument(
        "--pdf", help="Optional source PDF for digest, page-count, and quote verification."
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "manifest":
            _print_json(pdf_manifest(args.pdf))
            return 0

        if args.command == "read":
            manifest = pdf_manifest(args.pdf)
            source = manifest["source"]
            pages = parse_page_spec(args.pages, source["page_count"])
            extracted = extract_pages(args.pdf, pages)
            events = append_page_access_events(
                args.ledger, source_sha256=source["sha256"], pages=extracted
            )
            _print_json(
                {
                    "protocol_version": "0.1",
                    "source": source,
                    "pages": extracted,
                    "receipt_event_ids": [event["event_id"] for event in events],
                }
            )
            return 0

        if args.command == "verify":
            report = _load_json(args.report)
            events, ledger_errors = validate_ledger(args.ledger)
            result = verify_report(
                report, events, ledger_errors=ledger_errors, pdf_path=args.pdf
            )
            _print_json(result.to_dict())
            return 0 if result.publishable_at_claimed_level else 2

    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"rrc: error: {exc}", file=sys.stderr)
        return 2

    parser.error("Unknown command.")
    return 2
