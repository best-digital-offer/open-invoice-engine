# Security notes

- Do not expose the API publicly without authentication, authorization, throttling and monitoring.
- Keep customer PDFs in memory where possible; do not log document contents or extracted personal/financial data.
- Enforce request, page-count, execution-time and memory limits at both application and infrastructure layers.
- Add a retention/deletion policy before saving uploaded files or extracted text.
- Keep secrets in server-side environment variables; never commit credentials.
- Treat extraction output as untrusted input. Validate all fields and require user review for uncertain values.
- Review dependencies and their licenses before commercial distribution.
