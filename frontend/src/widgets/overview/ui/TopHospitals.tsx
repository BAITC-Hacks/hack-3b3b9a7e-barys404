import { t } from '../../../shared/lib/i18n'
import { ArrowRight, ChevronRight } from 'lucide-react'
import type { MetricRow } from '../../../shared/api/types'
import { number } from '../../../shared/lib/format'
import { Loading } from '../../../shared/ui/Loading'
import { ErrorState } from '../../../shared/ui/ErrorState'
import { hospitalDisplayName } from '../../../entities/hospital/index'

export function TopHospitals({
  items,
  openHospital,
  onAll,
  loading = false,
  error = '',
}: {
  items?: MetricRow[]
  openHospital: (name: string) => void
  onAll: () => void
  loading?: boolean
  error?: string
}) {
  return (
    <section className="panel top-panel">
      <div className="panel-heading">
        <div>
          <h2>{t('Стационары по числу направлений')}</h2>
        </div>
        <button className="text-button" onClick={onAll}>
          {t('Все стационары')} <ArrowRight size={16} />
        </button>
      </div>
      {loading && <Loading />}
      {error && <ErrorState message={error} />}
      {!loading && !error && (
        <div className="top-hospitals-head" aria-hidden="true">
          <span>{t('Организация')}</span>
          <span>{t('Направления')}</span>
        </div>
      )}
      {items?.map((row) => (
        <button
          className="top-hospital"
          key={row.organization_or_region}
          title={row.organization_or_region}
          onClick={() => openHospital(row.organization_or_region)}
        >
          <span>{hospitalDisplayName(row.organization_or_region)}</span>
          <strong>{number(row.referrals)}</strong>
          <ChevronRight size={16} />
        </button>
      ))}
    </section>
  )
}
