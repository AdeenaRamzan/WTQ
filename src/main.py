"""End-to-end pipeline.

    python -m src.main --bills test/bills \
        --level1-template test/csv/level1.csv \
        --level2-template test/csv/level2.csv \
        --out output/

Generates output/level1.csv and output/level2.csv, then validates them.
A failure on one bill never aborts the run.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from . import config
from .facts import extract_facts
from .io_utils import (
    find_bill_image, read_level1_template, read_level2_template,
    validate_level1_csv, validate_level2_csv, write_level1_csv, write_level2_csv,
)
from .level1 import extract_level1
from .level2 import answer_questions
from .llm_client import LLMClient
from .preprocess import load_bill_image
from .stats import compute_stats
from .validators import empty_level1

log = config.get_logger("main")


def parse_args():
    ap = argparse.ArgumentParser(description="Utility Bill Decoder pipeline")
    ap.add_argument("--bills", required=True, help="folder of bill images")
    ap.add_argument("--level1-template", required=True)
    ap.add_argument("--level2-template", required=True)
    ap.add_argument("--out", default="output")
    ap.add_argument("--skip-level2", action="store_true", help="only generate level1.csv")
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    config.validate()

    bills_dir = Path(args.bills)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    bill_ids = read_level1_template(Path(args.level1_template))
    l2_rows, questions = read_level2_template(Path(args.level2_template))
    log.info("bills=%d  level2 rows=%d  questions=%d",
             len(bill_ids), len(l2_rows), len(questions))

    client = LLMClient()
    json_by_bill: dict[str, dict] = {}
    answers_by_bill: dict[str, dict[str, str]] = {}

    t0 = time.time()
    for n, bid in enumerate(bill_ids, 1):
        log.info("[%d/%d] %s", n, len(bill_ids), bid)
        img_path = find_bill_image(bills_dir, bid)
        if img_path is None:
            log.error("  image not found for %s - writing fallback", bid)
            from .level1 import provider_from_bill_id
            hint = provider_from_bill_id(bid)
            json_by_bill[bid] = empty_level1(hint)
            if not args.skip_level2:
                answers_by_bill[bid] = {qid: "This could not be determined "
                                        "from the information shown on the bill."
                                        for qid, _ in questions}
            continue
        try:
            image = load_bill_image(img_path)
        except Exception as exc:  # noqa: BLE001
            log.error("  preprocess failed for %s: %s", bid, exc)
            json_by_bill[bid] = empty_level1(None)
            if not args.skip_level2:
                answers_by_bill[bid] = {qid: "This could not be determined "
                                        "from the information shown on the bill."
                                        for qid, _ in questions}
            continue

        # Level 1
        l1, warns = extract_level1(client, image, bid)
        json_by_bill[bid] = l1

        # Level 2
        if not args.skip_level2:
            facts = extract_facts(client, image, bid)
            stats = compute_stats(facts)
            answers_by_bill[bid] = answer_questions(client, stats, questions, bid)

    # Write CSVs
    l1_path = out_dir / "level1.csv"
    write_level1_csv(l1_path, bill_ids, json_by_bill)
    if not args.skip_level2:
        l2_path = out_dir / "level2.csv"
        write_level2_csv(l2_path, l2_rows, answers_by_bill)

    # Validate
    errs = validate_level1_csv(l1_path, bill_ids)
    if not args.skip_level2:
        errs += validate_level2_csv(l2_path, len(l2_rows))

    log.info("done in %.1fs", time.time() - t0)
    if errs:
        log.error("VALIDATION PROBLEMS (%d):", len(errs))
        for e in errs:
            log.error("  - %s", e)
        print("\nFINISHED WITH VALIDATION WARNINGS - see log above.")
        return 1
    print(f"\nSUCCESS: wrote {l1_path}" +
          ("" if args.skip_level2 else f" and {out_dir / 'level2.csv'}") +
          " - all validation checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
