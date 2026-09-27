import type { Overview } from '../../api/types'
import { number } from '../../lib/format'
export function OutcomeBreakdown({ stats }: { stats: Overview['stats'] }) {
  return (
    <section className="panel outcome-panel">
      <div className="panel-heading">
        <div>
          <span className="section-kicker">ИЗВЕСТНЫЕ ИСХОДЫ</span>
          <h2>Что произошло с направлениями</h2>
        </div>
      </div>
      <div className="outcome-stack">
        {[
          ['Госпитализации', stats.hospitalized, 'teal'],
          ['Отказы', stats.refused, 'coral'],
          ['Исход не записан', stats.unresolved, 'gray'],
        ].map(([label, value, color]) => (
          <div className="outcome-row" key={String(label)}>
            <span>{label}</span>
            <div className="outcome-track">
              <i
                className={`outcome-fill ${color}`}
                style={{
                  width: `${Math.max(1, (Number(value) / Math.max(1, stats.referrals)) * 100)}%`,
                }}
              />
            </div>
            <strong>{number(Number(value))}</strong>
          </div>
        ))}
      </div>
      <p className="panel-footnote">
        Отсутствие исхода в выгрузке не означает, что человек ожидает сейчас.
      </p>
    </section>
  )
}
