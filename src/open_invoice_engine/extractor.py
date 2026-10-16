from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

import pdfplumber
from fastapi import HTTPException


@dataclass
class ExtractionResult:
    page_count: int
    pages: list[dict[str, object]]
    text: str


def extract_pdf(data: bytes, max_pages: int) -> ExtractionResult:
    """Extract embedded text from a PDF. OCR is intentionally not performed here."""
    if not data.startswith(b"%PDF-"):
        raise HTTPException(status_code=415, detail="Uploaded file is not a valid PDF")

    try:
        with pdfplumber.open(BytesIO(data)) as pdf:
            count = len(pdf.pages)
            if count == 0:
                raise HTTPException(status_code=422, detail="PDF contains no pages")
            if count > max_pages:
                raise HTTPException(
                    status_code=413,
                    detail=f"PDF has {count} pages; maximum allowed is {max_pages}",
                )
            pages = [
                {"page_number": index, "text": page.extract_text() or ""}
                for index, page in enumerate(pdf.pages, start=1)
            ]
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=422, detail="PDF could not be parsed") from exc

    return ExtractionResult(
        page_count=count,
        pages=pages,
        text="\n\n".join(str(page["text"]) for page in pages),
    )
