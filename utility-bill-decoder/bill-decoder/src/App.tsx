import { useEffect, useState } from 'react'
import { ZoomIn } from 'lucide-react'
import type { Bill, Report } from './types'
import { fmtMonth, missing } from './utils'
import TopBar from './components/TopBar'
import Sidebar from './components/Sidebar'
import Hero from './components/Hero'
import BillSummary from './components/BillSummary'
import ChargesCard from './components/ChargesCard'
import TaxesCard from './components/TaxesCard'
import TotalsStrip from './components/TotalsStrip'
import ShareChart from './components/ShareChart'
import QAList from './components/QAList'
import RawJson from './components/RawJson'
import ZoomModal from './components/ZoomModal'
import EmptyState from './components/EmptyState'

function parse(text: string): Report {
  const j = JSON.parse(text)
  if (!j || !Array.isArray(j.bills)) throw new Error('Expected a "bills" array.')
  const bills: Bill[] = j.bills.filter((b: Bill) => b && b.bill_id).map((b: Bill) => ({ ...b, level1: b.level1 ?? {}, level2: Array.isArray(b.level2) ? b.level2 : [] }))
  return { generated_at: j.generated_at ?? null, bills }
}

export default function App() {
  const [report, setReport] = useState<Report | null>(null)
  const [err, setErr] = useState<string>()
  const [loading, setLoading] = useState(true)
  const [sel, setSel] = useState('')
  const [q, setQ] = useState('')
  const [dark, setDark] = useState(false)
  const [zoom, setZoom] = useState(false)
  const [imgOk, setImgOk] = useState(true)

  const apply = (t: string) => {
    try { const r = parse(t); setReport(r); setSel(r.bills[0]?.bill_id ?? ''); setErr(undefined) }
    catch (e) { setReport(null); setErr(`That file is not a valid report (${(e as Error).message}).`) }
  }
  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}data/report.json`).then(r => { if (!r.ok) throw new Error('missing'); return r.text() })
      .then(apply).catch(() => setErr('report.json was not found or could not be read.')).finally(() => setLoading(false))
  }, [])
  useEffect(() => { document.documentElement.classList.toggle('dark', dark) }, [dark])
  useEffect(() => setImgOk(true), [sel])

  const bills = report?.bills ?? []
  const bill = bills.find(b => b.bill_id === sel) ?? bills[0]
  const shown = bills.filter(b => `${b.bill_id} ${fmtMonth(b.level1.bill_month)} ${b.level1.provider ?? ''}`.toLowerCase().includes(q.toLowerCase()))
  const img = bill?.image ? `${import.meta.env.BASE_URL}data/${bill.image}` : ''

  return (
    <div className="min-h-screen">
      <TopBar generatedAt={report?.generated_at} dark={dark} onTheme={() => setDark(!dark)} onFile={f => f.text().then(apply)} />
      {loading ? (
        <div className="max-w-page mx-auto p-8 space-y-6"><div className="skel h-40" /><div className="grid md:grid-cols-2 gap-6"><div className="skel h-96" /><div className="skel h-96" /></div></div>
      ) : !bill ? <div className="p-6"><EmptyState reason={err ?? 'The report contains no bills.'} /></div> : (
        <div className="md:flex">
          <Sidebar bills={shown} all={bills} sel={bill.bill_id} q={q} onQ={setQ} onSel={setSel} />
          <main key={bill.bill_id} className="fade flex-1 min-w-0 p-4 md:p-8">
            <div className="max-w-page mx-auto space-y-6">
              <Hero l={bill.level1} miss={missing(bill)} />
              <section className="grid lg:grid-cols-2 gap-6">
                <div className="card !p-4">
                  {img && imgOk ? (
                    <button onClick={() => setZoom(true)} className="relative block w-full rounded-xl overflow-hidden border border-line group" aria-label="Zoom bill image">
                      <img src={img} alt={`Bill ${bill.bill_id}`} onError={() => setImgOk(false)} className="w-full" />
                      <span className="absolute right-3 bottom-3 rounded-full bg-card/90 border border-line p-2 opacity-0 group-hover:opacity-100 transition-opacity"><ZoomIn size={16} /></span>
                    </button>
                  ) : <div className="rounded-xl border border-line bg-bg grid place-items-center min-h-72 text-sm text-mute">No bill image</div>}
                </div>
                <BillSummary l={bill.level1} />
              </section>
              <section className="grid lg:grid-cols-2 gap-6">
                <ChargesCard title="Charges" items={bill.level1.charges ?? []} total={bill.level1.total_charges} totalLabel="Total charges" />
                <TaxesCard l={bill.level1} />
              </section>
              <TotalsStrip l={bill.level1} />
              <ShareChart l={bill.level1} />
              <QAList key={bill.bill_id} items={bill.level2} />
              <RawJson key={`r${bill.bill_id}`} bill={bill} />
            </div>
          </main>
        </div>
      )}
      {zoom && img && <ZoomModal src={img} onClose={() => setZoom(false)} />}
    </div>
  )
}
