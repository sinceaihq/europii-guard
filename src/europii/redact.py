"""Replace findings in text."""

from __future__ import annotations

import hashlib
import secrets
from collections.abc import Sequence

from .core import Finding

# Per-process salt: hashes are stable within a run (so the same e-mail gets the
# same token) but cannot be reversed by hashing guesses from another run.
_SALT = secrets.token_bytes(16)


def _token(f: Finding, style: str) -> str:
    if style == "placeholder":
        return f"<{f.entity}>"
    if style == "mask":
        return "*" * len(f.text)
    if style == "hash":
        digest = hashlib.blake2b(f.text.encode(), key=_SALT, digest_size=4).hexdigest()
        return f"<{f.entity}:{digest}>"
    raise ValueError(f"unknown redaction style {style!r}")


def redact_findings(text: str, findings: Sequence[Finding], style: str = "placeholder") -> str:
    out, pos = [], 0
    for f in sorted(findings, key=lambda f: f.start):
        if f.start < pos:  # overlapping findings: keep the first
            continue
        out.append(text[pos : f.start])
        out.append(_token(f, style))
        pos = f.end
    out.append(text[pos:])
    return "".join(out)
