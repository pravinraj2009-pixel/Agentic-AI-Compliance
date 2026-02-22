class ValidationResult:
    def __init__(
        self,
        check_id: str,
        category: str,
        status: str,
        reason: str = None,
        confidence_impact: float = 0.0,
        evidence=None,
    ):
        self.check_id = check_id
        self.category = category
        self.status = status
        self.reason = reason
        self.confidence_impact = confidence_impact
        self.evidence = evidence
        self.metadata = {}
