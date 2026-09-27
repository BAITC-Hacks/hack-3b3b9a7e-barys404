import { Building2, Landmark } from 'lucide-react'

export function WelcomeAudiences() {
  return (
    <section className="welcome-audiences" aria-label="Для кого платформа">
      <article>
        <span className="audience-icon">
          <Building2 size={22} />
        </span>
        <div>
          <span className="section-kicker">БОЛЬНИЦАМ</span>
          <h2>Своя организация в деталях</h2>
          <p>Динамика направлений, профили госпитализации и прогноз потока вашей больницы.</p>
        </div>
      </article>
      <article>
        <span className="audience-icon">
          <Landmark size={22} />
        </span>
        <div>
          <span className="section-kicker">ГОСОРГАНАМ</span>
          <h2>Вся система в одном обзоре</h2>
          <p>Сводные показатели, сравнение стационаров и изменения, требующие внимания.</p>
        </div>
      </article>
    </section>
  )
}
