"""Compare EuroPII Guard with Microsoft Presidio on the evaluation set.

    pip install -e ".[presidio]" && python -m spacy download en_core_web_lg
    python scripts/compare.py --data data/test.jsonl --out results/comparison.json

Systems:

* ``presidio_default`` – ``AnalyzerEngine()`` as shipped (English pipeline,
  default recognizers). Presidio needs one spaCy pipeline per language; the
  English one is what most deployments run on mixed-language text.
* ``presidio_eu`` – the same, plus every European country-specific recognizer
  Presidio ships (FI, SE, DE, ES, IT, PL) enabled for English.
* ``presidio_plus_europii`` – ``presidio_default`` plus :class:`EuroPIIRecognizer`.
* ``europii`` – EuroPII Guard alone, no country hint.
* ``europii_hint`` – EuroPII Guard told the country of each message.
* ``europii_recall`` – EuroPII Guard with threshold 0.25 (recall-oriented).
"""

from __future__ import annotations

import argparse
import json
import platform
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from europii import __version__, scan
from europii.bench.evaluate import LABELS, evaluate, load
from europii.bench.templates import COUNTRY

PRESIDIO_MAP = {
    "EMAIL_ADDRESS": "EMAIL",
    "PHONE_NUMBER": "PHONE",
    "IBAN_CODE": "IBAN",
    "CREDIT_CARD": "PAYMENT_CARD",
    "IP_ADDRESS": "IP_ADDRESS",
    "PERSON": "PERSON",
    "EU_VAT_ID": "VAT_ID",
    "IT_VAT_CODE": "VAT_ID",
    "DE_VAT_ID": "VAT_ID",
    "EU_NATIONAL_ID": "NATIONAL_ID",
    "FI_PERSONAL_IDENTITY_CODE": "NATIONAL_ID",
    "SE_PERSONNUMMER": "NATIONAL_ID",
    "PL_PESEL": "NATIONAL_ID",
    "ES_NIF": "NATIONAL_ID",
    "ES_NIE": "NATIONAL_ID",
    "IT_FISCAL_CODE": "NATIONAL_ID",
    "DE_TAX_ID": "NATIONAL_ID",
    "DE_SOCIAL_SECURITY": "NATIONAL_ID",
    "US_SSN": "NATIONAL_ID",
    "UK_NHS": "NATIONAL_ID",
    "UK_NINO": "NATIONAL_ID",
}
EU_RECOGNIZER_PREFIXES = ("Fi", "Se", "Pl", "Es", "It", "De")
STRUCTURED = tuple(label for label in LABELS if label != "PERSON")


def presidio_system(variant: str) -> Callable[[str], list[tuple[int, int, str]]]:
    from presidio_analyzer import AnalyzerEngine, RecognizerRegistry

    analyzer = AnalyzerEngine()
    if variant == "eu":
        from presidio_analyzer import predefined_recognizers as pr

        added = []
        for name in dir(pr):
            cls = getattr(pr, name)
            if (
                isinstance(cls, type)
                and name.startswith(EU_RECOGNIZER_PREFIXES)
                and name.endswith("Recognizer")
            ):
                try:
                    analyzer.registry.add_recognizer(cls(supported_language="en"))
                    added.append(name)
                except TypeError:
                    continue
        print("enabled Presidio EU recognizers:", sorted(added))
    elif variant == "plus_europii":
        from europii.presidio import EuroPIIRecognizer

        analyzer.registry.add_recognizer(EuroPIIRecognizer(supported_language="en"))
    assert isinstance(analyzer.registry, RecognizerRegistry)

    def run(text: str) -> list[tuple[int, int, str]]:
        out = []
        for r in analyzer.analyze(text, language="en"):
            if r.score < 0.5:  # same operating point as EuroPII's default
                continue
            out.append((r.start, r.end, PRESIDIO_MAP.get(r.entity_type, r.entity_type)))
        return out

    return run


def europii_system(
    rows: list[dict[str, Any]], hint: bool, threshold: float = 0.5
) -> Callable[[str], list[tuple[int, int, str]]]:
    lang_of = {r["text"]: r["language"] for r in rows}

    def run(text: str) -> list[tuple[int, int, str]]:
        countries = (COUNTRY[lang_of[text]],) if hint else ()
        return [
            (f.start, f.end, f.entity) for f in scan(text, countries=countries, threshold=threshold)
        ]

    return run


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--systems", nargs="+", default=[
        "presidio_default", "presidio_eu", "presidio_plus_europii", "europii", "europii_hint", "europii_recall"])  # fmt: skip
    args = parser.parse_args()
    rows = load(args.data)
    results: dict[str, Any] = {
        "data": str(args.data),
        "messages": len(rows),
        "europii_version": __version__,
        "python": platform.python_version(),
        "systems": {},
    }
    for name in args.systems:
        if name.startswith("presidio"):
            system = presidio_system(name.removeprefix("presidio_"))
        elif name == "europii":
            system = europii_system(rows, hint=False)
        elif name == "europii_hint":
            system = europii_system(rows, hint=True)
        else:
            system = europii_system(rows, hint=False, threshold=0.25)
        # Run the system once and score the cached output against each label set.
        t0 = time.perf_counter()
        cache = {r["text"]: list(system(r["text"])) for r in rows}
        seconds = time.perf_counter() - t0
        res = {
            "structured": evaluate(rows, cache.__getitem__, STRUCTURED),
            "person": evaluate(rows, cache.__getitem__, ("PERSON",)),
            "all": evaluate(rows, cache.__getitem__, LABELS),
            "seconds": seconds,
            "messages_per_second": len(rows) / seconds,
        }
        results["systems"][name] = res
        s = res["structured"]
        print(name, "structured", json.dumps({k: round(v, 3) for k, v in s["micro"].items() if v is not None}),
              "coverage", round(s["coverage"], 3), "neg", round(s["negatives_flagged_overall"], 3),
              "| person recall", round(res["person"]["micro"]["recall"] or 0, 3),
              "| all coverage", round(res["all"]["coverage"], 3), f"| {res['messages_per_second']:.0f} msg/s", flush=True)  # fmt: skip
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
