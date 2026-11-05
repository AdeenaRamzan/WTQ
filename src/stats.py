"""Level 2 step B: compute verified statistics from the facts in plain Python.

The LLM never does the arithmetic for the mechanical questions - it only
phrases answers around these code-computed numbers.
"""
from __future__ import annotations

import re
from typing import Optional

from . import config
from .validators import normalize_date, to_number

log = config.get_logger("stats")

_SUMMER = {6, 7, 8}
_WINTER = {12, 1, 2}


def _ym(label) -> Optional[tuple[int, int]]:
    """Parse a history month label like 'Aug 25' / 'JUL26' -> (year, month)."""
    if label is None:
        return None
    s = str(label)
    s = re.sub(r"(?<=[A-Za-z])(?=\d)", " ", s)  # 'Jul26' -> 'Jul 26'
    s = re.sub(r"(?<=\d)(?=[A-Za-z])", " ", s)
    iso = normalize_date(s, month_only=True)
    if not iso:
        return None
    y, m = iso.split("-")
    return int(y), int(m)


def _round(x, nd=0):
    if x is None:
        return None
    r = round(float(x), nd)
    return int(r) if nd == 0 else r


def compute_stats(facts: dict) -> dict:
    """Return a dict of verified stats derived from facts['history'] + current."""
    hist_raw = facts.get("history") or []
    entries = []
    for h in hist_raw:
        if not isinstance(h, dict):
            continue
        units = to_number(h.get("units"))
        billed = to_number(h.get("billed"))
        paid = to_number(h.get("paid"))
        ym = _ym(h.get("month"))
        entries.append({
            "label": h.get("month"), "ym": ym,
            "units": units, "billed": billed, "paid": paid,
        })

    dated = [e for e in entries if e["ym"] is not None]
    dated.sort(key=lambda e: e["ym"])

    unit_entries = [e for e in entries if e["units"] is not None]
    units_vals = [e["units"] for e in unit_entries]

    s: dict = {}
    s["history_months"] = len(entries)
    s["history"] = [
        {"month": e["label"], "units": e["units"],
         "billed": e["billed"], "paid": e["paid"]} for e in entries
    ]

    current_units = to_number(facts.get("current_units"))
    current_bill = to_number(facts.get("current_bill_amount"))
    s["current_units"] = current_units
    s["current_bill_amount"] = current_bill

    # averages & extremes (historical units)
    if units_vals:
        avg = sum(units_vals) / len(units_vals)
        s["avg_units"] = _round(avg, 1)
        mx = max(unit_entries, key=lambda e: e["units"])
        mn = min(unit_entries, key=lambda e: e["units"])
        s["max_units"] = {"month": mx["label"], "units": mx["units"]}
        s["min_units"] = {"month": mn["label"], "units": mn["units"]}
        if current_units is not None:
            s["current_vs_avg_diff"] = _round(current_units - avg, 1)
            s["current_vs_avg_pct"] = _round((current_units - avg) / avg * 100, 1) if avg else None
    else:
        s["avg_units"] = s["max_units"] = s["min_units"] = None

    # last 3 historical months + direction
    last3 = [e for e in dated if e["units"] is not None][-3:]
    s["last_3_months"] = [{"month": e["label"], "units": e["units"]} for e in last3]
    if len(last3) >= 2:
        delta = last3[-1]["units"] - last3[0]["units"]
        s["last_3_direction"] = ("up" if delta > 0 else "down" if delta < 0 else "flat")
        s["last_3_change"] = _round(delta, 1)
        s["next_month_estimate_units"] = _round(sum(e["units"] for e in last3) / len(last3), 0)

    # year-over-year (same calendar month, previous year)
    cur_ym = _ym(facts.get("bill_month")) or (dated[-1]["ym"] if dated else None)
    s["current_ym"] = f"{cur_ym[0]:04d}-{cur_ym[1]:02d}" if cur_ym else None
    if cur_ym and current_units is not None:
        yoy = next((e for e in dated if e["ym"] == (cur_ym[0] - 1, cur_ym[1])
                    and e["units"] is not None), None)
        if yoy:
            s["same_month_last_year"] = {"month": yoy["label"], "units": yoy["units"]}
            s["yoy_diff"] = _round(current_units - yoy["units"], 1)

    # last month (most recent historical month strictly before current)
    if cur_ym:
        before = [e for e in dated if e["ym"] < cur_ym]
        if before:
            lm = before[-1]
            s["last_month"] = {"month": lm["label"], "units": lm["units"], "billed": lm["billed"]}

    # summer vs winter (by month number)
    summer = [e["units"] for e in dated if e["ym"][1] in _SUMMER and e["units"] is not None]
    winter = [e["units"] for e in dated if e["ym"][1] in _WINTER and e["units"] is not None]
    if summer:
        s["summer_avg_units"] = _round(sum(summer) / len(summer), 1)
        s["summer_months_count"] = len(summer)
    if winter:
        s["winter_avg_units"] = _round(sum(winter) / len(winter), 1)
        s["winter_months_count"] = len(winter)
    if summer and winter:
        s["summer_minus_winter_avg"] = _round(sum(summer) / len(summer) - sum(winter) / len(winter), 1)

    # cost per unit & bill estimate helpers
    if current_units and current_bill and current_units != 0:
        s["cost_per_unit"] = _round(current_bill / current_units, 2)

    # spread evenly: mean of available billed amounts
    billed_vals = [e["billed"] for e in entries if e["billed"] is not None]
    if billed_vals:
        s["avg_monthly_bill"] = _round(sum(billed_vals) / len(billed_vals), 0)

    # payment consistency
    pay_pairs = [(e["billed"], e["paid"]) for e in entries
                 if e["billed"] is not None and e["paid"] is not None]
    if pay_pairs:
        paid_count = sum(1 for b, p in pay_pairs if p and abs(p) > 0)
        s["months_with_billed_and_paid"] = len(pay_pairs)
        s["months_paid"] = paid_count
        s["all_bills_paid"] = paid_count == len(pay_pairs)

    # passthrough facts the answerer needs verbatim
    s["is_net_metered"] = facts.get("is_net_metered")
    s["net_metering_evidence"] = facts.get("net_metering_evidence")
    s["fpa_amount"] = to_number(facts.get("fpa_amount"))
    s["fpa_month"] = facts.get("fpa_month")
    s["payable_within_due_date"] = to_number(facts.get("payable_within_due_date"))
    s["payable_after_due_date"] = to_number(facts.get("payable_after_due_date"))
    s["late_payment_surcharges"] = facts.get("late_payment_surcharges") or []
    return s
