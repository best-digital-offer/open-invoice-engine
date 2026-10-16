from __future__ import annotations

import os
from decimal import Decimal

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from open_invoice_engine.extractor import extract_pdf
from open_invoice_engine.validation import validate_invoice

MAX_UPLOAD_MB = max(1, int(os.getenv("MAX_UPLOAD_MB", "15")))
MAX_PDF_PAGES = max(1, int(os.getenv("MAX_PDF_PAGES", "100")))
VALIDATION_TOLERANCE = Decimal(os.getenv("VALIDATION_TOLERANCE", "0.02"))
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024

app = FastAPI(
    title="Open Invoice Engine",
    version="0.1.0",
    description="Self-hostable PDF text extraction and deterministic invoice validation.",
)


class ValidateRequest(BaseModel):
    invoice_number: str = Field(min_length=1, max_length=128)
    invoice_date: str = Field(min_length=1, max_length=32)
    currency: str = Field(min_length=3, max_length=3)
    subtotal: Decimal = Field(ge=0)
    tax: Decimal = Field(ge=0)
    discount: Decimal = Field(default=Decimal("0"), ge=0)
    total: Decimal = Field(ge=0)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "open-invoice-engine"}


@app.post("/extract")
async def extract(file: UploadFile = File(...)) -> dict[str, object]:
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=415, detail="Upload a PDF file")
    data = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"Upload exceeds {MAX_UPLOAD_MB} MB limit")
    result = extract_pdf(data, MAX_PDF_PAGES)
    return {"page_count": result.page_count, "pages": result.pages, "text": result.text}


@app.post("/validate")
def validate(request: ValidateRequest) -> dict[str, object]:
    return validate_invoice(request.model_dump(), VALIDATION_TOLERANCE)
