"""Deterministic normalization & validation for Level 1.

All the "clean up as printed" rules live here (numbers, signs, dates, enums)
so they are code-verified and never left to the model. We never *recompute*
printed amounts - we only strip formatting and coerce types.
"""
from __future__ import annotations

import re
from typing import Optional

from pydantic import ValidationError

from . import config
from .schemas import CHARGE_TYPES, FIELD_ORDER, TAX_TYPES, BillLevel1

log = config.get_logger("validators")

_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}
_NULLISH = {"", "null", "none", "n/a", "na", "-", "--", "not to be paid"}


# ---------------------------------------------------------------------------
# Scalars
# ---------------------------------------------------------------------------
def clean_str(v) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip()
    if s.lower() in _NULLISH:
        return None
    return s


def to_number(v) -> Optional[float]:
    """Parse a printed amount into a float. Handles commas, Rs/PKR, CR (credit
    -> negative) and parentheses-negatives. Returns None when not numeric."""
    if v is None:
        return None
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if not isinstance(v, str):
        return None

    s = v.strip()
    if s.lower() in _NULLISH:
        return None

    neg = False
    if re.search(r"(?i)cr\b", s) or s.upper().endswith("CR"):
        neg = True
    s = re.sub(r"(?i)\bcr\b", "", s)
    s = re.sub(r"(?i)(rs\.?|pkr|rupees)", "", s)
    s = s.replace(",", "").strip()
    if s.startswith("(") and s.endswith(")"):
        neg = True
        s = s[1:-1]

    m = re.search(r"-?\d+(?:\.\d+)?", s)
    if not m:
        return None
    num = float(m.group())
    if neg:
        num = -abs(num)
    return num


def _yr(n: int) -> int:
    return n if n >= 100 else 2000 + n


def normalize_date(v, month_only: bool = False) -> Optional[str]:
    """Return YYYY-MM-DD (or YYYY-MM when month_only). None if unparseable."""
    if v is None:
        return None
    s = str(v).strip()
    if s.lower() in _NULLISH:
        return None

    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return s[:7] if month_only else s
    if re.fullmatch(r"\d{4}-\d{2}", s):
        return s if month_only else None

    s2 = re.sub(r"(?i)(\d+)(st|nd|rd|th)", r"\1", s)
    s2 = re.sub(r"[\/,.]", " ", s2).replace("-", " ")
    toks = [t for t in s2.split() if t]

    month = midx = None
    for i, t in enumerate(toks):
        key = t.lower()[:3]
        if key in _MONTHS:
            month, midx = _MONTHS[key], i
            break

    nums = [(i, int(t)) for i, t in enumerate(toks) if t.isdigit()]

    if month is None:
        vals = [n for _, n in nums]
        if month_only and len(vals) >= 2:
            yrs = [n for n in vals if n > 31]
            mos = [n for n in vals if 1 <= n <= 12]
            if yrs and mos:
                return f"{_yr(yrs[0]):04d}-{mos[0]:02d}"
        return None

    before = [n for i, n in nums if i < midx]
    after = [n for i, n in nums if i > midx]
    year = day = None
    for n in after:
        if n > 31 or year is None:
            year = n
            break
    for n in before:
        if n > 31 and year is None:
            year = n
        elif day is None:
            day = n
    if year is None:
        return None
    year = _yr(year)

    if month_only:
        return f"{year:04d}-{month:02d}"
    if day is None:
        return None
    return f"{year:04d}-{month:02d}-{day:02d}"


# ---------------------------------------------------------------------------
# Enum coercion
# ---------------------------------------------------------------------------
def coerce_charge_type(t) -> str:
    if not isinstance(t, str):
        return "other"
    k = t.strip().lower().replace(" ", "_")
    if k in ("fca", "fuel_price_adjustment", "fuel_cost_adjustment"):
        return "fpa"
    return k if k in CHARGE_TYPES else "other"


def coerce_tax_type(t) -> str:
    if not isinstance(t, str):
        return "other_tax"
    k = t.strip().lower().replace(" ", "_")
    if k in ("sales_tax", "gst_on_fpa"):
        return "gst"
    if k in ("ed", "duty"):
        return "electricity_duty"
    return k if k in TAX_TYPES else "other_tax"


def classify_charge_from_label(label) -> Optional[str]:
    """Deterministic charge classification from the printed label.
    Returns None when the label is unrecognised (caller falls back to model type)."""
    if not isinstance(label, str):
        return None
    l = label.lower()
    if "fixed" in l:
        return "fixed"
    if "fca" in l or "fpa" in l or "fuel" in l:
        return "fpa"
    if "quarter" in l or "qta" in l:
        return "quarterly_adjustment"
    if "surcharge" in l:
        return "surcharge"
    if "meter rent" in l or "service rent" in l or "meter charges" in l:
        return "meter_rent"
    if "subsid" in l or "relief" in l:
        return "subsidy"
    if ("variable" in l or "energy" in l or "cost of electricity" in l
            or "unit" in l or "electric" in l):
        return "energy"
    return None


def classify_tax_from_label(label) -> Optional[str]:
    """Deterministic tax classification from the printed label."""
    if not isinstance(label, str):
        return None
    l = label.lower().strip()
    if "electricity duty" in l or "elec duty" in l or l in ("ed", "e.d", "e.d."):
        return "electricity_duty"
    if "sales tax" in l or "gst" in l or "g.s.t" in l:
        return "gst"
    if "income tax" in l:
        return "income_tax"
    if "muct" in l or "kmc" in l or "municipal" in l or "local tax" in l:
        return "municipal_tax"
    if "further tax" in l or "extra tax" in l or "tv" in l or "fee" in l:
        return "other_tax"
    return None


# ---------------------------------------------------------------------------
# Full normalization
# ---------------------------------------------------------------------------
def _norm_list(items, is_tax: bool):
    """Normalize a charges/taxes list. The printed label drives classification
    deterministically; the model's own 'type' is only a fallback when the label
    is unrecognised. This removes run-to-run enum variance."""
    out = []
    for it in items or []:
        if not isinstance(it, dict):
            continue
        amt = to_number(it.get("amount"))
        if amt is None or amt == 0:  # guide: skip blank / zero lines
            continue
        label = it.get("label")
        if is_tax:
            typ = classify_tax_from_label(label) or coerce_tax_type(it.get("type"))
            out.append({"type": typ, "amount": amt})
        else:
            typ = classify_charge_from_label(label) or coerce_charge_type(it.get("type"))
            if typ == "subsidy":
                amt = -abs(amt)  # subsidies are deductions
            out.append({"type": typ, "amount": amt})
    return out


def normalize_level1(raw: dict, provider_hint: Optional[str] = None) -> dict:
    raw = raw or {}
    prov = raw.get("provider")
    if prov not in ("KE", "LESCO", "IESCO"):
        prov = provider_hint

    out = {
        "provider": prov,
        "tariff": clean_str(raw.get("tariff")),
        "sanctioned_load_kw": to_number(raw.get("sanctioned_load_kw")),
        "bill_month": normalize_date(raw.get("bill_month"), month_only=True),
        "reading_date": normalize_date(raw.get("reading_date")),
        "issue_date": normalize_date(raw.get("issue_date")),
        "due_date": normalize_date(raw.get("due_date")),
        "previous_reading": to_number(raw.get("previous_reading")),
        "current_reading": to_number(raw.get("current_reading")),
        "units_consumed": to_number(raw.get("units_consumed")),
        "charges": _norm_list(raw.get("charges"), is_tax=False),
        "total_charges": to_number(raw.get("total_charges")),
        "taxes": _norm_list(raw.get("taxes"), is_tax=True),
        "total_taxes": to_number(raw.get("total_taxes")),
        "current_bill": to_number(raw.get("current_bill")),
        "arrears": to_number(raw.get("arrears")),
        "payable_within_due_date": to_number(raw.get("payable_within_due_date")),
        "payable_after_due_date": to_number(raw.get("payable_after_due_date")),
    }

    # Combined-tax rule (guide 5.3): a single unclassified tax line that equals
    # (or stands in for) the tax subtotal means only a combined amount was
    # printed -> taxes=[] and the amount lives in total_taxes.
    tx, tt = out["taxes"], out["total_taxes"]
    if len(tx) == 1 and tx[0]["type"] == "other_tax":
        amt = tx[0]["amount"]
        if tt is None:
            out["total_taxes"] = amt
            out["taxes"] = []
        elif abs(amt - tt) <= 1:
            out["taxes"] = []

    return out


def _collapse(x):
    if isinstance(x, float) and x.is_integer():
        return int(x)
    return x


def to_output_dict(clean: dict) -> dict:
    """Ordered, JSON-ready dict with whole floats collapsed to ints."""
    d = {}
    for k in FIELD_ORDER:
        v = clean.get(k)
        if k in ("charges", "taxes"):
            d[k] = [{"type": e["type"], "amount": _collapse(e["amount"])}
                    for e in (v or [])]
        elif isinstance(v, (int, float)) and not isinstance(v, bool):
            d[k] = _collapse(v)
        else:
            d[k] = v
    return d


def build_level1(raw: dict, provider_hint: Optional[str] = None) -> dict:
    """Normalize -> validate (pydantic) -> ordered output dict."""
    clean = normalize_level1(raw, provider_hint)
    try:
        clean = BillLevel1(**clean).model_dump()
    except ValidationError as e:
        log.warning("pydantic validation issues (keeping normalized values): %s",
                    e.errors())
    return to_output_dict(clean)


def empty_level1(provider_hint: Optional[str] = None) -> dict:
    """Safe fallback: all nulls / empty lists, provider from filename if known."""
    return to_output_dict(normalize_level1({}, provider_hint))


# ---------------------------------------------------------------------------
# Sanity checks (log-only; never overwrite printed values)
# ---------------------------------------------------------------------------
def sanity_check(out: dict) -> list[str]:
    warns = []
    tc = out.get("total_charges")
    if tc is not None and out.get("charges"):
        s = sum(c["amount"] for c in out["charges"])
        if abs(s - tc) > max(1.0, 0.02 * abs(tc)):
            warns.append(f"sum(charges)={s:.2f} != total_charges={tc}")
    tt = out.get("total_taxes")
    if tt is not None and out.get("taxes"):
        s = sum(t["amount"] for t in out["taxes"])
        if abs(s - tt) > max(1.0, 0.02 * abs(tt)):
            warns.append(f"sum(taxes)={s:.2f} != total_taxes={tt}")
    return warns
