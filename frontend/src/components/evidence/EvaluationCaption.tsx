import { type EvaluationPeriod } from '../../api/types'
import { day } from '../../lib/format'

export function EvaluationCaption({
  version,
  period,
}: {
  version: string | null
  period: Partial<EvaluationPeriod>
}) {
  return (
    <p className="evaluation-caption">
      Версия: {version || 'не указана'}
      <br />
      Проверка по регистрации: {day(period.start)} — {day(period.end)}
    </p>
  )
}
