import { ArrowRight } from 'lucide-react'
import { Brand } from '../../../shared/ui/Brand'
import { DisplayPreferences } from '../../../shared/ui/DisplayPreferences'
import { t } from '../../../shared/lib/i18n'

export function PublicHeader() {
  return (
    <header className="public-header">
      <Brand />
      <div className="public-header-actions">
        <DisplayPreferences />
        <a
          href="#login"
          className="secondary-button welcome-login"
          aria-label={t('Войти в кабинет')}
        >
          <span>{t('Войти')}</span>
          <ArrowRight size={16} aria-hidden="true" />
        </a>
      </div>
    </header>
  )
}
