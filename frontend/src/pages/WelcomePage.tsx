import { PublicFooter } from '../components/layout/PublicFooter'
import { PublicHeader } from '../components/layout/PublicHeader'
import { WelcomeAudiences } from '../components/welcome/WelcomeAudiences'
import { WelcomeHero } from '../components/welcome/WelcomeHero'
import { WelcomeMethod } from '../components/welcome/WelcomeMethod'

export function WelcomePage() {
  return (
    <div className="welcome-page">
      <PublicHeader />
      <main>
        <WelcomeHero />
        <WelcomeAudiences />
        <WelcomeMethod />
      </main>
      <PublicFooter />
    </div>
  )
}
