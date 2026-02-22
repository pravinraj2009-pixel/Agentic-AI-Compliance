
def detect_gst_tds_conflict(results):
    gst_issues = [r for r in results if r["category"]=="GST" and r["status"]=="FAIL"]
    tds_issues = [r for r in results if r["category"]=="TDS" and r["status"]=="FAIL"]

    if gst_issues and tds_issues:
        return {
            "conflict": True,
            "type": "GST_TDS_INTERPRETATION_CONFLICT",
            "details": {
                "gst": gst_issues,
                "tds": tds_issues
            }
        }
    return {"conflict": False}
