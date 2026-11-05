import type { Level1 } from '../types'
import { fmtDate, fmtMonth, num } from '../utils'
export default function BillSummary({ l }: { l: Level1 }) {
  const rows: [string, string][] = [
    ['Provider', l.provider ?? '—'], ['Tariff', l.tariff ?? '—'],
    ['Sanctioned load', l.sanctioned_load_kw == null ? '—' : `${l.sanctioned_load_kw} kW`], ['Bill month', fmtMonth(l.bill_month)],
    ['Reading date', fmtDate(l.reading_date)], ['Issue date', fmtDate(l.issue_date)], ['Due date', fmtDate(l.due_date)],
    ['Previous reading', num(l.previous_reading)], ['Current reading', num(l.current_reading)],
  ]
  return (
    <div className="card">
      <h2 className="h2">Bill summary</h2>
      <dl className="grid grid-cols-2 gap-x-8">
        {rows.map(([k, v]) => <div key={k} className="py-3.5 border-b border-line"><dt className="lab">{k}</dt><dd className="mt-1 text-[15px] font-medium">{v}</dd></div>)}
      </dl>
      <div className="mt-4 rounded-xl bg-soft px-6 py-5 flex items-baseline justify-between">
        <span className="lab !text-acc">Units consumed</span>
        <span className="text-4xl font-semibold tracking-tight text-acc">{num(l.units_consumed)} <span className="text-sm font-medium">kWh</span></span>
      </div>
    </div>
  )
}
