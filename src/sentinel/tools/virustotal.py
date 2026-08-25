import base64

import requests
from langchain_core.tools import tool

from sentinel.config import virustotal_key


def _headers() -> dict[str, str] | None:
    api_key = virustotal_key()
    return {"x-apikey": api_key} if api_key else None

@tool
def check_url_virustotal(url: str) -> dict:
    """Look up an existing URL report in VirusTotal without submitting it."""

    headers = _headers()
    if not headers:
        return {
            "status": "not_configured",
            "provider": "VirusTotal",
            "url": url,
            "message": "VIRUSTOTAL_API_KEY is optional and was not configured.",
        }
    url_id = base64.urlsafe_b64encode(url.encode("utf-8")).decode("ascii").rstrip("=")
    response = requests.get(
        f"https://www.virustotal.com/api/v3/urls/{url_id}",
        headers=headers,
        timeout=20,
    )
    if response.status_code == 404:
        return {
            "status": "not_found",
            "provider": "VirusTotal",
            "url": url,
            "message": "No existing VirusTotal URL report was found.",
        }
    response.raise_for_status()
    attributes = response.json().get("data", {}).get("attributes", {})
    return {
        "status": "ok",
        "provider": "VirusTotal",
        "url": url,
        "analysis_stats": attributes.get("last_analysis_stats", {}),
        "reputation": attributes.get("reputation"),
        "last_analysis_date": attributes.get("last_analysis_date"),
        "categories": attributes.get("categories", {}),
    }


@tool
def check_file_hash_virustotal(file_hash: str) -> dict:
    """Look up an MD5, SHA-1, or SHA-256 file hash in VirusTotal."""

    headers = _headers()
    if not headers:
        return {
            "status": "not_configured",
            "provider": "VirusTotal",
            "file_hash": file_hash,
            "message": "VIRUSTOTAL_API_KEY is optional and was not configured.",
        }
    response = requests.get(
        f"https://www.virustotal.com/api/v3/files/{file_hash}",
        headers=headers,
        timeout=20,
    )
    if response.status_code == 404:
        return {
            "status": "not_found",
            "provider": "VirusTotal",
            "file_hash": file_hash,
        }
    response.raise_for_status()
    attributes = response.json().get("data", {}).get("attributes", {})
    return {
        "status": "ok",
        "provider": "VirusTotal",
        "file_hash": file_hash,
        "meaningful_name": attributes.get("meaningful_name"),
        "file_type": attributes.get("type_description"),
        "size": attributes.get("size"),
        "analysis_stats": attributes.get("last_analysis_stats", {}),
        "reputation": attributes.get("reputation"),
    }
