
from datetime import datetime
from src.models.base_validation import BaseValidationCheck
from src.models.validation_result import ValidationResult

class E1_POAmountTolerance(BaseValidationCheck):
    check_id="E1"; category="Policy"
    description="Invoice within PO tolerance ±5%"; complexity="Medium"
    def validate(self, ctx):
        po = ctx.get("po_amount")
        inv = ctx.get("total_amount")
        if po is None: return ValidationResult(self.check_id,self.category,"SKIP","No PO linked")
        if abs(inv-po)/po <= 0.05:
            return ValidationResult(self.check_id,self.category,"PASS")
        return ValidationResult(self.check_id,self.category,"FAIL","PO tolerance exceeded",0.2)

class E2_ContractPeriod(BaseValidationCheck):
    check_id="E2"; category="Policy"
    description="Invoice date within contract period"; complexity="Low"
    def validate(self, ctx):
        start,end = ctx.get("contract_start"), ctx.get("contract_end")
        if not start or not end: return ValidationResult(self.check_id,self.category,"SKIP")
        d = datetime.fromisoformat(ctx["invoice_date"]).date()
        if start <= d <= end:
            return ValidationResult(self.check_id,self.category,"PASS")
        return ValidationResult(self.check_id,self.category,"FAIL","Outside contract period",0.1)

class E3_ApprovedVendor(BaseValidationCheck):
    check_id="E3"; category="Policy"; complexity="Low"
    def validate(self, ctx):
        return ValidationResult(self.check_id,self.category,"PASS") if ctx.get("vendor_approved") else ValidationResult(self.check_id,self.category,"FAIL","Vendor not approved",0.3)

class E6_ApprovalHierarchy(BaseValidationCheck):
    check_id="E6"; category="Policy"; complexity="Medium"
    def validate(self, ctx):
        limit = ctx.get("approver_limit",0)
        if ctx.get("total_amount",0) <= limit:
            return ValidationResult(self.check_id,self.category,"PASS")
        return ValidationResult(self.check_id,self.category,"FAIL","Approval escalation required",0.2)

CATEGORY_E_CHECKS=[
    E1_POAmountTolerance(),
    E2_ContractPeriod(),
    E3_ApprovedVendor(),
    E6_ApprovalHierarchy()
]
