from decimal import Decimal

from open_invoice_engine.validation import validate_invoice


def base_invoice():
    return {
        "invoice_number": "INV-100",
        "invoice_date": "2026-10-16",
        "currency": "USD",
        "subtotal": "100.00",
        "tax": "8.00",
        "discount": "0.00",
        "total": "108.00",
    }


def test_valid_invoice_passes():
    result = validate_invoice(base_invoice(), Decimal("0.02"))
    assert result["valid"] is True
    assert result["checks"][0]["passed"] is True


def test_mismatched_total_fails():
    payload = base_invoice()
    payload["total"] = "109.00"
    result = validate_invoice(payload, Decimal("0.02"))
    assert result["valid"] is False
    assert result["checks"][0]["passed"] is False


def test_bad_date_fails():
    payload = base_invoice()
    payload["invoice_date"] = "not-a-date"
    result = validate_invoice(payload, Decimal("0.02"))
    assert result["valid"] is False
    assert result["field_errors"]


def test_negative_amount_fails():
    payload = base_invoice()
    payload["subtotal"] = "-1"
    result = validate_invoice(payload, Decimal("0.02"))
    assert result["valid"] is False
