# Open Invoice Engine

A self-hostable PDF text extraction, optional OCR, and invoice-validation API. It uses local open-source components and does not require a per-page PDF SaaS API.

> **Capacity note:** open-source software removes per-page vendor charges, not compute limits. Throughput depends on your CPU/RAM, configured page/upload limits and concurrent jobs. This is an early implementation; validate accuracy on representative invoices before production use.

## Features

- FastAPI endpoints: `/health`, `/extract`, and `/validate`
- Embedded PDF text extraction using pdfplumber and pypdf
- Optional OCR for pages without embedded text, using Tesseract + Poppler
- Per-page extraction method reporting and OCR-needed indicators
- Pydantic invoice schema validation and deterministic total arithmetic checks
- Upload-size and page-count safeguards
- Docker image and automated tests

## Quick start (Python 3.11+)

Install Python dependencies:

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -e '.[dev]'
uvicorn open_invoice_engine.main:app --reload
```

OCR requires the Tesseract binary and Poppler utilities to be installed on the host. If they are unavailable, the service still extracts embedded text and flags pages that need OCR. Docker installs these system packages for you.

Open `http://127.0.0.1:8000/docs` for interactive API documentation.

## Run with Docker

```bash
docker compose up --build
```

The API listens on port 8000. The image includes Tesseract and Poppler for local OCR.

## API examples

### Extract text from a PDF

```bash
curl -X POST http://localhost:8000/extract -F 'file=@invoice.pdf'
```

The response includes page count, text per page, extraction method, combined text, and whether any page still requires OCR. OCR is attempted only on pages where embedded text extraction returns no text.

### Validate invoice fields

```bash
curl -X POST http://localhost:8000/validate \
  -H 'Content-Type: application/json' \
  -d '{"invoice_number":"INV-100","invoice_date":"2026-10-16","currency":"USD","subtotal":100,"tax":8,"discount":0,"total":108}'
```

The validator checks the normalized fields and whether subtotal + tax - discount matches total within the configured tolerance. It cannot prove an invoice is genuine or guarantee that OCR read every field correctly. Credit notes and other negative-value documents require business-specific rules.

## Groq integration

This service does not call Groq or transmit customer files to a third party. A consuming app can send extracted text to Groq for structured field extraction when appropriate. If OCR output is empty or uncertain, keep the result flagged for review rather than inventing missing values. Keep AI keys server-side and review provider data-handling terms before sending financial documents.

## Configuration

| Variable | Default | Purpose |
|---|---:|---|
| `MAX_UPLOAD_MB` | 15 | Maximum uploaded PDF size |
| `MAX_PDF_PAGES` | 100 | Maximum PDF page count |
| `VALIDATION_TOLERANCE` | 0.02 | Allowed absolute difference in invoice totals |
| `OCR_ENABLED` | true | Enable local OCR on pages without embedded text |
| `OCR_DPI` | 200 | Rendering resolution used for OCR |

Limits are safeguards, not a capacity guarantee. Before exposing this API publicly, add authentication, authorization, rate limiting, per-user quotas, structured monitoring, and a retention/deletion policy. Do not expose an unauthenticated instance to the public internet.

## License

The repository code is MIT-licensed; see `LICENSE`. Dependencies and external system packages have their own licenses. Review them before commercial distribution.
