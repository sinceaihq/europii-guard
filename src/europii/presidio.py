"""Use EuroPII Guard inside Microsoft Presidio.

    from presidio_analyzer import AnalyzerEngine
    from europii.presidio import EuroPIIRecognizer

    analyzer = AnalyzerEngine()
    analyzer.registry.add_recognizer(EuroPIIRecognizer(supported_language="en"))

Presidio contributes its NLP-based entities (e.g. PERSON); EuroPII adds
checksum-validated European identifiers, VAT numbers and phone numbers.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from presidio_analyzer import EntityRecognizer, RecognizerResult

from .core import DEFAULT_THRESHOLD, Scanner
from .detectors import ALL_DETECTORS

# EuroPII entity -> Presidio entity name (Presidio's own names where they exist).
PRESIDIO_NAMES = {
    "EMAIL": "EMAIL_ADDRESS",
    "PHONE": "PHONE_NUMBER",
    "IBAN": "IBAN_CODE",
    "PAYMENT_CARD": "CREDIT_CARD",
    "IP_ADDRESS": "IP_ADDRESS",
    "VAT_ID": "EU_VAT_ID",
    "NATIONAL_ID": "EU_NATIONAL_ID",
}


class EuroPIIRecognizer(EntityRecognizer):  # type: ignore[misc]
    def __init__(
        self,
        supported_language: str = "en",
        countries: Sequence[str] = (),
        threshold: float = DEFAULT_THRESHOLD,
    ) -> None:
        self._scanner = Scanner(ALL_DETECTORS, threshold=threshold, countries=frozenset(countries))
        super().__init__(
            supported_entities=list(PRESIDIO_NAMES.values()),
            supported_language=supported_language,
            name="EuroPIIRecognizer",
        )

    def load(self) -> None:  # nothing to load
        return None

    def analyze(
        self, text: str, entities: list[str], nlp_artifacts: Any = None
    ) -> list[RecognizerResult]:
        wanted = set(entities) if entities else set(PRESIDIO_NAMES.values())
        results = []
        for f in self._scanner.scan(text):
            name = PRESIDIO_NAMES[f.entity]
            if name in wanted:
                results.append(
                    RecognizerResult(
                        entity_type=name,
                        start=f.start,
                        end=f.end,
                        score=f.score,
                        analysis_explanation=None,
                        recognition_metadata={
                            RecognizerResult.RECOGNIZER_NAME_KEY: self.name,
                            "europii_detector": f.detector,
                            "country": f.country,
                        },
                    )
                )
        return results
