# EuroPII Guard

**Find and redact European personal data locally, before text is sent to an AI service.**

[![CI](https://github.com/sinceaihq/europii-guard/actions/workflows/ci.yml/badge.svg)](https://github.com/sinceaihq/europii-guard/actions/workflows/ci.yml)
[![Demo](https://img.shields.io/badge/%F0%9F%A4%97%20demo-in%20your%20browser-yellow)](https://huggingface.co/spaces/sinceaihq/europii-guard-demo)
[![Dataset](https://img.shields.io/badge/%F0%9F%A4%97%20dataset-europii--bench-yellow)](https://huggingface.co/datasets/sinceaihq/europii-bench)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)

General-purpose PII tools are built around US and UK identifiers. In European
text they miss national identity numbers, tax numbers and locally written
phone numbers. EuroPII Guard detects them with the **official checksum
rules** of each country:

| | |
|---|---|
| national IDs (22 countries) | AT SVNR · BE national number · BG EGN · CZ/SK rodné číslo · DE Steuer-ID · DK CPR · EE isikukood · ES DNI/NIE · FI henkilötunnus · FR NIR · HR OIB · IE PPSN · IT codice fiscale · LT asmens kodas · LV personas kods · NL BSN · NO fødselsnummer · PL PESEL · PT CC/NIF · RO CNP · SE personnummer · SI EMŠO |
| financial | IBAN (all countries) · EU VAT numbers (all member states) · payment cards (issuer, length, Luhn) |
| contact | e-mail (also `name(at)domain`) · phone numbers in EU/EEA national and international formats · IPv4/IPv6 |

It is a small, pure-Python library (dependencies: `python-stdnum`,
`phonenumbers`), runs offline, scans hundreds of messages per second on one
CPU core, and plugs into [Microsoft Presidio](https://github.com/microsoft/presidio)
when you also need names and other NLP-based entities.

> **Privacy assistance, not a guarantee.** EuroPII Guard does not detect
> names or postal addresses by itself, cannot find every piece of personal
> data, and using it does not make any processing GDPR-compliant. Treat it as
> one safeguard among others, and review what it misses on your own data.

## Install

```bash
pip install "europii-guard @ git+https://github.com/sinceaihq/europii-guard@v0.1.0"
```

## Use

```python
from europii import scan, redact

text = "Asiakas Aino Korhonen, henkilötunnus 150685A123D, puh. 040 123 4567, IBAN FI21 1234 5600 0007 85."
for f in scan(text):
    print(f.entity, f.text, f.detector, f.score)

print(redact(text))
# Asiakas Aino Korhonen, henkilötunnus <NATIONAL_ID>, puh. <PHONE>, IBAN <IBAN>.
```

* `countries=["FI", "SE"]` tells the scanner which countries to expect. Digit-only
  identifiers (e.g. a PESEL with no "PESEL" label next to it) and national
  phone formats are then trusted more, and precision improves.
* `threshold` (default 0.5) trades precision for recall; 0.25 hides more at
  the cost of more false alarms (see results below).
* `redact(..., style="hash")` replaces values by stable tokens such as
  `<EMAIL:3f2a9c1b>` so that references stay distinguishable.

Command line:

```bash
europii scan customer_mail.txt --countries FI
cat notes.txt | europii redact --style hash > notes.redacted.txt
```

With Presidio (adds names, locations, …):

```python
from presidio_analyzer import AnalyzerEngine
from europii.presidio import EuroPIIRecognizer

analyzer = AnalyzerEngine()
analyzer.registry.add_recognizer(EuroPIIRecognizer(supported_language="en"))
```

## How well does it work?

Measured on the [EuroPII benchmark](https://huggingface.co/datasets/sinceaihq/europii-bench)
test set: <!-- n:start -->2,075<!-- n:end --> synthetic messages in 12 languages (support requests, HR
records, refunds, login alerts, supplier details, contact lists) with
annotated personal data and **hard negatives** — order and invoice numbers,
dates, amounts, barcodes, postcodes and identifiers with a wrong check digit.
Scores are for the structured entities above; "names found" is the PERSON
recall of the system (EuroPII Guard has no name detector).

<!-- results:start -->
| system | precision | recall | F1 | values fully hidden | hard negatives flagged | names found | messages/s |
|---|---|---|---|---|---|---|---|
| Presidio (default) | 91.2 | 47.2 | 62.2 | 59.6 | 1.0 | 89.6 | 72 |
| Presidio + its EU recognizers | 87.6 | 55.4 | 67.9 | 66.0 | 2.5 | 89.6 | 64 |
| Presidio + EuroPII Guard | 91.4 | 96.8 | 94.0 | 98.9 | 4.8 | 89.6 | 58 |
| EuroPII Guard | 95.4 | 96.8 | 96.1 | 98.0 | 4.0 | 0.0 | 439 |
| EuroPII Guard, country hint | 98.3 | 98.1 | 98.2 | 98.5 | 1.4 | 0.0 | 1,434 |
| EuroPII Guard, threshold 0.25 | 86.4 | 98.8 | 92.2 | 100.0 | 16.8 | 0.0 | 495 |
<!-- results:end -->

Full tables (per entity, per identifier type, hard negatives) are in the
[report](docs/REPORT.md). The benchmark is synthetic: real documents are
messier, so measure on a sample of your own data before relying on it.

## How it works

Each detector proposes candidates with a regular expression (or
libphonenumber) and validates them with the national check-digit and
date rules from `python-stdnum`. A confidence score combines the strength of
the validation with *context*: label words in the local language within 60
characters before the value ("henkilötunnus", "Steuer-ID", "PESEL",
"tél.", …). A plain digit string that happens to pass a weak checksum is only
reported next to such a label, or when the caller says which country to
expect. Overlapping candidates are resolved in favour of the strongest one.

## Data and test values

The benchmark never contains a real person's identifier where this can be
avoided: identifiers that encode a birth date use dates no living person can
have (future dates or early-19th-century dates); payment cards are public
test numbers; e-mail addresses use the reserved `example.*` domains. See the
[dataset card](https://huggingface.co/datasets/sinceaihq/europii-bench).

## Licence

Apache-2.0. EuroPII Guard depends on python-stdnum (LGPL-2.1+) and
phonenumbers (Apache-2.0); see [NOTICE](NOTICE).

---

Built by [Since AI](https://sinceai.ai). Issues and pull requests are welcome
— especially missing countries and real-world false negatives.
