import { Info } from 'lucide-react'
import { useMemo } from 'react'
import { query } from '../../api/client'
import { type Forecast } from '../../api/types'
import { useRemote } from '../../hooks/useRemote'
import { day, decimal, number } from '../../lib/format'
import { TrendChart } from '../charts/TrendChart'
import { EvaluationCaption } from '../evidence/EvaluationCaption'
import { ErrorState } from '../ui/ErrorState'
import { Loading } from '../ui/Loading'
import { StatusPill } from '../ui/StatusPill'

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
  return (
    <>
      {loading && <Loading label="Рассчитываем прогноз" />}
      {error && <ErrorState message={error} />}
      {data && (
        <>
          <div className="forecast-summary">
            <div>
              <span className="section-kicker">
                {day(data.forecast[0]?.date)} — {day(data.forecast.at(-1)?.date)}
              </span>
              <h2>
                {number(data.total)} <small>направлений за 7 дней</small>
              </h2>
              <p>Прогноз после последнего наблюдения {day(data.history_end)}</p>
            </div>
            <StatusPill good={true}>Исторический прогноз</StatusPill>
          </div>
          <section className="panel forecast-chart">
            <div className="panel-heading">
              <div>
                <span className="section-kicker">ПОТОК НАПРАВЛЕНИЙ</span>
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
              текущую очередь.
            </div>
          </section>
          <div className="forecast-lower">
            <section className="panel">
              <span className="section-kicker">ПО ДНЯМ</span>
              <h2>Детали прогноза</h2>
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
              <span className="section-kicker">ТОЧНОСТЬ МОДЕЛИ</span>
              <StatusPill good={true}>Метрики актуальны</StatusPill>
              <h2>
                {decimal(data.metrics.mae, 2)} <small>направления</small>
              </h2>
              <p>
                Средняя абсолютная ошибка на всём историческом тесте: на организацию в день. Ошибка
                первого дня горизонта: {decimal(data.metrics_by_horizon[0]?.mae, 2)}.
              </p>
              <div className="quality-divider" />
              <span>Простой прогноз: {decimal(data.metrics.baseline_mae, 2)} направления</span>
              <EvaluationCaption version={data.model_version} period={data.test_period} />
            </section>
          </div>
        </>
      )}
    </>
  )
}
