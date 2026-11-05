import type { Level1 } from '../types'
import ChargesCard from './ChargesCard'
export default function TaxesCard({ l }: { l: Level1 }) {
  return <ChargesCard title="Taxes" items={l.taxes ?? []} total={l.total_taxes} totalLabel="Total taxes" />
}
