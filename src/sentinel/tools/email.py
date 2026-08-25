"""Local email-analysis tools that do real, deterministic parsing work."""

from __future__ import annotations

import re
from email import policy
from email.parser import Parser

from langchain_core.tools import tool


URL_PATTERN = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
SUSPICIOUS_PHRASES = (
    "urgent",
    "verify your account",
    "password expires",
    "click immediately",
    "wire transfer",
    "gift card",
    "suspended",
)


@tool
def extract_email_indicators(raw_email: str) -> dict:
    """Parse email text and extract headers, links, attachments, and risk phrases."""

    message = Parser(policy=policy.default).parsestr(raw_email)
    body_parts: list[str] = []
    attachments: list[str] = []
    if message.is_multipart():
        for part in message.walk():
            filename = part.get_filename()
            if filename:
                attachments.append(filename)
            if part.get_content_type() == "text/plain" and not filename:
                try:
                    body_parts.append(part.get_content())
                except (LookupError, UnicodeDecodeError):
                    continue
    else:
        try:
            body_parts.append(message.get_content())
        except (LookupError, UnicodeDecodeError):
            body_parts.append(raw_email)

    body = "\n".join(body_parts) or raw_email
    searchable_text = f"{message.get('Subject', '')}\n{body}".lower()
    return {
        "status": "ok",
        "provider": "Sentinel local parser",
        "from": message.get("From"),
        "reply_to": message.get("Reply-To"),
        "subject": message.get("Subject"),
        "urls": sorted(set(URL_PATTERN.findall(body))),
        "attachments": attachments,
        "suspicious_phrases": [
            phrase for phrase in SUSPICIOUS_PHRASES if phrase in searchable_text
        ],
    }
