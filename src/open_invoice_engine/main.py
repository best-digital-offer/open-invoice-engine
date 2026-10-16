from __future__ import annotations

import hmac
import os

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from . import __version__
from .config import MAX_UPLOAD_MB
from .groq_extraction import (
    GroqConfigurationError,
    GroqExtractionError,
    extract_invoice_fields_with_groq,
)
from .pdf_service import PDFProcessingError, extract_pdf_text
from .schemas import InvoiceInput
from .validation import validate_invoice

app = FastAPI(
    title="Open Invoice Engine",
    description="Self-hosted PDF text extraction and deterministic invoice validation API.",
    version=__version__,
)

# Browser clients need CORS when the frontend and API are deployed on different origins.
# Set CORS_ALLOWED_ORIGINS to a comma-separated list of production frontend origins.
_cors_origins = [origin.strip() for origin in os.getenv("CORS_ALLOWED_ORIGINS", "*").split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)

@app.middleware("http")
async def optional_api_key_auth(request: Request, call_next):
    """Protect API routes when API_KEY is configured; keep health checks public."""
    expected_key = os.getenv("API_KEY", "").strip()
    if expected_key and request.url.path not in {"/health", "/docs", "/openapi.json", "/redoc"} and request.method != "OPTIONS":
        supplied_key = request.headers.get("X-API-Key", "")
        authorization = request.headers.get("Authorization", "")
        if not supplied_key and authorization.lower().startswith("bearer "):
            supplied_key = authorization[7:].strip()
        if not supplied_key or not hmac.compare_digest(supplied_key, expected_key):
            return JSONResponse(status_code=401, content={"detail": "Missing or invalid API key"})
    return await call_next(request)


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


@app.post("/extract-invoice")
async def extract_invoice(file: UploadFile = File(...)) -> dict:
    """Extract PDF text locally, then send that text to Groq for structured extraction."""
    if file.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(status_code=415, detail="Upload a PDF file.")
    data = await file.read(MAX_UPLOAD_MB * 1024 * 1024 + 1)
    try:
        extracted = extract_pdf_text(data)
    except PDFProcessingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        await file.close()
    if not extracted["combined_text"].strip():
        raise HTTPException(
            status_code=422,
            detail="No readable text was extracted. Ensure local OCR is installed and enabled.",
        )
    try:
        ai_result = extract_invoice_fields_with_groq(extracted["combined_text"])
    except GroqConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except GroqExtractionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {
        "page_count": extracted["page_count"],
        "ocr_used": extracted["ocr_used"],
        "fields": ai_result["fields"],
        "model": ai_result["model"],
        "review_required": True,
        "notice": "AI-extracted values may be incorrect. Review before using for accounting.",
    }
