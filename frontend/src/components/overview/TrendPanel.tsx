import type { WeeklyPoint } from '../../api/types'
import { WeeklyTrend } from '../charts/WeeklyTrend'

export function TrendPanel({ rows }: { rows: WeeklyPoint[] }) {
  return (
    <section className="panel trend-panel">
      <div className="panel-heading">
        <div>
          <span className="section-kicker">ДИНАМИКА</span>
          <h2>Поступление направлений</h2>
          <p>По полным неделям регистрации в выбранной выборке</p>
        </div>
        <span className="legend">
          <i /> Направления
        </span>
      </div>
      <WeeklyTrend rows={rows} />
    </section>
  )
}
