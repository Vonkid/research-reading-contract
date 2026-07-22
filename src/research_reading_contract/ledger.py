from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


def canonical_json(value: dict[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def event_digest(event_without_digest: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(event_without_digest).encode("utf-8")).hexdigest()


def validate_ledger(path: str | Path) -> tuple[list[dict[str, Any]], list[str]]:
    ledger_path = Path(path)
    if not ledger_path.exists():
        return [], []

    valid_events: list[dict[str, Any]] = []
    errors: list[str] = []
    expected_previous: str | None = None

    with ledger_path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            if not raw_line.strip():
                continue
            try:
                event = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                errors.append(f"Ledger line {line_number} is invalid JSON: {exc.msg}.")
                break

            supplied_digest = event.get("event_sha256")
            unsigned_event = {key: value for key, value in event.items() if key != "event_sha256"}
            computed_digest = event_digest(unsigned_event)
            if supplied_digest != computed_digest:
                errors.append(f"Ledger line {line_number} has an invalid event digest.")
                break
            if event.get("previous_event_sha256") != expected_previous:
                errors.append(f"Ledger line {line_number} breaks the receipt chain.")
                break
            if event.get("event_type") != "page_access":
                errors.append(f"Ledger line {line_number} has an unsupported event type.")
                break
            if not isinstance(event.get("source_sha256"), str) or not re.fullmatch(
                r"[0-9a-f]{64}", event["source_sha256"]
            ):
                errors.append(f"Ledger line {line_number} has an invalid source digest.")
                break
            if not isinstance(event.get("page_text_sha256"), str) or not re.fullmatch(
                r"[0-9a-f]{64}", event["page_text_sha256"]
            ):
                errors.append(f"Ledger line {line_number} has an invalid page-text digest.")
                break
            if (
                not isinstance(event.get("page_number"), int)
                or isinstance(event.get("page_number"), bool)
                or event["page_number"] < 1
            ):
                errors.append(f"Ledger line {line_number} has an invalid page number.")
                break
            if (
                not isinstance(event.get("extracted_chars"), int)
                or isinstance(event.get("extracted_chars"), bool)
                or event["extracted_chars"] < 0
            ):
                errors.append(f"Ledger line {line_number} has an invalid extracted character count.")
                break

            valid_events.append(event)
            expected_previous = supplied_digest

    return valid_events, errors


def build_page_access_event(
    *,
    source_sha256: str,
    page_number: int,
    page_text_sha256: str,
    extracted_chars: int,
    previous_event_sha256: str | None,
    timestamp: str | None = None,
    event_id: str | None = None,
) -> dict[str, Any]:
    unsigned_event: dict[str, Any] = {
        "protocol_version": "0.1",
        "event_type": "page_access",
        "event_id": event_id or str(uuid.uuid4()),
        "timestamp": timestamp
        or datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "source_sha256": source_sha256,
        "page_number": page_number,
        "page_text_sha256": page_text_sha256,
        "extracted_chars": extracted_chars,
        "previous_event_sha256": previous_event_sha256,
    }
    return {**unsigned_event, "event_sha256": event_digest(unsigned_event)}


def append_page_access_events(
    path: str | Path,
    *,
    source_sha256: str,
    pages: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    ledger_path = Path(path)
    existing, errors = validate_ledger(ledger_path)
    if errors:
        raise ValueError("Refusing to append to an invalid ledger: " + " ".join(errors))

    previous = existing[-1]["event_sha256"] if existing else None
    new_events: list[dict[str, Any]] = []
    for page in pages:
        event = build_page_access_event(
            source_sha256=source_sha256,
            page_number=int(page["page_number"]),
            page_text_sha256=str(page["text_sha256"]),
            extracted_chars=int(page["extracted_chars"]),
            previous_event_sha256=previous,
        )
        new_events.append(event)
        previous = event["event_sha256"]

    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open("a", encoding="utf-8") as handle:
        for event in new_events:
            handle.write(canonical_json(event) + "\n")
    return new_events
