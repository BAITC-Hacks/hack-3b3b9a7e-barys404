import { t } from '../../../shared/lib/i18n'
import { RefreshCw } from 'lucide-react'
import { useState } from 'react'
import { useRemote } from '../../../shared/lib/useRemote'
import { decimal } from '../../../shared/lib/format'
import { ErrorState } from '../../../shared/ui/ErrorState'
import { Loading } from '../../../shared/ui/Loading'

type ModelInfo = {
  status: { available: boolean; stale?: boolean; reason?: string }
  metrics: { mae?: number }
}
type SystemInfo = { waiting: ModelInfo; flow: ModelInfo; data: { ready: boolean } }

export function AdminSystemPanel() {
  const [revision, setRevision] = useState(0)
  const { data, loading, error } = useRemote<SystemInfo>(`/models?refresh=${revision}`)
  return (
    <section className="panel admin-system">
      <div className="admin-system-heading">
        <div>
          <h2>{t('Данные и модели')}</h2>
        </div>
        <button
          className="secondary-button"
          disabled={loading}
          onClick={() => setRevision((value) => value + 1)}
        >
          <RefreshCw size={17} /> {t('Обновить')}{' '}
        </button>
      </div>
      {loading && <Loading />}
      {error && <ErrorState message={t(error)} />}
      {data && (
        <div className="admin-system-grid">
          <article>
            <h3>{t('Данные')}</h3>
            <span className={`admin-status ${data.data.ready ? 'is-active' : 'is-blocked'}`}>
              {data.data.ready ? t('Готовы') : t('Не подготовлены')}
            </span>
            <p>{t('Подготовленная история для аналитики.')}</p>
          </article>
          {(
            [
              [t('Ожидание'), data.waiting, t('дня')],
              [t('Поток направлений'), data.flow, t('напр. в день')],
            ] as const
          ).map(([title, model, unit]) => (
            <article key={title}>
              <h3>{title}</h3>
              <span
                className={`admin-status ${model.status.available ? 'is-active' : 'is-blocked'}`}
              >
                {model.status.available ? t('Готова') : t('Недоступна')}
              </span>
              <p>
                {model.status.available
                  ? t('Ошибка на исторической проверке: {error} {unit}.', {
                      error: decimal(model.metrics.mae, 2),
                      unit,
                    })
                  : t(model.status.reason || 'Проверьте артефакты модели.')}
              </p>
            </article>
          ))}
        </div>
      )}
    </section>
  )
}
