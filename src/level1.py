"""Level 1: extract one structured JSON object per bill (guide section 5)."""
from __future__ import annotations

import json
import re
from typing import Optional

from . import config
from .llm_client import LLMClient
from .validators import build_level1, empty_level1, sanity_check

log = config.get_logger("level1")

SYSTEM = (
    "You are a meticulous data-extraction engine for Pakistani electricity "
    "bills issued by K-Electric (KE), LESCO and IESCO. You read the ENGLISH "
    "printed labels on the bill image, even when parts of the bill are in Urdu "
    "or the image is tilted. You transcribe values EXACTLY as printed and never "
    "calculate, round or correct them. You output only a single JSON object."
)

PROMPT_TEMPLATE = """Extract the following fields from this electricity bill image and return ONE JSON object with EXACTLY these keys (no extra keys, no markdown):

{{
  "provider": "KE | LESCO | IESCO",
  "tariff": string,
  "sanctioned_load_kw": number,
  "bill_month": "YYYY-MM",
  "reading_date": "YYYY-MM-DD",
  "issue_date": "YYYY-MM-DD",
  "due_date": "YYYY-MM-DD",
  "previous_reading": number,
  "current_reading": number,
  "units_consumed": number,
  "charges": [{{"label": "<exact printed label>", "type": "energy|fixed|fpa|quarterly_adjustment|surcharge|meter_rent|subsidy|other", "amount": number}}],
  "total_charges": number,
  "taxes": [{{"label": "<exact printed label>", "type": "gst|electricity_duty|income_tax|municipal_tax|other_tax", "amount": number}}],
  "total_taxes": number,
  "current_bill": number,
  "arrears": number,
  "payable_within_due_date": number,
  "payable_after_due_date": number
}}

GENERAL RULES:
- Transcribe values EXACTLY as printed. Do NOT recalculate, round or correct anything.
- Numbers only for numeric fields (no quotes, no commas, no currency). "Rs. 19,964" -> 19964.
- When a charge/tax line sits in a table with Units / Rate / Amount columns, take the value from the AMOUNT (rightmost) column - NEVER the Units or Rate column. E.g. a "Fixed Charges" row showing Units 5, Rate 675, Amount 3375 has amount 3375.
- Credits and subsidies are NEGATIVE. A value shown as "38209CR" -> -38209. A subsidy/relief amount -> negative. This applies to EVERY field, including arrears, current_bill and the payable amounts: a "Payable within due date" of "54770CR" MUST be -54770. Never drop the CR.
- Dates: reading_date, issue_date, due_date as YYYY-MM-DD. bill_month as YYYY-MM. ("22nd Sep 2026" -> "2026-09-22"; "MAR 2026" -> "2026-03"; "07-Apr-2026" -> "2026-04-07").
- Use null when a value is not printed, is blank, is covered by a grey/black box, or is unreadable. DO NOT GUESS. Use [] for an empty list.
- NEVER output personal identifiers (names, address, CNIC, account/reference/consumer/meter numbers). They are not part of the schema.
- For EVERY entry in charges and taxes, also include "label": the EXACT printed label text of that line (e.g. "Electricity Duty", "Sales Tax u/s 3(1)", "Variable Upto 100 Units (Protected)"). Still give your best "type"; the label is used to verify the classification.

FIELD GUIDANCE:
- provider: this bill's filename indicates provider = "{provider_hint}". Use it unless the printed logo clearly says otherwise. K-Electric -> "KE".
- tariff: the tariff code exactly as printed (e.g. "A1-R", "A-1a(01)", "A-2a(04)", "A-1b(03)T").
- sanctioned_load_kw: the "Sanc Load" / "San Load" / "S.Load" value as a number.
- previous_reading / current_reading: the printed meter readings. If the bill shows MULTIPLE meter reading rows (e.g. net metering), use the FIRST (top) row's previous and current readings. Do not return null when any reading row is visible.
- units_consumed: the TOTAL units billed for the current month. ALWAYS prefer the single prominent total when shown - e.g. K-Electric prints a large "Current Month  901 units" (use 901); other bills show a "Units" total. Only if NO single total units figure is shown anywhere (some net-metering bills) use the FIRST meter row's units.

CHARGES (one entry per printed line in the charges / "Bill Calculation" section; skip blank lines and lines printed as 0; KEEP duplicate types as separate entries e.g. two energy lines = two energy entries):
- energy: cost of units used (e.g. "Variable Upto ... Units", "Cost of Electricity", "Energy Charges", "Variable Off Peak", "Variable Peak").
- fixed: "Fixed Charges".
- fpa: Fuel Price Adjustment. Use "fpa" for BOTH FPA and FCA (and "Total FPA").
- quarterly_adjustment: "QTA" / "Uniform Quarterly Adjustment".
- surcharge: surcharges e.g. "Additional Surcharge (PHL)", "F.C Surcharge".
- meter_rent: meter rent / service rent.
- subsidy: government subsidy or relief lines (amount NEGATIVE).
- other: any other charge line.
- total_charges: the printed charges subtotal (e.g. "Electricity Charges", "Net Electricity Charges", "Total Electricity Charges"), or null if no subtotal is printed.

TAXES (one entry per printed line in the tax / government section; classify a line by the SECTION it is printed in, not its name):
- gst: sales tax / GST, including GST on FPA.
- electricity_duty: electricity duty (often "ED").
- income_tax: income tax.
- municipal_tax: municipal / local charges under taxes, e.g. "MUCT (KMC)".
- other_tax: any other tax line (extra tax, further tax, TV fee).
- IMPORTANT: if ONLY a single combined tax amount is printed (e.g. just "Taxes 15.24%"), set "taxes": [] and put that amount in "total_taxes".
- total_taxes: the printed tax subtotal (e.g. "Taxes and Duties", "Taxes"), or null if none.

OTHER FIELDS:
- current_bill: the printed amount for THIS month's bill (e.g. "Electricity Charges for current month", "Current Bill").
- arrears: previous dues / arrears carried forward. Keep the printed sign (a credit -> negative). null if blank.
- payable_within_due_date: the amount payable by the due date.
- payable_after_due_date: the amount payable after the due date. If several late-payment amounts are shown, use the HIGHEST.

SPECIAL LAYOUT - compact "Bill Charges Breakdown" (common on LESCO and IESCO):
Some bills do NOT itemize energy slabs. They show a compact breakdown, e.g.:
  Total Electricity Charges <A>
  Subsidies <S>                 (may be blank / not printed)
  Net Electricity Charges <N>
  Taxes <pct>% <T>
  Current Bill <C>
alongside a side column listing Arrears, Installment, Adjustments, W.E Credit, Lock Open Credit, Total FPA, Grand Total.
For this layout:
- charges = [{{"type":"energy","amount":<A>}}]; and ONLY if a Subsidies amount is printed, also add {{"type":"subsidy","amount": -<S>}}.
- total_charges = <N> (Net Electricity Charges).
- The single "Taxes" figure is a COMBINED tax amount: set "taxes": [] and "total_taxes": <T>.
- Do NOT treat Total FPA, Arrears, Installment, Adjustments, W.E Credit, Lock Open Credit or Grand Total as charge lines. (Arrears belongs in the "arrears" field; Total FPA is informational and already included in Total Electricity Charges.)

Return ONLY the JSON object."""


def provider_from_bill_id(bill_id: str) -> Optional[str]:
    up = bill_id.upper()
    if up.startswith("KESC") or up.startswith("KE"):
        return "KE"
    if up.startswith("LESCO"):
        return "LESCO"
    if up.startswith("IESCO"):
        return "IESCO"
    return None


def _parse_json(text: str) -> dict:
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z]*", "", t).strip()
        if t.endswith("```"):
            t = t[:-3].strip()
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        i, j = t.find("{"), t.rfind("}")
        if i != -1 and j != -1 and j > i:
            return json.loads(t[i:j + 1])
        raise


def extract_level1(client: LLMClient, image: tuple[bytes, str], bill_id: str):
    """Return (output_dict, warnings). Never raises - falls back to nulls."""
    hint = provider_from_bill_id(bill_id)
    prompt = PROMPT_TEMPLATE.format(provider_hint=hint or "unknown")
    try:
        text = client.generate(
            prompt, image=image, json_mode=True, temperature=0.0,
            system_instruction=SYSTEM, cache_key_extra=bill_id,
        )
        raw = _parse_json(text)
        out = build_level1(raw, hint)
        warns = sanity_check(out)
        for w in warns:
            log.warning("[%s] %s", bill_id, w)
        return out, warns
    except Exception as exc:  # noqa: BLE001
        log.error("[%s] level1 extraction failed: %s", bill_id, exc)
        return empty_level1(hint), [f"extraction failed: {exc}"]
