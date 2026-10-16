from decimal import Decimal

from open_invoice_engine.schemas import InvoiceInput
from open_invoice_engine.validation import validate_invoice


def test_valid_invoice_arithmetic():
    invoice = InvoiceInput(
        invoice_number=" INV-100 ",
        currency="usd",
        subtotal="100.00",
        tax="8.00",
        discount="0.00",
        total="108.00",
    )
    result = validate_invoice(invoice)
    assert invoice.invoice_number == "INV-100"
    assert invoice.currency == "USD"
    assert result.valid is True
    assert result.difference == Decimal("0.00")


def test_total_mismatch_is_reported():
    invoice = InvoiceInput(
        invoice_number="INV-101",
        subtotal="100.00",
        tax="8.00",
        discount="0.00",
        total="109.00",
    )
    result = validate_invoice(invoice)
    assert result.valid is False
    assert any("Total mismatch" in error for error in result.errors)


def test_invalid_currency_is_rejected():
    try:
        InvoiceInput(
            invoice_number="INV-102",
            currency="US dollars",
            subtotal="1",
            tax="0",
            discount="0",
            total="1",
        )
    except ValueError:
        return
    raise AssertionError("Expected invalid currency to be rejected")
