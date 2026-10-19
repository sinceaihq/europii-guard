# Changelog

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and the project uses [Semantic Versioning](https://semver.org/).

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
