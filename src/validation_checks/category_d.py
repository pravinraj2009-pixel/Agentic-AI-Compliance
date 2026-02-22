from src.models.validation_result import ValidationResult


class D1_TDSApplicability:
    check_id = "D1"
    category = "TDS"
    description = "TDS applicability based on vendor type"
    complexity = "Medium"

    def validate(self, ctx):
        vendor_type = ctx.get("vendor_type")
        if vendor_type in ["Individual", "Proprietor"]:
            return ValidationResult(self.check_id, self.category, "PASS")
        return ValidationResult(self.check_id, self.category, "REVIEW", "TDS applicability needs confirmation", 0.05)


class D3_PANAvailability:
    check_id = "D3"
    category = "TDS"
    description = "Higher TDS if PAN not available"
    complexity = "Medium"

    def validate(self, ctx):
        pan = ctx.get("vendor_pan")
        
        # Also check nested fields if available
        if not pan:
            fields = ctx.get("fields", {})
            if isinstance(fields, dict):
                pan = fields.get("vendor_pan")
        
        if not pan:
            return ValidationResult(
                self.check_id,
                self.category,
                "FAIL",
                "PAN not available – higher TDS applicable",
                0.15
            )
        return ValidationResult(self.check_id, self.category, "PASS")


class D5_TDSThreshold:
    check_id = "D5"
    category = "TDS"
    description = "TDS threshold applicability"
    complexity = "Medium"

    def validate(self, ctx):
        amount = ctx.get("invoice_value", 0)
        threshold = ctx.get("tds_threshold", 30000)

        if amount > threshold:
            return ValidationResult(self.check_id, self.category, "PASS")
        return ValidationResult(self.check_id, self.category, "SKIP")


class D7_TDSOnGST:
    check_id = "D7"
    category = "TDS"
    description = "TDS on GST component"
    complexity = "High"

    def validate(self, ctx):
        if ctx.get("tds_on_gst_component", False):
            return ValidationResult(
                self.check_id,
                self.category,
                "FAIL",
                "TDS deducted on GST component",
                0.10
            )
        return ValidationResult(self.check_id, self.category, "PASS")


class D9_TANFormat:
    check_id = "D9"
    category = "TDS"
    description = "TAN availability"
    complexity = "Low"

    def validate(self, ctx):
        if not ctx.get("company_tan"):
            return ValidationResult(self.check_id, self.category, "REVIEW", "TAN not configured", 0.05)
        return ValidationResult(self.check_id, self.category, "PASS")


CATEGORY_D_CHECKS = [
    D1_TDSApplicability(),
    D3_PANAvailability(),
    D5_TDSThreshold(),
    D7_TDSOnGST(),
    D9_TANFormat(),
]
