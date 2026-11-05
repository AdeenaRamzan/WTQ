"""Build the viewer's report.json from the pipeline outputs, and copy bill images.

    python report_export.py --bills test/bills
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VIEWER = ROOT / "utility-bill-decoder" / "bill-decoder" / "public" / "data"
IMG_EXT = (".png", ".jpg", ".jpeg")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bills", default="test/bills")
    ap.add_argument("--out", default=str(ROOT / "output"))
    args = ap.parse_args()

    out = Path(args.out)
    bills_dir = Path(args.bills)

    # level1
    l1 = {}
    with open(out / "level1.csv", newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            l1[row["bill_id"]] = json.loads(row["json"])

    # level2
    l2: dict[str, list] = {}
    with open(out / "level2.csv", newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            l2.setdefault(row["bill_id"], []).append({
                "question_id": row["question_id"],
                "question": row["question"],
                "answer": row["answer"],
            })

    (VIEWER / "images").mkdir(parents=True, exist_ok=True)
    bills = []
    for bid in l1:
        image_rel = None
        for ext in IMG_EXT:
            src = bills_dir / f"{bid}{ext}"
            if src.exists():
                shutil.copy(src, VIEWER / "images" / f"{bid}{ext}")
                image_rel = f"images/{bid}{ext}"
                break
        bills.append({
            "bill_id": bid,
            "image": image_rel,
            "level1": l1[bid],
            "level2": l2.get(bid, []),
        })

    report = {"generated_at": datetime.now().isoformat(timespec="seconds"), "bills": bills}
    (VIEWER / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {VIEWER / 'report.json'} with {len(bills)} bills and copied images")


if __name__ == "__main__":
    main()
