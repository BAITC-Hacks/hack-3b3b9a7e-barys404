import type { Overview } from '../../../shared/api/types'
import { TrendChart } from '../../../shared/ui/TrendChart'

export function TrendPanel({ rows }: { rows: Overview['trend'] }) {
  return (
    <section className="panel trend-panel">
      <div className="panel-heading">
        <div>
          <h2>Поступление направлений</h2>
          <p>По неделям регистрации</p>
        </div>
        <span className="legend">
          <i /> Направления
        </span>
      </div>
      <TrendChart rows={rows.map((row) => ({ date: row.week, value: row.referrals }))} />
    </section>
  )
}
