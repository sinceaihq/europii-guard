"""Fill the generated result sections of README.md and docs/REPORT.md.

python scripts/render_docs.py --results results/comparison.json
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
NAMES = {
    "presidio_default": "Presidio (default)",
    "presidio_eu": "Presidio + its EU recognizers",
    "presidio_plus_europii": "Presidio + EuroPII Guard",
    "europii": "EuroPII Guard",
    "europii_hint": "EuroPII Guard, country hint",
    "europii_recall": "EuroPII Guard, threshold 0.25",
}
LABEL_NAMES = {"EMAIL": "e-mail", "PHONE": "phone", "IBAN": "IBAN", "PAYMENT_CARD": "payment card",
               "IP_ADDRESS": "IP address", "VAT_ID": "EU VAT number", "NATIONAL_ID": "national ID"}  # fmt: skip


def pct(x: float | None) -> str:
    return "—" if x is None else f"{100 * x:.1f}"


def fill(text: str, name: str, content: str) -> str:
    pattern = re.compile(rf"<!-- {name}:start -->.*?<!-- {name}:end -->", re.DOTALL)
    if not pattern.search(text):
        raise KeyError(name)
    return pattern.sub(lambda _: f"<!-- {name}:start -->\n{content}\n<!-- {name}:end -->", text)


def main_table(res: dict[str, Any]) -> str:
    rows = [
        "| system | precision | recall | F1 | values fully hidden | hard negatives flagged | names found | messages/s |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for key, label in NAMES.items():
        s = res["systems"][key]
        st, pe = s["structured"], s["person"]
        rows.append(
            f"| {label} | {pct(st['micro']['precision'])} | {pct(st['micro']['recall'])} "
            f"| {pct(st['micro']['f1'])} | {pct(st['coverage'])} | {pct(st['negatives_flagged_overall'])} "
            f"| {pct(pe['micro']['recall'])} | {s['messages_per_second']:,.0f} |"
        )
    return "\n".join(rows)


def label_table(res: dict[str, Any], systems: tuple[str, ...]) -> str:
    head = "| entity | " + " | ".join(f"{NAMES[s]} P / R" for s in systems) + " |"
    rows = [head, "|---|" + "---|" * len(systems)]
    for lab, name in LABEL_NAMES.items():
        cells = []
        for s in systems:
            v = res["systems"][s]["structured"]["labels"][lab]
            cells.append(f"{pct(v['precision'])} / {pct(v['recall'])}")
        rows.append(f"| {name} | " + " | ".join(cells) + " |")
    return "\n".join(rows)


def detector_table(res: dict[str, Any]) -> str:
    e = res["systems"]["europii"]["structured"]["recall_by_detector"]
    h = res["systems"]["europii_hint"]["structured"]["recall_by_detector"]
    p = res["systems"]["presidio_eu"]["structured"]["recall_by_detector"]
    rows = [
        "| identifier | EuroPII | EuroPII, country hint | Presidio + its EU recognizers |",
        "|---|---|---|---|",
    ]
    for det in sorted(e):
        rows.append(f"| `{det}` | {pct(e[det])} | {pct(h.get(det))} | {pct(p.get(det))} |")
    return "\n".join(rows)


def negatives_table(res: dict[str, Any]) -> str:
    kinds = list(res["systems"]["europii"]["structured"]["negatives_flagged"])
    rows = ["| system | " + " | ".join(kinds) + " |", "|---|" + "---|" * len(kinds)]
    for key, label in NAMES.items():
        neg = res["systems"][key]["structured"]["negatives_flagged"]
        rows.append(f"| {label} | " + " | ".join(pct(neg[k]) for k in kinds) + " |")
    return "\n".join(rows)


def person_table(res: dict[str, Any]) -> str:
    by = res["systems"]["presidio_default"]["person"]["recall_by_language"]
    langs = sorted(by)
    return "\n".join(
        [
            "| " + " | ".join(langs) + " |",
            "|" + "---|" * len(langs),
            "| " + " | ".join(pct(by[lang].get("PERSON")) for lang in langs) + " |",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--results", type=Path, required=True)
    args = parser.parse_args()
    res = json.loads(args.results.read_text(encoding="utf-8"))
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    readme = fill(readme, "results", main_table(res))
    readme = re.sub(
        r"<!-- n:start -->.*?<!-- n:end -->",
        f"<!-- n:start -->{res['messages']:,}<!-- n:end -->",
        readme,
    )
    (ROOT / "README.md").write_text(readme, encoding="utf-8")
    report = (ROOT / "docs/REPORT.md").read_text(encoding="utf-8")
    report = fill(report, "main", main_table(res))
    report = fill(
        report,
        "labels",
        label_table(res, ("presidio_default", "presidio_eu", "europii", "europii_hint")),
    )
    report = fill(report, "detectors", detector_table(res))
    report = fill(report, "negatives", negatives_table(res))
    report = fill(report, "person", person_table(res))
    report = fill(report, "n", f"{res['messages']:,}")
    (ROOT / "docs/REPORT.md").write_text(report, encoding="utf-8")
    print("updated README.md and docs/REPORT.md")


if __name__ == "__main__":
    main()
