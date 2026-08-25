import requests
from langchain_core.tools import tool

from sentinel.config import abuseipdb_key

@tool
def check_ip_reputation(ip: str) -> dict:
    """Look up an IPv4/IPv6 address in AbuseIPDB's live reputation service."""

    api_key = abuseipdb_key()
    if not api_key:
        return {
            "status": "not_configured",
            "provider": "AbuseIPDB",
            "ip": ip,
            "message": "ABUSEIPDB_API_KEY is optional and was not configured.",
        }
    response = requests.get(
        "https://api.abuseipdb.com/api/v2/check",
        headers={"Key": api_key, "Accept": "application/json"},
        params={"ipAddress": ip, "maxAgeInDays": 90},
        timeout=15,
    )
    response.raise_for_status()
    data = response.json().get("data", {})
    return {
        "status": "ok",
        "provider": "AbuseIPDB",
        "ip": data.get("ipAddress", ip),
        "abuse_confidence_score": data.get("abuseConfidenceScore"),
        "total_reports": data.get("totalReports"),
        "last_reported_at": data.get("lastReportedAt"),
        "country_code": data.get("countryCode"),
        "usage_type": data.get("usageType"),
        "isp": data.get("isp"),
        "is_whitelisted": data.get("isWhitelisted"),
    }
