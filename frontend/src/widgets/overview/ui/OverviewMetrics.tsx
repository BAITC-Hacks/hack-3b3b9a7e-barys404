import { t } from '../../../shared/lib/i18n'
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
        label={t('Направления')}
        value={number(data.stats.referrals)}
        note={t('Зарегистрировано за период')}
        icon={Activity}
        tone="accent"
      />
      <MetricCard
        label={t('Стационары')}
        value={number(data.stats.hospitals)}
        note={t('С направлениями в выборке')}
        icon={Building2}
      />
      <MetricCard
        label={t('Медиана ожидания')}
        value={decimal(data.stats.median_wait)}
        suffix={t('дня')}
        note={t('По завершённым госпитализациям')}
        icon={Clock3}
      />
      <MetricCard
        label={t('Госпитализации')}
        value={number(data.stats.hospitalized)}
        note={t('С известным исходом')}
        icon={TrendingUp}
      />
    </div>
  )
}
