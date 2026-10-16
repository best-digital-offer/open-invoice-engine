# Open Invoice Engine

A self-hostable PDF text extraction, optional OCR, and invoice-validation API. It uses local open-source components and does not require a per-page PDF SaaS API.

> **Capacity note:** open-source software removes per-page vendor charges, not compute limits. Throughput depends on your CPU/RAM, configured page/upload limits and concurrent jobs. This is an early implementation; validate accuracy on representative invoices before production use.

## Features

- FastAPI endpoints: `/health`, `/extract`, and `/validate`
- Embedded PDF text extraction using pdfplumber and pypdf
- Optional OCR for pages without embedded text, using Tesseract + Poppler
- Optional Groq-powered structured invoice-field and line-item extraction from extracted text
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

The optional `/extract-invoice` endpoint sends extracted invoice text to Groq for structured fields and line items. It is disabled until `GROQ_API_KEY` is configured. This sends customer financial text to a third-party AI provider: disclose this clearly, obtain the appropriate customer consent, and review the provider's data-handling terms before enabling it. API keys stay server-side. The model is instructed not to guess and returns uncertain fields for human review. OCR remains local.

## API authentication and CORS

Set `API_KEY` on the backend to require `X-API-Key` or `Authorization: Bearer <key>` on API routes. `/health` remains public for connection checks. If `API_KEY` is empty, API routes are unauthenticated; do not expose that configuration publicly. Set `CORS_ALLOWED_ORIGINS` to your InvoiceFlow frontend origin(s), comma-separated. The API key entered in the browser connector is visible to that browser, so for a public multi-user SaaS, put the API behind a server-side proxy rather than sharing one secret in client code.

## Configuration

| Variable | Default | Purpose |
|---|---:|---|
| `MAX_UPLOAD_MB` | 15 | Maximum uploaded PDF size |
| `MAX_PDF_PAGES` | 100 | Maximum PDF page count |
| `VALIDATION_TOLERANCE` | 0.02 | Allowed absolute difference in invoice totals |
| `OCR_ENABLED` | true | Enable local OCR on pages without embedded text |
| `OCR_DPI` | 200 | Rendering resolution used for OCR |
| `GROQ_API_KEY` | unset | Optional server-side key; enables `/extract-invoice` |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Groq model for structured extraction |

Limits are safeguards, not a capacity guarantee. Before exposing this API publicly, add authentication, authorization, rate limiting, per-user quotas, structured monitoring, and a retention/deletion policy. Do not expose an unauthenticated instance to the public internet.

## License

The repository code is MIT-licensed; see `LICENSE`. Dependencies and external system packages have their own licenses. Review them before commercial distribution.
