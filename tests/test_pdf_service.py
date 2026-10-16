import pytest

from open_invoice_engine.pdf_service import PDFProcessingError, extract_pdf_text


def test_rejects_non_pdf():
    with pytest.raises(PDFProcessingError, match="does not appear to be a PDF"):
        extract_pdf_text(b"not a pdf")


def test_rejects_empty_file():
    with pytest.raises(PDFProcessingError, match="empty"):
        extract_pdf_text(b"")
