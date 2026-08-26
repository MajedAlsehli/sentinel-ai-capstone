"""Local validation for file hashes supplied to the file specialist."""

from __future__ import annotations

import re

from langchain_core.tools import tool


HASH_TYPES = {32: "MD5", 40: "SHA-1", 64: "SHA-256"}


@tool
def validate_file_hash(file_hash: str) -> dict:
    """Validate a hash value and identify whether it is MD5, SHA-1, or SHA-256."""

    normalized = file_hash.strip().lower()
    is_hex = bool(re.fullmatch(r"[0-9a-f]+", normalized))
    hash_type = HASH_TYPES.get(len(normalized)) if is_hex else None
    return {
        "status": "ok",
        "provider": "Sentinel local hash check",
        "normalized_hash": normalized,
        "valid": hash_type is not None,
        "hash_type": hash_type,
        "length": len(normalized),
    }
