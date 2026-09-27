import { type User } from '../api/types'
import { UserMenu } from '../components/layout/UserMenu'

export function AccessPendingPage({ user, logout }: { user: User; logout: () => Promise<void> }) {
  return (
    <div className="auth-state">
      <h1>Доступ ещё не настроен</h1>
      <p>Администратор должен назначить действующую организацию.</p>
      <UserMenu user={user} logout={logout} />
    </div>
  )
}
