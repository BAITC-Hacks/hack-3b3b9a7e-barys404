import { Activity, Building2, Clock3, TrendingUp } from 'lucide-react'
import type { Overview } from '../../../shared/api/types'
import { decimal, number } from '../../../shared/lib/format'
import { MetricCard } from '../../../shared/ui/MetricCard'
import { useStaggeredEntrance } from '../../../shared/lib/useEntrance'

export function OverviewMetrics({ data }: { data: Overview }) {
  const entrance = useStaggeredEntrance<HTMLDivElement>(data)
  return (
    <div className="metrics-grid overview-metrics" ref={entrance}>
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
        note="По завершённым госпитализациям"
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
