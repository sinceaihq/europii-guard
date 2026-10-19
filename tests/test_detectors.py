from __future__ import annotations

import random

import pytest

from europii import redact, scan
from europii.bench.identities import GENERATORS, invalid_id, valid_id
from europii.core import Finding, resolve_overlaps
from europii.detectors import ALL_DETECTORS, COUNTRY_ID_WORDS, NATIONAL_DETECTORS

ID_LABEL = {
    "fi_hetu": "henkilötunnus", "se_personnummer": "personnummer", "no_fodselsnummer": "fødselsnummer",
    "dk_cpr": "CPR-nr.", "de_steuer_id": "Steuer-ID", "fr_nir": "numéro de sécurité sociale",
    "nl_bsn": "BSN", "be_national_number": "rijksregisternummer", "es_dni": "DNI", "es_nie": "NIE",
    "it_codice_fiscale": "codice fiscale", "pl_pesel": "PESEL", "pt_cc": "cartão de cidadão",
    "pt_nif": "NIF", "cz_rodne_cislo": "rodné číslo", "sk_rodne_cislo": "rodné číslo",
    "ee_isikukood": "isikukood", "lt_asmens_kodas": "asmens kodas", "lv_personas_kods": "personas kods",
    "at_svnr": "SVNR", "ie_ppsn": "PPSN", "hr_oib": "OIB", "si_emso": "EMŠO", "ro_cnp": "CNP", "bg_egn": "EGN",
}  # fmt: skip


@pytest.mark.parametrize("name", sorted(GENERATORS))
def test_labelled_valid_ids_are_found(name: str) -> None:
    rng = random.Random(name)
    for _ in range(20):
        value = valid_id(name, rng)
        text = f"Customer record. {ID_LABEL[name]}: {value}. Thank you."
        found = [f for f in scan(text) if f.entity == "NATIONAL_ID"]
        assert found, text
        assert found[0].text == value
        assert found[0].context


@pytest.mark.parametrize("name", sorted(GENERATORS))
def test_invalid_look_alikes_are_not_national_ids(name: str) -> None:
    rng = random.Random(f"bad-{name}")
    for _ in range(20):
        text = f"{ID_LABEL[name]}: {invalid_id(name, rng)}"
        assert not [f for f in scan(text) if f.entity == "NATIONAL_ID" and f.detector == name], text


def test_every_national_detector_has_a_generator_and_labels() -> None:
    names = {d.name for d in NATIONAL_DETECTORS} - {"se_personnummer_compact"}
    assert names == set(GENERATORS)
    assert {d.country for d in NATIONAL_DETECTORS} <= set(COUNTRY_ID_WORDS)


@pytest.mark.parametrize(
    ("text", "entity", "value"),
    [
        ("Write to anna.virtanen@example.com today", "EMAIL", "anna.virtanen@example.com"),
        ("Write to anna(at)example.org today", "EMAIL", "anna(at)example.org"),
        ("Call +358 40 123 4567 tomorrow", "PHONE", "+358 40 123 4567"),
        ("puh. 040 123 4567", "PHONE", "040 123 4567"),
        ("Tel.: 030 12345678", "PHONE", "030 12345678"),
        ("IBAN DE89 3704 0044 0532 0130 00", "IBAN", "DE89 3704 0044 0532 0130 00"),
        ("Karte 4111 1111 1111 1111", "PAYMENT_CARD", "4111 1111 1111 1111"),
        ("USt-IdNr. DE136695976", "VAT_ID", "DE136695976"),
        ("from 192.168.10.25 at noon", "IP_ADDRESS", "192.168.10.25"),
        ("from 2001:db8::1 at noon", "IP_ADDRESS", "2001:db8::1"),
    ],
)
def test_contact_and_financial(text: str, entity: str, value: str) -> None:
    found = [f for f in scan(text) if f.entity == entity]
    assert [f.text for f in found] == [value]


@pytest.mark.parametrize(
    "text",
    [
        "Order 4000123456 shipped on 2026-03-05.",
        "Invoice 2026-0042 totals 3 041,84 € incl. VAT.",
        "Amount due: €1,234.56 by 05/03/2026.",
        "Version 1.2.3.4 is installed.",
        "EAN 4006381333931, postcode 00100.",
        "IBAN DE89 3704 0044 0532 0130 01 (typo).",  # wrong check digits
        "Card 4111 1111 1111 1112 was declined.",  # fails Luhn
    ],
)
def test_business_numbers_are_not_pii(text: str) -> None:
    assert scan(text) == [], [(f.entity, f.text) for f in scan(text)]


def test_digit_only_ids_need_a_label_or_a_country_hint() -> None:
    pesel = valid_id("pl_pesel", random.Random(1))
    assert not scan(f"Kowalski; {pesel}; kowalski@example.com")[:-1] or all(
        f.entity != "NATIONAL_ID" for f in scan(f"Kowalski; {pesel}")
    )
    assert any(f.entity == "NATIONAL_ID" for f in scan(f"Kowalski; {pesel}", countries=["PL"]))
    assert any(f.entity == "NATIONAL_ID" for f in scan(f"PESEL {pesel}"))


def test_threshold_controls_recall() -> None:
    bsn = valid_id("nl_bsn", random.Random(2)).replace(".", "")
    text = f"Jansen; {bsn}"
    assert not [f for f in scan(text) if f.entity == "NATIONAL_ID"]
    assert [f for f in scan(text, threshold=0.25) if f.entity == "NATIONAL_ID"]


def test_entities_filter() -> None:
    text = "mail anna@example.com, tel. +358 40 123 4567"
    assert {f.entity for f in scan(text, entities=["EMAIL"])} == {"EMAIL"}


def test_redact_styles() -> None:
    text = "Contact anna@example.com or anna@example.com."
    assert redact(text) == "Contact <EMAIL> or <EMAIL>."
    assert redact(text, style="mask") == "Contact " + "*" * 16 + " or " + "*" * 16 + "."
    hashed = redact(text, style="hash")
    tokens = [t for t in hashed.split() if t.startswith("<EMAIL:")]
    assert len(tokens) == 2
    assert tokens[0].rstrip(".") == tokens[1].rstrip(".")
    with pytest.raises(ValueError, match="style"):
        redact(text, style="nope")


def test_resolve_overlaps_prefers_score_then_length() -> None:
    a = Finding("A", 0, 10, "x" * 10, 0.6, "a")
    b = Finding("B", 5, 8, "x" * 3, 0.9, "b")
    c = Finding("C", 12, 20, "x" * 8, 0.5, "c")
    assert resolve_overlaps([a, b, c]) == [b, c]


def test_findings_are_serialisable() -> None:
    f = scan("anna@example.com")[0]
    d = f.to_dict()
    assert d["entity"] == "EMAIL"
    assert d["start"] == 0


def test_empty_and_unicode_text() -> None:
    assert scan("") == []
    assert scan("Ääkköset ja emoji 🚀 ilman henkilötietoja.") == []


def test_detector_names_are_unique() -> None:
    names = [d.name for d in ALL_DETECTORS]
    assert len(names) == len(set(names))
