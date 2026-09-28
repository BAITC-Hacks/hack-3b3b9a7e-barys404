import { ArrowRight } from 'lucide-react'
import { query } from '../../../entities/hospital/index'
import {
  type Bootstrap,
  type Filters,
  type MetricRow,
  type Overview,
} from '../../../shared/api/types'
import { type Mode, type View } from '../../../shared/config/navigation'
import { AttentionPanel } from '../../../widgets/overview/index'
import { OutcomeBreakdown } from '../../../widgets/overview/index'
import { OverviewMetrics } from '../../../widgets/overview/index'
import { TopHospitals } from '../../../widgets/overview/index'
import { TrendPanel } from '../../../widgets/overview/index'
import { EmptyState } from '../../../shared/ui/EmptyState'
import { ErrorState } from '../../../shared/ui/ErrorState'
import { Loading } from '../../../shared/ui/Loading'
import { PageHeading } from '../../../shared/ui/PageHeading'
import { useRemote } from '../../../shared/lib/useRemote'
import { regionLabel } from '../../../entities/region/index'
import { FilterBar } from '../../../features/filter-referrals/index'
import { useStaggeredEntrance } from '../../../shared/lib/useEntrance'

export function OverviewPage({
  mode,
  hospital,
  filters,
  setFilters,
  bootstrap,
  openHospital,
  go,
}: {
  mode: Mode
  hospital: string
  filters: Filters
  setFilters: (value: Filters) => void
  bootstrap: Bootstrap
  openHospital: (name: string) => void
  go: (view: View) => void
}) {
  const params = query({ ...filters, hospital: mode === 'hospital' ? hospital : '' })
  const { data, loading, error } = useRemote<Overview>(`/overview${params}`)
  const panels = useStaggeredEntrance<HTMLDivElement>(data)
  const top = useRemote<{
    items: MetricRow[]
  }>(mode === 'government' ? `/hospitals${query({ ...filters, limit: 5 })}` : null)
  const title = mode === 'hospital' ? 'Обзор больницы' : 'Обзор направлений'
  const description =
    mode === 'hospital' ? hospital : 'Поступление направлений и результаты госпитализации.'
  return (
    <>
      <PageHeading
        eyebrow=""
        title={title}
        description={
          filters.region
            ? `${description} Регион происхождения: ${regionLabel(filters.region)}.`
            : description
        }
        action={<span className="overview-source">Исторические данные · 2025</span>}
      />
      <FilterBar filters={filters} setFilters={setFilters} bootstrap={bootstrap} />
      {loading && <Loading />}
      {error && <ErrorState message={error} />}
      {data && data.stats.referrals === 0 && (
        <EmptyState
          title="По этим фильтрам записей нет"
          text="Выберите другой регион или профиль либо сбросьте фильтры над обзором."
        />
      )}
      {data && data.stats.referrals > 0 && (
        <>
          <OverviewMetrics data={data} />
          <div className="overview-layout" ref={panels}>
            <TrendPanel rows={data.trend} />
            <OutcomeBreakdown stats={data.stats} />
            {mode === 'government' ? (
              <TopHospitals
                items={top.data?.items}
                openHospital={openHospital}
                onAll={() => go('hospitals')}
                loading={top.loading}
                error={top.error}
              />
            ) : (
              <section className="panel next-panel">
                <h2>Карточка больницы</h2>
                <p>
                  Профили направлений, наблюдаемое ожидание и прогноз входящего потока находятся в
                  одной карточке.
                </p>
                <button className="primary-button" onClick={() => openHospital(hospital)}>
                  Открыть карточку <ArrowRight size={17} />
                </button>
              </section>
            )}
            <AttentionPanel items={data.attention} openHospital={openHospital} />
          </div>
        </>
      )}
    </>
  )
}
