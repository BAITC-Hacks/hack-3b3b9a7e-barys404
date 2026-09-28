import { ArrowRight } from 'lucide-react'
import { Brand } from '../../../shared/ui/Brand'

export function PublicHeader() {
  return (
    <header className="public-header">
      <Brand />
      <a href="#login" className="secondary-button welcome-login" aria-label="Войти в кабинет">
        <span>
          Войти<span className="welcome-login-detail"> в кабинет</span>
        </span>
        <ArrowRight size={16} />
      </a>
    </header>
  )
}
