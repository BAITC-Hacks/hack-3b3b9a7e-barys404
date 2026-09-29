import { t } from '../../../shared/lib/i18n'
import { type BriefingPreview } from '../../../shared/api/types'
import { count, metric } from '../../../shared/lib/evidenceFormat'

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
      <h3>{t('Проверьте содержимое PDF')}</h3>
      <p>{t(preview.snapshot.review_question)}</p>
      <div className="evidence-table-wrap">
        <table className="evidence-table">
          <thead>
            <tr>
              <th>{t('Стационар')}</th>
              <th>{t('Направления')}</th>
              <th>{t('Медиана, дни')}</th>
              <th>{t('P90, дни')}</th>
              <th>{t('Отказы, %')}</th>
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
        {t(
          'Минимум группы и статистик: {minimum}. Прочерк означает недостаточно наблюдений. P90 — описательный квантиль ожидания, не интервал прогноза.',
          { minimum: preview.snapshot.minimum_group_size },
        )}
      </p>
      {(['waiting', 'forecast'] as const).map((key) => (
        <p key={key}>
          {key === 'waiting' ? t('Ожидание, дни') : t('Поток, направления / организацию в день')}:{' '}
          {preview.metrics[key]
            ? t('MAE {mae}, базовый прогноз {baseline}. Версия {version}; тест {period}.', {
                mae: metric(preview.metrics[key].mae),
                baseline: metric(preview.metrics[key].baseline_mae),
                version: preview.metrics[key].model_version,
                period: preview.metrics[key].period,
              })
            : t('Актуальные метрики недоступны.')}
        </p>
      ))}
      <p>
        {t(
          'Ошибки относятся ко всему тесту. Сравнение не учитывает тяжесть случаев и мощность. Прогноз потока не измеряет занятость коек. Полноту данных и доступные ресурсы нужно уточнить у специалиста.',
        )}{' '}
      </p>
      <label className="review-check">
        <input type="checkbox" checked={confirmed} onChange={(e) => change(e.target.checked)} />
        {t('Я проверил период, выбранные стационары, показатели и ограничения.')}{' '}
      </label>
    </div>
  )
}
