from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

Money = Annotated[Decimal, Field(max_digits=16, decimal_places=4)]


class InvoiceInput(BaseModel):
    """Normalized invoice values to validate after extraction or user review."""

    model_config = ConfigDict(extra="forbid")

    invoice_number: str = Field(min_length=1, max_length=200)
    invoice_date: date | None = None
    supplier_name: str | None = Field(default=None, max_length=300)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    subtotal: Money
    tax: Money = Decimal("0")
    discount: Money = Decimal("0")
    total: Money

    @field_validator("invoice_number")
    @classmethod
    def trim_invoice_number(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("invoice_number cannot be blank")
        return value

    @field_validator("currency")
    @classmethod
    def uppercase_currency(cls, value: str) -> str:
        value = value.strip().upper()
        if len(value) != 3 or not value.isalpha():
            raise ValueError("currency must be a 3-letter currency code")
        return value


class ValidationResult(BaseModel):
    valid: bool
    arithmetic_expected_total: Decimal
    difference: Decimal
    tolerance: Decimal
    errors: list[str]
    warnings: list[str]
