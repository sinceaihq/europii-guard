"""EuroPII Guard: detect and redact personal data in European text, locally.

This is a privacy-assistance tool. It does not guarantee that all personal
data is found and does not make any processing GDPR-compliant by itself.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from .core import DEFAULT_THRESHOLD, Detector, Finding, Scanner
from .detectors import ALL_DETECTORS
from .redact import redact_findings

__version__ = "0.1.1"

__all__ = [
    "ALL_DETECTORS",
    "DEFAULT_THRESHOLD",
    "Detector",
    "Finding",
    "Scanner",
    "__version__",
    "redact",
    "scan",
]


def scan(
    text: str,
    *,
    entities: Iterable[str] | None = None,
    threshold: float = DEFAULT_THRESHOLD,
    countries: Sequence[str] = (),
) -> list[Finding]:
    """Find personal data in ``text``.

    Args:
        entities: restrict to these entity types (e.g. ``["EMAIL", "IBAN"]``).
        threshold: minimum confidence (0–1). Lower it to favour recall.
        countries: ISO country codes whose identifiers are expected; matches
            for these countries get a small confidence boost.
    """
    scanner = Scanner(ALL_DETECTORS, threshold=threshold, countries=frozenset(countries))
    return scanner.scan(text, entities)


def redact(
    text: str,
    *,
    entities: Iterable[str] | None = None,
    threshold: float = DEFAULT_THRESHOLD,
    countries: Sequence[str] = (),
    style: str = "placeholder",
) -> str:
    """Return ``text`` with detected personal data replaced.

    ``style``: ``"placeholder"`` (``<EMAIL>``), ``"mask"`` (``*****``) or
    ``"hash"`` (``<EMAIL:3f2a9c1b>``, stable within the process, useful to keep
    references distinguishable without exposing the value).
    """
    return redact_findings(
        text, scan(text, entities=entities, threshold=threshold, countries=countries), style
    )
