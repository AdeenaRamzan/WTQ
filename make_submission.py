"""Build the submission ZIP exactly per the portal rules.

    python make_submission.py

Produces submission.zip containing ONLY:
    output/level1.csv, output/level2.csv
    source/  (README.md, .env.example, requirements.txt, code; NO secrets/venv/caches)
    demo/    (optional, if a demo/ folder with a video exists)

It uses an explicit allow-list (so venv, node_modules, dist, __pycache__, cache,
logs, .env and bill images can never leak in), verifies CSV headers/rows,
scans every bundled text file for a Google API key, then prints the file list
and total size and checks the 15 MB limit.
"""
from __future__ import annotations

import csv
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"
ZIP_PATH = ROOT / "submission.zip"
MAX_BYTES = 15 * 1024 * 1024
KEY_RE = re.compile(r"AIza[0-9A-Za-z_\-]{20,}")  # Google AI Studio key prefix

L1_HEADER = ["bill_id", "json"]
L2_HEADER = ["bill_id", "question_id", "question", "answer"]
L1_KEYS = [
    "provider", "tariff", "sanctioned_load_kw", "bill_month", "reading_date",
    "issue_date", "due_date", "previous_reading", "current_reading",
    "units_consumed", "charges", "total_charges", "taxes", "total_taxes",
    "current_bill", "arrears", "payable_within_due_date", "payable_after_due_date",
]


def fail(msg: str):
    print(f"ERROR: {msg}")
    sys.exit(1)


def check_level1(path: Path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader, [])
        if header != L1_HEADER:
            fail(f"{path.name} header {header} != {L1_HEADER}")
        rows = list(reader)
    if not rows:
        fail("level1.csv has no data rows")
    for i, row in enumerate(rows):
        if len(row) < 2 or not row[1].strip():
            fail(f"level1.csv row {i} ({row[0] if row else '?'}) has empty json")
        try:
            obj = json.loads(row[1])
        except json.JSONDecodeError as e:
            fail(f"level1.csv row {i} broken JSON: {e}")
        missing = [k for k in L1_KEYS if k not in obj]
        if missing:
            fail(f"level1.csv row {i} ({row[0]}) missing keys {missing}")
    print(f"  level1.csv OK: header exact, {len(rows)} rows, all JSON valid with all keys")


def check_level2(path: Path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader, [])
        if header != L2_HEADER:
            fail(f"{path.name} header {header} != {L2_HEADER}")
        rows = list(reader)
    if not rows:
        fail("level2.csv has no data rows")
    for i, row in enumerate(rows):
        if len(row) < 4 or not row[3].strip():
            fail(f"level2.csv row {i} has empty answer")
    print(f"  level2.csv OK: header exact, {len(rows)} rows, no empty answers")


def collect_source_files() -> list[tuple[Path, str]]:
    """Return (disk_path, arcname) pairs using an explicit allow-list."""
    pairs: list[tuple[Path, str]] = []

    def add(disk: Path, arc: str):
        if disk.exists():
            pairs.append((disk, arc))

    add(ROOT / "README.md", "source/README.md")
    add(ROOT / ".env.example", "source/.env.example")
    add(ROOT / "requirements.txt", "source/requirements.txt")
    add(ROOT / "make_submission.py", "source/make_submission.py")
    for p in sorted((ROOT / "src").glob("*.py")):
        add(p, f"source/src/{p.name}")
    for p in sorted((ROOT / "scripts").glob("*.py")):
        add(p, f"source/scripts/{p.name}")
    for p in sorted((ROOT / "tests" / "golden").glob("*.json")):
        add(p, f"source/tests/golden/{p.name}")
    return pairs


def scan_for_secrets(pairs: list[tuple[Path, str]]):
    text_ext = {".py", ".md", ".txt", ".json", ".csv", ".env", ".example", ".html", ".js"}
    for disk, arc in pairs:
        if Path(arc).name == ".env":
            fail(f"refusing to bundle a .env file: {arc}")
        if disk.suffix.lower() in text_ext or disk.name == ".env.example":
            try:
                content = disk.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            if KEY_RE.search(content):
                fail(f"a Google API key was found in {arc} - aborting")


def main():
    print("Validating result CSVs...")
    l1 = OUT / "level1.csv"
    l2 = OUT / "level2.csv"
    if not l1.exists():
        fail("output/level1.csv not found - run the pipeline first")
    if not l2.exists():
        fail("output/level2.csv not found - run the pipeline first")
    check_level1(l1)
    check_level2(l2)

    pairs = [(l1, "output/level1.csv"), (l2, "output/level2.csv")]
    pairs += collect_source_files()

    # optional demo
    demo_dir = ROOT / "demo"
    if demo_dir.exists():
        for p in sorted(demo_dir.iterdir()):
            if p.suffix.lower() in (".mp4", ".mov", ".webm"):
                pairs.append((p, f"demo/{p.name}"))

    print("Scanning bundled files for secrets...")
    scan_for_secrets(pairs)

    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        for disk, arc in pairs:
            zf.write(disk, arc)

    # report
    print(f"\nBuilt {ZIP_PATH.name}:")
    total = 0
    with zipfile.ZipFile(ZIP_PATH) as zf:
        for info in zf.infolist():
            total += info.file_size
            print(f"  {info.file_size:>9,} B  {info.filename}")
    zbytes = ZIP_PATH.stat().st_size
    print(f"\n  files: {len(pairs)}   uncompressed: {total:,} B   zip: {zbytes:,} B "
          f"({zbytes / 1024 / 1024:.2f} MB)")
    if zbytes > MAX_BYTES:
        fail(f"ZIP is {zbytes/1024/1024:.2f} MB, over the 15 MB limit")

    # final guard: structure must be only output/ source/ demo/
    tops = {Path(a).parts[0] for _, a in pairs}
    if not tops <= {"output", "source", "demo"}:
        fail(f"unexpected top-level folders: {tops}")
    print("\nOK: ZIP contains only output/, source/" +
          (" and demo/" if demo_dir.exists() else "") +
          f", under 15 MB. Ready to upload: {ZIP_PATH}")


if __name__ == "__main__":
    main()
