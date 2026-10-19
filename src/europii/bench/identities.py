"""Synthetic identifiers for the evaluation set.

Every *valid* value passes the same stdnum validator the detector uses. To
avoid producing the identifier of a living person, identifiers that encode a
birth date use dates no living person can have: dates in the future
(Finland, Poland, Estonia, Lithuania, Czechia, Slovakia, Slovenia, Romania,
Bulgaria) or in the early 19th century, before the numbering schemes existed
(Sweden, Norway, Denmark, Latvia), or 1900–1905 (Belgium, whose scheme cannot
encode other centuries in the 1900 form). Identifiers without a date (DE, NL,
ES, PT, IE, HR, AT, FR, IT) are random checksum-valid numbers; they may
coincide with an issued number, but nothing else in the dataset relates to
any real person. Payment cards use the public test numbers of the card
networks, e-mail addresses the reserved ``example.*`` domains (RFC 2606).

*Invalid* look-alikes have the same layout but fail the checksum or the date
check; they are the hard negatives of the benchmark.
"""

from __future__ import annotations

import random
import string
from collections.abc import Callable

from ..detectors import NATIONAL_DETECTORS

_DETECTOR = {d.name: d for d in NATIONAL_DETECTORS}


def _digits(rng: random.Random, n: int) -> str:
    return "".join(str(rng.randint(0, 9)) for _ in range(n))


def _dd_mm(rng: random.Random) -> tuple[int, int]:
    return rng.randint(1, 28), rng.randint(1, 12)


def _luhn_digit(body: str) -> str:
    total = 0
    for i, ch in enumerate(reversed(body)):
        d = int(ch) * (2 if i % 2 == 0 else 1)
        total += d - 9 if d > 9 else d
    return str((10 - total % 10) % 10)


def _fi(rng: random.Random) -> str:
    d, m = _dd_mm(rng)
    body = f"{d:02d}{m:02d}{rng.randint(80, 99)}"
    ind = f"{rng.randint(2, 899):03d}"
    check = "0123456789ABCDEFHJKLMNPRSTUVWXY"[int(body + ind) % 31]
    return f"{body}A{ind}{check}"  # born 2080–2099


def _se(rng: random.Random) -> str:
    d, m = _dd_mm(rng)
    body = f"{rng.randint(10, 39):02d}{m:02d}{d:02d}{_digits(rng, 3)}"
    return f"{body[:6]}+{body[6:]}{_luhn_digit(body)}"  # "+": born 1810–1839


def _no(rng: random.Random) -> str:
    while True:
        d, m = _dd_mm(rng)
        n9 = f"{d:02d}{m:02d}{rng.randint(54, 59)}{rng.randint(500, 749)}"  # 1854–1859
        w1 = [3, 7, 6, 1, 8, 9, 4, 5, 2]
        k1 = (11 - sum(int(a) * b for a, b in zip(n9, w1, strict=True)) % 11) % 11
        if k1 == 10:
            continue
        n10 = n9 + str(k1)
        w2 = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
        k2 = (11 - sum(int(a) * b for a, b in zip(n10, w2, strict=True)) % 11) % 11
        if k2 != 10:
            return f"{n10[:6]} {n10[6:]}{k2}"


def _dk(rng: random.Random) -> str:
    d, m = _dd_mm(rng)
    # 7th digit 5–8 with year 58–99 means 1858–1899.
    return f"{d:02d}{m:02d}{rng.randint(58, 62)}-{rng.randint(5, 8)}{_digits(rng, 3)}"


def _pl(rng: random.Random) -> str:
    d, m = _dd_mm(rng)
    body = f"{rng.randint(10, 99):02d}{m + 40:02d}{d:02d}{_digits(rng, 4)}"  # 2110–2199
    w = [1, 3, 7, 9, 1, 3, 7, 9, 1, 3]
    return body + str((10 - sum(int(a) * b for a, b in zip(body, w, strict=True)) % 10) % 10)


def _ee_like(rng: random.Random) -> str:
    d, m = _dd_mm(rng)
    n = f"{rng.choice('78')}{rng.randint(10, 99):02d}{m:02d}{d:02d}{_digits(rng, 3)}"  # 2110–2199
    w1 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 1]
    s = sum(int(a) * b for a, b in zip(n, w1, strict=True)) % 11
    if s == 10:
        w2 = [3, 4, 5, 6, 7, 8, 9, 1, 2, 3]
        s = sum(int(a) * b for a, b in zip(n, w2, strict=True)) % 11 % 10
    return n + str(s)


def _cz_sk(rng: random.Random) -> str:
    while True:
        d, m = _dd_mm(rng)
        body = f"{rng.randint(27, 53):02d}{m + rng.choice((0, 50)):02d}{d:02d}{_digits(rng, 3)}"
        for last in range(10):  # 10-digit numbers with YY < 54 are born 2027–2053
            if int(body + str(last)) % 11 == 0:
                return f"{body[:6]}/{body[6:]}{last}"


def _si(rng: random.Random) -> str:
    while True:
        d, m = _dd_mm(rng)
        n = f"{d:02d}{m:02d}{rng.randint(80, 99):03d}50{rng.randint(0, 499):03d}"  # 2080–2099
        w = [7, 6, 5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
        c = (11 - sum(int(a) * b for a, b in zip(n, w, strict=True)) % 11) % 11
        if c < 10:
            return n + str(c)


def _ro(rng: random.Random) -> str:
    d, m = _dd_mm(rng)
    n = f"{rng.choice('56')}{rng.randint(80, 99)}{m:02d}{d:02d}{rng.randint(1, 46):02d}{_digits(rng, 3)}"
    w = [2, 7, 9, 1, 4, 6, 3, 5, 8, 2, 7, 9]
    c = sum(int(a) * b for a, b in zip(n, w, strict=True)) % 11
    return n + ("1" if c == 10 else str(c))  # 2080–2099


def _bg(rng: random.Random) -> str:
    d, m = _dd_mm(rng)
    n = f"{rng.randint(80, 99)}{m + 40:02d}{d:02d}{_digits(rng, 3)}"  # 2080–2099
    w = [2, 4, 8, 5, 10, 9, 7, 3, 6]
    return n + str(sum(int(a) * b for a, b in zip(n, w, strict=True)) % 11 % 10)


def _lv(rng: random.Random) -> str:
    while True:
        d, m = _dd_mm(rng)
        b = f"{d:02d}{m:02d}{rng.randint(10, 60):02d}0{_digits(rng, 3)}"  # century digit 0: 1800s
        w = [1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
        c = (1101 - sum(int(a) * x for a, x in zip(b, w, strict=True))) % 11
        if c < 10:
            return f"{b[:6]}-{b[6:]}{c}"


def _be(rng: random.Random) -> str:
    d, m = _dd_mm(rng)
    body = f"{rng.randint(0, 5):02d}{m:02d}{d:02d}{rng.randint(1, 997):03d}"  # 1900–1905
    check = 97 - int(body) % 97
    return f"{body[:2]}.{body[2:4]}.{body[4:6]}-{body[6:]}.{check:02d}"


def _random_valid(
    name: str, make: Callable[[random.Random], str]
) -> Callable[[random.Random], str]:
    det = _DETECTOR[name]

    def gen(rng: random.Random) -> str:
        for _ in range(100_000):
            value = make(rng)
            if det.check(value):
                return value
        raise RuntimeError(f"no valid value for {name}")

    return gen


def _de_raw(rng: random.Random) -> str:
    n = f"{rng.randint(1, 9)}{_digits(rng, 10)}"
    return f"{n[:2]} {n[2:5]} {n[5:8]} {n[8:]}"


def _nl_raw(rng: random.Random) -> str:
    n = _digits(rng, 9)
    return rng.choice((n, f"{n[:4]}.{n[4:6]}.{n[6:]}"))


def _it_raw(rng: random.Random) -> str:
    cons = "BCDFGHLMNPRSTVZ"
    letters = "".join(rng.choice(cons) for _ in range(6))
    month = rng.choice("ABCDEHLMPRST")
    day = rng.randint(1, 28) + rng.choice((0, 40))
    town = rng.choice("ABCDEFGHLM") + f"{rng.randint(1, 999):03d}"
    body = f"{letters}{rng.randint(0, 99):02d}{month}{day:02d}{town}"
    return body + rng.choice(string.ascii_uppercase)


def _fr_raw(rng: random.Random) -> str:
    body = f"{rng.choice('12')}{rng.randint(0, 99):02d}{rng.randint(1, 12):02d}{rng.randint(1, 95):02d}{_digits(rng, 6)}"
    key = 97 - int(body) % 97
    return f"{body[0]} {body[1:3]} {body[3:5]} {body[5:7]} {body[7:10]} {body[10:]} {key:02d}"


def _pt_cc(rng: random.Random) -> str:
    from stdnum.pt import cc

    body = (
        f"{_digits(rng, 9)}{rng.choice(string.ascii_uppercase)}{rng.choice(string.ascii_uppercase)}"
    )
    return f"{body[:8]} {body[8]} {body[9:]}{cc.calc_check_digit(body)}"


def _at_raw(rng: random.Random) -> str:
    d, m = _dd_mm(rng)
    return f"{rng.randint(1, 9)}{_digits(rng, 3)} {d:02d}{m:02d}{rng.randint(40, 99)}"


GENERATORS: dict[str, Callable[[random.Random], str]] = {
    "pt_cc": _pt_cc,
    "fi_hetu": _fi,
    "se_personnummer": _se,
    "no_fodselsnummer": _no,
    "dk_cpr": _dk,
    "pl_pesel": _pl,
    "ee_isikukood": _ee_like,
    "lt_asmens_kodas": _ee_like,
    "cz_rodne_cislo": _cz_sk,
    "sk_rodne_cislo": _cz_sk,
    "si_emso": _si,
    "ro_cnp": _ro,
    "bg_egn": _bg,
    "lv_personas_kods": _lv,
    "be_national_number": _be,
    "de_steuer_id": _random_valid("de_steuer_id", _de_raw),
    "nl_bsn": _random_valid("nl_bsn", _nl_raw),
    "it_codice_fiscale": _random_valid("it_codice_fiscale", _it_raw),
    "fr_nir": _fr_raw,
    "es_dni": lambda r: (lambda n: f"{n}{'TRWAGMYFPDXBNJZSQVHLCKE'[int(n) % 23]}")(_digits(r, 8)),
    "es_nie": lambda r: (
        lambda p, n: f"{p}{n}{'TRWAGMYFPDXBNJZSQVHLCKE'[int(str('XYZ'.index(p)) + n) % 23]}"
    )(r.choice("XYZ"), _digits(r, 7)),
    "ie_ppsn": _random_valid("ie_ppsn", lambda r: f"{_digits(r, 7)}{r.choice('ABCDEFGHJKLMNPQRSTVW')}"),
    "pt_nif": _random_valid("pt_nif", lambda r: f"{r.choice('123')}{_digits(r, 8)}"),
    "hr_oib": _random_valid("hr_oib", lambda r: f"{r.randint(1, 9)}{_digits(r, 10)}"),
    "at_svnr": _random_valid("at_svnr", lambda r: _at_raw(r)),
}  # fmt: skip


def valid_id(name: str, rng: random.Random) -> str:
    value = GENERATORS[name](rng)
    if not _DETECTOR[name].check(value):
        raise AssertionError(f"generated {name} {value!r} does not validate")
    return value


def invalid_id(name: str, rng: random.Random) -> str:
    """Same layout as a valid identifier, but failing validation."""
    det = _DETECTOR[name]
    if name == "dk_cpr":  # no checksum since 2007: only an impossible date fails
        value = GENERATORS[name](rng)
        return f"{value[:2]}{rng.randint(13, 19)}{value[4:]}"
    for _ in range(1000):
        chars = list(GENERATORS[name](rng))
        positions = [i for i, ch in enumerate(chars) if ch.isdigit()]
        i = rng.choice(positions[-3:])
        chars[i] = str((int(chars[i]) + rng.randint(1, 9)) % 10)
        candidate = "".join(chars)
        if not det.check(candidate):
            return candidate
    raise RuntimeError(f"could not make an invalid {name}")
