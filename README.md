# Open Invoice Engine

A self-hostable PDF text extraction and invoice-validation API. It is designed to avoid per-page PDF SaaS fees by using local open-source libraries.

> **Important:** This is a starter implementation, not a production-certified invoice OCR system. It extracts embedded PDF text; scanned/image-only PDFs require an OCR engine, which is not enabled in this first version. No tool can provide unlimited compute for free: throughput depends on your own hosting resources.

## Features

- FastAPI HTTP service with `/health`, `/extract`, and `/validate` endpoints
- PDF page and upload-size limits
- Embedded text extraction using `pdfplumber`
- Invoice-field schema validation using Pydantic
- Arithmetic checks for subtotal, tax, discount, and total
- No external AI API required for PDF text extraction or deterministic validation
- Docker image and basic tests

## Quick start (Python 3.11+)

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -e '.[dev]'
uvicorn open_invoice_engine.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for interactive API documentation.

## Run with Docker

```bash
docker compose up --build
```

The API listens on port 8000.

## API examples

### Extract text from a PDF

```bash
curl -X POST http://localhost:8000/extract \\
  -F 'file=@invoice.pdf'
```

Returns page count, per-page text, and combined text. This endpoint does not use Groq and does not perform OCR.

### Validate extracted invoice fields

```bash
curl -X POST http://localhost:8000/validate \\
  -H 'Content-Type: application/json' \\
  -d '{"invoice_number":"INV-100","invoice_date":"2026-10-16","currency":"USD","subtotal":100,"tax":8,"discount":0,"total":108}'
```

Validation is deterministic. It checks required fields, numeric values, and whether `subtotal + tax - discount` agrees with `total` within a configurable tolerance. It cannot prove the source invoice itself is genuine or that OCR read every field correctly.

## Groq integration

This service deliberately does not call Groq. A consuming application can send extracted text to Groq when text extraction is sufficient. For image-only/scanned invoices, add a separate PDF-to-image + OCR/vision step and validate its output before saving it. Keep API keys server-side and never send customer documents without reviewing the AI provider's data-handling terms.

## Limits and production notes

Configure `MAX_UPLOAD_MB`, `MAX_PDF_PAGES`, and `VALIDATION_TOLERANCE` in the environment. Defaults are conservative safeguards, not guarantees of capacity. Before exposing this service publicly, add authentication, per-user quotas, request throttling, structured logs, malware scanning where appropriate, private storage/retention rules, and deployment-specific resource limits. Do not expose an unauthenticated instance to the public internet.

## License

The code in this repository is licensed under MIT; see `LICENSE`. Dependencies retain their own licenses. Check dependency licenses and notices before distributing a combined product.
