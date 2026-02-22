import tempfile
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


def generate_pdf(df):
    """
    Generates a clean, readable PDF report
    with no truncation or indentation issues.
    """

    if df is None or df.empty:
        return None

    temp_dir = tempfile.mkdtemp()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(
        temp_dir, f"compliance_report_{timestamp}.pdf"
    )

    # -------------------------------------------------
    # Layout: Landscape for wide tables
    # -------------------------------------------------
    pagesize = landscape(A4)

    doc = SimpleDocTemplate(
        file_path,
        pagesize=pagesize,
        rightMargin=20,
        leftMargin=20,
        topMargin=24,
        bottomMargin=24,
    )

    styles = getSampleStyleSheet()

    cell_style = ParagraphStyle(
        "CellStyle",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        leftIndent=0,
        rightIndent=0,
        spaceBefore=0,
        spaceAfter=0,
    )

    header_style = ParagraphStyle(
        "HeaderStyle",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        textColor=colors.black,
        alignment=1,  # center
        spaceBefore=4,
        spaceAfter=4,
    )

    elements = []

    # -------------------------------------------------
    # Title
    # -------------------------------------------------
    elements.append(
        Paragraph(
            "<b>Agentic AI Compliance Validation Report</b>",
            styles["Title"]
        )
    )
    elements.append(Spacer(1, 10))

    # -------------------------------------------------
    # Metadata block
    # -------------------------------------------------
    elements.append(
        Paragraph(
            f"""
            <b>Generated On:</b> {datetime.now().strftime("%d %b %Y, %H:%M:%S")}<br/>
            <b>Total Records:</b> {len(df)}
            """,
            styles["Normal"]
        )
    )
    elements.append(Spacer(1, 12))

    # -------------------------------------------------
    # Prepare table data
    # -------------------------------------------------
    table_data = []

    # Header row
    table_data.append([
        Paragraph(str(col), header_style) for col in df.columns
    ])

    # Data rows
    for _, row in df.iterrows():
        table_data.append([
            Paragraph(
                "" if cell is None else str(cell).replace("\n", "<br/>"),
                cell_style
            )
            for cell in row
        ])

    # -------------------------------------------------
    # Dynamic column widths (NO TRUNCATION)
    # -------------------------------------------------
    usable_width = pagesize[0] - doc.leftMargin - doc.rightMargin
    col_count = len(df.columns)

    # Weight columns slightly based on text-heavy fields
    weights = []
    for col in df.columns:
        if "Reason" in col or "Checks" in col or "Conflicts" in col:
            weights.append(2)
        else:
            weights.append(1)

    total_weight = sum(weights)
    col_widths = [
        (usable_width * w) / total_weight
        for w in weights
    ]

    table = Table(
        table_data,
        colWidths=col_widths,
        repeatRows=1,
        hAlign="LEFT",
    )

    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ])
    )

    elements.append(table)

    # -------------------------------------------------
    # Build PDF
    # -------------------------------------------------
    doc.build(elements)

    return file_path
