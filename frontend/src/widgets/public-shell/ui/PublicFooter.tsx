import { ArrowUpRight, Mail, Phone } from 'lucide-react'
import { t } from '../../../shared/lib/i18n'
import { Brand } from '../../../shared/ui/Brand'

export function PublicFooter() {
  return (
    <footer className="public-footer">
      <div className="public-footer-main">
        <div className="public-footer-about">
          <Brand />
          <p>{t('Помогаем видеть картину направлений и принимать обоснованные решения.')}</p>
          <span className="public-footer-status">
            <span aria-hidden="true" />
            {t('Локальное демо')}
          </span>
        </div>
        <nav aria-label={t('Платформа')}>
          <h2>{t('Платформа')}</h2>
          <a href="#welcome/features">{t('Возможности платформы')}</a>
          <a href="#welcome/data">{t('Что показывают данные')}</a>
          <a href="#login">
            {t('Войти в кабинет')}
            <ArrowUpRight size={15} aria-hidden="true" />
          </a>
        </nav>
        <div className="public-footer-contacts">
          <h2>{t('Контакты')}</h2>
          <address>
            <span>
              <Phone size={16} aria-hidden="true" />
              <span>
                <small>{t('Телефон')}</small>+7 (XXX) XXX-XX-XX
              </span>
            </span>
            <a href="mailto:info@example.com">
              <Mail size={16} aria-hidden="true" />
              <span>
                <small>{t('Электронная почта')}</small>info@example.com
              </span>
            </a>
          </address>
        </div>
      </div>
      <div className="public-footer-bottom">
        <span>© {new Date().getFullYear()} MedFlow AI</span>
        <a href="#privacy">{t('Политика конфиденциальности')}</a>
        <span>{t('Исторические данные: январь–март 2025 · Решения принимает специалист.')}</span>
      </div>
    </footer>
  )
}
