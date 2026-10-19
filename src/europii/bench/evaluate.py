"""Score PII detections against the synthetic evaluation set.

A *system* is any function ``text -> [(start, end, label), ...]`` using the
labels of :data:`LABELS`; detections with other labels are counted
separately and never as true positives.
"""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path
from typing import Any

LABELS = ("EMAIL", "PHONE", "IBAN", "PAYMENT_CARD", "IP_ADDRESS", "VAT_ID", "NATIONAL_ID", "PERSON")
Span = tuple[int, int, str]
System = Callable[[str], Sequence[Span]]


def load(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def _overlaps(a: tuple[int, int], b: tuple[int, int]) -> bool:
    return a[0] < b[1] and b[0] < a[1]


def _prf(tp: int, n_pred: int, n_gold: int) -> dict[str, float | int | None]:
    p = tp / n_pred if n_pred else None
    r = tp / n_gold if n_gold else None
    f = 2 * p * r / (p + r) if p and r else (0.0 if n_gold else None)
    return {"precision": p, "recall": r, "f1": f, "n_gold": n_gold, "n_pred": n_pred}


def evaluate(
    rows: Iterable[dict[str, Any]], system: System, labels: Sequence[str] = LABELS
) -> dict[str, Any]:
    gold_n: dict[str, int] = defaultdict(int)
    pred_n: dict[str, int] = defaultdict(int)
    tp_overlap_r: dict[str, int] = defaultdict(int)  # gold spans found (recall)
    tp_overlap_p: dict[str, int] = defaultdict(int)  # predictions that hit gold (precision)
    tp_exact: dict[str, int] = defaultdict(int)
    by_lang: dict[str, dict[str, list[bool]]] = defaultdict(lambda: defaultdict(list))
    by_detector: dict[str, list[bool]] = defaultdict(list)
    by_template: dict[str, list[bool]] = defaultdict(list)
    covered, covered_n = 0, 0
    neg_hit: dict[str, list[bool]] = defaultdict(list)
    other_labels: dict[str, int] = defaultdict(int)
    for row in rows:
        text = row["text"]
        preds = list(system(text))
        known = [p for p in preds if p[2] in labels]
        for p in preds:
            if p[2] not in labels:
                other_labels[p[2]] += 1
        gold = [(s["start"], s["end"], s["label"]) for s in row["spans"] if s["label"] in labels]
        for g in gold:
            gold_n[g[2]] += 1
            hit = any(p[2] == g[2] and _overlaps(p[:2], g[:2]) for p in known)
            tp_overlap_r[g[2]] += hit
            tp_exact[g[2]] += any(p == g for p in known)
            by_lang[row["language"]][g[2]].append(hit)
            by_template[str(row["template"])].append(hit)
            det = next(
                (s["detector"] for s in row["spans"]
                 if (s["start"], s["end"]) == g[:2] and s.get("detector")),
                None,
            )  # fmt: skip
            if det:
                by_detector[det].append(hit)
            # Would the value be hidden, whatever label the system gave it?
            covered_n += 1
            covered += any(p[0] <= g[0] and p[1] >= g[1] for p in preds)
        for p in known:
            pred_n[p[2]] += 1
            tp_overlap_p[p[2]] += any(g[2] == p[2] and _overlaps(p[:2], g[:2]) for g in gold)
        for n in row.get("negatives", []):
            neg_hit[n["kind"]].append(any(_overlaps(p[:2], (n["start"], n["end"])) for p in known))

    per_label = {}
    for lab in labels:
        prf = _prf(tp_overlap_p[lab], pred_n[lab], gold_n[lab])
        prf["recall"] = tp_overlap_r[lab] / gold_n[lab] if gold_n[lab] else None
        prec, rec = prf["precision"], prf["recall"]
        prf["f1"] = (
            2 * prec * rec / (prec + rec) if prec and rec else (0.0 if gold_n[lab] else None)
        )
        prf["exact_recall"] = tp_exact[lab] / gold_n[lab] if gold_n[lab] else None
        per_label[lab] = prf
    total_gold = sum(gold_n.values())
    total_pred = sum(pred_n.values())
    micro_r = sum(tp_overlap_r.values()) / total_gold if total_gold else None
    micro_p = sum(tp_overlap_p.values()) / total_pred if total_pred else None
    micro_f = 2 * micro_p * micro_r / (micro_p + micro_r) if micro_p and micro_r else 0.0
    return {
        "micro": {"precision": micro_p, "recall": micro_r, "f1": micro_f},
        "labels": per_label,
        "coverage": covered / covered_n if covered_n else None,
        "negatives_flagged": {k: sum(v) / len(v) for k, v in sorted(neg_hit.items())},
        "negatives_flagged_overall": (
            sum(sum(v) for v in neg_hit.values()) / max(1, sum(len(v) for v in neg_hit.values()))
        ),
        "recall_by_language": {
            lang: {lab: sum(v) / len(v) for lab, v in labs.items()}
            for lang, labs in sorted(by_lang.items())
        },
        "recall_by_detector": {k: sum(v) / len(v) for k, v in sorted(by_detector.items())},
        "recall_by_template": {k: sum(v) / len(v) for k, v in sorted(by_template.items())},
        "other_labels": dict(other_labels),
    }


def europii_system(threshold: float = 0.5) -> System:
    from .. import scan

    def run(text: str) -> list[Span]:
        return [(f.start, f.end, f.entity) for f in scan(text, threshold=threshold)]

    return run
