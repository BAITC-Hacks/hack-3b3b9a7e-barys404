import { type WeeklyPoint } from '../../api/types'
import { day, number } from '../../lib/format'
import { EmptyState } from '../ui/EmptyState'
import { TrendChart } from './TrendChart'

export function WeeklyTrend({ rows }: { rows: WeeklyPoint[] }) {
  const full = rows.filter((row) => !row.partial_week)
  const partial = rows.filter((row) => row.partial_week)
  return (
    <>
      {full.length ? (
        <TrendChart rows={full.map((row) => ({ date: row.week, value: row.referrals }))} />
      ) : (
        <EmptyState
          title="Нет полных календарных недель"
          text="Выберите более длинный период. Доступные неполные интервалы показаны ниже."
        />
      )}
      {partial.length > 0 && (
        <div className="partial-weeks" role="note">
          <strong>Неполные недели — отдельно от графика</strong>
          <p>Их объёмы нельзя напрямую сравнивать с полными неделями.</p>
          {partial.map((row) => (
            <div key={row.week}>
              <span>
                {day(row.period_start)} — {day(row.period_end)}{' '}
                <small>({row.days_in_period} из 7 дней)</small>
              </span>
              <b>{number(row.referrals)} направл.</b>
            </div>
          ))}
        </div>
      )}
      <p className="panel-footnote">
        На графике — полные календарные недели выбранного интервала. Ноль означает отсутствие
        записей в выгрузке; полнота передачи данных не подтверждена.
      </p>
    </>
  )
}
