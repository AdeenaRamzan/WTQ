export interface Line { type: string; amount: number | null }
export interface Level1 {
  provider?: string | null; tariff?: string | null; sanctioned_load_kw?: number | null
  bill_month?: string | null; reading_date?: string | null; issue_date?: string | null; due_date?: string | null
  previous_reading?: number | null; current_reading?: number | null; units_consumed?: number | null
  charges?: Line[] | null; total_charges?: number | null; taxes?: Line[] | null; total_taxes?: number | null
  current_bill?: number | null; arrears?: number | null
  payable_within_due_date?: number | null; payable_after_due_date?: number | null
}
export interface QA { question_id: string; question: string; answer: string }
export interface Bill { bill_id: string; image?: string | null; level1: Level1; level2: QA[] }
export interface Report { generated_at?: string | null; bills: Bill[] }
