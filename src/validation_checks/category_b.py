import re
from src.models.validation_result import ValidationResult


GSTIN_REGEX = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")


class B1_GSTINFormat:
    check_id = "B1"
    category = "GST"
    description = "GSTIN format validation"
    complexity = "Low"

    def validate(self, ctx):
        gstin = ctx.get("seller_gstin")
        if not gstin or not GSTIN_REGEX.match(gstin):
            return ValidationResult(
                self.check_id,
                self.category,
                "FAIL",
                "Invalid GSTIN format",
                0.10
            )
        return ValidationResult(self.check_id, self.category, "PASS")


class B3_StateCodeMatch:
    check_id = "B3"
    category = "GST"
    description = "State code matches seller address"
    complexity = "Medium"

    def validate(self, ctx):
        gstin = ctx.get("seller_gstin")
        state_code = ctx.get("seller_state_code")

        if not gstin or not state_code:
            return ValidationResult(self.check_id, self.category, "REVIEW", "Missing seller state data", 0.05)

        if gstin[:2] != state_code:
            return ValidationResult(
                self.check_id,
                self.category,
                "FAIL",
                "GSTIN state code mismatch with address",
                0.15
            )
        return ValidationResult(self.check_id, self.category, "PASS")


class B8_InterIntraState:
    check_id = "B8"
    category = "GST"
    description = "Inter/Intra-state tax correctness"
    complexity = "Medium"

    def validate(self, ctx):
        seller = ctx.get("seller_state_code")
        buyer = ctx.get("buyer_state_code")
        tax_type = ctx.get("tax_type")  # IGST / CGST_SGST

        if not seller or not buyer or not tax_type:
            return ValidationResult(self.check_id, self.category, "REVIEW", "Insufficient data", 0.05)

        if seller != buyer and tax_type != "IGST":
            return ValidationResult(self.check_id, self.category, "FAIL", "Inter-state supply without IGST", 0.10)

        if seller == buyer and tax_type == "IGST":
            return ValidationResult(self.check_id, self.category, "FAIL", "Intra-state supply with IGST", 0.10)

        return ValidationResult(self.check_id, self.category, "PASS")


class B15_EInvoiceThreshold:
    check_id = "B15"
    category = "GST"
    description = "Invoice value threshold for e-invoice"
    complexity = "Medium"

    def validate(self, ctx):
        value = ctx.get("invoice_value", 0)
        if value >= 500000 and not ctx.get("irn"):
            return ValidationResult(
                self.check_id,
                self.category,
                "REVIEW",
                "Invoice value above threshold but IRN missing",
                0.10
            )
        return ValidationResult(self.check_id, self.category, "PASS")


CATEGORY_B_CHECKS = [
    B1_GSTINFormat(),
    B3_StateCodeMatch(),
    B8_InterIntraState(),
    B15_EInvoiceThreshold(),
]
