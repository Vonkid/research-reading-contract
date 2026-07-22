from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from pypdf import PdfReader


def file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pdf_manifest(path: str | Path) -> dict[str, Any]:
    pdf_path = Path(path)
    reader = PdfReader(str(pdf_path))
    if reader.is_encrypted:
        raise ValueError("Encrypted PDFs are not supported without prior decryption.")
    return {
        "protocol_version": "0.1",
        "source": {
            "file_name": pdf_path.name,
            "sha256": file_sha256(pdf_path),
            "page_count": len(reader.pages),
        },
    }


def parse_page_spec(spec: str, page_count: int) -> list[int]:
    pages: set[int] = set()
    if not spec.strip():
        raise ValueError("Page specification is empty.")

    for token in spec.split(","):
        token = token.strip()
        if not token:
            continue
        if "-" in token:
            start_text, end_text = token.split("-", 1)
            start, end = int(start_text), int(end_text)
            if start > end:
                raise ValueError(f"Invalid descending page range: {token}")
            pages.update(range(start, end + 1))
        else:
            pages.add(int(token))

    invalid = sorted(page for page in pages if page < 1 or page > page_count)
    if invalid:
        raise ValueError(
            f"Pages outside document range 1-{page_count}: "
            + ", ".join(str(page) for page in invalid)
        )
    if not pages:
        raise ValueError("Page specification selected no pages.")
    return sorted(pages)


def extract_pages(path: str | Path, pages: list[int]) -> list[dict[str, Any]]:
    reader = PdfReader(str(path))
    if reader.is_encrypted:
        raise ValueError("Encrypted PDFs are not supported without prior decryption.")

    extracted: list[dict[str, Any]] = []
    for page_number in pages:
        text = reader.pages[page_number - 1].extract_text() or ""
        extracted.append(
            {
                "page_number": page_number,
                "text": text,
                "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "extracted_chars": len(text),
            }
        )
    return extracted


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()
