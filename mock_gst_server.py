from flask import Flask, request, jsonify
import json
from datetime import datetime

app = Flask(__name__)

# Load vendor registry as mock DB
with open("data/vendor_registry.json", "r", encoding="utf-8") as f:
    vendors = {v["gstin"]: v for v in json.load(f)["vendors"] if v.get("gstin")}

@app.route("/api/gst/validate-gstin", methods=["POST"])
def validate_gstin():
    gstin = request.json.get("gstin", "").upper().strip()

    if len(gstin) != 15 or not gstin.isalnum():
        return jsonify({
            "valid": False,
            "error": "INVALID_FORMAT",
            "message": "GSTIN must be 15 characters alphanumeric"
        }), 400

    vendor = vendors.get(gstin)
    if not vendor:
        return jsonify({
            "valid": False,
            "error": "NOT_FOUND",
            "message": "GSTIN not registered"
        }), 404

    return jsonify({
        "valid": True,
        "gstin": gstin,
        "legal_name": vendor["legal_name"],
        "status": vendor["status"],
        "state_code": vendor["state_code"],
        "taxpayer_type": vendor.get("gst_filing_status", "Regular"),
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route("/api/gst/validate-irn", methods=["POST"])
def validate_irn():
    irn = request.json.get("irn")
    if not irn or len(irn) < 10:
        return jsonify({"valid": False, "error": "IRN_NOT_FOUND"}), 404
    return jsonify({"valid": True, "status": "ACTIVE"})

@app.route("/api/gst/hsn-rate", methods=["GET"])
def hsn_rate():
    code = request.args.get("code")
    date = request.args.get("date")
    return jsonify({
        "hsn_sac": code,
        "rate": {"cgst": 9, "sgst": 9, "igst": 18},
        "effective_from": "2017-07-01",
        "requested_date": date
    })

@app.route("/api/gst/e-invoice-required", methods=["POST"])
def einvoice_required():
    value = request.json.get("invoice_value", 0)
    return jsonify({
        "required": value > 500000,
        "threshold": 500000
    })

@app.route("/api/gst/verify-206ab", methods=["POST"])
def verify_206ab():
    return jsonify({
        "section_206ab_applicable": False
    })

if __name__ == "__main__":
    app.run(port=8080, debug=True)
