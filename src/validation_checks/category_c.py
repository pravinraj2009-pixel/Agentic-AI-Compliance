
from decimal import Decimal
from src.models.validation_result import ValidationResult
from src.models.base_validation import BaseValidationCheck

class C1_LineItemMath(BaseValidationCheck):
    check_id="C1"; category="Arithmetic"
    def validate(self, ctx):
        for item in ctx["fields"].get("line_items",[]):
            if Decimal(item["qty"])*Decimal(item["rate"])!=Decimal(item["amount"]):
                return ValidationResult(self.check_id,self.category,"FAIL","Line item math mismatch",0.1)
        return ValidationResult(self.check_id,self.category,"PASS")

class C2_Subtotal(BaseValidationCheck):
    check_id="C2"; category="Arithmetic"
    def validate(self, ctx):
        items=ctx["fields"].get("line_items",[])
        subtotal=sum(Decimal(i["amount"]) for i in items)
        if subtotal!=Decimal(ctx["fields"].get("subtotal",subtotal)):
            return ValidationResult(self.check_id,self.category,"FAIL","Subtotal mismatch",0.1)
        return ValidationResult(self.check_id,self.category,"PASS")

class C3_TaxAccuracy(BaseValidationCheck):
    check_id="C3"; category="Arithmetic"
    def validate(self, ctx):
        expected=Decimal(ctx["fields"].get("taxable_amount","0"))*Decimal("0.18")
        actual=Decimal(ctx["fields"].get("tax_amount","0"))
        if abs(expected-actual)>1:
            return ValidationResult(self.check_id,self.category,"FAIL","Tax calculation error",0.15)
        return ValidationResult(self.check_id,self.category,"PASS")

CATEGORY_C_CHECKS=[C1_LineItemMath(),C2_Subtotal(),C3_TaxAccuracy()]
