import { useRef } from 'react'
import { Zap, Sun, Moon, Upload } from 'lucide-react'
import { fmtStamp } from '../utils'
interface P { generatedAt?: string | null; dark: boolean; onTheme: () => void; onFile: (f: File) => void }
export default function TopBar({ generatedAt, dark, onTheme, onFile }: P) {
  const ref = useRef<HTMLInputElement>(null)
  return (
    <header className="h-16 bg-card border-b border-line px-4 md:px-8 flex items-center justify-between gap-4">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-[10px] bg-[#4F46E5] grid place-items-center"><Zap size={18} strokeWidth={1.75} color="#fff" /></div>
        <span className="font-semibold tracking-tight">Utility Bill Decoder</span>
      </div>
      <div className="flex items-center gap-3">
        <span className="hidden md:block text-[13px] text-mute">Generated {fmtStamp(generatedAt)}</span>
        <button className="btn !px-0 w-10 justify-center" onClick={onTheme} aria-label="Toggle theme">{dark ? <Sun size={17} strokeWidth={1.5} /> : <Moon size={17} strokeWidth={1.5} />}</button>
        <button className="btn" onClick={() => ref.current?.click()}><Upload size={16} strokeWidth={1.5} className="text-acc" />Load report.json</button>
        <input ref={ref} type="file" accept=".json,application/json" hidden onChange={e => { const f = e.target.files?.[0]; if (f) onFile(f); e.target.value = '' }} />
      </div>
    </header>
  )
}
