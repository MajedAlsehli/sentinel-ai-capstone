"""Pure presentation helpers shared by the dashboard and its tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping


SAMPLE_INVESTIGATIONS = {
    "Phishing email": """Review this complete raw email for phishing indicators.

From: Account Security <alerts@contoso-security.example>
Reply-To: recovery-team@example.net
Subject: Urgent - verify your account

Your password expires today. Verify your account at https://example.net/login immediately.""",
    "Suspicious URL": "Assess https://example.net/login without opening it.",
    "Network indicator": "Investigate network traffic associated with 1.1.1.1.",
    "File hash": "Check SHA-256 " + "a" * 64 + " for malware indicators.",
}

VERDICT_COLORS = {
    "malicious": "#FB7185",
    "suspicious": "#FBBF24",
    "benign": "#34D399",
    "unknown": "#94A3B8",
}

ROUTE_LABELS = {
    "email_agent": "Email specialist",
    "url_agent": "URL specialist",
    "ip_agent": "IP specialist",
    "file_agent": "File specialist",
}


def confidence_percent(value: Any) -> str:
    """Format a model confidence value without allowing an invalid percentage."""

    try:
        bounded = min(1.0, max(0.0, float(value)))
    except (TypeError, ValueError):
        bounded = 0.0
    return f"{bounded:.0%}"


def route_label(destination: str | None) -> str:
    """Return a human-readable specialist label."""

    return ROUTE_LABELS.get(str(destination), "Pending model decision")


def verdict_color(verdict: str | None) -> str:
    """Return the dashboard accent associated with a verdict."""

    return VERDICT_COLORS.get(str(verdict).lower(), VERDICT_COLORS["unknown"])


def redact_secrets(message: object, environment: Mapping[str, str | None]) -> str:
    """Remove configured credential values from an exception shown in the UI."""

    redacted = str(message)
    for name in (
        "OPENAI_API_KEY",
        "LANGCHAIN_API_KEY",
        "LANGSMITH_API_KEY",
        "ABUSEIPDB_API_KEY",
        "VIRUSTOTAL_API_KEY",
    ):
        secret = environment.get(name)
        if secret and len(secret) >= 8:
            redacted = redacted.replace(secret, f"[{name} redacted]")
    return redacted


def downloadable_pdf(result: Mapping[str, Any] | None) -> Path | None:
    """Return the final PDF only when the approved workflow really wrote it."""

    if not result:
        return None
    finalization = result.get("finalization") or {}
    candidate = finalization.get("output_path")
    if finalization.get("status") != "written" or not candidate:
        return None
    path = Path(candidate)
    return path if path.is_file() and path.suffix.lower() == ".pdf" else None
