import { useState } from 'react'
import { ChevronDown, Copy } from 'lucide-react'
import type { Bill } from '../types'
export default function RawJson({ bill }: { bill: Bill }) {
  const [open, setOpen] = useState(false), txt = JSON.stringify(bill, null, 2)
  return (
    <section className="card !py-5">
      <div className="flex items-center justify-between">
        <button onClick={() => setOpen(!open)} aria-expanded={open} className="flex items-center gap-2 font-semibold text-base"><ChevronDown size={18} strokeWidth={1.5} className={`transition-transform ${open ? 'rotate-180' : ''}`} />Raw JSON</button>
        <button className="btn !h-9" onClick={() => navigator.clipboard?.writeText(txt)}><Copy size={14} strokeWidth={1.5} />Copy</button>
      </div>
      {open && <pre className="fade mt-4 max-h-96 overflow-auto rounded-xl bg-bg border border-line p-4 text-xs font-mono leading-relaxed">{txt}</pre>}
    </section>
  )
}
