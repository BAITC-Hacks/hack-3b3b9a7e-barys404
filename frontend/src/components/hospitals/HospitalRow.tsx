import { Building2, ChevronRight } from 'lucide-react'
import { type MetricRow } from '../../api/types'
import { decimal, number } from '../../lib/format'

export function HospitalRow({
  row,
  onOpen,
}: {
  row: MetricRow
  onOpen: (hospital: string) => void
}) {
  return (
    <button className="hospital-row" onClick={() => onOpen(row.organization_or_region)}>
      <span className="hospital-cell name-cell">
        <span className="hospital-avatar">
          <Building2 size={17} />
        </span>
        <span>{row.organization_or_region}</span>
      </span>
      <span className="hospital-cell numeric-cell" data-label="Направления">
        {number(row.referrals)}
      </span>
      <span className="hospital-cell numeric-cell" data-label="Ожидание">
        {decimal(row.median_wait_days)} <small>дн.</small>
      </span>
      <span className="hospital-cell numeric-cell">
        {decimal(row.refusal_share_pct)}
        <small>%</small>
      </span>
      <ChevronRight size={17} className="row-chevron" />
    </button>
  )
}
