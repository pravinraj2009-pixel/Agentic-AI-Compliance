import pandas as pd
import tempfile
import os
from datetime import datetime


def generate_csv(df: pd.DataFrame):
    """
    Generates a clean, Excel-friendly CSV
    that exactly matches the UI table.
    """

    if df is None or df.empty:
        return None

    temp_dir = tempfile.mkdtemp()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(
        temp_dir, f"compliance_report_{timestamp}.csv"
    )

    # -------------------------------------------------
    # Metadata header (human-friendly)
    # -------------------------------------------------
    meta_rows = [
        ["Report Name", "Agentic AI Compliance Validation Report"],
        ["Generated On", datetime.now().strftime("%d %b %Y, %H:%M:%S")],
        ["Total Records", len(df)],
        [],
    ]

    df_meta = pd.DataFrame(meta_rows)

    # Combine metadata + data
    final_df = pd.concat([df_meta, df], ignore_index=True)

    # -------------------------------------------------
    # Write CSV (Excel safe)
    # -------------------------------------------------
    final_df.to_csv(
        file_path,
        index=False,
        encoding="utf-8-sig",   # Excel UTF-8
        lineterminator="\n"
    )

    return file_path
