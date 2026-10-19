# Changelog

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and the project uses [Semantic Versioning](https://semver.org/).

## [0.1.1] - 2026-10-19

### Fixed
- Phone spans no longer include an unmatched closing bracket ("(tel. 040 …)").
- Numbers written with thousands separators ("11 987 654", "1.234.567") and
  national candidates longer than 12 digits (e.g. French SIRET numbers) are no
  longer reported as phone numbers. Phone numbers grouped 3-3-3 ("512 345 678")
  are still found.

### Changed
- Benchmark results re-measured on the unchanged v0.1 test set: structured
  precision 96.9 % (was 95.4 %), recall 96.8 % (unchanged); with a country
  hint 99.3 % / 98.1 %. Values fully hidden: 97.4 % (was 98.0 %).

## [0.1.0] - 2026-10-19

First public release.

### Added
- Detectors for national identifiers of 22 European countries, EU VAT
  numbers, IBANs, payment cards, phone numbers (EU/EEA), e-mail and IP
  addresses, validated with python-stdnum and phonenumbers.
- Multilingual label words, country hints and confidence scoring.
- `scan`, `redact` (placeholder, mask, hash) and the `europii` CLI.
- Presidio integration (`europii.presidio.EuroPIIRecognizer`).
- EuroPII benchmark generator (12 languages, hard negatives) and evaluation
  against Presidio.
- In-browser demo (Pyodide).
