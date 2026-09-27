import { ArrowRight } from 'lucide-react'
import { query } from '../api/client'
import { type Filters, type MetricRow, type Overview } from '../api/types'
import { type Mode, type View } from '../app/navigation'
import { AttentionPanel } from '../components/overview/AttentionPanel'
import { OutcomeBreakdown } from '../components/overview/OutcomeBreakdown'
import { OverviewMetrics } from '../components/overview/OverviewMetrics'
import { TopHospitals } from '../components/overview/TopHospitals'
import { TrendPanel } from '../components/overview/TrendPanel'
import { EmptyState } from '../components/ui/EmptyState'
import { ErrorState } from '../components/ui/ErrorState'
import { Loading } from '../components/ui/Loading'
import { PageHeading } from '../components/ui/PageHeading'
import { useRemote } from '../hooks/useRemote'

export function OverviewPage({
  mode,
  hospital,
  filters,
  openHospital,
  go,
}: {
  mode: Mode
  hospital: string
  filters: Filters
  openHospital: (name: string) => void
  go: (view: View) => void
}) {
  const params = query({ ...filters, hospital: mode === 'hospital' ? hospital : '' })
  const { data, loading, error } = useRemote<Overview>(`/overview${params}`)
  const top = useRemote<{
    items: MetricRow[]
  }>(mode === 'government' ? `/hospitals${query({ ...filters, limit: 5 })}` : null)
  const title = mode === 'hospital' ? 'Ваша больница в цифрах' : 'Обзор госпитального потока'
  return (
    <>
      <PageHeading
        eyebrow={mode === 'hospital' ? 'РАБОЧЕЕ МЕСТО БОЛЬНИЦЫ' : 'НАЦИОНАЛЬНЫЙ ОБЗОР'}
        title={title}
        description={
          mode === 'hospital'
            ? hospital
            : 'Направления, наблюдаемое ожидание и изменения активности за выбранный период.'
        }
        action={
          <span className="heading-badge">
            <span /> Исторические данные
          </span>
        }
      />
      {loading && <Loading />}
      {error && <ErrorState message={error} />}
      {data && data.stats.referrals === 0 && (
        <EmptyState
          title="По этим фильтрам записей нет"
          text="Выберите другой профиль или сбросьте фильтры над обзором."
        />
      )}
      {data && data.stats.referrals > 0 && (
        <>
          <OverviewMetrics data={data} />
          <div className="main-grid">
            <TrendPanel rows={data.trend} />
            <AttentionPanel items={data.attention} openHospital={openHospital} />
          </div>
          <div className="bottom-grid">
            <OutcomeBreakdown stats={data.stats} />
            {mode === 'government' ? (
              <TopHospitals
                items={top.data?.items}
                openHospital={openHospital}
                onAll={() => go('hospitals')}
              />
            ) : (
              <section className="panel next-panel">
                <span className="section-kicker">СЛЕДУЮЩИЙ ШАГ</span>
                <h2>Посмотрите детали больницы</h2>
                <p>
                  Профили направлений, наблюдаемое ожидание и прогноз входящего потока находятся в
                  одной карточке.
                </p>
                <button className="primary-button" onClick={() => openHospital(hospital)}>
                  Открыть карточку <ArrowRight size={17} />
                </button>
              </section>
            )}
          </div>
        </>
      )}
    </>
  )
}
