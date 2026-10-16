from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

import pdfplumber
from pypdf import PdfReader

from .config import MAX_PDF_PAGES, MAX_UPLOAD_MB


class PDFProcessingError(ValueError):
    """Raised when an uploaded file is not a supported/acceptable PDF."""


@dataclass
class ExtractedPage:
    page_number: int
    text: str


def extract_pdf_text(data: bytes) -> dict:
    if not data:
        raise PDFProcessingError("The uploaded file is empty.")
    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        raise PDFProcessingError(f"File exceeds the {MAX_UPLOAD_MB} MB upload limit.")
    if not data.startswith(b"%PDF-"):
        raise PDFProcessingError("The uploaded file does not appear to be a PDF.")

    try:
        reader = PdfReader(BytesIO(data), strict=True)
        if reader.is_encrypted:
            raise PDFProcessingError("Password-protected PDFs are not supported yet.")
        page_count = len(reader.pages)
        if page_count == 0:
            raise PDFProcessingError("The PDF contains no pages.")
        if page_count > MAX_PDF_PAGES:
            raise PDFProcessingError(f"PDF exceeds the {MAX_PDF_PAGES}-page limit.")

        pages: list[dict] = []
        with pdfplumber.open(BytesIO(data)) as pdf:
            for index, page in enumerate(pdf.pages, start=1):
                text = (page.extract_text(layout=False) or "").strip()
                pages.append({"page_number": index, "text": text})
    except PDFProcessingError:
        raise
    except Exception as exc:
        raise PDFProcessingError(
            "Could not read this PDF. It may be malformed or unsupported."
        ) from exc

    combined = "\n\n".join(page["text"] for page in pages if page["text"])
    has_text = any(page["text"] for page in pages)
    return {
        "page_count": page_count,
        "has_embedded_text": has_text,
        "ocr_required": not has_text,
        "pages": pages,
        "combined_text": combined,
    }
