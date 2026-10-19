"""Detector definitions.

Validation is delegated to ``python-stdnum`` (national identifiers, VAT, IBAN,
Luhn) and Google's ``libphonenumber`` port ``phonenumbers``, both widely used
and maintained, rather than re-implemented here.
"""

from __future__ import annotations

import ipaddress
import re
from collections.abc import Iterator

import phonenumbers
from stdnum import iban as std_iban
from stdnum import luhn
from stdnum.at import vnr as at_vnr
from stdnum.be import nn as be_nn
from stdnum.bg import egn as bg_egn
from stdnum.cz import rc as cz_rc
from stdnum.de import idnr as de_idnr
from stdnum.dk import cpr as dk_cpr
from stdnum.ee import ik as ee_ik
from stdnum.es import dni as es_dni
from stdnum.es import nie as es_nie
from stdnum.eu import vat as eu_vat
from stdnum.fi import hetu as fi_hetu
from stdnum.fr import nir as fr_nir
from stdnum.hr import oib as hr_oib
from stdnum.ie import pps as ie_pps
from stdnum.it import codicefiscale as it_cf
from stdnum.lt import asmens as lt_asmens
from stdnum.lv import pvn as lv_pvn
from stdnum.nl import bsn as nl_bsn
from stdnum.no import fodselsnummer as no_fnr
from stdnum.pl import pesel as pl_pesel
from stdnum.pt import cc as pt_cc
from stdnum.pt import nif as pt_nif
from stdnum.ro import cnp as ro_cnp
from stdnum.se import personnummer as se_pnr
from stdnum.si import emso as si_emso
from stdnum.sk import rc as sk_rc

from .core import MEDIUM, PHONE_GROUPED, PHONE_PLAIN, STRONG, WEAK, Detector

# Entity types -----------------------------------------------------------------
EMAIL = "EMAIL"
PHONE = "PHONE"
IBAN = "IBAN"
PAYMENT_CARD = "PAYMENT_CARD"
IP_ADDRESS = "IP_ADDRESS"
VAT_ID = "VAT_ID"
NATIONAL_ID = "NATIONAL_ID"

# Context words ----------------------------------------------------------------
# Generic words, then country-specific labels (see COUNTRY_ID_WORDS).
GENERIC_ID_WORDS = (
    "personal id", "national id", "id number", "identity number", "identification number",
    "social security number", "personal number", "personal code", "personal identity code",
    "tax id", "tax identification number", "personal identification number",
    "identification code", "personal identification code", "personal numeric code",
    "national identity number", "national identification number", "citizen number",
)  # fmt: skip
COUNTRY_ID_WORDS: dict[str, tuple[str, ...]] = {
    "FI": ("henkilötunnus", "henkilötunnusta", "henkilötunnuksen", "hetu", "personbeteckning"),
    "SE": ("personnummer", "personnr", "samordningsnummer", "pnr"),
    "NO": ("fødselsnummer", "fodselsnummer", "personnummer", "fnr"),
    "DK": ("cpr", "cpr-nr", "cpr-nummer", "personnummer"),
    "DE": ("steuer-id", "steuer-identifikationsnummer", "steueridentifikationsnummer",
           "identifikationsnummer", "idnr", "steuerliche identifikationsnummer"),
    "FR": ("sécurité sociale", "numéro de sécurité sociale", "nir", "insee", "n° ss"),
    "NL": ("bsn", "burgerservicenummer", "sofinummer"),
    "BE": ("rijksregisternummer", "numéro national", "registre national", "national number", "insz"),
    "ES": ("dni", "nie", "nif", "documento nacional de identidad"),
    "IT": ("codice fiscale", "c.f.", "cod. fisc."),
    "PL": ("pesel",),
    "PT": ("cartão de cidadão", "contribuinte", "número de contribuinte", "nif", "n.º cc"),
    "CZ": ("rodné číslo", "r.č.", "rč"),
    "SK": ("rodné číslo", "r.č.", "rč"),
    "EE": ("isikukood",),
    "LT": ("asmens kodas",),
    "LV": ("personas kods",),
    "AT": ("sozialversicherungsnummer", "svnr", "sv-nummer", "versicherungsnummer"),
    "IE": ("pps", "ppsn", "pps number", "personal public service"),
    "HR": ("oib",),
    "SI": ("emšo", "emso"),
    "RO": ("cnp", "cod numeric personal"),
    "BG": ("егн", "egn"),
}  # fmt: skip
PHONE_WORDS = (
    "phone", "tel", "telephone", "mobile", "mob", "cell", "call", "puh", "puhelin",
    "matkapuhelin", "gsm", "telefon", "mobil", "mobiltelefon", "handy", "rufnummer",
    "téléphone", "tél", "portable", "telefoon", "mobiel", "telefono", "cellulare", "cell.",
    "teléfono", "móvil", "telefone", "telemóvel", "telefonu", "tlf", "tlf.", "nr tel",
    "soita", "ring", "ringer", "anrufen", "rufen sie", "appelez", "appeler", "bel", "bellen",
    "chiamare", "chiamate", "llame", "llamar", "zadzwoń", "ligue", "ligar", "volejte", "fax",
)  # fmt: skip
ACCOUNT_WORDS = (
    "iban", "account", "bank account", "tilinumero", "tili", "konto", "kontonummer",
    "bankkonto", "bankverbindung", "compte", "rib", "rekening", "rekeningnummer", "conto",
    "cuenta", "numer konta", "conta", "nib", "účet", "číslo účtu", "kontonr",
)  # fmt: skip
CARD_WORDS = (
    "card", "credit card", "debit card", "visa", "mastercard", "amex", "kortti",
    "luottokortti", "kort", "kreditkort", "betalkort", "karte", "kreditkarte", "carte",
    "carte bancaire", "cb", "kaart", "creditcard", "carta", "carta di credito", "tarjeta",
    "karta", "karty", "cartão", "kartu",
)  # fmt: skip
VAT_WORDS = (
    "vat", "vat number", "alv", "moms", "momsreg", "ust", "ust-idnr", "umsatzsteuer",
    "tva", "btw", "iva", "partita iva", "nif-iva", "dph", "dič", "nip", "cvr",
)  # fmt: skip


# Candidate patterns -------------------------------------------------------------
def _p(pattern: str, flags: int = 0) -> re.Pattern[str]:
    return re.compile(rf"(?<![\w@]){pattern}(?![\w@])", flags)


EMAIL_RE = re.compile(
    r"(?<![\w.+-])[\w.+-]+\s?(?:@|\((?:at|AT)\)|\[(?:at|AT)\])\s?[\w-]+(?:\.[\w-]+)*\.[A-Za-z]{2,}(?![\w-])"
)
IPV4_RE = _p(r"(?:25[0-5]|2[0-4]\d|1?\d?\d)(?:\.(?:25[0-5]|2[0-4]\d|1?\d?\d)){3}")
IPV6_RE = _p(r"(?:[0-9A-Fa-f]{1,4}:){2,7}[0-9A-Fa-f]{0,4}(?::[0-9A-Fa-f]{1,4}){0,6}")
IBAN_RE = _p(r"[A-Z]{2}\d{2}(?:[ ]?[A-Z0-9]){11,30}")
CARD_RE = _p(r"\d(?:[ -]?\d){12,18}")
VAT_RE = _p(
    r"(?:AT|BE|BG|CY|CZ|DE|DK|EE|EL|ES|FI|FR|HR|HU|IE|IT|LT|LU|LV|MT|NL|PL|PT|RO|SE|SI|SK|XI)"
    r"[ ]?[0-9A-Z](?:[ .]?[0-9A-Z]){6,13}"
)
CARD_PREFIXES = re.compile(
    r"^(?:4|5[1-5]|2(?:2[2-9]|[3-6]\d|7[01]|720)|3[47]|6(?:011|5|4[4-9])|35)"
)

COUNTRY_CODES_EU = (
    "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "ES", "FI", "FR", "GR", "HR", "HU", "IE",
    "IT", "LT", "LU", "LV", "MT", "NL", "PL", "PT", "RO", "SE", "SI", "SK", "NO", "IS", "LI",
)  # fmt: skip


def _ip_finder(text: str, countries: frozenset[str] = frozenset()) -> Iterator[tuple[int, int]]:
    for rx in (IPV4_RE, IPV6_RE):
        for m in rx.finditer(text):
            value = m.group(0)
            try:
                addr = ipaddress.ip_address(value)
            except ValueError:
                continue
            # "1.2.3.4" as a version number is the usual false positive;
            # require at least one octet with two or more digits.
            if isinstance(addr, ipaddress.IPv4Address) and all(
                len(o) == 1 for o in value.split(".")
            ):
                continue
            yield m.start(), m.end()


# Dates and year-prefixed references ("2026-0042") that libphonenumber accepts
# as valid numbers in some region.
DATE_LIKE_RE = re.compile(
    r"^\d{4}[-./]\d{1,2}[-./]\d{1,2}$|^\d{1,2}[-./]\d{1,2}[-./]\d{2,4}$|^(?:19|20)\d{2}[-/]\d{2,6}$"
)


# Optional (0)/(CC) prefix, then digit groups joined by single separators.
PHONE_CANDIDATE_RE = re.compile(
    r"(?<![\w+.,/-])(?:\+|00)?(?:\(\d{1,4}\) ?)?\d{1,5}(?:[ .\-/]?\(?\d{1,5}\)?){1,6}(?![\w.,/-]?\d)"
)
MONEY_AFTER_RE = re.compile(
    r"^\s*(?:[.,]\d{2}(?!\d)|€|kr|zł|kč|eur|sek|dkk|pln|czk)", re.IGNORECASE
)
MONEY_BEFORE_RE = re.compile(r"(?:€|\$|£|kr\.?|eur|sek|dkk)\s*$", re.IGNORECASE)
IPV4_LIKE_RE = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}$")
# "11 987 654", "1.234.567": a number written with thousands separators. Real
# phone numbers grouped 3-3-3 ("512 345 678") start with a three-digit group.
THOUSANDS_RE = re.compile(r"^\d{1,2}(?:[ .\u00a0\u202f]\d{3})+$")
MAX_NATIONAL_DIGITS = 12


def _phone_finder(text: str, countries: frozenset[str] = frozenset()) -> Iterator[tuple[int, int]]:
    """Phone numbers valid for libphonenumber in an EU/EEA country.

    Candidates are digit groups with phone punctuation. Amounts ("3 041,84 €"),
    dates, IPv4 addresses, year-prefixed references and undivided runs of 12+
    digits (barcodes, order numbers) are skipped; national numbers need at
    least seven digits and are parsed with the rules of ``countries`` when the
    caller gives them, otherwise with those of every EU/EEA country.
    """
    regions_national = tuple(sorted(countries)) or COUNTRY_CODES_EU
    for m in PHONE_CANDIDATE_RE.finditer(text):
        raw = m.group(0).rstrip(" .-/(")
        if raw.count(")") > raw.count("("):  # "(Q2: 11 987 654)" - drop the closing bracket
            raw = raw.rstrip(")")
        start, end = m.start(), m.start() + len(raw)
        compact = re.sub(r"\D", "", raw)
        international = raw.startswith(("+", "00"))
        if DATE_LIKE_RE.match(raw) or IPV4_LIKE_RE.match(raw):
            continue
        if MONEY_AFTER_RE.match(text[end : end + 5]) or MONEY_BEFORE_RE.search(
            text[max(0, start - 5) : start]
        ):
            continue
        body = raw.split(" ", 1)[1] if international and " " in raw else raw
        if "." in body and " " in body:  # mixed separators: two adjacent tokens, not one number
            continue
        if not international and (
            len(compact) < 7
            or len(compact) > MAX_NATIONAL_DIGITS
            or (raw.isdigit() and len(compact) >= 12)
            or THOUSANDS_RE.match(raw)
        ):
            continue
        for region in (None,) if international else regions_national:
            try:
                number = phonenumbers.parse(raw, region)
            except phonenumbers.NumberParseException:
                continue
            if phonenumbers.is_valid_number(number):
                yield start, end
                break


def _international(value: str) -> bool:
    return value.lstrip().startswith(("+", "00"))


def _grouped(value: str) -> bool:
    """National number written with phone-style grouping ("040 123 4567")."""
    return bool(re.search(r"\d[ -]\d", value)) or "(" in value


CARD_LENGTHS = (
    (re.compile(r"^3[47]"), (15,)),  # American Express
    (re.compile(r"^4"), (13, 16, 19)),  # Visa
    (re.compile(r"^(?:5[1-5]|2(?:2[2-9]|[3-6]\d|7[01]|720))"), (16,)),  # Mastercard
    (re.compile(r"^(?:6011|65|64[4-9])"), (16, 17, 18, 19)),  # Discover
    (re.compile(r"^35"), (16, 17, 18, 19)),  # JCB
)


def _card_ok(compact: str) -> bool:
    for prefix, lengths in CARD_LENGTHS:
        if prefix.match(compact):
            return len(compact) in lengths and luhn.is_valid(compact)
    return False


def _card_finder(text: str, countries: frozenset[str] = frozenset()) -> Iterator[tuple[int, int]]:
    for m in CARD_RE.finditer(text):
        # Digits that continue an IBAN ("DE89 3704 0044 ...") are not a card.
        if re.search(r"[A-Z]{2}\d{2} ?$", text[max(0, m.start() - 5) : m.start()]):
            continue
        yield m.start(), m.end()


def _vat_ok(compact: str) -> bool:
    return bool(eu_vat.is_valid(compact))


def _hetu_ok(compact: str) -> bool:
    return bool(fi_hetu.is_valid(compact, allow_temporary=True))


def _lv_personal_ok(compact: str) -> bool:
    # stdnum.lv.pvn validates both company VAT numbers and personal codes.
    # Company numbers start with 4-9; personal codes start with a day of birth
    # (0-3) or with "32" (the date-free form issued since 2017).
    return len(compact) == 11 and compact[0] in "0123" and bool(lv_pvn.is_valid(compact))


def _id(name: str, country: str, pattern: str, validator: object, strength: float,
        description: str, flags: int = 0, strip: str = " .-/") -> Detector:  # fmt: skip
    return Detector(
        name=name,
        entity=NATIONAL_ID,
        pattern=_p(pattern, flags),
        strength=strength,
        validate=validator,  # type: ignore[arg-type]
        context=GENERIC_ID_WORDS + COUNTRY_ID_WORDS[country],
        country=country,
        description=description,
        strip=strip,
    )


NATIONAL_DETECTORS = [
    _id("fi_hetu", "FI", r"\d{6}[-+A-FU-Y]\d{3}[0-9A-Y]", _hetu_ok, STRONG,
        "Finnish personal identity code (henkilötunnus)", re.IGNORECASE,
        strip=""),  # "-" is the century sign (born 1900-1999), not a separator
    _id("it_codice_fiscale", "IT", r"[A-Z]{6}[0-9LMNPQRSTUV]{2}[A-EHLMPRST][0-9LMNPQRSTUV]{2}[A-Z][0-9LMNPQRSTUV]{3}[A-Z]",
        it_cf.is_valid, STRONG, "Italian tax code (codice fiscale)", re.IGNORECASE),
    _id("fr_nir", "FR", r"[123478] ?\d{2} ?(?:0[1-9]|1[0-2]|[2-9]\d) ?(?:\d{2}|2[AB]) ?\d{3} ?\d{3} ?\d{2}",
        fr_nir.is_valid, STRONG, "French social security number (NIR)"),
    _id("es_nie", "ES", r"[XYZ]-?\d{7}-?[A-Z]", es_nie.is_valid, STRONG,
        "Spanish foreigner identity number (NIE)", re.IGNORECASE),
    _id("es_dni", "ES", r"\d{8}-?[A-Z]", es_dni.is_valid, STRONG,
        "Spanish national identity number (DNI)", re.IGNORECASE),
    _id("ie_ppsn", "IE", r"\d{7}[A-W][ABWTXZ]?", ie_pps.is_valid, STRONG,
        "Irish Personal Public Service Number (PPSN)", re.IGNORECASE),
    _id("pt_cc", "PT", r"\d{8} ?\d ?[A-Z]{2}\d", pt_cc.is_valid, STRONG,
        "Portuguese citizen card number (cartão de cidadão)", re.IGNORECASE),
    _id("se_personnummer", "SE", r"(?:\d{2})?\d{6}[-+]\d{4}", se_pnr.is_valid, STRONG,
        "Swedish personal identity number (personnummer), with separator"),
    _id("se_personnummer_compact", "SE", r"(?:19|20)\d{10}|\d{10}", se_pnr.is_valid, WEAK,
        "Swedish personal identity number without separator"),
    _id("no_fodselsnummer", "NO", r"\d{6} ?\d{5}", no_fnr.is_valid, MEDIUM,
        "Norwegian national identity number (fødselsnummer)"),
    _id("be_national_number", "BE", r"\d{2}\.?\d{2}\.?\d{2}[- ]?\d{3}\.?\d{2}", be_nn.is_valid, MEDIUM,
        "Belgian national register number"),
    _id("pl_pesel", "PL", r"\d{11}", pl_pesel.is_valid, MEDIUM, "Polish PESEL number"),
    _id("ee_isikukood", "EE", r"[1-8]\d{10}", ee_ik.is_valid, MEDIUM, "Estonian personal identification code"),
    _id("lt_asmens_kodas", "LT", r"[1-8]\d{10}", lt_asmens.is_valid, MEDIUM, "Lithuanian personal code"),
    _id("lv_personas_kods", "LV", r"\d{6}-?\d{5}", _lv_personal_ok, MEDIUM, "Latvian personal code"),
    _id("cz_rodne_cislo", "CZ", r"\d{6}/?\d{3,4}", cz_rc.is_valid, MEDIUM, "Czech birth number (rodné číslo)"),
    _id("sk_rodne_cislo", "SK", r"\d{6}/?\d{3,4}", sk_rc.is_valid, MEDIUM, "Slovak birth number (rodné číslo)"),
    _id("si_emso", "SI", r"\d{13}", si_emso.is_valid, MEDIUM, "Slovenian personal number (EMŠO)"),
    _id("ro_cnp", "RO", r"[1-9]\d{12}", ro_cnp.is_valid, MEDIUM, "Romanian personal numeric code (CNP)"),
    _id("bg_egn", "BG", r"\d{10}", bg_egn.is_valid, MEDIUM, "Bulgarian personal number (EGN)"),
    _id("dk_cpr", "DK", r"\d{6}-?\d{4}", dk_cpr.is_valid, WEAK, "Danish CPR number (no checksum since 2007)"),
    _id("de_steuer_id", "DE", r"\d{2} ?\d{3} ?\d{3} ?\d{3}", de_idnr.is_valid, WEAK, "German tax identification number"),
    _id("nl_bsn", "NL", r"\d{4}\.?\d{2}\.?\d{3}|\d{3}\.\d{3}\.\d{3}|\d{9}", nl_bsn.is_valid, WEAK,
        "Dutch citizen service number (BSN)"),
    _id("at_svnr", "AT", r"\d{4} ?\d{6}", at_vnr.is_valid, WEAK, "Austrian social insurance number"),
    _id("hr_oib", "HR", r"\d{11}", hr_oib.is_valid, WEAK, "Croatian personal identification number (OIB)"),
    _id("pt_nif", "PT", r"[1-35-9]\d{8}", pt_nif.is_valid, WEAK, "Portuguese tax number (NIF)"),
]  # fmt: skip


CONTACT_DETECTORS = [
    Detector("email", EMAIL, EMAIL_RE, STRONG, description="E-mail address, also name(at)domain"),
    Detector(
        "phone_international", PHONE, None, STRONG, context=PHONE_WORDS,
        finder=lambda t, c: ((s, e) for s, e in _phone_finder(t, c) if _international(t[s:e])),
        description="Phone number in international format (+CC or 00CC)",
    ),
    Detector(
        "phone_national", PHONE, None, PHONE_GROUPED, context=PHONE_WORDS,
        finder=lambda t, c: (
            (s, e) for s, e in _phone_finder(t, c) if not _international(t[s:e]) and _grouped(t[s:e])
        ),
        description="Phone number in a national format of an EU/EEA country, grouped",
    ),
    Detector(
        "phone_national_plain", PHONE, None, PHONE_PLAIN, context=PHONE_WORDS,
        finder=lambda t, c: (
            (s, e)
            for s, e in _phone_finder(t, c)
            if not _international(t[s:e]) and not _grouped(t[s:e])
        ),
        description="Undivided digit string that is a valid national phone number",
    ),
    Detector("ip_address", IP_ADDRESS, None, PHONE_GROUPED, finder=_ip_finder,
             description="IPv4 or IPv6 address"),
]  # fmt: skip

FINANCIAL_DETECTORS = [
    Detector("iban", IBAN, IBAN_RE, STRONG, std_iban.is_valid, ACCOUNT_WORDS,
             description="IBAN with valid check digits"),
    Detector("payment_card", PAYMENT_CARD, None, STRONG, _card_ok, CARD_WORDS, strip=" -",
             finder=_card_finder, description="Payment card number (issuer prefix, length, Luhn)"),
    Detector("eu_vat", VAT_ID, VAT_RE, STRONG, _vat_ok, VAT_WORDS,
             description="EU VAT identification number with valid checksum"),
]  # fmt: skip

ALL_DETECTORS: list[Detector] = [*CONTACT_DETECTORS, *FINANCIAL_DETECTORS, *NATIONAL_DETECTORS]
