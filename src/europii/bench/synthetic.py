"""Generate the EuroPII evaluation set.

    python -m europii.bench.synthetic --out data --seed 2026

Writes ``dev.jsonl`` and ``test.jsonl``; each line is a message with
character-offset annotations::

    {"id": ..., "language": "fi", "template": 1, "text": "...",
     "spans": [{"start": 10, "end": 21, "label": "NATIONAL_ID", "detector": "fi_hetu"}, ...],
     "negatives": [{"start": .., "end": .., "kind": "ORDER"}, ...]}
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import random
import re
import string
import unicodedata
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import phonenumbers
from stdnum import ean as std_ean
from stdnum import iban as std_iban
from stdnum.eu import vat as eu_vat

from ..detectors import NATIONAL_DETECTORS
from .identities import invalid_id, valid_id
from .templates import COUNTRY, FIRST_NAMES, FOREIGN_TEMPLATES, LAST_NAMES, LOCAL_ID, TEMPLATES

PII_SLOTS = {
    "NAME": "PERSON",
    "EMAIL": "EMAIL",
    "PHONE": "PHONE",
    "PHONE_INTL": "PHONE",
    "IBAN": "IBAN",
    "CARD": "PAYMENT_CARD",
    "ID": "NATIONAL_ID",
    "VAT": "VAT_ID",
    "IP": "IP_ADDRESS",
}
NEGATIVE_SLOTS = ("ORDER", "INVOICE", "DATE", "AMOUNT", "BAD_ID", "BAD_IBAN", "EAN", "POSTCODE")
# A row from an exported contact list: no labels at all, so detectors must
# rely on the value alone.
UNLABELLED_TEMPLATE = "{NAME}; {ID}; {EMAIL}; {PHONE}"

# Public test card numbers published by the card networks / payment providers.
TEST_CARDS = (
    "4111 1111 1111 1111", "4012 8888 8888 1881", "5555 5555 5555 4444", "5105 1051 0510 5100",
    "3782 822463 10005", "3714 496353 98431", "6011 1111 1111 1117", "4000 0566 5566 5556",
)  # fmt: skip
EMAIL_DOMAINS = ("example.com", "example.org", "example.net", "mail.example.com")
IBAN_LENGTH = {"IE": 22, "FI": 18, "SE": 24, "DE": 22, "FR": 27, "NL": 18, "IT": 27,
               "ES": 24, "PL": 28, "PT": 25, "CZ": 24, "DK": 18}  # fmt: skip
VAT_BODY = {"IE": "7dL", "FI": "8d", "SE": "10d01", "DE": "9d", "FR": "11d", "NL": "9dB01",
            "IT": "11d", "ES": "L7d1d", "PL": "10d", "PT": "9d", "CZ": "8d", "DK": "8d"}  # fmt: skip
DATE_FORMATS = {"en": "%d/%m/%Y", "fi": "%-d.%-m.%Y", "sv": "%Y-%m-%d", "de": "%d.%m.%Y",
                "fr": "%d/%m/%Y", "nl": "%d-%m-%Y", "it": "%d/%m/%Y", "es": "%d/%m/%Y",
                "pl": "%d.%m.%Y", "pt": "%d/%m/%Y", "cs": "%-d. %-m. %Y", "da": "%d.%m.%Y"}  # fmt: skip
POSTCODES = {"IE": "D02 X285", "FI": "00100", "SE": "114 55", "DE": "10115", "FR": "75001",
             "NL": "1012 AB", "IT": "20121", "ES": "28013", "PL": "00-950", "PT": "1100-148",
             "CZ": "110 00", "DK": "1050"}  # fmt: skip


def _digits(rng: random.Random, n: int) -> str:
    return "".join(str(rng.randint(0, 9)) for _ in range(n))


def _ascii(name: str) -> str:
    """E-mail local part from a name: strip diacritics, keep letters and dots."""
    special = {"ß": "ss", "ł": "l", "ø": "o", "æ": "ae", "đ": "d", "'": ""}
    text = "".join(special.get(ch, ch) for ch in name.lower())
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z.]", "", text.replace(" ", "."))


def person(rng: random.Random, lang: str) -> str:
    return f"{rng.choice(FIRST_NAMES[lang])} {rng.choice(LAST_NAMES[lang])}"


def email(rng: random.Random, name: str) -> str:
    first, last = name.split(" ", 1)
    local = rng.choice((f"{first}.{last}", f"{first[0]}{last}", f"{first}{rng.randint(1, 99)}"))
    return f"{_ascii(local)}@{rng.choice(EMAIL_DOMAINS)}"


def phone(rng: random.Random, country: str, international: bool) -> str:
    example = phonenumbers.example_number_for_type(country, phonenumbers.PhoneNumberType.MOBILE)
    assert example is not None, country
    national = str(example.national_number)
    for _ in range(1000):
        candidate = national[:3] + _digits(rng, len(national) - 3)
        num = phonenumbers.parse(candidate, country)
        if phonenumbers.is_valid_number(num):
            fmt = (
                phonenumbers.PhoneNumberFormat.INTERNATIONAL
                if international
                else phonenumbers.PhoneNumberFormat.NATIONAL
            )
            return phonenumbers.format_number(num, fmt)
    raise RuntimeError(f"no valid phone number for {country}")


# BBAN layouts (a = letter, n = digit, c = alphanumeric) from the IBAN registry.
BBAN_LAYOUT = {"IE": "aaaannnnnnnnnnnnnn", "IT": "annnnnnnnnnnnnnnnnnnnnn", "NL": "aaaannnnnnnnnn"}


def iban(rng: random.Random, country: str, valid: bool = True) -> str:
    """IBAN that passes stdnum's checks, including national check digits (ES, FR, PT...)."""
    n = IBAN_LENGTH[country] - 4
    layout = BBAN_LAYOUT.get(country, "n" * n)
    for _ in range(100_000):
        bban = "".join(
            rng.choice(string.ascii_uppercase) if ch == "a" else str(rng.randint(0, 9))
            for ch in layout
        )
        value = country + std_iban.calc_check_digits(country + "00" + bban) + bban
        if std_iban.is_valid(value):
            break
    else:
        raise RuntimeError(f"no valid IBAN for {country}")
    if not valid:
        check = f"{(int(value[2:4]) + rng.randint(1, 50)) % 97 + 2:02d}"
        value = value[:2] + check + value[4:]
        assert not std_iban.is_valid(value)
    return " ".join(value[i : i + 4] for i in range(0, len(value), 4))


def vat(rng: random.Random, country: str) -> str:
    pattern = VAT_BODY[country]
    for _ in range(100_000):
        body = re.sub(r"(\d+)d", lambda m: _digits(rng, int(m[1])), pattern)
        body = body.replace("L", rng.choice("ABCDEFGHJKLMNPQRSTUVW"))
        if eu_vat.is_valid(country + body):
            return country + body
    raise RuntimeError(f"no valid VAT number for {country}")


def ean13(rng: random.Random) -> str:
    body = f"{rng.choice(('400', '590', '640', '730', '800', '871'))}{_digits(rng, 9)}"
    return body + std_ean.calc_check_digit(body)


def ip(rng: random.Random) -> str:
    if rng.random() < 0.8:
        first = rng.choice((10, 172, 192, 85, 91, 213))
        return f"{first}.{rng.randint(0, 255)}.{rng.randint(0, 255)}.{rng.randint(1, 254)}"
    return f"2001:db8:{rng.randint(0, 65535):x}::{rng.randint(1, 65535):x}"  # documentation prefix


def amount(rng: random.Random, lang: str) -> str:
    value = rng.randint(1000, 999_999) / 100
    whole, cents = f"{value:.2f}".split(".")
    if lang == "en":
        return f"€{int(whole):,}.{cents}"
    sep = {"de": ".", "nl": ".", "it": ".", "es": ".", "da": "."}.get(lang, " ")
    grouped = f"{int(whole):,}".replace(",", sep)
    unit = {"sv": "kr", "pl": "zł", "cs": "Kč", "da": "kr."}.get(lang, "€")
    return f"{grouped},{cents} {unit}"


def date(rng: random.Random, lang: str) -> str:
    d = dt.date(2025, 1, 1) + dt.timedelta(days=rng.randint(0, 600))
    return d.strftime(DATE_FORMATS[lang])


def fill(
    template: str, values: dict[str, str]
) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]]]:
    text, spans, negatives = "", [], []
    pos = 0
    for m in re.finditer(r"\{([A-Z_]+)\}", template):
        text += template[pos : m.start()]
        slot = m.group(1)
        value = values[slot]
        start, end = len(text), len(text) + len(value)
        text += value
        if slot in PII_SLOTS:
            span = {"start": start, "end": end, "label": PII_SLOTS[slot]}
            if slot == "ID":
                span["detector"] = values["_ID_DETECTOR"]
            spans.append(span)
        else:
            negatives.append({"start": start, "end": end, "kind": slot})
        pos = m.end()
    text += template[pos:]
    return text, spans, negatives


def make_values(rng: random.Random, lang: str, id_detector: str) -> dict[str, str]:
    country = COUNTRY[lang]
    name = person(rng, lang)
    return {
        "NAME": name,
        "EMAIL": email(rng, name),
        "PHONE": phone(rng, country, international=False),
        "PHONE_INTL": phone(rng, country, international=True),
        "IBAN": iban(rng, country),
        "CARD": rng.choice(TEST_CARDS),
        "ID": valid_id(id_detector, rng),
        "_ID_DETECTOR": id_detector,
        "VAT": vat(rng, country),
        "IP": ip(rng),
        "ORDER": _digits(rng, rng.choice((8, 9, 10, 11, 12))),
        "INVOICE": rng.choice(
            (f"{rng.randint(2024, 2026)}-{_digits(rng, 4)}", f"INV-{_digits(rng, 6)}")
        ),
        "DATE": date(rng, lang),
        "AMOUNT": amount(rng, lang),
        "BAD_ID": invalid_id(LOCAL_ID[lang][0], rng),
        "BAD_IBAN": iban(rng, country, valid=False),
        "EAN": ean13(rng),
        "POSTCODE": POSTCODES[country],
    }


def generate(seed: int, per_template: int) -> list[dict[str, Any]]:
    rows = []
    for lang, templates in TEMPLATES.items():
        for t_index, template in enumerate([*templates, UNLABELLED_TEMPLATE]):
            for i in range(per_template):
                rng = random.Random(f"{seed}:{lang}:{t_index}:{i}")
                det = rng.choice(LOCAL_ID[lang])
                text, spans, negatives = fill(template, make_values(rng, lang, det))
                rows.append(
                    {"id": f"{lang}-{t_index}-{i:03d}", "language": lang, "template": t_index,
                     "text": text, "spans": spans, "negatives": negatives}
                )  # fmt: skip
    for det, templates in FOREIGN_TEMPLATES.items():
        for t_index, template in enumerate(templates):
            for i in range(per_template):
                rng = random.Random(f"{seed}:foreign:{det}:{i}")
                text, spans, negatives = fill(template, make_values(rng, "en", det))
                rows.append(
                    {"id": f"en-{det}-{i:03d}", "language": "en", "template": f"foreign-{t_index}",
                     "text": text, "spans": spans, "negatives": negatives}
                )  # fmt: skip
    return rows


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Generate the EuroPII evaluation set.")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--dev", type=int, default=5, help="messages per template in dev")
    parser.add_argument("--test", type=int, default=25, help="messages per template in test")
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    for split, n, seed in (("dev", args.dev, args.seed + 1), ("test", args.test, args.seed)):
        rows = generate(seed, n)
        with (args.out / f"{split}.jsonl").open("w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(split, len(rows))
    assert {d.name for d in NATIONAL_DETECTORS} >= set(FOREIGN_TEMPLATES)


if __name__ == "__main__":
    main()
