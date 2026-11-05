"""Level 2 step A: extract a rich 'bill facts' JSON (history, FPA, late fees,
net-metering signals) with one cached vision call per bill."""
from __future__ import annotations

import json
import re
from typing import Optional

from . import config
from .llm_client import LLMClient

log = config.get_logger("facts")

SYSTEM = (
    "You extract structured facts from Pakistani electricity bills (KE, LESCO, "
    "IESCO). You read the ENGLISH labels, transcribe values exactly as printed, "
    "and output only one JSON object. Use null when a value is absent/unreadable."
)

PROMPT = """Read this electricity bill image and return ONE JSON object (no markdown) with these keys:

{
  "provider": "KE | LESCO | IESCO",
  "bill_month": "YYYY-MM",
  "current_units": number,                      // units billed this month
  "current_bill_amount": number,                // this month's bill (before arrears)
  "cost_per_unit_hint": number|null,            // current_bill_amount / current_units if both known, else null
  "is_net_metered": true|false,                 // true if solar / net metering connection
  "net_metering_evidence": "string|null",       // e.g. "NET METERING CONNECTION printed", "Net Metering Benefit line", "Import/Export rows", or null
  "fpa_amount": number|null,                     // Fuel Price/Cost Adjustment (FPA or FCA) amount
  "fpa_month": "string|null",                    // month the FPA/FCA is for, as printed (e.g. "Feb-26")
  "payable_within_due_date": number|null,
  "payable_after_due_date": number|null,         // highest late amount if several
  "late_payment_surcharges": [                    // each distinct late-payment surcharge line
    {"label": "string", "amount": number}
  ],
  "history": [                                    // the 12/13-month usage & payment history, OLDEST first (left to right)
    {"month": "string as printed e.g. Aug 25", "units": number|null, "billed": number|null, "paid": number|null}
  ]
}

RULES:
- Transcribe exactly as printed; remove commas/currency. A value with "CR" is a credit -> negative.
- history: include every month shown in the usage-history chart and/or the bill/payment history table, in chronological order (oldest first). Put units, billed amount and payment where available; use null where a column is absent. Read the number printed for each month/bar carefully.
- is_net_metered: true if the bill says "NET METERING", shows a "Net Metering Benefit", has Import/Export energy rows, or customer type NM. Otherwise false.
- late_payment_surcharges: capture each late surcharge (e.g. "Late Payment Surcharge (5%)", "LP Surcharge", "After <date>") with its amount. If none, use [].
- Do NOT output names, addresses, or ID/account/meter numbers.

Return ONLY the JSON object."""


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


def extract_facts(client: LLMClient, image: tuple[bytes, str], bill_id: str) -> dict:
    """Return a facts dict. Never raises - returns a minimal dict on failure."""
    try:
        text = client.generate(
            PROMPT, image=image, json_mode=True, temperature=0.0,
            system_instruction=SYSTEM, cache_key_extra="facts:" + bill_id,
        )
        facts = _parse_json(text)
        if not isinstance(facts, dict):
            raise ValueError("facts not a dict")
        facts.setdefault("history", [])
        facts.setdefault("late_payment_surcharges", [])
        return facts
    except Exception as exc:  # noqa: BLE001
        log.error("[%s] facts extraction failed: %s", bill_id, exc)
        return {"provider": None, "history": [], "late_payment_surcharges": [],
                "_error": str(exc)}
