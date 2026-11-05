import { FileJson } from 'lucide-react'
export default function EmptyState({ reason }: { reason?: string }) {
  return (
    <div className="card max-w-xl mx-auto text-center mt-16">
      <FileJson size={36} strokeWidth={1.25} className="mx-auto text-acc" />
      <h1 className="text-2xl font-semibold tracking-tight mt-4">No report loaded</h1>
      <p className="text-mute mt-2 text-sm">{reason ?? 'We could not find a report to show.'}</p>
      <ol className="text-left text-sm mt-6 space-y-2 list-decimal pl-6">
        <li>Place your file at <code className="font-mono">public/data/report.json</code>.</li>
        <li>Put bill images in <code className="font-mono">public/data/images/</code>.</li>
        <li>Or use <b>Load report.json</b> in the top bar to pick a file.</li>
      </ol>
    </div>
  )
}
