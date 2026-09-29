import { t } from '../../../shared/lib/i18n'
import { useState } from 'react'
import { hospitalId } from '../../../entities/hospital/index'
import { type BriefingInput, type Filters } from '../../../shared/api/types'
import { day } from '../../../shared/lib/evidenceFormat'
import { regionLabel } from '../../../entities/region/index'
import { BriefingForm } from './BriefingForm'

export function BriefingPanel({
  filters,
  hospitals,
  minimum = 30,
}: {
  filters: Filters
  hospitals: string[]
  minimum?: number
}) {
  const [question, setQuestion] = useState<BriefingInput['question']>('flow')
  const request: BriefingInput = {
    ...filters,
    hospital_ids: hospitals.map(hospitalId),
    minimum,
    question,
  }
  return (
    <section className="panel evidence-section">
      <span className="section-kicker">{t('ПРОВЕРКА СПЕЦИАЛИСТОМ')}</span>
      <h2>{t('Сводка для обсуждения')}</h2>
      <p>
        {t(
          'Период регистрации: {start} — {end}. Профиль: {profile}. Регион происхождения: {region}.',
          {
            start: day(filters.start),
            end: day(filters.end),
            profile: filters.profile ? t(filters.profile) : t('все'),
            region: regionLabel(filters.region),
          },
        )}
      </p>
      <label className="briefing-question">
        {t('Вопрос для проверки')}{' '}
        <select
          value={question}
          onChange={(e) => setQuestion(e.target.value as BriefingInput['question'])}
        >
          <option value="flow">{t('Поток направлений и доступная мощность')}</option>
          <option value="waiting">{t('Различия наблюдаемого ожидания')}</option>
          <option value="refusals">{t('Причины отказов и полнота регистрации')}</option>
        </select>
      </label>
      {hospitals.length ? (
        <BriefingForm key={JSON.stringify(request)} request={request} />
      ) : (
        <p>{t('Выберите хотя бы один стационар.')}</p>
      )}
      <p className="panel-footnote">
        {t(
          'PDF содержит агрегаты и общие метрики моделей. Подтверждение означает просмотр аналитиком, а не формальное согласование решения или назначение лечения.',
        )}{' '}
      </p>
      <p className="panel-footnote">{t('PDF-сводка формируется на русском языке.')}</p>
    </section>
  )
}
