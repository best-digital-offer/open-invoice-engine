from __future__ import annotations

import os


def positive_int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer") from exc
    if value <= 0:
        raise RuntimeError(f"{name} must be greater than zero")
    return value


MAX_UPLOAD_MB = positive_int_env("MAX_UPLOAD_MB", 15)
MAX_PDF_PAGES = positive_int_env("MAX_PDF_PAGES", 100)
VALIDATION_TOLERANCE = float(os.getenv("VALIDATION_TOLERANCE", "0.02"))
if VALIDATION_TOLERANCE < 0:
    raise RuntimeError("VALIDATION_TOLERANCE cannot be negative")
