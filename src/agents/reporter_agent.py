from typing import List
from src.models.validation_result import ValidationResult


# =====================================================
# User-facing decision labels (presentation only)
# =====================================================
DECISION_LABELS = {
    "APPROVE": "PASS",
    "APPROVE_WITH_REVIEW": "REVIEW",
    "ESCALATE": "REJECTED",
}

# =====================================================
# Flag Display Mapping (Evaluation Alignment)
# =====================================================
FLAG_DISPLAY_MAP = {
    "COMP_SCHEME": "Comp Scheme",
    "IGST_CHECK": "IGST Check",
    "B2": "GSTIN Suspended",
    "B6": "Rate Mismatch",
    "194Q": "194Q Threshold",
    "MIXED_RATES": "Mixed Rates",
    "FY_CHECK": "FY Check",
    "HIGH_VALUE": ">5M Approval",
    "DATA_QUALITY": "Data Quality",
    "RCM": "RCM",
    "GTA_RCM": "GTA RCM",
    "194C": "194C",
    "194I": "194I",
    "194J": "194J",
    "GST_COMPONENT": "GST Component",
    "RELATED_PARTY": "Related Party",
    "DUPLICATE": "Duplicate",
    "206AB": "206AB",
    "CREDIT_NOTE": "Credit Note",
    "EXPORT": "Export",
    "ZERO_RATED": "Zero-rated",
}


class ReporterAgent:
    """
    ReporterAgent
    --------------
    ROLE:
    Transforms final resolution output into human-readable compliance reports.

    ONLY handles:
    - Mapping internal decisions to user-facing labels (PASS / REVIEW / REJECTED)
    - Deriving primary reason for UI display
    - Formatting failed and review flags for display
    - Structuring audit-ready report rows
    - Ensuring deterministic output per invoice
    - Providing system-level error reporting

    DOES NOT:
    - Execute validation logic
    - Compute confidence scores
    - Detect conflicts
    - Invoke LLM tools
    - Persist decision history
    - Perform invoice extraction

    OUTPUT CONTRACT:
    Returns a structured report dictionary per invoice
    ready for UI rendering or export.
    """


    def __init__(self, config=None):
        """
        Config is accepted for pipeline consistency and future extensibility.
        Currently not required by ReporterAgent logic.
        """
        self.config = config

    def generate(
        self,
        invoice_ctx: dict,
        validation_results: List[ValidationResult],
        resolution: dict,
    ) -> dict:
        invoice_id = invoice_ctx.get("invoice_id", "UNKNOWN")

        # -------------------------------
        # Failed & Review checks
        # -------------------------------
        failed = [r for r in validation_results if r.status == "FAIL"]
        review = [r for r in validation_results if r.status == "REVIEW"]

        # -------------------------------
        # Primary reason derivation
        # -------------------------------
        if failed:
            primary_reason = failed[0].reason or failed[0].check_id
        elif review:
            primary_reason = review[0].reason or review[0].check_id
        else:
            primary_reason = "All compliance checks passed"

        # -------------------------------
        # Confidence handling
        # -------------------------------
        confidence = resolution.get("final_confidence")
        if confidence is None:
            confidence = resolution.get("confidence", 0.0)

        # -------------------------------
        # Decision & escalation semantics
        # -------------------------------
        raw_decision = resolution.get("decision", "ESCALATE")
        decision = DECISION_LABELS.get(raw_decision, raw_decision)
        # Escalation ONLY for hard failures
        escalation_required = raw_decision == "ESCALATE"

        # -------------------------------
        # Final report row
        # -------------------------------
        return {
            "invoice_id": invoice_id,
            "decision": decision,
            "final_confidence": round(float(confidence), 3),
            "primary_reason": primary_reason,
            "failed_checks": [
                FLAG_DISPLAY_MAP.get(r.check_id, r.check_id)
                for r in failed
            ],
            "review_flags": [
                FLAG_DISPLAY_MAP.get(r.check_id, r.check_id)
                for r in review
            ],

            "conflicts": resolution.get("conflicts", []),
            "escalation_required": escalation_required,
            "llm_reasoning": resolution.get("llm_resolver")
            or resolution.get("llm_reasoning"),
        }

    # ----------------------------------------------------
    # SYSTEM-LEVEL FAILURE (never break pipeline)
    # ----------------------------------------------------
    def system_error(self, invoice_id: str, error_message: str) -> dict:
        return {
            "invoice_id": invoice_id,
            "decision": DECISION_LABELS["ESCALATE"],  # Now maps to REJECTED
            "final_confidence": 0.0,
            "primary_reason": error_message,
            "failed_checks": ["SYSTEM_ERROR"],
            "review_flags": [],
            "conflicts": [],
            "escalation_required": True,
            "llm_reasoning": None,
        }
