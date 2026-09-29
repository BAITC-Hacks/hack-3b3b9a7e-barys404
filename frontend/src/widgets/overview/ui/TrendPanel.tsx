import { t } from '../../../shared/lib/i18n'
import type { Overview } from '../../../shared/api/types'
import { TrendChart } from '../../../shared/ui/TrendChart'

export function TrendPanel({ rows }: { rows: Overview['trend'] }) {
  return (
    <section className="panel trend-panel">
      <div className="panel-heading">
        <div>
          <h2>{t('Поступление направлений')}</h2>
          <p>{t('По неделям регистрации')}</p>
        </div>
        <span className="legend">
          <i /> {t('Направления')}{' '}
        </span>
      </div>
      <TrendChart rows={rows.map((row) => ({ date: row.week, value: row.referrals }))} />
    </section>
  )
}
