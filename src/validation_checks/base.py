
from dataclasses import dataclass
from typing import Dict, Any, List

@dataclass
class ValidationResult:
    check_id: str
    category: str
    status: str
    confidence_impact: float
    explanation: str
    evidence: Dict[str, Any]
    requires_review: bool


class BaseValidationCheck:
    check_id: str
    category: str
    description: str
    complexity: str
    required_inputs: List[str]

    def validate(self, ctx: Dict[str, Any]) -> ValidationResult:
        raise NotImplementedError
