import type { Line } from '../types'
import { pkr } from '../utils'
import Pill from './Pill'
interface P { title: string; items: Line[]; total: number | null | undefined; totalLabel: string }
export default function ChargesCard({ title, items, total, totalLabel }: P) {
  return (
    <div className="card">
      <h2 className="h2">{title}</h2>
      {items.length === 0 && <p className="text-sm text-mute py-3">No items on this bill.</p>}
      {items.map((it, i) => {
        const neg = (it.amount ?? 0) < 0
        return (
          <div key={i} className="row">
            <Pill type={it.type} />
            <span className={`flex items-center gap-2 font-medium ${neg ? 'text-green-700 dark:text-green-400' : ''}`}>
              {neg && <span className="rounded-full bg-green-100 dark:bg-green-900/40 px-2 py-0.5 text-[11px]">credit</span>}{pkr(it.amount)}
            </span>
          </div>
        )
      })}
      <div className="flex items-center justify-between h-12 mt-2 px-3 rounded-lg bg-soft font-semibold text-sm"><span>{totalLabel}</span><span>{pkr(total)}</span></div>
    </div>
  )
}
