from __future__ import annotations

import shutil
from io import BytesIO

import pdfplumber
from pypdf import PdfReader

from .config import MAX_PDF_PAGES, MAX_UPLOAD_MB, OCR_DPI, OCR_ENABLED


class PDFProcessingError(ValueError):
    """Raised when an uploaded file is not a supported/acceptable PDF."""


def _ocr_page(data: bytes, page_number: int) -> str:
    """OCR one page. Requires Tesseract and Poppler installed on the host."""
    if not shutil.which("tesseract"):
        return ""
    try:
        from pdf2image import convert_from_bytes
        import pytesseract

        images = convert_from_bytes(
            data,
            dpi=OCR_DPI,
            first_page=page_number,
            last_page=page_number,
            fmt="png",
            thread_count=1,
        )
        if not images:
            return ""
        try:
            return (pytesseract.image_to_string(images[0]) or "").strip()
        finally:
            for image in images:
                image.close()
    except Exception:
        # Preserve the extraction result and mark OCR as still required if it failed.
        return ""


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

        with pdfplumber.open(BytesIO(data)) as pdf:
            pages = []
            for index, page in enumerate(pdf.pages, start=1):
                text = (page.extract_text(layout=False) or "").strip()
                source = "embedded_text" if text else "none"
                if not text and OCR_ENABLED:
                    text = _ocr_page(data, index)
                    if text:
                        source = "tesseract_ocr"
                pages.append(
                    {"page_number": index, "text": text, "extraction_method": source}
                )
    except PDFProcessingError:
        raise
    except Exception as exc:
        raise PDFProcessingError(
            "Could not read this PDF. It may be malformed or unsupported."
        ) from exc

    combined = "\n\n".join(page["text"] for page in pages if page["text"])
    missing_pages = [page["page_number"] for page in pages if not page["text"]]
    has_text = any(page["text"] for page in pages)
    return {
        "page_count": page_count,
        "has_embedded_text": any(p["extraction_method"] == "embedded_text" for p in pages),
        "ocr_used": any(p["extraction_method"] == "tesseract_ocr" for p in pages),
        "ocr_required": bool(missing_pages),
        "pages_requiring_ocr": missing_pages,
        "pages": pages,
        "combined_text": combined,
    }
