import { DisplayPreferences } from '../../../shared/ui/DisplayPreferences'
import { t } from '../../../shared/lib/i18n'
import { Server, Users } from 'lucide-react'
import { useState } from 'react'
import { type User } from '../../../shared/api/types'
import { AdminAccountsPanel } from '../../../widgets/platform-admin/index'
import { AdminSystemPanel } from '../../../widgets/platform-admin/index'
import { UserMenu } from '../../../entities/user/index'
import { PageHeading } from '../../../shared/ui/PageHeading'
import { Brand } from '../../../shared/ui/Brand'
import { useEntrance } from '../../../shared/lib/useEntrance'

export function AdminPage({ user, logout }: { user: User; logout: () => Promise<void> }) {
  const [section, setSection] = useState<'accounts' | 'system'>('accounts')
  const entrance = useEntrance<HTMLDivElement>(section, 'slide')
  return (
    <div className="admin-shell">
      <header className="topbar">
        <Brand />
        <DisplayPreferences />
        <UserMenu user={user} logout={logout} />
      </header>
      <div className="admin-workspace">
        <aside className="admin-sidebar">
          <p>{t('Администрирование')}</p>
          <nav className="admin-navigation" aria-label={t('Разделы администрирования')}>
            <button aria-pressed={section === 'accounts'} onClick={() => setSection('accounts')}>
              <Users size={18} /> {t('Аккаунты')}{' '}
            </button>
            <button aria-pressed={section === 'system'} onClick={() => setSection('system')}>
              <Server size={18} /> {t('Система')}{' '}
            </button>
          </nav>
          <small>{t('Аккаунты сотрудников и состояние системы.')}</small>
        </aside>
        <main className="content admin-content">
          <PageHeading
            eyebrow=""
            title={t(section === 'accounts' ? 'Аккаунты' : 'Система')}
            description={t('Аккаунты сотрудников и состояние системы.')}
          />
          <div ref={entrance}>
            {section === 'accounts' ? <AdminAccountsPanel user={user} /> : <AdminSystemPanel />}
          </div>
        </main>
      </div>
    </div>
  )
}
