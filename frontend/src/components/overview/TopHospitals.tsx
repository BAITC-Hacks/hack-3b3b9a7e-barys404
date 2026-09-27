import { ArrowRight, ChevronRight } from 'lucide-react'
import type { MetricRow } from '../../api/types'
import { number } from '../../lib/format'

export function TopHospitals({
  items,
  openHospital,
  onAll,
}: {
  items?: MetricRow[]
  openHospital: (name: string) => void
  onAll: () => void
}) {
  return (
    <section className="panel top-panel">
      <div className="panel-heading">
        <div>
          <span className="section-kicker">ОРГАНИЗАЦИИ</span>
          <h2>Стационары по объёму</h2>
        </div>
        <button className="text-button" onClick={onAll}>
          Все стационары <ArrowRight size={16} />
        </button>
      </div>
      {items?.map((row) => (
        <button
          className="top-hospital"
          key={row.organization_or_region}
          onClick={() => openHospital(row.organization_or_region)}
        >
          <span>{row.organization_or_region}</span>
          <strong>{number(row.referrals)}</strong>
          <ChevronRight size={16} />
        </button>
      ))}
    </section>
  )
}
