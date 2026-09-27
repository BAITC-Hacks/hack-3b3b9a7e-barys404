import { Activity, Building2, Clock3, TrendingUp } from 'lucide-react'
import type { Overview } from '../../api/types'
import { decimal, number } from '../../lib/format'
import { MetricCard } from '../ui/MetricCard'

export function OverviewMetrics({ data }: { data: Overview }) {
  return (
    <div className="metrics-grid">
      <MetricCard
        label="Направления"
        value={number(data.stats.referrals)}
        note="Зарегистрировано за период"
        icon={Activity}
        tone="accent"
      />
      <MetricCard
        label="Стационары"
        value={number(data.stats.hospitals)}
        note="С направлениями в выборке"
        icon={Building2}
      />
      <MetricCard
        label="Медиана ожидания"
        value={decimal(data.stats.median_wait)}
        suffix="дня"
        note={
          data.stats.median_wait == null
            ? `Недостаточно допустимых случаев: ${number(data.stats.eligible)} из ${data.metric_minimum}`
            : `По ${number(data.stats.eligible)} допустимым завершённым случаям`
        }
        icon={Clock3}
      />
      <MetricCard
        label="Госпитализации"
        value={number(data.stats.hospitalized)}
        note="С известным исходом"
        icon={TrendingUp}
      />
    </div>
  )
}
