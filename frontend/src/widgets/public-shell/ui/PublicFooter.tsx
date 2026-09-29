import { t } from '../../../shared/lib/i18n'
export function PublicFooter() {
  return (
    <footer className="public-footer">
      <span>{t('MedFlow AI · Демонстрационная платформа')}</span>
      <span>{t('Исторические данные: январь–март 2025 · Решения принимает специалист')}</span>
    </footer>
  )
}
