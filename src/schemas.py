"""Pydantic models and enums for Level 1 output (guide section 5.1)."""
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict

CHARGE_TYPES = (
    "energy", "fixed", "fpa", "quarterly_adjustment",
    "surcharge", "meter_rent", "subsidy", "other",
)
TAX_TYPES = (
    "gst", "electricity_duty", "income_tax", "municipal_tax", "other_tax",
)

# Canonical output key order (matches guide 5.1 exactly).
FIELD_ORDER = [
    "provider", "tariff", "sanctioned_load_kw", "bill_month",
    "reading_date", "issue_date", "due_date",
    "previous_reading", "current_reading", "units_consumed",
    "charges", "total_charges", "taxes", "total_taxes",
    "current_bill", "arrears", "payable_within_due_date", "payable_after_due_date",
]


class Charge(BaseModel):
    type: Literal[
        "energy", "fixed", "fpa", "quarterly_adjustment",
        "surcharge", "meter_rent", "subsidy", "other",
    ]
    amount: float


class Tax(BaseModel):
    type: Literal["gst", "electricity_duty", "income_tax", "municipal_tax", "other_tax"]
    amount: float


class BillLevel1(BaseModel):
    model_config = ConfigDict(extra="ignore")

    provider: Optional[Literal["KE", "LESCO", "IESCO"]] = None
    tariff: Optional[str] = None
    sanctioned_load_kw: Optional[float] = None
    bill_month: Optional[str] = None
    reading_date: Optional[str] = None
    issue_date: Optional[str] = None
    due_date: Optional[str] = None
    previous_reading: Optional[float] = None
    current_reading: Optional[float] = None
    units_consumed: Optional[float] = None
    charges: List[Charge] = []
    total_charges: Optional[float] = None
    taxes: List[Tax] = []
    total_taxes: Optional[float] = None
    current_bill: Optional[float] = None
    arrears: Optional[float] = None
    payable_within_due_date: Optional[float] = None
    payable_after_due_date: Optional[float] = None
