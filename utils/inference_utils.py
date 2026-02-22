def infer_missing_fields(invoice, vendor_registry):
    """
    Safely infer missing invoice attributes using vendor registry.
    This function MUST NOT mutate invoice structure.
    """

    if not isinstance(invoice, dict):
        raise TypeError("infer_missing_fields expects invoice dict")

    if not isinstance(vendor_registry, dict):
        raise TypeError("vendor_registry must be dict")

    # ---------------------------------------------------------
    # Ensure fields dict exists
    # ---------------------------------------------------------
    fields = invoice.get("fields")
    if not isinstance(fields, dict):
        raise TypeError("invoice['fields'] must be dict during inference")

    # ---------------------------------------------------------
    # Extract vendor info from nested vendor object if present
    # ---------------------------------------------------------
    vendor_obj = fields.get("vendor") or {}
    if isinstance(vendor_obj, dict):
        # Extract PAN from vendor object
        if not fields.get("vendor_pan") and vendor_obj.get("pan"):
            fields["vendor_pan"] = vendor_obj.get("pan")
        
        # Flatten vendor PAN to top level for validators
        if vendor_obj.get("pan") and not invoice.get("vendor_pan"):
            invoice["vendor_pan"] = vendor_obj.get("pan")
        
        # Extract state code from vendor object if available
        if not fields.get("seller_state_code") and vendor_obj.get("state_code"):
            fields["seller_state_code"] = vendor_obj.get("state_code")
            invoice["seller_state_code"] = vendor_obj.get("state_code")
    
    # ---------------------------------------------------------
    # Extract buyer info from nested buyer object if present
    # ---------------------------------------------------------
    buyer_obj = fields.get("buyer") or {}
    if isinstance(buyer_obj, dict):
        # Extract buyer state code if available
        if not fields.get("buyer_state_code") and buyer_obj.get("state_code"):
            fields["buyer_state_code"] = buyer_obj.get("state_code")
            invoice["buyer_state_code"] = buyer_obj.get("state_code")

    # ---------------------------------------------------------
    # Infer state codes from GSTIN if not available
    # ---------------------------------------------------------
    if invoice.get("seller_gstin") and not invoice.get("seller_state_code"):
        gstin = invoice["seller_gstin"]
        if isinstance(gstin, str) and len(gstin) >= 2:
            try:
                state_code = gstin[:2]
                if state_code.isdigit():
                    invoice["seller_state_code"] = state_code
                    fields["seller_state_code"] = state_code
            except:
                pass
    
    if invoice.get("buyer_gstin") and not invoice.get("buyer_state_code"):
        gstin = invoice["buyer_gstin"]
        if isinstance(gstin, str) and len(gstin) >= 2:
            try:
                state_code = gstin[:2]
                if state_code.isdigit():
                    invoice["buyer_state_code"] = state_code
                    fields["buyer_state_code"] = state_code
            except:
                pass

    # ---------------------------------------------------------
    # Infer tax type (IGST vs CGST_SGST) based on state codes
    # ---------------------------------------------------------
    if not fields.get("tax_type"):
        seller_state = invoice.get("seller_state_code")
        buyer_state = invoice.get("buyer_state_code")
        
        if seller_state and buyer_state:
            if seller_state == buyer_state:
                fields["tax_type"] = "CGST_SGST"
                invoice["tax_type"] = "CGST_SGST"
            else:
                fields["tax_type"] = "IGST"
                invoice["tax_type"] = "IGST"
        # Also check raw data
        elif fields.get("igst_rate") and float(fields.get("igst_rate", 0)) > 0:
            fields["tax_type"] = "IGST"
            invoice["tax_type"] = "IGST"
        elif fields.get("cgst_rate") and float(fields.get("cgst_rate", 0)) > 0:
            fields["tax_type"] = "CGST_SGST"
            invoice["tax_type"] = "CGST_SGST"

    # ---------------------------------------------------------
    # Infer seller GSTIN from vendor registry
    # ---------------------------------------------------------
    if not invoice.get("seller_gstin"):
        vendor_name = fields.get("vendor_name")
        
        # Also check nested vendor object for name
        if not vendor_name and isinstance(vendor_obj, dict):
            vendor_name = vendor_obj.get("name")

        if vendor_name:
            for vendor in vendor_registry.get("vendors", []):
                if vendor.get("legal_name") == vendor_name or vendor.get("name") == vendor_name or vendor.get("trade_name") == vendor_name:
                    invoice["seller_gstin"] = vendor.get("gstin")
                    break

    # ---------------------------------------------------------
    # Infer vendor PAN from GSTIN if still missing
    # ---------------------------------------------------------
    if invoice.get("seller_gstin") and not invoice.get("vendor_pan"):
        gstin = invoice["seller_gstin"]
        if isinstance(gstin, str) and len(gstin) >= 12:
            pan = gstin[2:12]
            invoice["vendor_pan"] = pan
            fields["vendor_pan"] = pan

    # ---------------------------------------------------------
    # Infer invoice value from line items
    # ---------------------------------------------------------
    if not invoice.get("invoice_value"):
        total = 0.0
        for item in invoice.get("line_items", []):
            amount = item.get("amount")
            try:
                total += float(amount)
            except (TypeError, ValueError):
                pass

        invoice["invoice_value"] = round(total, 2)
    
    return invoice
