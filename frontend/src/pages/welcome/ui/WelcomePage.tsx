import { PublicFooter } from '../../../widgets/public-shell/index'
import { PublicHeader } from '../../../widgets/public-shell/index'
import { WelcomeAudiences } from './WelcomeAudiences'
import { WelcomeHero } from './WelcomeHero'
import { WelcomeMethod } from './WelcomeMethod'

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
