import { useState } from 'react'
import { ChevronDown, Copy, Check } from 'lucide-react'
import type { QA } from '../types'
export default function QAList({ items }: { items: QA[] }) {
  const [q, setQ] = useState(''), [open, setOpen] = useState<Set<string>>(new Set()), [copied, setCopied] = useState('')
  const f = items.filter(i => `${i.question} ${i.answer}`.toLowerCase().includes(q.toLowerCase()))
  const all = f.length > 0 && f.every(i => open.has(i.question_id))
  const toggle = (id: string) => setOpen(s => { const n = new Set(s); n.has(id) ? n.delete(id) : n.add(id); return n })
  const copy = (i: QA) => { navigator.clipboard?.writeText(i.answer); setCopied(i.question_id); setTimeout(() => setCopied(''), 1200) }
  return (
    <section className="card">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <h2 className="h2 !mb-0">Ask about this bill</h2>
        <div className="flex gap-2">
          <input value={q} onChange={e => setQ(e.target.value)} placeholder="Filter questions" aria-label="Filter questions" className="h-10 px-3 rounded-lg border border-line bg-bg text-sm" />
          <button className="btn" onClick={() => setOpen(all ? new Set() : new Set(f.map(i => i.question_id)))}>{all ? 'Collapse all' : 'Expand all'}</button>
        </div>
      </div>
      {f.length === 0 && <p className="text-sm text-mute">No questions to show.</p>}
      <div className="space-y-3">
        {f.map(i => {
          const on = open.has(i.question_id)
          return (
            <div key={i.question_id} className="border border-line rounded-2xl px-6 transition-colors duration-150 hover:border-acc">
              <div className="flex items-center gap-3 py-4">
                <button onClick={() => toggle(i.question_id)} aria-expanded={on} className="flex-1 flex items-center justify-between gap-4 text-left text-[15px] font-semibold">
                  {i.question}<ChevronDown size={18} strokeWidth={1.5} className={`shrink-0 transition-transform duration-200 ${on ? 'rotate-180' : ''}`} />
                </button>
                <span className="rounded-full bg-bg px-2 py-0.5 text-[11px] text-mute font-medium">{i.question_id}</span>
                <button onClick={() => copy(i)} aria-label="Copy answer" className="w-8 h-8 grid place-items-center rounded-lg border border-line hover:bg-soft">{copied === i.question_id ? <Check size={14} /> : <Copy size={14} strokeWidth={1.5} />}</button>
              </div>
              {on && <p className="fade text-[15px] leading-relaxed max-w-[70ch] pb-5 text-ink">{i.answer || '—'}</p>}
            </div>
          )
        })}
      </div>
    </section>
  )
}
