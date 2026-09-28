import { Server, Users } from 'lucide-react'
import { useState } from 'react'
import { type User } from '../../../shared/api/types'
import { AdminAccountsPanel } from '../../../widgets/platform-admin/index'
import { AdminSystemPanel } from '../../../widgets/platform-admin/index'
import { UserMenu } from '../../../entities/user/index'
import { PageHeading } from '../../../shared/ui/PageHeading'
import { Brand } from '../../../shared/ui/Brand'
import { useEntrance } from '../../../shared/lib/useEntrance'
import { useSlidingIndicator } from '../../../shared/lib/useSlidingIndicator'

export function AdminPage({ user, logout }: { user: User; logout: () => Promise<void> }) {
  const [section, setSection] = useState<'accounts' | 'system'>('accounts')
  const entrance = useEntrance<HTMLDivElement>(section, 'slide')
  const { trackRef, indicatorRef } = useSlidingIndicator<HTMLElement>(section)
  return (
    <div className="admin-shell">
      <header className="topbar">
        <Brand />
        <UserMenu user={user} logout={logout} />
      </header>
      <main className="content admin-content">
        <PageHeading
          eyebrow=""
          title="Администрирование"
          description="Аккаунты сотрудников и состояние системы."
        />
        <nav
          className="admin-navigation sliding-tabs"
          aria-label="Разделы администрирования"
          ref={trackRef}
        >
          <span className="tab-indicator" aria-hidden="true" ref={indicatorRef} />
          <button aria-pressed={section === 'accounts'} onClick={() => setSection('accounts')}>
            <Users size={18} /> Аккаунты
          </button>
          <button aria-pressed={section === 'system'} onClick={() => setSection('system')}>
            <Server size={18} /> Система
          </button>
        </nav>
        <div ref={entrance}>
          {section === 'accounts' ? <AdminAccountsPanel user={user} /> : <AdminSystemPanel />}
        </div>
      </main>
    </div>
  )
}
