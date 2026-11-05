import type { Level1 } from '../types'
import { HUE, label } from '../utils'
export default function ShareChart({ l }: { l: Level1 }) {
  const c = l.total_charges ?? 0, t = l.total_taxes ?? 0, tot = c + t
  const pc = tot ? (c / tot) * 100 : 0, pt = tot ? 100 - pc : 0
  const by: Record<string, number> = {}
  ;(l.charges ?? []).forEach(x => { if (x.amount && x.amount > 0) by[x.type] = (by[x.type] ?? 0) + x.amount })
  const sum = Object.values(by).reduce((a, b) => a + b, 0), C = 2 * Math.PI * 40
  let off = 0
  const segs = Object.entries(by).map(([k, v]) => { const len = (v / sum) * C, s = { k, v, len, off }; off += len; return s })
  const Dot = ({ c }: { c: string }) => <span className="inline-block w-2.5 h-2.5 rounded-full mr-2" style={{ background: c }} />
  return (
    <section className="grid md:grid-cols-2 gap-6">
      <div className="card">
        <h2 className="h2">Charges vs taxes</h2>
        {tot ? <>
          <div className="flex h-4 rounded-full overflow-hidden bg-line" role="img" aria-label={`Charges ${pc.toFixed(1)}%, taxes ${pt.toFixed(1)}%`}>
            <div style={{ width: `${pc}%`, background: '#0F766E' }} /><div style={{ width: `${pt}%`, background: '#1D4ED8' }} />
          </div>
          <div className="flex gap-8 mt-5 text-sm"><span><Dot c="#0F766E" />Charges <b>{pc.toFixed(1)}%</b></span><span><Dot c="#1D4ED8" />Taxes <b>{pt.toFixed(1)}%</b></span></div>
        </> : <p className="text-sm text-mute">—</p>}
      </div>
      <div className="card flex items-center gap-8 flex-wrap">
        <h2 className="sr-only">Charge types</h2>
        {sum ? <>
          <svg width="140" height="140" viewBox="0 0 100 100" role="img" aria-label="Share of charge types" className="-rotate-90">
            <circle cx="50" cy="50" r="40" fill="none" stroke="var(--line)" strokeWidth="14" />
            {segs.map(s => <circle key={s.k} cx="50" cy="50" r="40" fill="none" stroke={HUE[s.k] ?? HUE.other} strokeWidth="14" strokeDasharray={`${s.len} ${C}`} strokeDashoffset={-s.off} />)}
          </svg>
          <ul className="text-sm space-y-2">{segs.map(s => <li key={s.k}><Dot c={HUE[s.k] ?? HUE.other} /><span className="capitalize">{label(s.k)}</span> <b>{((s.v / sum) * 100).toFixed(1)}%</b></li>)}</ul>
        </> : <p className="text-sm text-mute">No charge data.</p>}
      </div>
    </section>
  )
}
