"""Regenerate the v0.1 test set, check its checksum and the headline scores.

python scripts/check_benchmark.py
"""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path

from europii.bench.evaluate import evaluate, load
from europii.bench.synthetic import main as generate
from europii.bench.templates import COUNTRY

ROOT = Path(__file__).resolve().parents[1]
STRUCTURED = ("EMAIL", "PHONE", "IBAN", "PAYMENT_CARD", "IP_ADDRESS", "VAT_ID", "NATIONAL_ID")


def main() -> int:
    manifest = json.loads((ROOT / "releases/v0.1/manifest.json").read_text(encoding="utf-8"))
    expected = json.loads((ROOT / "releases/v0.1/expected.json").read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        generate(["--out", str(out), "--seed", str(manifest["seed"]),
                  "--dev", str(manifest["dev_per_template"]), "--test", str(manifest["test_per_template"])])  # fmt: skip
        ok = True
        for name, digest in manifest["files"].items():
            actual = hashlib.sha256((out / name).read_bytes()).hexdigest()
            print(name, "OK" if actual == digest else f"MISMATCH {actual}")
            ok &= actual == digest
        rows = load(out / "test.jsonl")
    from europii import scan

    lang_of = {r["text"]: r["language"] for r in rows}
    for key, hint in (("europii", False), ("europii_hint", True)):
        res = evaluate(
            rows,
            lambda t, h=hint: [  # type: ignore[misc]
                (f.start, f.end, f.entity)
                for f in scan(t, countries=(COUNTRY[lang_of[t]],) if h else ())
            ],
            STRUCTURED,
        )
        f1, cov = res["micro"]["f1"], res["coverage"]
        good = abs(f1 - expected[key]["f1"]) < 1e-9 and abs(cov - expected[key]["coverage"]) < 1e-9
        print(key, f"F1 {f1:.4f} coverage {cov:.4f}", "OK" if good else "CHANGED")
        ok &= good
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
