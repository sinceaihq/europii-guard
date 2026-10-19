from __future__ import annotations

import pytest

presidio = pytest.importorskip("presidio_analyzer")
pytestmark = pytest.mark.presidio


def test_recognizer_adds_european_entities() -> None:
    from presidio_analyzer import AnalyzerEngine
    from presidio_analyzer.nlp_engine import NlpEngineProvider

    from europii.presidio import EuroPIIRecognizer

    try:
        nlp = NlpEngineProvider(
            nlp_configuration={
                "nlp_engine_name": "spacy",
                "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
            }
        ).create_engine()
    except OSError:
        pytest.skip("spaCy model en_core_web_sm is not installed")
    analyzer = AnalyzerEngine(nlp_engine=nlp, supported_languages=["en"])
    analyzer.registry.add_recognizer(EuroPIIRecognizer(supported_language="en"))
    text = "Henkilötunnus 150685A123D, USt-IdNr. DE136695976."
    results = analyzer.analyze(text, language="en", entities=["EU_NATIONAL_ID", "EU_VAT_ID"])
    found = {(r.entity_type, text[r.start : r.end]) for r in results}
    assert ("EU_NATIONAL_ID", "150685A123D") in found
    assert ("EU_VAT_ID", "DE136695976") in found
