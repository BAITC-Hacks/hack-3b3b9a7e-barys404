import { t } from '../lib/i18n'

export function Loading({ label = 'Загружаем данные' }: { label?: string }) {
  return (
    <div className="loading-state">
      <div className="spinner" />
      <span>{t(label)}…</span>
    </div>
  )
}
