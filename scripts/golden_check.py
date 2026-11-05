"""Compare our Level 1 output for KESC_0008 against the guide's golden JSON.

Numbers pass within +-1 (per scoring); text/dates must match exactly; charge
and tax lists are matched as multisets of (type, amount+-1).

    python -m scripts.run_level1          # produce the output first
    python -m scripts.golden_check
"""
import json

from src.config import GOLDEN_DIR, OUTPUT_DIR

SCALAR = ["provider", "tariff", "bill_month", "reading_date", "issue_date", "due_date"]
NUMERIC = [
    "sanctioned_load_kw", "previous_reading", "current_reading", "units_consumed",
    "total_charges", "total_taxes", "current_bill", "arrears",
    "payable_within_due_date", "payable_after_due_date",
]


def num_ok(a, b, tol=1.0) -> bool:
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    try:
        return abs(float(a) - float(b)) <= tol
    except (TypeError, ValueError):
        return False


def list_match(out_list, gold_list):
    out_list = list(out_list or [])
    used = [False] * len(out_list)
    matched = 0
    for ge in gold_list or []:
        for i, oe in enumerate(out_list):
            if (not used[i] and oe.get("type") == ge.get("type")
                    and num_ok(oe.get("amount"), ge.get("amount"))):
                used[i] = True
                matched += 1
                break
    exact = matched == len(gold_list or []) and len(out_list) == len(gold_list or [])
    return exact, matched, len(gold_list or []), len(out_list)


def main() -> None:
    bill = "KESC_0008"
    gold = json.loads((GOLDEN_DIR / f"{bill}.json").read_text(encoding="utf-8"))
    out_path = OUTPUT_DIR / "debug_level1" / f"{bill}.json"
    if not out_path.exists():
        raise SystemExit("Run 'python -m scripts.run_level1' first.")
    out = json.loads(out_path.read_text(encoding="utf-8"))

    rows, passed = [], 0
    for f in SCALAR:
        ok = out.get(f) == gold.get(f)
        rows.append((f, ok, out.get(f), gold.get(f)))
    for f in NUMERIC:
        ok = num_ok(out.get(f), gold.get(f))
        rows.append((f, ok, out.get(f), gold.get(f)))
    for f in ("charges", "taxes"):
        ok, m, g, o = list_match(out.get(f), gold.get(f))
        rows.append((f, ok, f"{m}/{g} matched (out has {o})", g))

    for f, ok, ov, gv in rows:
        print(f"[{'PASS' if ok else 'FAIL'}] {f}: got={ov!r} gold={gv!r}")
        passed += 1 if ok else 0

    print(f"\nGOLDEN SCORE: {passed}/{len(rows)} fields pass")
    if passed == len(rows):
        print("ALL FIELDS PASS ✔")


if __name__ == "__main__":
    main()
