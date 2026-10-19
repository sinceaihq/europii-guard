# Changelog

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and the project uses [Semantic Versioning](https://semver.org/).

## [0.1.3] - 2026-10-19

### Fixed
- International phone numbers written with `00` (`0049 30 12345678`) were never detected; they are now found when
  grouped after the country code or next to a phone label (plain `00…` order numbers are still ignored).
- Candidate patterns with alternatives (Dutch BSN, Swedish personnummer without separator) were bounded only on
  their first/last alternative, so pieces of longer numbers became candidates — e.g. part of an EAN barcode, or a
  Lithuanian personal code reported truncated as a Swedish number. All patterns are now bounded on both sides.
- Irish PPSNs in the 2013 format with second letter `H` were not matched.

These were found while porting the engine to TypeScript for [SafePrompt](https://github.com/sinceaihq/safeprompt).
Benchmark: structured precision 97.0 % (was 96.9 %), recall unchanged at 96.8 %.

## [0.1.2] - 2026-10-19

### Fixed
- Finnish personal identity codes with the "-" century sign (born
  1900–1999, e.g. `131052-308T`) were not detected: the separator stripping
  applied before validation removed the century sign. They are now found.
  The synthetic benchmark only uses impossible birth dates and so never
  contained this form; benchmark scores are unchanged.
- Latvian company registration / VAT numbers (11 digits starting with 4–9)
  are no longer reported as Latvian personal codes.

### Added
- Unit tests with documented example identifiers for 12 countries.

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
