"""Findings, detectors and the scanner that runs them."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable, Iterable, Iterator, Sequence
from dataclasses import asdict, dataclass, field
from typing import Any

# Confidence before context. A *strong* match has structure that random text
# almost never has (a check character, a country prefix, a fixed layout); a
# *weak* one is a plain digit string whose checksum passes by chance often
# enough that it should only be reported next to a context word.
# A *medium* match (a digit-only identifier with a checksum and a date check)
# is reported without a label only if the caller expects that country.
# Grouped national phone numbers sit just above the default threshold.
# An undivided digit run that is merely a valid phone number is the weakest
# evidence of all, so a checksum-validated identifier wins a tie against it.
STRONG, PHONE_GROUPED, MEDIUM, WEAK, PHONE_PLAIN = 0.9, 0.55, 0.45, 0.3, 0.28
CONTEXT_BONUS = {STRONG: 0.09, PHONE_GROUPED: 0.4, MEDIUM: 0.45, WEAK: 0.55, PHONE_PLAIN: 0.57}
COUNTRY_BONUS = 0.1
DEFAULT_THRESHOLD = 0.5
# Labels precede values in all supported languages ("tel. 040...", "PESEL: ...").
# Looking after the value would borrow the label of the next field.
CONTEXT_BEFORE = 60


@dataclass(frozen=True)
class Finding:
    """One detected span. ``start``/``end`` are character offsets into the text."""

    entity: str
    start: int
    end: int
    text: str
    score: float
    detector: str
    country: str | None = None
    validated: bool = False
    context: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Detector:
    """A candidate pattern plus a validator.

    ``pattern`` finds candidates; ``validate`` (if given) receives the
    candidate with separators removed and must return True for a match.
    """

    name: str
    entity: str
    pattern: re.Pattern[str] | None
    strength: float
    validate: Callable[[str], bool] | None = None
    context: tuple[str, ...] = ()
    country: str | None = None
    strip: str = " .-/"
    finder: Callable[[str, frozenset[str]], Iterable[tuple[int, int]]] | None = None
    description: str = ""

    def candidates(
        self, text: str, countries: frozenset[str] = frozenset()
    ) -> Iterator[tuple[int, int]]:
        if self.finder is not None:
            yield from self.finder(text, countries)
            return
        assert self.pattern is not None
        for m in self.pattern.finditer(text):
            yield m.start(), m.end()

    def check(self, value: str) -> bool:
        if self.validate is None:
            return True
        compact = value.translate({ord(c): None for c in self.strip}).upper()
        try:
            return bool(self.validate(compact))
        except Exception:  # validators of third-party libraries may raise on odd input
            return False


def _fold(text: str) -> str:
    return unicodedata.normalize("NFKC", text).casefold()


def has_context(text: str, start: int, end: int, words: Sequence[str]) -> bool:
    if not words:
        return False
    window = _fold(text[max(0, start - CONTEXT_BEFORE) : start])
    return any(re.search(rf"(?<![^\W\d_]){re.escape(_fold(w))}(?![^\W\d_])", window) for w in words)


@dataclass
class Scanner:
    detectors: Sequence[Detector]
    threshold: float = DEFAULT_THRESHOLD
    countries: frozenset[str] = field(default_factory=frozenset)

    def scan(self, text: str, entities: Iterable[str] | None = None) -> list[Finding]:
        wanted = set(entities) if entities is not None else None
        found: list[Finding] = []
        for det in self.detectors:
            if wanted is not None and det.entity not in wanted:
                continue
            for start, end in det.candidates(text, self.countries):
                value = text[start:end]
                if not det.check(value):
                    continue
                ctx = has_context(text, start, end, det.context)
                score = det.strength + (CONTEXT_BONUS.get(det.strength, 0.0) if ctx else 0.0)
                if det.country and det.country in self.countries:
                    score += COUNTRY_BONUS
                found.append(
                    Finding(
                        entity=det.entity,
                        start=start,
                        end=end,
                        text=value,
                        score=round(min(score, 0.99), 3),
                        detector=det.name,
                        country=det.country,
                        validated=det.validate is not None,
                        context=ctx,
                    )
                )
        return [f for f in resolve_overlaps(found) if f.score >= self.threshold]


def resolve_overlaps(findings: Iterable[Finding]) -> list[Finding]:
    """Keep the best finding among overlapping ones: higher score, then longer span."""
    ranked = sorted(findings, key=lambda f: (-f.score, -(f.end - f.start), f.start))
    kept: list[Finding] = []
    for f in ranked:
        if all(f.end <= k.start or f.start >= k.end for k in kept):
            kept.append(f)
    return sorted(kept, key=lambda f: f.start)
