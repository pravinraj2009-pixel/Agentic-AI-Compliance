from src.models.validation_result import ValidationResult
from src.agents.gst_tds_validator_agent import GSTTDSValidatorAgent


class ValidatorAgent:
    """
    ValidatorAgent
    ----------------
    ROLE:
    Orchestrates all compliance validators and aggregates results.

    ONLY handles:
    - Invoking GST/TDS validation agent
    - Invoking additional category validators
    - Aggregating ValidationResult objects
    - Enforcing fail-fast behavior for critical GST failures
    - Ensuring consistent output structure

    DOES NOT:
    - Perform invoice extraction
    - Make final approval or escalation decisions
    - Generate user-facing reports
    - Compute final confidence scores
    - Persist decisions to storage
    - Invoke LLM tools

    OUTPUT CONTRACT:
    Returns a list of ValidationResult objects for downstream resolution.
    """


    def __init__(self, config=None):
        if config is None:
            raise ValueError("config is required for ValidatorAgent")

        self.config = config
        self.validators = config.get("validators", [])
        self.gst_tds_agent = GSTTDSValidatorAgent(config)

    def validate(self, invoice_ctx: dict):
        results = []

        # =================================================
        # GST / TDS Agent (FAIL-FAST)
        # =================================================
        try:
            gst_tds_results = self.gst_tds_agent.validate(invoice_ctx)

            if gst_tds_results:
                for item in gst_tds_results:

                    if isinstance(item, ValidationResult):
                        results.append(item)

                        # 🚨 FAIL-FAST: stop everything on GST FAIL
                        if item.category == "GST" and item.status == "FAIL":
                            return results

                    elif isinstance(item, str):
                        results.append(
                            ValidationResult(
                                check_id="GSTTDSValidatorAgent",
                                category="GST_TDS",
                                status="REVIEW",
                                reason=item
                            )
                        )

                    else:
                        results.append(
                            ValidationResult(
                                check_id="GSTTDSValidatorAgent",
                                category="GST_TDS",
                                status="REVIEW",
                                reason=f"Unexpected GST/TDS output: {type(item)}"
                            )
                        )

        except Exception as e:
            # If GST/TDS agent itself errors, treat as REVIEW and stop
            return [
                ValidationResult(
                    check_id="GSTTDSValidatorAgent",
                    category="GST_TDS",
                    status="REVIEW",
                    reason=f"GST/TDS agent error: {str(e)}"
                )
            ]

        # =================================================
        # OTHER VALIDATORS (ONLY IF GST PASSED)
        # =================================================
        for validator in self.validators:
            try:
                output = validator.validate(invoice_ctx)

                if not output:
                    continue

                for item in output:
                    if isinstance(item, ValidationResult):
                        results.append(item)

                    elif isinstance(item, str):
                        results.append(
                            ValidationResult(
                                check_id=validator.__class__.__name__,
                                category="VALIDATION",
                                status="REVIEW",
                                reason=item
                            )
                        )

                    else:
                        results.append(
                            ValidationResult(
                                check_id=validator.__class__.__name__,
                                category="VALIDATION",
                                status="REVIEW",
                                reason=f"Unexpected validator output: {type(item)}"
                            )
                        )

            except Exception as e:
                results.append(
                    ValidationResult(
                        check_id=validator.__class__.__name__,
                        category="VALIDATION",
                        status="REVIEW",
                        reason=f"Validator exception: {str(e)}"
                    )
                )

        return results
