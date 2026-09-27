import { useState } from 'react'
import { hospitalId } from '../../api/client'
import { type BriefingInput, type Filters } from '../../api/types'
import { day } from '../../lib/evidenceFormat'
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
      <span className="section-kicker">ПРОВЕРКА СПЕЦИАЛИСТОМ</span>
      <h2>Сводка для обсуждения</h2>
      <p>
        Период регистрации: {day(filters.start)} — {day(filters.end)}. Профиль:{' '}
        {filters.profile || 'все'}. Регион происхождения: {filters.region || 'все'}.
      </p>
      <label className="briefing-question">
        Вопрос для проверки{' '}
        <select
          value={question}
          onChange={(e) => setQuestion(e.target.value as BriefingInput['question'])}
        >
          <option value="flow">Поток направлений и доступная мощность</option>
          <option value="waiting">Различия наблюдаемого ожидания</option>
          <option value="refusals">Причины отказов и полнота регистрации</option>
        </select>
      </label>
      {hospitals.length ? (
        <BriefingForm key={JSON.stringify(request)} request={request} />
      ) : (
        <p>Выберите хотя бы один стационар.</p>
      )}
      <p className="panel-footnote">
        PDF содержит агрегаты и общие метрики моделей. Подтверждение означает просмотр аналитиком, а
        не формальное согласование решения или назначение лечения.
      </p>
    </section>
  )
}
