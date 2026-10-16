from unittest.mock import patch

import pytest

from open_invoice_engine.groq_extraction import (
    GroqConfigurationError,
    extract_invoice_fields_with_groq,
)


def test_groq_requires_api_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(GroqConfigurationError):
        extract_invoice_fields_with_groq("Invoice #100 Total $10")
