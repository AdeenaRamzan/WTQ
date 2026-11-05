"""CSV template reading, result writing, and validation.

Uses the stdlib csv module so quoting / quote-doubling / UTF-8 are handled
correctly, and preserves the template's exact rows and order.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from . import config
from .schemas import FIELD_ORDER

log = config.get_logger("io")

IMG_EXT = (".png", ".jpg", ".jpeg")


def find_bill_image(bills_dir: Path, bill_id: str) -> Path | None:
    for ext in IMG_EXT:
        p = bills_dir / f"{bill_id}{ext}"
        if p.exists():
            return p
    # case-insensitive fallback
    for p in bills_dir.iterdir():
        if p.stem == bill_id and p.suffix.lower() in IMG_EXT:
            return p
    return None


def read_level1_template(path: Path) -> list[str]:
    """Return ordered list of bill_ids from the level1 template."""
    bill_ids = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            bid = (row.get("bill_id") or "").strip()
            if bid:
                bill_ids.append(bid)
    return bill_ids


def read_level2_template(path: Path):
    """Return (rows, questions).

    rows: list of dicts {bill_id, question_id, question} in template order.
    questions: ordered unique list of (question_id, question).
    """
    rows = []
    seen = {}
    questions = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            bid = (row.get("bill_id") or "").strip()
            qid = (row.get("question_id") or "").strip()
            q = (row.get("question") or "").strip()
            if not bid or not qid:
                continue
            rows.append({"bill_id": bid, "question_id": qid, "question": q})
            if qid not in seen:
                seen[qid] = q
                questions.append((qid, q))
    return rows, questions


def write_level1_csv(path: Path, bill_ids: list[str], json_by_bill: dict[str, dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        w.writerow(["bill_id", "json"])
        for bid in bill_ids:
            obj = json_by_bill.get(bid) or {}
            js = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
            w.writerow([bid, js])
    log.info("wrote %s (%d rows)", path, len(bill_ids))


def write_level2_csv(path: Path, template_rows: list[dict],
                     answers_by_bill: dict[str, dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        w.writerow(["bill_id", "question_id", "question", "answer"])
        for r in template_rows:
            ans = (answers_by_bill.get(r["bill_id"], {}) or {}).get(r["question_id"], "")
            w.writerow([r["bill_id"], r["question_id"], r["question"], ans])
    log.info("wrote %s (%d rows)", path, len(template_rows))


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def validate_level1_csv(path: Path, expected_bill_ids: list[str]) -> list[str]:
    errs = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader, [])
        if header != ["bill_id", "json"]:
            errs.append(f"level1: header is {header}, expected ['bill_id','json']")
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != len(expected_bill_ids):
        errs.append(f"level1: {len(rows)} rows, expected {len(expected_bill_ids)}")
    for i, row in enumerate(rows):
        bid = row.get("bill_id", "")
        js = row.get("json", "")
        if not js.strip():
            errs.append(f"level1 row {i} ({bid}): empty json")
            continue
        try:
            obj = json.loads(js)
        except json.JSONDecodeError as e:
            errs.append(f"level1 row {i} ({bid}): invalid JSON: {e}")
            continue
        missing = [k for k in FIELD_ORDER if k not in obj]
        if missing:
            errs.append(f"level1 row {i} ({bid}): missing keys {missing}")
    return errs


def validate_level2_csv(path: Path, expected_rows: int) -> list[str]:
    errs = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader, [])
        if header != ["bill_id", "question_id", "question", "answer"]:
            errs.append(f"level2: header is {header}, expected "
                        "['bill_id','question_id','question','answer']")
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != expected_rows:
        errs.append(f"level2: {len(rows)} rows, expected {expected_rows}")
    for i, row in enumerate(rows):
        if not (row.get("answer") or "").strip():
            errs.append(f"level2 row {i} ({row.get('bill_id')},{row.get('question_id')}): empty answer")
    return errs
