import type { Bill } from './types'
const M = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
type N = number | null | undefined
export const pkr = (n: N, d = 2) => n == null ? '—' :
  `${n < 0 ? '−' : ''}Rs ${Math.abs(n).toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d })}`
export const num = (n: N) => n == null ? '—' : n.toLocaleString('en-US')
export const fmtDate = (s?: string | null) => { const m = s?.match(/^(\d{4})-(\d{2})-(\d{2})/); return m ? `${+m[3]} ${M[+m[2] - 1]} ${m[1]}` : '—' }
export const fmtMonth = (s?: string | null) => { const m = s?.match(/^(\d{4})-(\d{2})/); return m ? `${M[+m[2] - 1]} ${m[1]}` : '—' }
export const fmtStamp = (s?: string | null) => { const m = s?.match(/T(\d{2}:\d{2})/); return s && m ? `${fmtDate(s)}, ${m[1]}` : '—' }
export const label = (t: string) => t.replace(/_/g, ' ')
const P: Record<string, string> = {
  energy: 'bg-teal-100 text-teal-800 dark:bg-teal-900/40 dark:text-teal-300',
  fixed: 'bg-slate-100 text-slate-700 dark:bg-slate-700/50 dark:text-slate-300',
  fpa: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300',
  quarterly_adjustment: 'bg-violet-100 text-violet-800 dark:bg-violet-900/40 dark:text-violet-300',
  surcharge: 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-300',
  subsidy: 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300',
  gst: 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300',
  electricity_duty: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/40 dark:text-indigo-300',
  municipal_tax: 'bg-cyan-100 text-cyan-800 dark:bg-cyan-900/40 dark:text-cyan-300',
  other: 'bg-gray-100 text-gray-700 dark:bg-gray-700/50 dark:text-gray-300',
}
export const pillCls = (t: string) => P[t] ?? P.other
export const HUE: Record<string, string> = { energy: '#0F766E', fixed: '#64748B', fpa: '#B45309', quarterly_adjustment: '#7C3AED', surcharge: '#BE123C', subsidy: '#15803D', other: '#9CA3AF' }
const KEYS = ['provider','tariff','sanctioned_load_kw','bill_month','reading_date','issue_date','due_date','previous_reading','current_reading','units_consumed','charges','total_charges','taxes','total_taxes','current_bill','arrears','payable_within_due_date','payable_after_due_date']
export const missing = (b: Bill) => [
  ...KEYS.filter(k => !(k in b.level1)),
  ...b.level2.filter(q => !q.answer?.trim()).map(q => `${q.question_id} answer`),
]
