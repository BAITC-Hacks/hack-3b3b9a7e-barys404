import { type BriefingPreview } from '../../api/types'
import { count, metric } from '../../lib/evidenceFormat'

export function BriefingReview({
  preview,
  confirmed,
  change,
}: {
  preview: BriefingPreview
  confirmed: boolean
  change: (value: boolean) => void
}) {
  return (
    <div className="briefing-preview">
      <h3>Проверьте содержимое PDF</h3>
      <p>{preview.snapshot.review_question}</p>
      <div className="evidence-table-wrap">
        <table className="evidence-table">
          <thead>
            <tr>
              <th>Стационар</th>
              <th>Направления</th>
              <th>Медиана, дни</th>
              <th>P90, дни</th>
              <th>Отказы, %</th>
            </tr>
          </thead>
          <tbody>
            {preview.snapshot.aggregates.map((row) => (
              <tr key={row.organization_or_region}>
                <th>{row.organization_or_region}</th>
                <td>{count(row.referrals)}</td>
                <td>{metric(row.median_wait_days)}</td>
                <td>{metric(row.p90_wait_days)}</td>
                <td>{metric(row.refusal_share_pct)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p>
        Минимум группы и статистик: {preview.snapshot.minimum_group_size}. Прочерк означает
        недостаточно наблюдений. P90 — описательный квантиль ожидания, не интервал прогноза.
      </p>
      {(['waiting', 'forecast'] as const).map((key) => (
        <p key={key}>
          {key === 'waiting' ? 'Ожидание, дни' : 'Поток, направления / организацию в день'}:{' '}
          {preview.metrics[key] ? (
            <>
              MAE {metric(preview.metrics[key].mae)}, baseline{' '}
              {metric(preview.metrics[key].baseline_mae)}. Версия{' '}
              {preview.metrics[key].model_version}; тест {preview.metrics[key].period}.
            </>
          ) : (
            'Актуальные метрики недоступны.'
          )}
        </p>
      ))}
      <p>
        Ошибки относятся ко всему тесту. Сравнение не учитывает тяжесть случаев и мощность. Прогноз
        потока не измеряет занятость коек. Полноту данных и доступные ресурсы нужно уточнить у
        специалиста.
      </p>
      <label className="review-check">
        <input type="checkbox" checked={confirmed} onChange={(e) => change(e.target.checked)} />Я
        проверил период, выбранные стационары, показатели и ограничения.
      </label>
    </div>
  )
}
