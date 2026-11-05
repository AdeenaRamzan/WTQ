"""Phase 2/3 helper: run Level 1 on a folder of bills and dump per-bill JSON.

    python -m scripts.run_level1                 # defaults to train/bills
    python -m scripts.run_level1 --bills path\to\bills
"""
import argparse
import json
from pathlib import Path

from src.config import OUTPUT_DIR, PROJECT_ROOT, get_logger
from src.level1 import extract_level1
from src.llm_client import LLMClient
from src.preprocess import load_bill_image

log = get_logger("run_level1")
IMG_EXT = {".png", ".jpg", ".jpeg"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bills", default=str(PROJECT_ROOT / "train" / "bills"))
    args = ap.parse_args()

    bills_dir = Path(args.bills)
    if not bills_dir.is_dir():
        raise SystemExit(f"Bills folder not found: {bills_dir}")

    out_dir = OUTPUT_DIR / "debug_level1"
    out_dir.mkdir(parents=True, exist_ok=True)

    client = LLMClient()
    files = sorted(p for p in bills_dir.iterdir() if p.suffix.lower() in IMG_EXT)
    if not files:
        raise SystemExit(f"No .png/.jpg bills in {bills_dir}")

    for p in files:
        bill_id = p.stem
        image = load_bill_image(p)
        out, warns = extract_level1(client, image, bill_id)
        (out_dir / f"{bill_id}.json").write_text(
            json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"\n===== {bill_id} =====")
        print(json.dumps(out, ensure_ascii=False))
        for w in warns:
            print("  WARN:", w)

    print(f"\nWrote {len(files)} JSON files to {out_dir}")


if __name__ == "__main__":
    main()
