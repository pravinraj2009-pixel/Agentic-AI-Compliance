
from src.models.validation_result import ValidationResult

class BaseValidationCheck:
    check_id = ""
    category = ""
    description = ""
    complexity = ""

    def validate(self, ctx) -> ValidationResult:
        raise NotImplementedError
