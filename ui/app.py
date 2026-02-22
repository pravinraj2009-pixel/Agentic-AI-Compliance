import pandas as pd
import gradio as gr

from src.orchestration.compliance_pipeline import run_compliance_pipeline
from src.config import load_config

from utils.download_csv import generate_csv
from utils.download_pdf import generate_pdf


# =========================================================
# TABLE CONFIGURATION
# =========================================================

TABLE_COLUMN_LABELS = [
    "Invoice ID",
    "Compliance\nDecision",
    "Confidence\nScore",
    "Primary Reason",
    "Decision Rationale",
    "Escalation\nRequired",
    "Failed Checks",
    "Review Flags",
    "Conflicts Identified",
]


TABLE_COLUMNS = [
    "invoice_id",
    "decision",
    "final_confidence",
    "primary_reason",
    "decision_rationale",
    "escalation_required",
    "failed_checks",
    "review_flags",
    "conflicts",
]


# =========================================================
# VALIDATION CODE → User Friendly text
# =========================================================

VALIDATION_TEXT_MAP = {
    "B1": "Invalid GSTIN format",
    "B2": "GSTIN suspended or not registered",
    "B3": "Seller state information missing",
    "B8": "Insufficient data to determine tax type",
    "B12": "E-invoice required but IRN missing",
    "B15": "E-invoice required but IRN missing",
    "D1": "TDS applicability needs confirmation",
    "D3": "PAN not available - higher TDS applicable",
    "D5": "TDS threshold validation passed",
    "D7": "TDS on GST component handled correctly",
    "D9": "TAN not configured",
}


def resolve_validation_text(code: str) -> str:
    """
    Guarantees readable validation text even if a new
    rule code is introduced without UI mapping.
    """
    return VALIDATION_TEXT_MAP.get(
        code,
        f"Validation rule {code} failed"
    )

def aggregate_ai_summary(llm_reasoning_list):   
    """
    Convert per-invoice LLM reasoning into
    generalized, de-duplicated AI summary bullets.
    """
    bullets = set()

    for reasoning in llm_reasoning_list:
        if not reasoning:
            continue

        for line in reasoning:
            text = line.lower()

            if "missing" in text:
                bullets.add(
                    "Missing critical invoice fields can lead to compliance failure"
                )
            elif "incomplete" in text:
                bullets.add(
                    "Incomplete data often results in REVIEW outcomes"
                )
            elif "ambigu" in text:
                bullets.add(
                    "Ambiguous invoice data can cause mixed compliance outcomes"
                )
            elif "conflict" in text:
                bullets.add(
                    "Conflicting compliance signals may require human review"
                )

    return sorted(bullets)

    # =========================================================
    # PIPELINE EXECUTION + NORMALIZATION
    # =========================================================

def run_pipeline(show_only_escalated: bool):
    """
    Executes the compliance pipeline and prepares
    data for UI consumption.
    """

    # -----------------------------------------------------
    # Load configuration
    # -----------------------------------------------------
    config = load_config()

    # -----------------------------------------------------
    # Run compliance pipeline (core engine)
    # -----------------------------------------------------
    summary, reports = run_compliance_pipeline(
        config,
        force_run=True
    )

    # -----------------------------------------------------
    # Initialize aggregation
    # -----------------------------------------------------
    rows = []
    escalation_count = 0

    # Collect ALL LLM reasoning across invoices
    all_llm_reasoning = []

    # Collect rule-based conflicts (per invoice)
    conflicts = []

    # -----------------------------------------------------
    # Process each invoice report
    # -----------------------------------------------------
    for r in reports:

        decision = r.get("decision", "")
        decision_lower = decision.strip().lower()

        is_escalated = decision_lower == "rejected"

        if is_escalated:
            escalation_count += 1

        failed_checks = r.get("failed_checks") or []
        review_flags = r.get("review_flags") or []
        invoice_conflicts = r.get("conflicts") or []
        decision = r.get("decision", "")
        decision_lower = r.get("decision", "").strip().lower()
        # -------------------------------------------------
        # Decision rationale (UI-friendly)
        # -------------------------------------------------
        if decision_lower == "rejected":
            rationale = "One or more critical compliance failures detected"
        elif decision_lower == "review":
            rationale = "Compliance requires human or conditional review"
        elif decision_lower == "pass":
            rationale = "All compliance checks passed"
        else:
            rationale = "Decision pending review"


        # -------------------------------------------------
        # SAFE LIST HANDLING
        # -------------------------------------------------
            if r.get("escalation_required") and not review_flags:
                review_flags = [
                    "Escalated due to critical GST compliance failure"
                ]
        # Aggregate rule-based conflicts
        for c in invoice_conflicts:
            if c not in conflicts:
                conflicts.append(c)

        # -------------------------------------------------
        # Collect LLM reasoning (for AI summary)
        # -------------------------------------------------
        if r.get("llm_reasoning"):
            all_llm_reasoning.append(r["llm_reasoning"])

        # -------------------------------------------------
        # Build table row
        # -------------------------------------------------
        rows.append({
            "invoice_id": r.get("invoice_id", ""),
            "decision": decision,
            "final_confidence": (
                f"{round(float(r.get('final_confidence', 0)) * 100)}%"
                if r.get("final_confidence") is not None else ""
            ),
            "primary_reason": r.get("primary_reason", ""),
            "decision_rationale": rationale,
            "escalation_required": "Yes" if is_escalated else "No",

            "failed_checks": "\n".join(
                resolve_validation_text(code)
                for code in failed_checks
            ),
            "review_flags": "\n".join(
                resolve_validation_text(code) if code.isupper() else code
                for code in review_flags
            ),
            "conflicts": "\n".join(invoice_conflicts),
        })

    # -----------------------------------------------------
    # Create DataFrame
    # -----------------------------------------------------
    df = pd.DataFrame(rows, columns=TABLE_COLUMNS)
    df.columns = TABLE_COLUMN_LABELS

    # -----------------------------------------------------
    # Filtering
    # -----------------------------------------------------
    if show_only_escalated:
        df = df[df["Escalation\nRequired"] == "Yes"]

    # -----------------------------------------------------
    # Summary text
    # -----------------------------------------------------
    approved = len(reports) - escalation_count

    summary_text = f"""
    **Total Invoices:** {len(reports)}  
    **Approved Invoices:** {approved}  
    **Escalated Invoices:** {escalation_count}  
    **Processing Time (seconds):** {summary.get("processing_time_sec")}
    """

    # -----------------------------------------------------
    # GLOBAL AI COMPLIANCE SUMMARY (AGGREGATED)
    # -----------------------------------------------------
    ai_compliance_summary = []

    seen = set()
    for reasoning in all_llm_reasoning:
        for line in reasoning:
            text = line.lower()

            if "missing" in text:
                msg = "Missing critical invoice fields can lead to compliance failure"
            elif "incomplete" in text:
                msg = "Incomplete data often results in REVIEW outcomes"
            elif "ambigu" in text:
                msg = "Ambiguous invoice data can cause mixed compliance outcomes"
            elif "conflict" in text:
                msg = "Conflicting compliance signals may require human review"
            else:
                continue

            if msg not in seen:
                seen.add(msg)
                ai_compliance_summary.append(msg)

    return (
        summary_text,          # for summary panel
        df,                    # main table
        escalation_count,      # escalation count
        "",                    # escalation message (unchanged)
        conflicts,             # rule-based conflicts
        ai_compliance_summary  # ✅ AI Compliance Summary
    )


# =========================================================
# UI DEFINITION
# =========================================================

def launch_ui():

    with gr.Blocks(
        title="Agentic AI Compliance Validator"
    ) as app:

        # -------------------------------------------------
        # HEADER
        # -------------------------------------------------
        gr.HTML(
            """
            <div class="navbar">
                <div>
                    <h2>🧾 Agentic AI Compliance Validator</h2>
                    <div class="subtitle">
                        Automated invoice compliance review using explainable multi-agent intelligence
                    </div>
                </div>
                <div class="nav-links">
                    <a href="https://docs.google.com/document/d/1WK0BGHVOBgTPo0uH_4OpeGNKTMAxGEAd/edit?usp=sharing&ouid=106462723989474464636&rtpof=true&sd=true"
                    target="_blank">Architecture</a>

                    <a href="https://docs.google.com/document/d/1MylwiHJOaJ7vLUV6QQKWUGHhlh-_y6Ib/edit?usp=sharing&ouid=106462723989474464636&rtpof=true&sd=true"
                    target="_blank">Walkthrough</a>

                    <a href="https://drive.google.com/file/d/1AIbu1FbB24K__khOVbzM2CmzoLUrSHuh/view?usp=sharing"
                    target="_blank">README</a>
                </div>

            </div>
            """
        )

        # -------------------------------------------------
        # TABS
        # -------------------------------------------------
        with gr.Tabs():

            with gr.Tab("Overview"):
                gr.Markdown(
                    """
                    ### 📌 System Overview

                    This system implements an **agentic AI–based Accounts Payable compliance engine**.

                    - Deterministic GST, TDS, and policy validations  
                    - Human-in-the-loop escalation for ambiguity  
                    - Explainable, audit-ready decisions  
                    """
                )

            with gr.Tab("Agent Architecture"):
                gr.Markdown(
                    """
                    ### 🧠 Agent Architecture

                    **Extractor Agent**  
                    Normalizes incoming invoice data

                    **Validator Agents**  
                    Perform rule-based GST, TDS, and policy checks

                    **Resolver Agent**  
                    Handles ambiguity and conflicts

                    **Reporter Agent**  
                    Produces structured compliance reports
                    """
                )

            with gr.Tab("Audit & Traceability"):
                gr.Markdown(
                    """
                    ### 📂 Audit & Traceability

                    - Rule-level outcomes preserved  
                    - Confidence scores explain decisions  
                    - Escalation reasons clearly stated  
                    """
                )

            with gr.Tab("Documentation"):
                gr.Markdown(
                    """
                    ### 📖 Documentation

                    - JSON-only processing  
                    - Exportable reports  
                    - Extensible architecture  
                    """
                )

        # -------------------------------------------------
        # CONTROLS
        # -------------------------------------------------
        with gr.Row():
            run_btn = gr.Button("🚀 Run Compliance Validation")
            show_escalated = gr.Checkbox(
                label="Show only escalated invoices",
                value=False
            )

        # -------------------------------------------------
        # OUTPUTS
        # -------------------------------------------------
        summary_md = gr.Markdown(visible=False)
        escalation_note = gr.Markdown(visible=False)

        table_title = gr.Markdown(
            "### 📋 Actionable Compliance Report",
            visible=False
        )

        table_out = gr.Dataframe(
            headers=TABLE_COLUMN_LABELS,
            interactive=False,
            visible=False,
            wrap=True
        )

        llm_reasoning_out = gr.Markdown(
            visible=False,
            label="🧠 Compliance Summary using AI"
        )

        export_section = gr.Markdown(
            "### 📥 Export Report",
            visible=False
        )

        with gr.Row(visible=False) as export_row:
            csv_btn = gr.Button("Download CSV")
            pdf_btn = gr.Button("Download PDF")
            file_out = gr.File()

        # -------------------------------------------------
        # BUTTON HANDLER
        # -------------------------------------------------
        def handle_run(show_only_escalated):

            yield (
                gr.update(value="⏳ Processing invoices...", visible=True),
                gr.update(value="", visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
            )

            summary_text, df, esc_count, esc_msg, conflicts, ai_compliance_summary = (
                run_pipeline(show_only_escalated)
            )

            has_rows = len(df) > 0

            # ---- Rule-based conflicts (per invoice / table context) ----
            conflicts_md = (
                "### Conflicts Identified\n\n"
                + "\n".join(f"- {c}" for c in conflicts)
                if conflicts else ""
            )

            # ---- LLM-based AI summary (global, aggregated) ----
            ai_md = (
                "### Compliance Summary using AI\n\n"
                + "\n".join(f"- {p}" for p in ai_compliance_summary)
                if ai_compliance_summary else ""
            )


            yield (
                gr.update(value=summary_text, visible=True),
                gr.update(value=esc_msg, visible=esc_count == 0),
                gr.update(value=df, visible=has_rows),
                gr.update(value=conflicts_md, visible=bool(conflicts_md)),
                gr.update(value=ai_md, visible=bool(ai_md)),
                gr.update(visible=has_rows),
            )


        # -------------------------------------------------
        # WIRING
        # -------------------------------------------------
        run_btn.click(
            fn=handle_run,
            inputs=[show_escalated],
            outputs=[
                summary_md,
                escalation_note,
                table_out,
                llm_reasoning_out,
                export_section,
                export_row
            ]
        )

        csv_btn.click(fn=generate_csv, inputs=table_out, outputs=file_out)
        pdf_btn.click(fn=generate_pdf, inputs=table_out, outputs=file_out)

        # -------------------------------------------------
        # FOOTER
        # -------------------------------------------------
        gr.HTML(
            """
            <hr>
            <div style="text-align:center;font-size:13px;color:#6b7280;">
                © Agentic AI Compliance Validator |
                <a href="https:www.linkedin.com/in/pravin-waghe-40646779" target="_blank">LinkedIn</a> |
                <a href="https://github.com/pravinraj2009-pixel/Compliance_Validator_Challenge"
                   target="_blank">GitHub</a>
            </div>
            """
        )

    # -------------------------------------------------
    # LAUNCH
    # -------------------------------------------------
    app.launch(
        css="""
        .navbar {
            display:flex;
            justify-content:space-between;
            border-bottom:1px solid #e5e7eb;
            margin-bottom:12px;
        }
        .subtitle {
            font-size:14px;
            color:#6b7280;
        }
        .nav-links a {
            margin-left:16px;
            font-size:14px;
            color:#2563eb;
            text-decoration:none;
        }
        .gradio-dataframe table {
            border-collapse: collapse !important;
            width: 100% !important;
            border: 2px solid #9ca3af !important;
        }

        .gradio-dataframe thead th {
            border-bottom: 2px solid #9ca3af !important;
            border-right: 1px solid #d1d5db !important;
            background-color: #f3f4f6 !important;
            font-weight: 700 !important;
            padding: 10px !important;
        }

        .gradio-dataframe tbody tr {
            border-bottom: 1px solid #d1d5db !important; 
        }

        .gradio-dataframe tbody td {
            border-right: 1px solid #e5e7eb !important;
            border-bottom: 1px solid #e5e7eb !important;
            padding: 10px !important;
            white-space: pre-wrap !important;
            word-break: break-word !important;
            vertical-align: top !important;
            max-width: 300px;
        }

        .gradio-dataframe tbody tr:last-child td {
            border-bottom: 2px solid #9ca3af !important;
        }

        """,
        allowed_paths=[".", "./docs", "./text"]
    )


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    launch_ui()
