import { type WaitResult } from '../../api/types'
import { decimal, number } from '../../lib/format'
import { waitBasis } from './waitConfig'

export function WaitEstimateCard({ result }: { result: WaitResult }) {
  return (
    <section className="result-hero">
      <span className="section-kicker">ОЦЕНКА ОЖИДАНИЯ</span>
      <div className="result-number">
        {result.clipped ? '—' : result.prediction < 0.1 ? '<0,1' : decimal(result.prediction)}{' '}
        {!result.clipped && <span>дня</span>}
      </div>
      <h2>{result.clipped ? 'Оценка недоступна' : 'Типичное время ожидания'}</h2>
      <p>От регистрации направления до госпитализации, не оставшееся время в очереди.</p>
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
        Это не дата госпитализации.
      </div>
    </section>
  )
}
