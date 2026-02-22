# src/mcp/tools/gst_api_tool.py

def gst_validate_tool(gst_client):
    """
    MCP tool wrapper around GSTPortalClient.validate_gstin
    """

    def run(payload):
        gstin = payload.get("gstin")
        if not gstin:
            return {
                "error": "INVALID_INPUT",
                "message": "GSTIN not provided"
            }

        status, data = gst_client.validate_gstin(gstin)
        return {
            "status_code": status,
            "response": data
        }

    return run
