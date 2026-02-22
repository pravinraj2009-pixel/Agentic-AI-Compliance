import json
from src.mcp.server import MCPServer
from src.mcp.tools.groq_api_tool import groq_resolver_tool
from src.storage.decision_store import DecisionStore


def normalize_llm_explanation(text):
    """
    ResolverAgent
    --------------
    ROLE:
    Converts validation results into final compliance decisions.

    ONLY handles:
    - Conflict detection across validation categories
    - Confidence threshold evaluation
    - Historical decision deviation detection
    - Escalation logic enforcement
    - Human-in-the-loop routing
    - LLM-based reasoning summarization (if enabled)
    - Final decision generation (APPROVE / REVIEW / ESCALATE)
    - Decision persistence to audit store

    DOES NOT:
    - Extract invoice data
    - Perform compliance validation
    - Modify invoice context
    - Perform file IO related to invoices
    - Render UI reports

    OUTPUT CONTRACT:
    Returns structured decision payload containing:
    - decision
    - confidence
    - failed checks
    - review flags
    - conflicts
    - escalation indicator
    """

    if not text:
        return []

    lines = text.split("\n")
    normalized = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        line = line.lstrip("-•0123456789. ").strip()

        # Drop generic intro fluff
        if line.lower().startswith("based on"):
            continue

        normalized.append(line)

    return normalized


class ResolverAgent:
    """
    Resolver Agent
    --------------
    Responsibilities:
    - Detect conflicts & ambiguity
    - Apply confidence threshold
    - Detect historical-decision traps
    - Use LLM for summarization
    - Decide APPROVE / APPROVE_WITH_REVIEW / ESCALATE
    - Persist final decision (SQLite)
    """

    def __init__(self, config):
        self.config = config
        self.confidence_threshold = config["confidence_threshold"]

        # ---- Historical decisions (JSONL) ----
        self.history_path = config["historical_decisions_path"]
        self.history = self._load_history()

        # ---- SQLite audit store ----
        self.db = DecisionStore(config["sqlite"]["db_path"])

        # ---- MCP + LLM ----
        self.mcp = None
        if (
            config["agentic"]["use_mcp"]
            and config["agentic"]["use_llm_resolver"]
        ):
            self.mcp = MCPServer()
            self.mcp.register_tool(
                "groq.reason",
                groq_resolver_tool(config)
            )

    def _load_history(self):
        history = []
        try:
            with open(self.history_path, "r", encoding="utf-8") as f:
                for line in f:
                    history.append(json.loads(line))
        except FileNotFoundError:
            pass
        return history

    # =====================================================
    # CONFLICT DETECTION (RULE-BASED)
    # =====================================================
    def _detect_conflicts(self, results):
        conflicts = []

        failed = [r for r in results if r.status == "FAIL"]
        review = [r for r in results if r.status == "REVIEW"]

        if failed and review:
            conflicts.append(
                "Mixed FAIL and REVIEW outcomes across compliance categories"
            )

        gst_fail = any(r.category == "GST" for r in failed)
        tds_fail = any(r.category == "TDS" for r in failed)

        if gst_fail and tds_fail:
            conflicts.append(
                "GST and TDS rules conflict or jointly violated"
            )

        # ✅ NEW: Explicit conflict when GST FAIL occurs
        if gst_fail and not conflicts:
            conflicts.append(
                "Critical GST compliance failure detected requiring escalation"
            )

        return conflicts

    # =====================================================
    # RESOLUTION
    # =====================================================
    def resolve(self, invoice_ctx, validation_payload):
        results = validation_payload["results"]
        confidence = validation_payload["final_confidence"]

        failed = [r for r in results if r.status == "FAIL"]
        review_flags = [r for r in results if r.status == "REVIEW"]

        # ---- Conflict detection ----
        conflicts = self._detect_conflicts(results)

        # ---- Historical Trap Detection ----
        deviated_from_history = False
        invoice_id = invoice_ctx.get("invoice_id")

        for record in self.history:
            if record.get("invoice_id") == invoice_id:
                if record.get("decision") == "APPROVE" and failed:
                    deviated_from_history = True

        # ---- Determine blocking REVIEWs ----
        blocking_review = any(
            r.category == "GST" for r in review_flags
        )

        # =====================================================
        # FINAL DECISION LOGIC
        # =====================================================
        # Classify review types
        blocking_review = any(
            r.category in ["GST", "TDS", "POLICY"]
            and r.check_id not in ["DATA_QUALITY"]
            for r in review_flags
        )

        informational_review = any(
            r.check_id == "DATA_QUALITY"
            for r in review_flags
        )

        if failed:
            decision = "ESCALATE"
            primary_reason = "One or more critical compliance checks failed"

        elif blocking_review:
            decision = "APPROVE_WITH_REVIEW"
            primary_reason = "Compliance requires human or conditional review"

        elif informational_review:
            decision = "APPROVE"
            primary_reason = "All compliance checks passed"

        elif confidence < self.confidence_threshold:
            decision = "APPROVE_WITH_REVIEW"
            primary_reason = "Confidence below approval threshold"

        else:
            decision = "APPROVE"
            primary_reason = "All compliance checks passed"


        # =====================================================
        # LLM RESOLVER (AI SUMMARY)
        # =====================================================
        llm_explanation = None

        # ✅ Allow LLM on ESCALATE even if conflicts are minimal
        if (conflicts or decision == "ESCALATE") and self.mcp:
            try:
                raw_llm_output = self.mcp.call_tool(
                    "groq.reason",
                    {
                        "invoice_context": {
                            "invoice_id": invoice_id,
                            "vendor_gstin": invoice_ctx.get("vendor_gstin"),
                            "amount": invoice_ctx.get("total_amount"),
                        },
                        "conflicts": conflicts,
                    }
                )

                llm_explanation = normalize_llm_explanation(raw_llm_output)

            except Exception as llm_error:
                print(f"[WARNING] LLM resolver failed: {llm_error}")
                llm_explanation = None

        # =====================================================
        # UI SAFETY FIXES
        # =====================================================

        # ✅ If escalated and no review flags (fail-fast case)
        if decision == "ESCALATE" and not review_flags:
            review_flags = [
                type(
                    "SyntheticReview",
                    (),
                    {"check_id": "Critical GST failure — manual review required"}
                )()
            ]

        # ---- Persist decision ----
        self.db.log_decision(
            invoice_id=invoice_id,
            decision=decision,
            confidence=confidence
        )

        # ---- DEBUG ----
        print(
            f"[DECISION DEBUG] Invoice={invoice_id} | "
            f"Decision={decision} | "
            f"Confidence={confidence} | "
            f"Failed={len(failed)} | "
            f"Review={len(review_flags)} | "
            f"Conflicts={len(conflicts)}"
        )

        # =====================================================
        # FINAL PAYLOAD
        # =====================================================
        return {
            "decision": decision,
            "final_confidence": round(confidence, 3),
            "failed_checks": [r.check_id for r in failed],
            "review_flags": [r.check_id for r in review_flags],
            "conflicts": conflicts,                 # rule-based (table)
            "llm_reasoning": llm_explanation,        # AI summary
            "deviated_from_history": deviated_from_history,
            "primary_reason": primary_reason,
            "escalation_required": decision == "ESCALATE",
        }