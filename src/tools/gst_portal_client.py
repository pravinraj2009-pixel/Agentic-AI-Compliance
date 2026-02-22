# src/tools/gst_portal_client.py
import time
import requests
from utils.simple_cache import SimpleTTLCache


class GSTPortalClient:
    """
    Client for interacting with mock GST portal API.
    Handles retries, rate limiting, error normalization,
    and SAFE caching (no behavior change).
    """

    def __init__(self, base_url, api_key, max_retries=3, cache_ttl=3600):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.max_retries = max_retries
        self.cache = SimpleTTLCache(ttl_seconds=cache_ttl)

    def _headers(self):
        return {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
        }

    # -------------------------------------------------
    # INTERNAL HELPERS (CACHE SAFE DATA ONLY)
    # -------------------------------------------------

    def _post(self, endpoint, payload, cache_key=None):
        if cache_key:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        url = f"{self.base_url}/{endpoint}"

        for _ in range(self.max_retries):
            resp = requests.post(
                url, json=payload, headers=self._headers(), timeout=5
            )

            if resp.status_code == 429:
                time.sleep(int(resp.headers.get("Retry-After", 1)))
                continue

            result = (resp.status_code, self._safe_json_response(resp))

            if cache_key:
                self.cache.set(cache_key, result)

            return result

        raise RuntimeError(f"Rate limit exceeded for {endpoint}")

    def _get(self, endpoint, params, cache_key=None):
        if cache_key:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        url = f"{self.base_url}/{endpoint}"

        for _ in range(self.max_retries):
            resp = requests.get(
                url, params=params, headers=self._headers(), timeout=5
            )

            if resp.status_code == 429:
                time.sleep(int(resp.headers.get("Retry-After", 1)))
                continue

            result = (resp.status_code, self._safe_json_response(resp))

            if cache_key:
                self.cache.set(cache_key, result)

            return result

        raise RuntimeError(f"Rate limit exceeded for {endpoint}")

    def _safe_json_response(self, response):
        try:
            return response.json()
        except ValueError:
            return {"error": "Invalid JSON response"}

    # -------------------------------------------------
    # API METHODS (WITH CORRECT CACHE KEYS)
    # -------------------------------------------------

    def validate_gstin(self, gstin):
        return self._post(
            "validate-gstin",
            {"gstin": gstin},
            cache_key=f"gstin:{gstin}",
        )

    def validate_irn(self, irn):
        return self._post(
            "validate-irn",
            {"irn": irn},
            cache_key=f"irn:{irn}",
        )

    def get_hsn_rate(self, hsn_code, invoice_date):
        return self._get(
            "hsn-rate",
            {"code": hsn_code, "date": invoice_date},
            cache_key=f"hsn:{hsn_code}:{invoice_date}",
        )

    def check_einvoice_required(self, seller_gstin, invoice_date, invoice_value):
        return self._post(
            "e-invoice-required",
            {
                "seller_gstin": seller_gstin,
                "invoice_date": invoice_date,
                "invoice_value": invoice_value,
            },
            # ✅ invoice_value INCLUDED
            cache_key=f"einvoice:{seller_gstin}:{invoice_date}:{invoice_value}",
        )

    def verify_206ab(self, pan):
        return self._post(
            "verify-206ab",
            {"pan": pan},
            cache_key=f"pan:{pan}",
        )
