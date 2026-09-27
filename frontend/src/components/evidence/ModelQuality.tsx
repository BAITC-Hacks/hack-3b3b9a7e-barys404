import { type ModelEvidence } from '../../api/types'
import { decimal } from '../../lib/format'
import { StatusPill } from '../ui/StatusPill'
import { EvaluationCaption } from './EvaluationCaption'

export function ModelQuality({
  name,
  unit,
  baseline,
  evidence,
}: {
  name: string
  unit: string
  baseline: string
  evidence: ModelEvidence
}) {
  const available = evidence.status.available && evidence.metrics !== null
  return (
    <section className="panel quality-callout">
      <span className="section-kicker">{name}</span>
      <StatusPill good={available}>
        {available ? 'Метрики актуальны' : 'Модель недоступна'}
      </StatusPill>
      {available && evidence.metrics ? (
        <>
          <h2>
            {decimal(evidence.metrics.mae, 2)} <small>{unit}</small>
          </h2>
          <p>
            MAE — средняя абсолютная ошибка на исторической проверке. Ошибка отдельных групп может
            отличаться.
          </p>
          <div className="quality-divider" />
          <p>
            {baseline}:{' '}
            <strong>
              {decimal(evidence.metrics.baseline_mae, 2)} {unit}
            </strong>
          </p>
          <p>
            RMSE: {decimal(evidence.metrics.rmse, 2)} {unit}
          </p>
          <EvaluationCaption version={evidence.model_version} period={evidence.test_period} />
        </>
      ) : (
        <>
          <h2>Нет актуальной оценки качества</h2>
          <p>
            Артефакты отсутствуют, устарели или не прошли проверку. Обратитесь к оператору для
            обновления данных и модели.
          </p>
          {evidence.model_version && (
            <p className="evaluation-caption">
              Сохранённая версия: {evidence.model_version}. Её метрики скрыты до подтверждения
              актуальности.
            </p>
          )}
        </>
      )}
    </section>
  )
}
