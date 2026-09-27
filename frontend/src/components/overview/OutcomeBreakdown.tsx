import { type Overview } from '../../api/types'
import { number } from '../../lib/format'

export function OutcomeBreakdown({ stats }: { stats: Overview['stats'] }) {
  const categories = [
    ['Госпитализации', stats.hospitalized, 'teal'],
    ['Отказы', stats.refused, 'coral'],
    ['Исход не записан', stats.unresolved, 'gray'],
    ['Некорректные / конфликтующие', stats.invalid_outcome + stats.conflicting, 'amber'],
  ] as const
  return (
    <section className="panel outcome-panel">
      <div className="panel-heading">
        <div>
          <span className="section-kicker">ИСХОДЫ И КАЧЕСТВО ДАННЫХ</span>
          <h2>Что произошло с направлениями</h2>
        </div>
      </div>
      <div className="outcome-stack">
        {categories.map(([label, value, color]) => (
          <div className="outcome-row" key={label}>
            <span>{label}</span>
            <div className="outcome-track">
              <i
                className={`outcome-fill ${color}`}
                style={{ width: `${(value / Math.max(1, stats.referrals)) * 100}%` }}
              />
            </div>
            <strong>{number(value)}</strong>
          </div>
        ))}
      </div>
      <p className="panel-footnote">
        Все категории входят в {number(stats.referrals)} направлений. Некорректных исходов:{' '}
        {number(stats.invalid_outcome)}, конфликтующих: {number(stats.conflicting)}. Они исключены
        из оценки ожидания. Отсутствие исхода не означает, что человек ожидает сейчас.
      </p>
    </section>
  )
}
