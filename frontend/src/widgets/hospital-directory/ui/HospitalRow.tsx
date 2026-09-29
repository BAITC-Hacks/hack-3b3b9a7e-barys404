import { t } from '../../../shared/lib/i18n'
import { Building2, ChevronRight } from 'lucide-react'
import { type MetricRow } from '../../../shared/api/types'
import { decimal, number } from '../../../shared/lib/format'
import { hospitalDisplayName } from '../../../entities/hospital/index'

export function HospitalRow({
  row,
  onOpen,
}: {
  row: MetricRow
  onOpen: (hospital: string) => void
}) {
  return (
    <button
      className="hospital-row"
      onClick={() => onOpen(row.organization_or_region)}
      title={row.organization_or_region}
    >
      <span className="hospital-cell name-cell">
        <span className="hospital-avatar">
          <Building2 size={17} />
        </span>
        <span>{hospitalDisplayName(row.organization_or_region)}</span>
      </span>
      <span className="hospital-cell numeric-cell" data-label={t('Направления')}>
        {number(row.referrals)}
      </span>
      <span className="hospital-cell numeric-cell" data-label={t('Ожидание')}>
        {decimal(row.median_wait_days)} <small>{t('дн.')}</small>
      </span>
      <span className="hospital-cell numeric-cell">
        {decimal(row.refusal_share_pct)}
        <small>%</small>
      </span>
      <ChevronRight size={17} className="row-chevron" />
    </button>
  )
}
