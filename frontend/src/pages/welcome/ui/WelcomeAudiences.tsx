import { t } from '../../../shared/lib/i18n'
import { Building2, Landmark } from 'lucide-react'
import { useStaggeredEntrance } from '../../../shared/lib/useEntrance'

export function WelcomeAudiences() {
  const entrance = useStaggeredEntrance<HTMLElement>()
  return (
    <section className="welcome-audiences" aria-label={t('Для кого платформа')} ref={entrance}>
      <article>
        <span className="audience-icon">
          <Building2 size={22} />
        </span>
        <div>
          <h2>{t('Больницам')}</h2>
          <p>
            {t('Динамика направлений, профили госпитализации и прогноз потока вашей больницы.')}
          </p>
        </div>
      </article>
      <article>
        <span className="audience-icon">
          <Landmark size={22} />
        </span>
        <div>
          <h2>{t('Госорганам')}</h2>
          <p>{t('Сводные показатели, сравнение стационаров и изменения, требующие внимания.')}</p>
        </div>
      </article>
    </section>
  )
}
