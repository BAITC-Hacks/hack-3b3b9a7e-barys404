import { t } from '../../../shared/lib/i18n'
import { ArrowRight, ShieldCheck } from 'lucide-react'
import heroPhoto from '../assets/welcome-team.jpeg'
import { useStaggeredEntrance } from '../../../shared/lib/useEntrance'

export function WelcomeHero() {
  const entrance = useStaggeredEntrance<HTMLElement>(undefined, 'lift', '.welcome-copy')
  return (
    <section className="welcome-hero welcome-hero--photo" ref={entrance}>
      <img
        className="welcome-hero-photo"
        src={heroPhoto}
        alt=""
        width="1600"
        height="900"
        fetchPriority="high"
      />
      <div className="welcome-copy">
        <span className="public-eyebrow">{t('Для больниц и органов здравоохранения')}</span>
        <h1>{t('Аналитика госпитализаций')}</h1>
        <p>
          {t(
            'Следите за направлениями, сравнивайте стационары и оценивайте поток и время ожидания по историческим данным.',
          )}
        </p>
        <a className="primary-button welcome-cta" href="#login">
          {t('Войти в кабинет')}
          <ArrowRight size={18} aria-hidden="true" />
        </a>
        <div className="welcome-access">
          <ShieldCheck size={17} aria-hidden="true" />
          <span>{t('Доступ по учётной записи вашей организации')}</span>
        </div>
      </div>
    </section>
  )
}
