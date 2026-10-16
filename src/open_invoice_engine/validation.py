from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class InvoiceInput(BaseModel):
    """Normalized invoice fields to validate; amounts use decimal arithmetic."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    invoice_number: str = Field(min_length=1, max_length=128)
    invoice_date: str = Field(min_length=1, max_length=32)
    currency: str = Field(min_length=3, max_length=3)
    subtotal: Decimal = Field(ge=0)
    tax: Decimal = Field(ge=0)
    discount: Decimal = Field(default=Decimal("0"), ge=0)
    total: Decimal = Field(ge=0)

    @field_validator("currency")
    @classmethod
    def currency_is_uppercase(cls, value: str) -> str:
        value = value.upper()
        if not value.isalpha():
            raise ValueError("currency must be a three-letter code")
        return value

    @field_validator("invoice_date")
    @classmethod
    def date_is_iso_format(cls, value: str) -> str:
        from datetime import date
        try:
            date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError("invoice_date must use YYYY-MM-DD format") from exc
        return value


def validate_invoice(payload: dict[str, Any], tolerance: Decimal) -> dict[str, Any]:
    """Validate fields and arithmetic without guessing or modifying invoice data."""
    try:
        invoice = InvoiceInput.model_validate(payload)
    except Exception as exc:
        return {"valid": False, "field_errors": str(exc), "checks": []}

    expected = invoice.subtotal + invoice.tax - invoice.discount
    difference = abs(expected - invoice.total)
    arithmetic_ok = difference <= tolerance
    return {
        "valid": arithmetic_ok,
        "field_errors": None,
        "checks": [
            {
                "name": "subtotal_plus_tax_minus_discount_equals_total",
                "passed": arithmetic_ok,
                "expected_total": str(expected),
                "actual_total": str(invoice.total),
                "absolute_difference": str(difference),
                "tolerance": str(tolerance),
            }
        ],
        "invoice": invoice.model_dump(mode="json"),
    }
