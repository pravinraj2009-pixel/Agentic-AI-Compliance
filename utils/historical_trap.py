
import json

def analyze_historical(invoice_id, current_decision, history_file):
    flags = []
    with open(history_file, "r", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            if record.get("invoice_id") == invoice_id:
                if record.get("decision") != current_decision:
                    flags.append({
                        "issue": "HISTORICAL_DEVIATION",
                        "past_decision": record.get("decision"),
                        "current_decision": current_decision
                    })
    return flags
