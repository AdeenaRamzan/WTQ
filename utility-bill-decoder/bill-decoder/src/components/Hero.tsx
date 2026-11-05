import { CalendarClock, CheckCircle2, AlertTriangle } from 'lucide-react'
import type { Level1 } from '../types'
import { fmtDate, pkr } from '../utils'
export default function Hero({ l, miss }: { l: Level1; miss: string[] }) {
  const ok = miss.length === 0
  return (
    <section className="card flex flex-wrap items-end justify-between gap-6">
      <div>
        <div className="lab">Amount due</div>
        <div className="text-5xl md:text-6xl font-semibold tracking-tight my-2">{pkr(l.payable_within_due_date, 0)}</div>
        <div className="flex flex-wrap gap-2 mt-4">
          <span className="inline-flex items-center gap-1.5 rounded-full bg-tint text-[#4F46E5] dark:text-acc px-3.5 py-1.5 text-[13px] font-medium"><CalendarClock size={14} strokeWidth={1.5} />Due {fmtDate(l.due_date)}</span>
          <span className="rounded-full bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300 px-3.5 py-1.5 text-[13px] font-medium">After due date: {pkr(l.payable_after_due_date, 0)}</span>
        </div>
      </div>
      <span title={ok ? 'All 18 fields and answers present' : `Missing: ${miss.join(', ')}`}
        className={`inline-flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-[13px] font-medium ${ok ? 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300' : 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300'}`}>
        {ok ? <CheckCircle2 size={14} /> : <AlertTriangle size={14} />}{ok ? 'All fields present' : `Data checks: ${miss.length} missing`}
      </span>
    </section>
  )
}
