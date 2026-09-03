"""Canonical serialization and hashing shared by upload and verification."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(post_data: dict[str, Any]) -> str:
    """Serialize a post deterministically according to the Stage 3 contract."""
    return json.dumps(post_data, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def post_hash(post_data: dict[str, Any]) -> str:
    """Return the SHA-256 digest as a 0x-prefixed bytes32-compatible hex string."""
    digest = hashlib.sha256(canonical_json(post_data).encode("utf-8")).hexdigest()
    return "0x" + digest
