import { useEffect } from 'react'
import { PublicFooter } from '../../../widgets/public-shell/index'
import { PublicHeader } from '../../../widgets/public-shell/index'
import { WelcomeAudiences } from './WelcomeAudiences'
import { WelcomeHero } from './WelcomeHero'
import { WelcomeMap } from './WelcomeMap'
import { WelcomeMethod } from './WelcomeMethod'

export function WelcomePage({ section }: { section?: string }) {
  useEffect(() => {
    const target = section && document.getElementById(`welcome-${section}`)
    if (target) {
      target.scrollIntoView({ block: 'start' })
      target.focus({ preventScroll: true })
    } else {
      window.scrollTo(0, 0)
    }
  }, [section])
  return (
    <div className="welcome-page">
      <PublicHeader />
      <main>
        <WelcomeHero />
        <WelcomeMap />
        <WelcomeAudiences />
        <WelcomeMethod />
      </main>
      <PublicFooter />
    </div>
  )
}
