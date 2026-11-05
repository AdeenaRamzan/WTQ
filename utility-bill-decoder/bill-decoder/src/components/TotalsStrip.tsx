import type { Level1 } from '../types'
import { pkr } from '../utils'
export default function TotalsStrip({ l }: { l: Level1 }) {
  const late = l.payable_after_due_date != null && l.payable_within_due_date != null ? l.payable_after_due_date - l.payable_within_due_date : null
  const items: [string, string, string?][] = [
    ['Current bill', pkr(l.current_bill)], ['Arrears', pkr(l.arrears), (l.arrears ?? 0) < 0 ? 'text-green-700 dark:text-green-400' : ''],
    ['Payable by due date', pkr(l.payable_within_due_date)], ['Payable after due date', pkr(l.payable_after_due_date)],
    ['Late-payment difference', pkr(late), 'text-amber-700 dark:text-amber-400'],
  ]
  return (
    <section className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-4">
      {items.map(([k, v, c]) => <div key={k} className="card !p-5"><div className="lab">{k}</div><div className={`mt-2 text-2xl font-semibold tracking-tight ${c ?? ''}`}>{v}</div></div>)}
    </section>
  )
}
