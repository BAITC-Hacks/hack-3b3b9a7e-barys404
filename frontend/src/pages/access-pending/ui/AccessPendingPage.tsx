import { DisplayPreferences } from '../../../shared/ui/DisplayPreferences'
import { t } from '../../../shared/lib/i18n'
import { type User } from '../../../shared/api/types'
import { UserMenu } from '../../../entities/user/index'

export function AccessPendingPage({ user, logout }: { user: User; logout: () => Promise<void> }) {
  return (
    <div className="auth-state">
      <div className="auth-preferences">
        <DisplayPreferences />
      </div>
      <h1>{t('Доступ ещё не настроен')}</h1>
      <p>{t('Администратор должен назначить действующую организацию.')}</p>
      <UserMenu user={user} logout={logout} />
    </div>
  )
}
