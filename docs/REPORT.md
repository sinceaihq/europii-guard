# EuroPII Guard: checksum-validated detection of European personal data

*Since AI technical report, version 0.1.1 (October 2026)*

## Summary

Organisations increasingly send documents and messages to external AI
services and need to remove personal data first. Widely used open-source
detectors cover e-mail, phone and card numbers well, but European national
identifiers and locally formatted phone numbers much less. EuroPII Guard is a
small, pure-Python library that detects identity numbers of 22 European
countries, EU VAT numbers, IBANs, payment cards, phone numbers, e-mail and IP
addresses using the official validation rules, plus multilingual label words.
On a new synthetic benchmark of <!-- n:start -->
2,075
<!-- n:end --> messages in 12 languages it finds
European identifiers and contact data far more reliably than Microsoft
Presidio's default configuration, and combined with Presidio it hides about
95 % of all annotated personal data including names. It does not detect names
or addresses on its own and is not a compliance tool.

## 1. Problem and users

Developers who forward support tickets, HR documents, invoices or chat logs
to LLM APIs, analytics or external vendors need a cheap first line of
defence that runs locally and understands European identifiers. False
negatives — personal data that slips through — are the main risk; false
positives cost readability and, in pipelines, downstream accuracy.

## 2. Prior work and what this adds

* **Microsoft Presidio** (MIT) is the de-facto open-source framework. Its
  default English pipeline detects e-mail, card, IBAN and IP addresses well
  and ships country recognizers for a few EU states (Finland, Sweden, Poland,
  Spain, Italy, Germany), most of which are not enabled by default.
* **python-stdnum** (LGPL) implements validation for hundreds of national
  number formats but does not find them in free text.
* **libphonenumber** (Apache-2.0) parses and validates phone numbers per
  region.

EuroPII Guard combines the last two into a detector with multilingual
context and confidence scoring, covers 22 countries' personal identifiers and
all EU VAT numbers, plugs into Presidio as a recognizer, and comes with a
reproducible multilingual benchmark that includes hard negatives.

## 3. Method

* **Candidates**: one regular expression per identifier layout; phone
  numbers are digit groups with phone punctuation, excluding amounts, dates,
  IPv4 addresses, year-prefixed references and undivided runs of 12+ digits.
* **Validation**: `python-stdnum` (identifiers, VAT, IBAN, Luhn) and
  `phonenumbers` (valid numbers of any EU/EEA country, or of the caller's
  countries). Payment cards also need a matching issuer prefix and length.
* **Confidence**: *strong* matches (structure + check character, country
  prefix, international phone) score 0.9; grouped national phone numbers
  0.55; digit-only identifiers with a checksum and date check 0.45; weaker
  ones (no checksum, or a checksum that random digits pass 1 time in 10) 0.3.
  A label word in the local language before the value adds up to 0.55; a
  matching country hint adds 0.1. The default threshold is 0.5.
* **Overlaps**: the highest-scoring candidate wins, then the longest.

## 4. Benchmark

`europii.bench.synthetic` generates messages from five templates per
language (support request, HR record, refund request, login alert, supplier
details) plus an unlabelled contact-list row, in 12 languages, and English
messages quoting identifiers of the 11 remaining countries. Every message is
annotated with character offsets for PERSON, EMAIL, PHONE, IBAN,
PAYMENT_CARD, IP_ADDRESS, VAT_ID and NATIONAL_ID, and with hard-negative
spans: order and invoice numbers, dates, amounts, EAN barcodes, postcodes,
IBANs with a wrong check digit and identifiers whose checksum fails.

Splits: dev (seed 2027, 5 messages per template, 415 messages) was used for
all development; test (seed 2026, 25 per template, 2,075 messages) was
scored once for this report. A handful of test-seed messages were printed
while developing the generator to check formatting; no test scores were
computed before the detectors were frozen.

Metrics: per entity, precision and recall with overlap matching (a
prediction counts if it overlaps a gold span of the same type); *values fully
hidden* — the share of gold values completely covered by some detection of
any type, i.e. what a redaction would actually remove; and the share of each
hard-negative kind that is flagged.

## 5. Results (test split)

<!-- main:start -->
| system | precision | recall | F1 | values fully hidden | hard negatives flagged | names found | messages/s |
|---|---|---|---|---|---|---|---|
| Presidio (default) | 91.2 | 47.2 | 62.2 | 59.6 | 1.0 | 89.6 | 71 |
| Presidio + its EU recognizers | 87.6 | 55.4 | 67.9 | 66.0 | 2.5 | 89.6 | 67 |
| Presidio + EuroPII Guard | 92.8 | 96.8 | 94.7 | 98.3 | 3.7 | 89.6 | 62 |
| EuroPII Guard | 96.9 | 96.8 | 96.8 | 97.4 | 2.9 | 0.0 | 956 |
| EuroPII Guard, country hint | 99.3 | 98.1 | 98.7 | 98.1 | 0.8 | 0.0 | 1,580 |
| EuroPII Guard, threshold 0.25 | 87.6 | 99.4 | 93.1 | 100.0 | 15.8 | 0.0 | 982 |
<!-- main:end -->

Per entity (precision / recall):

<!-- labels:start -->
| entity | Presidio (default) P / R | Presidio + its EU recognizers P / R | EuroPII Guard P / R | EuroPII Guard, country hint P / R |
|---|---|---|---|---|
| e-mail | 100.0 / 100.0 | 100.0 / 100.0 | 100.0 / 100.0 | 100.0 / 100.0 |
| phone | 16.9 / 2.8 | 16.9 / 2.8 | 90.2 / 100.0 | 99.6 / 100.0 |
| IBAN | 100.0 / 100.0 | 100.0 / 100.0 | 100.0 / 100.0 | 100.0 / 100.0 |
| payment card | 92.6 / 100.0 | 92.6 / 100.0 | 99.3 / 100.0 | 99.3 / 100.0 |
| IP address | 100.0 / 100.0 | 100.0 / 100.0 | 100.0 / 100.0 | 100.0 / 100.0 |
| EU VAT number | — / 0.0 | 21.2 / 8.3 | 100.0 / 100.0 | 100.0 / 100.0 |
| national ID | 14.7 / 0.6 | 82.3 / 33.8 | 97.5 / 85.7 | 97.6 / 91.4 |
<!-- labels:end -->

Recall per identifier type (labelled and unlabelled occurrences together;
the unlabelled contact-list rows are where 50 % appears):

<!-- detectors:start -->
| identifier | EuroPII | EuroPII, country hint | Presidio + its EU recognizers |
|---|---|---|---|
| `at_svnr` | 100.0 | 100.0 | 0.0 |
| `be_national_number` | 100.0 | 100.0 | 0.0 |
| `bg_egn` | 100.0 | 100.0 | 0.0 |
| `cz_rodne_cislo` | 50.0 | 100.0 | 0.0 |
| `de_steuer_id` | 50.0 | 50.0 | 0.0 |
| `dk_cpr` | 50.0 | 50.0 | 10.0 |
| `ee_isikukood` | 100.0 | 100.0 | 12.0 |
| `es_dni` | 100.0 | 100.0 | 100.0 |
| `es_nie` | 100.0 | 100.0 | 100.0 |
| `fi_hetu` | 100.0 | 100.0 | 100.0 |
| `fr_nir` | 100.0 | 100.0 | 0.0 |
| `hr_oib` | 100.0 | 100.0 | 84.0 |
| `ie_ppsn` | 100.0 | 100.0 | 4.0 |
| `it_codice_fiscale` | 100.0 | 100.0 | 100.0 |
| `lt_asmens_kodas` | 100.0 | 100.0 | 44.0 |
| `lv_personas_kods` | 100.0 | 100.0 | 8.0 |
| `nl_bsn` | 50.0 | 50.0 | 0.0 |
| `no_fodselsnummer` | 100.0 | 100.0 | 0.0 |
| `pl_pesel` | 50.0 | 100.0 | 100.0 |
| `pt_cc` | 100.0 | 100.0 | 0.0 |
| `ro_cnp` | 100.0 | 100.0 | 8.0 |
| `se_personnummer` | 100.0 | 100.0 | 100.0 |
| `si_emso` | 100.0 | 100.0 | 0.0 |
| `sk_rodne_cislo` | 100.0 | 100.0 | 0.0 |
<!-- detectors:end -->

Hard negatives flagged as personal data:

<!-- negatives:start -->
| system | AMOUNT | BAD_ID | DATE | EAN | INVOICE | ORDER | POSTCODE |
|---|---|---|---|---|---|---|---|
| Presidio (default) | 0.0 | 0.3 | 0.0 | 1.3 | 0.3 | 7.0 | 0.0 |
| Presidio + its EU recognizers | 0.0 | 3.7 | 0.0 | 5.7 | 0.3 | 13.5 | 0.0 |
| Presidio + EuroPII Guard | 0.0 | 17.0 | 0.0 | 1.3 | 0.3 | 10.5 | 8.3 |
| EuroPII Guard | 0.0 | 17.0 | 0.0 | 0.7 | 0.0 | 4.2 | 8.3 |
| EuroPII Guard, country hint | 0.0 | 2.0 | 0.0 | 0.7 | 0.0 | 4.5 | 0.0 |
| EuroPII Guard, threshold 0.25 | 0.0 | 58.0 | 0.0 | 9.0 | 0.0 | 73.5 | 8.3 |
<!-- negatives:end -->

Names (PERSON) found by Presidio's English spaCy pipeline, per message
language:

<!-- person:start -->
| cs | da | de | en | es | fi | fr | it | nl | pl | pt | sv |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 80.0 | 87.2 | 100.0 | 92.8 | 86.4 | 78.4 | 72.0 | 84.8 | 89.6 | 97.6 | 100.0 | 100.0 |
<!-- person:end -->

### Reading the results

* Presidio's default pipeline misses almost all European phone numbers and
  national identifiers in this data; enabling its EU country recognizers
  helps for the six countries they cover.
* EuroPII Guard finds every e-mail, IBAN, payment card, IP address and VAT
  number, every labelled national identifier, and national identifiers
  without a label when they have strong structure (FI, IT, FR, ES, IE, PT
  CC, SE with separator) or when a country hint is given (PL, CZ).
* **What it still misses by default**: digit-only identifiers with weak or
  no checksums (DE Steuer-ID, NL BSN, DK CPR) when nothing labels them. A
  threshold of 0.25 recovers most of them but then flags far more order
  numbers and invalid identifiers as personal data.
* **Main false positive**: an identifier with a wrong check digit is often
  still a valid phone number somewhere in Europe. A country hint removes most
  of these.
* Names are left to an NLP model; Presidio's English pipeline found 72–100 %
  of the (simple, capitalised) names here. Real text is harder.

## 6. Limitations

* Synthetic, template-based messages: real documents have typos, OCR noise,
  unusual formatting and identifiers split across lines.
* No name, address or date-of-birth detection in the standalone library.
* Phone validation depends on libphonenumber metadata and accepts many digit
  strings as valid numbers in some country.
* Identifiers without a checksum (DK CPR) can only be validated by their
  date; without a label they are indistinguishable from other numbers.
* Only the 12 benchmark languages have tuned label words; other languages
  rely on the English and country terms.

## 7. Responsible use

Use EuroPII Guard to *reduce* exposure, not to certify that data is
anonymous. Redacted output can still identify people through names, rare
facts or combinations of attributes. Keep humans in the loop for sensitive
data and test on a sample of your own documents.

## 8. Reproduction

```bash
pip install -e ".[presidio,dev]" && python -m spacy download en_core_web_lg
python -m europii.bench.synthetic --out data --seed 2026 --dev 5 --test 25
python scripts/compare.py --data data/test.jsonl --out results/comparison.json
python scripts/render_docs.py --results results/comparison.json
```

## References

1. Microsoft Presidio. <https://github.com/microsoft/presidio>
2. A. de Jong. python-stdnum. <https://arthurdejong.org/python-stdnum/>
3. Google libphonenumber; D. Drysdale, python-phonenumbers. <https://github.com/daviddrysdale/python-phonenumbers>
4. D. Eastlake, A. Panitz. RFC 2606: Reserved Top Level DNS Names. 1999.
