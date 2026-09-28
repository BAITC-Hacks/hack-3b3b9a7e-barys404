import { ArrowRight, ShieldCheck } from 'lucide-react'
import { WelcomeVisual } from './WelcomeVisual'
import { useStaggeredEntrance } from '../../../shared/lib/useEntrance'

export function WelcomeHero() {
  const entrance = useStaggeredEntrance<HTMLElement>()
  return (
    <section className="welcome-hero" ref={entrance}>
      <div className="welcome-copy">
        <span className="public-eyebrow">Для больниц и органов здравоохранения</span>
        <h1>Аналитика госпитализаций</h1>
        <p>
          Следите за направлениями, сравнивайте стационары и оценивайте поток и время ожидания по
          историческим данным.
        </p>
        <a className="primary-button welcome-cta" href="#login">
          Войти в кабинет <ArrowRight size={18} />
        </a>
        <div className="welcome-access">
          <ShieldCheck size={17} />
          <span>Доступ по учётной записи вашей организации</span>
        </div>
      </div>
      <WelcomeVisual />
    </section>
  )
}
