import { t } from '../../../shared/lib/i18n'
import { LogOut } from 'lucide-react'
import { useState } from 'react'
import { type User } from '../../../shared/api/types'
import { roleLabel } from '../model/roles'

export function UserMenu({ user, logout }: { user: User; logout: () => Promise<void> }) {
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  return (
    <div className="user-menu">
      <div>
        <strong>{user.display_name}</strong>
        <small>{roleLabel(user.role)}</small>
      </div>
      <button
        className="icon-button"
        disabled={busy}
        title={t('Выйти')}
        aria-label={t('Выйти из аккаунта')}
        onClick={async () => {
          setBusy(true)
          setError('')
          try {
            await logout()
          } catch {
            setError('Не удалось выйти. Повторите.')
            setBusy(false)
          }
        }}
      >
        <LogOut size={17} />
      </button>
      {error && <span role="alert">{t(error)}</span>}
    </div>
  )
}
