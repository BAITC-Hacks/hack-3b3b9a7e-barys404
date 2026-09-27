import { ArrowRight, ShieldCheck } from 'lucide-react'
import { WelcomeVisual } from './WelcomeVisual'

export function WelcomeHero() {
  return (
    <section className="welcome-hero">
      <div className="welcome-copy">
        <span className="public-eyebrow">
          <span /> ДАННЫЕ ДЛЯ ОБОСНОВАННЫХ РЕШЕНИЙ
        </span>
        <h1>
          Видеть поток.
          <br />
          Понимать ожидание.
        </h1>
        <p>
          Направления, работа стационаров и прогноз входящего потока — в одном рабочем пространстве
          для больниц и органов здравоохранения.
        </p>
        <a className="primary-button welcome-cta" href="#login">
          Войти в рабочий кабинет <ArrowRight size={18} />
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
