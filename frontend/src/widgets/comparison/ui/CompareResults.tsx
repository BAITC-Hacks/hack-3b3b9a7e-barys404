import { ArrowUpRight } from 'lucide-react'
import type { MetricRow } from '../../../shared/api/types'
import { decimal, number } from '../../../shared/lib/format'
import { EmptyState } from '../../../shared/ui/EmptyState'

export function CompareResults({
  chosen,
  openHospital,
}: {
  chosen: MetricRow[]
  openHospital: (name: string) => void
}) {
  const maxWait = Math.max(1, ...chosen.map((item) => item.median_wait_days ?? 0))
  return (
    <section className="panel compare-results">
      <div className="panel-heading">
        <div>
          <span className="section-kicker">ОДИН ПЕРИОД · ОДИН КОНТЕКСТ</span>
          <h2>Наблюдаемое ожидание</h2>
          <p>Медиана по завершённым госпитализациям</p>
        </div>
      </div>
      {chosen.length ? (
        <>
          <div className="compare-bars">
            {chosen.map((item, index) => (
              <div className="compare-bar-row" key={item.organization_or_region}>
                <div className="compare-name">
                  <b>{String.fromCharCode(65 + index)}</b>
                  <span>{item.organization_or_region}</span>
                </div>
                <div className="compare-track">
                  <i style={{ width: `${((item.median_wait_days ?? 0) / maxWait) * 100}%` }} />
                </div>
                <strong>{decimal(item.median_wait_days)} дн.</strong>
              </div>
            ))}
          </div>
          <div className="compare-cards">
            {chosen.map((item, index) => (
              <button
                className="compare-card"
                key={item.organization_or_region}
                onClick={() => openHospital(item.organization_or_region)}
              >
                <span>
                  Стационар {String.fromCharCode(65 + index)} <ArrowUpRight size={15} />
                </span>
                <strong>{number(item.referrals)}</strong>
                <small>направлений · отказы {decimal(item.refusal_share_pct)}%</small>
              </button>
            ))}
          </div>
        </>
      ) : (
        <EmptyState
          title="Выберите стационары"
          text="Отметьте от одной до трёх организаций слева."
        />
      )}
    </section>
  )
}
