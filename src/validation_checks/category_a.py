
import re
from src.models.validation_result import ValidationResult
from src.models.base_validation import BaseValidationCheck

class A1_InvoiceNumberFormat(BaseValidationCheck):
    check_id="A1"; category="Document"
    def validate(self, ctx):
        inv = ctx["fields"].get("invoice_number","")
        if re.match(r"^[A-Z0-9\-/]+$", inv):
            return ValidationResult(self.check_id,self.category,"PASS")
        return ValidationResult(self.check_id,self.category,"FAIL","Invalid invoice number format",0.1)

class A2_DuplicateInvoice(BaseValidationCheck):
    check_id="A2"; category="Document"
    def __init__(self):
        self.seen = set()
    
    def validate(self, ctx):
        key=(ctx["fields"].get("vendor_gstin"),ctx["fields"].get("invoice_number"))
        if key in self.seen:
            return ValidationResult(self.check_id,self.category,"FAIL","Duplicate invoice detected",0.3)
        self.seen.add(key)
        return ValidationResult(self.check_id,self.category,"PASS")

class A3_SequentialInvoice(BaseValidationCheck):
    check_id="A3"; category="Document"
    def __init__(self):
        self.last = None
    
    def validate(self, ctx):
        inv=ctx["fields"].get("invoice_number")
        if self.last and inv < self.last:
            return ValidationResult(self.check_id,self.category,"FAIL","Invoice sequence anomaly",0.2)
        self.last=inv
        return ValidationResult(self.check_id,self.category,"PASS")

class A5_DateVsMetadata(BaseValidationCheck):
    check_id="A5"; category="Document"
    def validate(self, ctx):
        inv_date=ctx["fields"].get("invoice_date")
        meta_date=ctx["metadata"].get("file_created_date")
        if meta_date and inv_date and inv_date>meta_date:
            return ValidationResult(self.check_id,self.category,"FAIL","Invoice date later than file creation",0.1)
        return ValidationResult(self.check_id,self.category,"PASS")

CATEGORY_A_CHECKS=[A1_InvoiceNumberFormat(),A2_DuplicateInvoice(),A3_SequentialInvoice(),A5_DateVsMetadata()]
