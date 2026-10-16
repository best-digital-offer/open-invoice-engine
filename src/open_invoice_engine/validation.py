from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from .config import VALIDATION_TOLERANCE
from .schemas import InvoiceInput, ValidationResult


def validate_invoice(invoice: InvoiceInput, tolerance: Decimal | None = None) -> ValidationResult:
    allowed = tolerance if tolerance is not None else Decimal(str(VALIDATION_TOLERANCE))
    expected = (invoice.subtotal + invoice.tax - invoice.discount).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    difference = (invoice.total - expected).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    errors: list[str] = []
    warnings: list[str] = []

    if invoice.subtotal < 0 or invoice.tax < 0 or invoice.discount < 0 or invoice.total < 0:
        warnings.append("One or more monetary values are negative; verify credit-note handling.")
    if abs(difference) > allowed:
        errors.append(
            f"Total mismatch: expected {expected} from subtotal + tax - discount, "
            f"but received {invoice.total}."
        )
    if invoice.invoice_date is None:
        warnings.append("Invoice date is missing; confirm it from the source document.")
    if invoice.supplier_name is None or not invoice.supplier_name.strip():
        warnings.append("Supplier name is missing; confirm it from the source document.")

    return ValidationResult(
        valid=not errors,
        arithmetic_expected_total=expected,
        difference=difference,
        tolerance=allowed,
        errors=errors,
        warnings=warnings,
    )
