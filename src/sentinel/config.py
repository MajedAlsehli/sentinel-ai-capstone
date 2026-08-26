"""Environment configuration for Sentinel AI.

Secrets are deliberately read at call time instead of import time. This makes
notebook restarts, tests, and secret rotation behave predictably without ever
placing credentials in source control.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env", override=False)

DEFAULT_CHAT_MODEL = "gpt-4o-mini"
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"


def get_env(name: str, default: str | None = None) -> str | None:
    """Return a stripped environment variable or the supplied default."""

    value = os.getenv(name)
    return value.strip() if value and value.strip() else default


def get_chat_model() -> str:
    return get_env("OPENAI_MODEL", DEFAULT_CHAT_MODEL) or DEFAULT_CHAT_MODEL


def get_embedding_model() -> str:
    return (
        get_env("OPENAI_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)
        or DEFAULT_EMBEDDING_MODEL
    )


def require_openai() -> str:
    """Return the configured OpenAI key or fail with an actionable message."""

    key = get_env("OPENAI_API_KEY")
    if not key:
        raise RuntimeError(
            "OPENAI_API_KEY is not configured. Copy .env.example to .env, add "
            "the key locally, and never commit .env."
        )
    return key


def abuseipdb_key() -> str | None:
    return get_env("ABUSEIPDB_API_KEY")


def virustotal_key() -> str | None:
    return get_env("VIRUSTOTAL_API_KEY")


def langsmith_status() -> dict[str, object]:
    """Expose tracing readiness without revealing any credential value."""

    tracing_value = (get_env("LANGCHAIN_TRACING_V2") or "").lower()
    return {
        "tracing_enabled": tracing_value in {"1", "true", "yes", "on"},
        "api_key_configured": bool(
            get_env("LANGCHAIN_API_KEY") or get_env("LANGSMITH_API_KEY")
        ),
        "project": get_env("LANGCHAIN_PROJECT", "sentinel-ai"),
    }
