import { t } from '../../../shared/lib/i18n'
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
        {available ? t('Типичное время ожидания') : t('Оценка недоступна')}
      </h2>
      <div
        className="result-number result-duration"
        aria-label={
          available
            ? parts
                .map(
                  ({ value, unit }) =>
                    `${typeof value === 'number' ? number(value) : value} ${t(unit)}`,
                )
                .join(' ')
            : '—'
        }
      >
        {available
          ? parts.map(({ value, unit }) => (
              <b key={unit}>
                {typeof value === 'number' ? number(value) : value}
                <span> {t(unit)}</span>
              </b>
            ))
          : '—'}
      </div>
      <p>{t('Общий срок до госпитализации, не оставшееся время в очереди.')}</p>
      <div className="result-reference">
        {waitBasis(result.method)}
        {result.support > 0 && (
          <>
            {' '}
            · {number(result.support)} {t('случаев')}
          </>
        )}
        . {result.method !== 'catboost' && t('Это групповая медиана, не индивидуальный срок.')}
      </div>
      <div className="result-caveat">
        {result.group_quality
          ? t('Ошибка для этой больницы и профиля: {mae} дня на {count} более поздних случаях.', {
              mae: decimal(result.group_quality.mae, 1),
              count: number(result.group_quality.observations),
            })
          : t('Общая ошибка на проверке: {mae} дня. Для этой группы отдельная ошибка не оценена.', {
              mae: decimal(result.mae, 2),
            })}{' '}
        {t('Это не дата госпитализации. Оценка не изменяет очередь и не назначает лечение.')}{' '}
      </div>
    </section>
  )
}
