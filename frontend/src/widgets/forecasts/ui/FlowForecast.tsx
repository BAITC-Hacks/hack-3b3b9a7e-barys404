import { useRemote } from '../../../shared/lib/useRemote'
import { type Forecast } from '../../../shared/api/types'
import { query } from '../../../entities/hospital/index'
import { useMemo } from 'react'
import { Loading } from '../../../shared/ui/Loading'
import { ErrorState } from '../../../shared/ui/ErrorState'
import { number, day, decimal } from '../../../shared/lib/format'
import { StatusPill } from '../../../shared/ui/StatusPill'
import { TrendChart } from '../../../shared/ui/TrendChart'
import { Info } from 'lucide-react'
import { useStaggeredEntrance } from '../../../shared/lib/useEntrance'

export function FlowForecast({ hospital }: { hospital: string }) {
  const { data, loading, error } = useRemote<Forecast>(
    hospital ? `/hospital/forecast${query({ hospital })}` : null,
  )
  const rows = useMemo(
    () =>
      data
        ? [
            ...data.history.map((row) => ({ date: row.date, value: row.referrals })),
            ...data.forecast.map((row) => ({ date: row.date, value: row.predicted_referrals })),
          ]
        : [],
    [data],
  )
  const entrance = useStaggeredEntrance<HTMLDivElement>(data)
  return (
    <>
      {loading && <Loading label="Рассчитываем прогноз" />}
      {error && <ErrorState message={error} />}
      {data && (
        <div ref={entrance}>
          <div className="forecast-summary">
            <div>
              <span className="forecast-period">
                {day(data.forecast[0]?.date)} — {day(data.forecast.at(-1)?.date)}
              </span>
              <h2>
                {number(data.total)} <small>направлений за 7 дней</small>
              </h2>
              <p>Последнее наблюдение: {day(data.history_end)}</p>
            </div>
            <StatusPill good={false}>По историческим данным</StatusPill>
          </div>
          <section className="panel forecast-chart">
            <div className="panel-heading">
              <div>
                <h2>История и следующие семь дней</h2>
              </div>
              <div className="chart-legend">
                <span>
                  <i /> Наблюдения
                </span>
                <span>
                  <i /> Прогноз
                </span>
              </div>
            </div>
            <TrendChart rows={rows} forecastFrom={data.history.length} />
            <div className="forecast-note">
              <Info size={16} /> Прогноз показывает входящие направления, а не занятость коек или
              текущую очередь. Он не изменяет очередь и не назначает лечение.
            </div>
          </section>
          <div className="forecast-lower">
            <section className="panel">
              <h2>Прогноз по дням</h2>
              <div className="forecast-days">
                {data.forecast.map((row, index) => (
                  <div key={row.date}>
                    <span>
                      {day(row.date)} <small>день {index + 1}</small>
                    </span>
                    <strong>
                      {decimal(row.predicted_referrals)} <small>напр.</small>
                    </strong>
                  </div>
                ))}
              </div>
            </section>
            <section className="panel quality-callout">
              <span className="forecast-period">Средняя ошибка на проверке</span>
              <h2>
                {decimal(data.metrics.mae, 2)} <small>направления</small>
              </h2>
              <p>
                Средняя абсолютная ошибка на историческом тесте для организации в день. На первом
                дне горизонта ошибка выше: {decimal(data.metrics_by_horizon[0]?.mae, 2)}.
              </p>
              <div className="quality-divider" />
              <span>Простой прогноз: {decimal(data.metrics.baseline_mae, 2)} направления</span>
            </section>
          </div>
        </div>
      )}
    </>
  )
}
