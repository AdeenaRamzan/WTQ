"""Level 2 step C: answer all 12 questions for a bill in one LLM call, grounded
in code-computed stats + extracted facts."""
from __future__ import annotations

import json
import re

from . import config
from .llm_client import LLMClient

log = config.get_logger("level2")

SYSTEM = (
    "You are a helpful assistant that explains a customer's electricity bill in "
    "plain English. You answer ONLY from the data provided (extracted facts and "
    "pre-computed statistics from THIS bill). You never use outside tariff or "
    "rate knowledge. You give specific, concise answers with correct numbers."
)

FALLBACK = "This could not be determined from the information shown on the bill."

PROMPT_TEMPLATE = """Here are verified, code-computed statistics and facts for ONE electricity bill (all numbers already calculated from the bill; trust them):

{stats_json}

Answer the following customer questions. Return ONE JSON object: {{"answers": [{{"question_id": "Q1", "answer": "..."}}, ...]}} with an entry for EVERY question id.

QUESTIONS:
{questions}

RULES FOR ANSWERS:
- Use the numbers from the stats above. Do not invent or recalculate differently. Round money to whole PKR and units sensibly.
- Ground every answer ONLY in this bill's data. If a needed value is not present in the stats/facts, say clearly that the bill does not show it - do not guess.
- For any estimate or forecast (e.g. expected next-month units, money to set aside, a projected bill), SAY it is an estimate and briefly state how it was derived (e.g. "average of the last 3 months").
- If a question is ambiguous, state the interpretation you used.
- Plain English, even if the bill is partly in Urdu. Be specific and concise (1-4 sentences). No personal identifiers.
- NEVER mention internal field names, variable names, JSON keys, or the words "stats"/"facts" in your answer. Describe evidence in natural terms a customer understands - e.g. for net metering say "the bill shows no net-metering label and no import/export meter rows", not "is_net_metered is false".
- Q guidance: net-metered is indicated by is_net_metered/net_metering_evidence; "highest units month" = max_units; "average monthly units" = avg_units with current_vs_avg comparison; year-over-year uses same_month_last_year; summer vs winter uses summer_avg_units/winter_avg_units/summer_minus_winter_avg; "paying every bill" uses months_paid/months_with_billed_and_paid/all_bills_paid; "up or down last 3 months" uses last_3_months/last_3_direction; "expect next month" uses next_month_estimate_units (estimate); "set aside each month" uses avg_monthly_bill (estimate); "same units as last month -> bill" uses last_month.billed (or cost_per_unit x last_month.units) as an estimate; FPA uses fpa_amount/fpa_month; late surcharges use late_payment_surcharges / payable_after_due_date.

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


def _questions_block(questions: list[tuple[str, str]]) -> str:
    return "\n".join(f"{qid}: {q}" for qid, q in questions)


def _ask(client: LLMClient, stats: dict, questions: list[tuple[str, str]],
         bill_id: str, extra: str) -> dict[str, str]:
    prompt = PROMPT_TEMPLATE.format(
        stats_json=json.dumps(stats, ensure_ascii=False, indent=1),
        questions=_questions_block(questions),
    )
    text = client.generate(
        prompt, json_mode=True, temperature=0.0,
        system_instruction=SYSTEM, cache_key_extra=f"l2:{bill_id}:{extra}",
    )
    data = _parse_json(text)
    out = {}
    for item in data.get("answers", []):
        qid = str(item.get("question_id", "")).strip()
        ans = (item.get("answer") or "").strip()
        if qid and ans:
            out[qid] = ans
    return out


def answer_questions(client: LLMClient, stats: dict,
                     questions: list[tuple[str, str]], bill_id: str) -> dict[str, str]:
    """Return {question_id: answer} for all questions. Never raises; fills any
    gap with an honest fallback."""
    answers: dict[str, str] = {}
    try:
        answers = _ask(client, stats, questions, bill_id, "all")
    except Exception as exc:  # noqa: BLE001
        log.error("[%s] level2 answering failed: %s", bill_id, exc)

    missing = [(qid, q) for qid, q in questions if qid not in answers]
    if missing:
        log.warning("[%s] retrying %d missing answers: %s",
                    bill_id, len(missing), [q for q, _ in missing])
        try:
            answers.update(_ask(client, stats, missing, bill_id, "retry"))
        except Exception as exc:  # noqa: BLE001
            log.error("[%s] level2 retry failed: %s", bill_id, exc)

    for qid, _ in questions:
        if qid not in answers or not answers[qid].strip():
            answers[qid] = FALLBACK
    return answers
