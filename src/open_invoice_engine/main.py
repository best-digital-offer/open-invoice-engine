from __future__ import annotations

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import ValidationError

from . import __version__
from .config import MAX_UPLOAD_MB
from .pdf_service import PDFProcessingError, extract_pdf_text
from .schemas import InvoiceInput
from .validation import validate_invoice

app = FastAPI(
    title="Open Invoice Engine",
    description="Self-hosted PDF text extraction and deterministic invoice validation API.",
    version=__version__,
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": __version__}


@app.post("/extract")
async def extract(file: UploadFile = File(...)) -> dict:
    if file.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(status_code=415, detail="Upload a PDF file.")
    data = await file.read(MAX_UPLOAD_MB * 1024 * 1024 + 1)
    try:
        return extract_pdf_text(data)
    except PDFProcessingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        await file.close()


@app.post("/validate")
def validate(payload: dict) -> dict:
    try:
        invoice = InvoiceInput.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors(include_input=False)) from exc
    result = validate_invoice(invoice)
    return result.model_dump(mode="json")
