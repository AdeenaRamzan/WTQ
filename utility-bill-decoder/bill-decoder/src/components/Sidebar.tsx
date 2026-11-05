import { Search } from 'lucide-react'
import type { Bill } from '../types'
import { fmtMonth, missing } from '../utils'
interface P { bills: Bill[]; all: Bill[]; sel: string; q: string; onQ: (s: string) => void; onSel: (id: string) => void }
export default function Sidebar({ bills, all, sel, q, onQ, onSel }: P) {
  return (
    <aside className="md:w-[280px] md:shrink-0 md:border-r border-line md:bg-card p-4 md:p-5">
      <select className="md:hidden w-full h-11 rounded-lg border border-line bg-card px-3 text-sm" value={sel} onChange={e => onSel(e.target.value)} aria-label="Select bill">
        {all.map(b => <option key={b.bill_id} value={b.bill_id}>{b.bill_id} · {fmtMonth(b.level1.bill_month)}</option>)}
      </select>
      <div className="hidden md:block">
        <label className="relative block mb-4">
          <Search size={16} strokeWidth={1.5} className="absolute left-3 top-3 text-mute" />
          <input value={q} onChange={e => onQ(e.target.value)} placeholder="Search bills" aria-label="Search bills" className="w-full h-10 pl-9 pr-3 rounded-lg border border-line bg-bg text-sm" />
        </label>
        <ul className="space-y-1">
          {bills.map(b => {
            const on = b.bill_id === sel, ok = missing(b).length === 0
            return (
              <li key={b.bill_id}>
                <button onClick={() => onSel(b.bill_id)} className={`w-full flex items-center justify-between gap-2 px-4 py-3 rounded-xl text-left border-l-[3px] transition-colors duration-150 ${on ? 'bg-soft border-acc' : 'border-transparent hover:bg-soft'}`}>
                  <span><span className="block text-sm font-semibold">{b.bill_id}</span><span className="text-xs text-mute">{fmtMonth(b.level1.bill_month)}</span></span>
                  <span className="flex items-center gap-2">
                    <span className="rounded-full px-2 py-0.5 text-xs font-medium bg-tint text-acc">{b.level1.provider ?? '—'}</span>
                    <span className={`w-2 h-2 rounded-full ${ok ? 'bg-green-600' : 'bg-amber-600'}`} title={ok ? 'All fields present' : 'Missing data'} />
                  </span>
                </button>
              </li>
            )
          })}
          {!bills.length && <li className="text-sm text-mute px-2">No matches</li>}
        </ul>
      </div>
    </aside>
  )
}
