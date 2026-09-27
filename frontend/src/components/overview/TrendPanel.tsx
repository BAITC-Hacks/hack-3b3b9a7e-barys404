import type { Overview } from '../../api/types'
import { TrendChart } from '../charts/TrendChart'

export function TrendPanel({ rows }: { rows: Overview['trend'] }) {
  return (
    <section className="panel trend-panel">
      <div className="panel-heading">
        <div>
          <span className="section-kicker">ДИНАМИКА</span>
          <h2>Поступление направлений</h2>
          <p>По неделям регистрации в выбранной выборке</p>
        </div>
        <span className="legend">
          <i /> Направления
        </span>
      </div>
      <TrendChart rows={rows.map((row) => ({ date: row.week, value: row.referrals }))} />
    </section>
  )
}
