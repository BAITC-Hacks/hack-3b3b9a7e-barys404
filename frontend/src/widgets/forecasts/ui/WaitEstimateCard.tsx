import { type WaitResult } from '../../../shared/api/types'
import { decimal, number } from '../../../shared/lib/format'
import { durationParts } from '../../../shared/lib/duration'
import { waitBasis } from './waitConfig'
import { useEntrance } from '../../../shared/lib/useEntrance'

export function WaitEstimateCard({ result }: { result: WaitResult }) {
  const entrance = useEntrance<HTMLElement>(result)
  const parts = durationParts(result.clipped ? null : result.prediction)
  const available = parts.length > 0
  return (
    <section className="result-hero" ref={entrance} role="status" aria-live="polite">
      <h2 className="result-title">
        {available ? 'Типичное время ожидания' : 'Оценка недоступна'}
      </h2>
      <div
        className="result-number result-duration"
        aria-label={available ? parts.map(({ value, unit }) => `${value} ${unit}`).join(' ') : '—'}
      >
        {available
          ? parts.map(({ value, unit }) => (
              <b key={unit}>
                {typeof value === 'number' ? number(value) : value}
                <span> {unit}</span>
              </b>
            ))
          : '—'}
      </div>
      <p>Общий срок до госпитализации, не оставшееся время в очереди.</p>
      <div className="result-reference">
        {waitBasis(result.method)}
        {result.support > 0 && <> · {number(result.support)} случаев</>}.{' '}
        {result.method !== 'catboost' && 'Это групповая медиана, не индивидуальный срок.'}
      </div>
      <div className="result-caveat">
        {result.group_quality ? (
          <>
            Ошибка для этой больницы и профиля: {decimal(result.group_quality.mae, 1)} дня на{' '}
            {number(result.group_quality.observations)} более поздних случаях.
          </>
        ) : (
          <>
            Общая ошибка на проверке: {decimal(result.mae, 2)} дня. Для этой группы отдельная ошибка
            не оценена.
          </>
        )}{' '}
        Это не дата госпитализации. Оценка не изменяет очередь и не назначает лечение.
      </div>
    </section>
  )
}
