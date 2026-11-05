import { label, pillCls } from '../utils'
export default function Pill({ type }: { type: string }) {
  return <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${pillCls(type)}`}>{label(type)}</span>
}
