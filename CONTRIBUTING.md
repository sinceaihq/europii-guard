# Contributing to EuroPII Guard

Contributions are welcome — new countries, better label words in your
language, and above all **real-world false negatives**, described with
synthetic look-alike examples.

```bash
git clone https://github.com/sinceaihq/europii-guard.git
cd europii-guard
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
ruff format --check . && ruff check . && mypy && pytest
python scripts/check_benchmark.py
```

## Adding a country

1. Add a detector in `src/europii/detectors.py` using the `python-stdnum`
   validator, with the right strength (strong / medium / weak) and the local
   label words in `COUNTRY_ID_WORDS`.
2. Add a synthetic generator in `src/europii/bench/identities.py`. If the
   identifier encodes a birth date, use a date no living person can have.
3. Add tests; `tests/test_detectors.py` picks new generators up
   automatically.
4. Changing detection behaviour changes the benchmark scores: rerun
   `scripts/compare.py` and `scripts/render_docs.py`, and update
   `releases/<version>/expected.json` in the same pull request.

## Rules

- Never commit real personal data, not even in tests.
- Conventional commit messages (`feat:`, `fix:`, `docs:`, `test:`).
- Participation is governed by the [Code of Conduct](CODE_OF_CONDUCT.md).
