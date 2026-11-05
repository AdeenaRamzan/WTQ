import { useEffect, useState } from 'react'
import { X, ZoomIn, ZoomOut } from 'lucide-react'
export default function ZoomModal({ src, onClose }: { src: string; onClose: () => void }) {
  const [z, setZ] = useState(1)
  useEffect(() => { const h = (e: KeyboardEvent) => e.key === 'Escape' && onClose(); window.addEventListener('keydown', h); return () => window.removeEventListener('keydown', h) }, [onClose])
  return (
    <div role="dialog" aria-modal="true" aria-label="Bill image" className="fade fixed inset-0 z-50 bg-black/70 flex flex-col" onClick={onClose}>
      <div className="flex justify-end gap-2 p-4" onClick={e => e.stopPropagation()}>
        <button className="btn !px-0 w-10 justify-center" aria-label="Zoom in" onClick={() => setZ(Math.min(4, z + 0.5))}><ZoomIn size={17} /></button>
        <button className="btn !px-0 w-10 justify-center" aria-label="Zoom out" onClick={() => setZ(Math.max(0.5, z - 0.5))}><ZoomOut size={17} /></button>
        <button className="btn !px-0 w-10 justify-center" aria-label="Close" autoFocus onClick={onClose}><X size={17} /></button>
      </div>
      <div className="flex-1 overflow-auto p-4"><img src={src} alt="Bill" onClick={e => e.stopPropagation()} className="mx-auto rounded-lg bg-white transition-all duration-200" style={{ width: `${z * 60}%`, minWidth: 280 }} /></div>
    </div>
  )
}
