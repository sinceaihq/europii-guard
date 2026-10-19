from __future__ import annotations

import io
import json
import re
from pathlib import Path

import pytest
from stdnum import iban as std_iban
from stdnum import luhn
from stdnum.eu import vat as eu_vat

from europii.bench.evaluate import europii_system, evaluate
from europii.bench.synthetic import TEST_CARDS, generate, main
from europii.bench.templates import FIRST_NAMES, LAST_NAMES, LOCAL_ID, TEMPLATES
from europii.cli import main as cli_main


@pytest.fixture(scope="module")
def rows() -> list[dict]:  # type: ignore[type-arg]
    return generate(seed=7, per_template=2)


def test_generation_is_deterministic(rows: list[dict]) -> None:  # type: ignore[type-arg]
    assert generate(seed=7, per_template=2) == rows
    assert generate(seed=8, per_template=2) != rows


def test_every_language_and_template_is_present(rows: list[dict]) -> None:  # type: ignore[type-arg]
    langs = {r["language"] for r in rows}
    assert langs == set(TEMPLATES)
    assert set(LOCAL_ID) == set(TEMPLATES) == set(FIRST_NAMES) == set(LAST_NAMES)


def test_spans_and_values_are_valid(rows: list[dict]) -> None:  # type: ignore[type-arg]
    for r in rows:
        text = r["text"]
        for s in r["spans"]:
            value = text[s["start"] : s["end"]]
            assert value == value.strip()
            assert value
            if s["label"] == "IBAN":
                assert std_iban.is_valid(value)
            if s["label"] == "VAT_ID":
                assert eu_vat.is_valid(value)
            if s["label"] == "PAYMENT_CARD":
                assert value in TEST_CARDS
                assert luhn.is_valid(value.replace(" ", ""))
            if s["label"] == "EMAIL":
                assert re.search(r"@(?:mail\.)?example\.(?:com|org|net)$", value)
        for n in r["negatives"]:
            assert text[n["start"] : n["end"]]
            assert not any(s["start"] < n["end"] and n["start"] < s["end"] for s in r["spans"])


def test_evaluate_perfect_and_empty_systems(rows: list[dict]) -> None:  # type: ignore[type-arg]
    gold = {r["text"]: [(s["start"], s["end"], s["label"]) for s in r["spans"]] for r in rows}
    perfect = evaluate(rows, lambda t: gold[t])
    assert perfect["micro"]["f1"] == pytest.approx(1.0)
    assert perfect["coverage"] == pytest.approx(1.0)
    assert perfect["negatives_flagged_overall"] == 0.0
    empty = evaluate(rows, lambda t: [])
    assert empty["micro"]["recall"] == 0.0
    assert empty["coverage"] == 0.0


def test_unknown_labels_are_not_true_positives(rows: list[dict]) -> None:  # type: ignore[type-arg]
    r = evaluate(rows, lambda t: [(0, len(t), "DATE_TIME")])
    assert r["micro"]["recall"] == 0.0
    assert r["other_labels"]["DATE_TIME"] == len(rows)
    assert r["coverage"] == pytest.approx(1.0)  # everything is hidden, though


def test_europii_on_generated_set(rows: list[dict]) -> None:  # type: ignore[type-arg]
    labels = ("EMAIL", "PHONE", "IBAN", "PAYMENT_CARD", "IP_ADDRESS", "VAT_ID", "NATIONAL_ID")
    r = evaluate(rows, europii_system(), labels)
    assert r["micro"]["f1"] > 0.9
    assert r["labels"]["IBAN"]["recall"] == 1.0
    assert r["labels"]["EMAIL"]["recall"] == 1.0


def test_generator_cli(tmp_path: Path) -> None:
    main(["--out", str(tmp_path), "--dev", "1", "--test", "1"])
    for split in ("dev", "test"):
        lines = (tmp_path / f"{split}.jsonl").read_text(encoding="utf-8").splitlines()
        assert lines
        assert json.loads(lines[0])["spans"]


def test_cli_scan_and_redact(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO("mail anna@example.com, puh. 040 123 4567"))
    assert cli_main(["redact"]) == 0
    assert capsys.readouterr().out == "mail <EMAIL>, puh. <PHONE>"
    monkeypatch.setattr("sys.stdin", io.StringIO("IBAN DE89 3704 0044 0532 0130 00"))
    assert cli_main(["scan", "--entities", "IBAN"]) == 0
    line = json.loads(capsys.readouterr().out.strip())
    assert line["entity"] == "IBAN"
