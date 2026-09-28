import { type Filters, type HospitalDetail, type Overview } from '../../../shared/api/types'
import { type Mode, type View } from '../../../shared/config/navigation'
import { useRemote } from '../../../shared/lib/useRemote'
import { query } from '../../../entities/hospital/index'
import { ArrowLeft, ArrowRight, Activity, Clock3, TrendingUp, Info } from 'lucide-react'
import { PageHeading } from '../../../shared/ui/PageHeading'
import { Loading } from '../../../shared/ui/Loading'
import { ErrorState } from '../../../shared/ui/ErrorState'
import { EmptyState } from '../../../shared/ui/EmptyState'
import { MetricCard } from '../../../shared/ui/MetricCard'
import { number, decimal } from '../../../shared/lib/format'
import { TrendChart } from '../../../shared/ui/TrendChart'
import { BriefingPanel } from '../../../features/export-briefing/index'

export function HospitalPage({
  hospital,
  filters,
  mode,
  go,
  compare,
}: {
  hospital: string
  filters: Filters
  mode: Mode
  go: (view: View) => void
  compare: () => void
}) {
  const detail = useRemote<HospitalDetail>(
    hospital ? `/hospital/overview${query({ ...filters, hospital })}` : null,
  )
  const trend = useRemote<Overview>(hospital ? `/overview${query({ ...filters, hospital })}` : null)
  const stats = detail.data?.stats
  return (
    <>
      {mode === 'government' && (
        <button className="back-link" onClick={() => go('hospitals')}>
          <ArrowLeft size={16} /> К списку стационаров
        </button>
      )}
      <PageHeading
        eyebrow="КАРТОЧКА СТАЦИОНАРА"
        title={hospital}
        description="Наблюдаемые показатели по выбранному периоду и профилю."
        action={
          <div className="heading-actions">
            {mode === 'government' && (
              <button className="secondary-button" onClick={compare}>
                Сравнить
              </button>
            )}
            <button className="secondary-button" onClick={() => go('forecasts')}>
              Открыть прогноз <ArrowRight size={16} />
            </button>
          </div>
        }
      />
      {(detail.loading || trend.loading) && <Loading />}
      {detail.error && <ErrorState message={detail.error} />}
      {trend.error && <ErrorState message={trend.error} />}
      {detail.data && !stats && (
        <EmptyState
          title="Нет записей для выбранных фильтров"
          text="Измените период, регион или профиль, чтобы увидеть показатели стационара."
        />
      )}
      {stats && (
        <>
          <div className="metrics-grid">
            <MetricCard
              label="Направления"
              value={number(stats.referrals)}
              note="За выбранный период"
              icon={Activity}
              tone="accent"
            />
            <MetricCard
              label="Медиана ожидания"
              value={decimal(stats.median_wait_days)}
              suffix="дня"
              note="По завершённым случаям"
              icon={Clock3}
            />
            <MetricCard
              label="90% ожидали до"
              value={decimal(stats.p90_wait_days)}
              suffix="дня"
              note="Наблюдаемый P90"
              icon={TrendingUp}
            />
            <MetricCard
              label="Доля отказов"
              value={decimal(stats.refusal_share_pct)}
              suffix="%"
              note="Среди известных исходов"
              icon={Info}
            />
          </div>
          <div className="main-grid hospital-main">
            <section className="panel">
              <div className="panel-heading">
                <div>
                  <span className="section-kicker">ПОСТУПЛЕНИЕ</span>
                  <h2>Направления по неделям</h2>
                  <p>История выбранного стационара</p>
                </div>
              </div>
              {trend.data && (
                <TrendChart
                  rows={trend.data.trend.map((row) => ({ date: row.week, value: row.referrals }))}
                />
              )}
            </section>
            <section className="panel">
              <div className="panel-heading">
                <div>
                  <span className="section-kicker">ПРОФИЛИ</span>
                  <h2>Что поступает чаще</h2>
                  <p>Восемь наиболее частых профилей</p>
                </div>
              </div>
              <div className="profile-list">
                {(detail.data?.profiles ?? []).map((profile) => (
                  <div className="profile-row" key={profile.profile}>
                    <span>{profile.profile === '__MISSING__' ? 'Не указан' : profile.profile}</span>
                    <strong>{number(profile.referrals)}</strong>
                  </div>
                ))}
              </div>
            </section>
          </div>
          <section className="panel pathway-panel">
            <div>
              <span className="section-kicker">ПРОГНОЗ</span>
              <h2>Что ожидается дальше?</h2>
              <p>
                Для этого стационара можно посмотреть прогноз входящих направлений на семь дней
                после последней даты в данных.
              </p>
            </div>
            <button className="primary-button" onClick={() => go('forecasts')}>
              Показать прогноз <ArrowRight size={17} />
            </button>
          </section>
          <p className="page-note">
            P90 — наблюдённый срок у 90% завершённых случаев, а не доверительный интервал. Фильтры
            выше не меняют обученную модель прогноза.
          </p>
          <BriefingPanel filters={filters} hospitals={[hospital]} minimum={10} />
        </>
      )}
    </>
  )
}
