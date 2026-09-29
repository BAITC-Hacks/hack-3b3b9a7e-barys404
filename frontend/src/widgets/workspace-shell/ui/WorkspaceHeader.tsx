import { CalendarDays, ChevronRight, Menu } from 'lucide-react'
import { type Bootstrap, type User } from '../../../shared/api/types'
import { day } from '../../../shared/lib/format'
import { UserMenu } from '../../../entities/user/index'
import { DisplayPreferences } from '../../../shared/ui/DisplayPreferences'
import { t } from '../../../shared/lib/i18n'

export function WorkspaceHeader({
  title,
  period,
  user,
  logout,
  openMenu,
}: {
  title: string
  period?: Bootstrap['period']
  user: User
  logout: () => Promise<void>
  openMenu: () => void
}) {
  return (
    <header className="topbar">
      <button className="mobile-menu icon-button" onClick={openMenu} aria-label={t('Открыть меню')}>
        <Menu size={22} />
      </button>
      <div className="breadcrumbs">
        <span>MedFlow AI</span>
        <ChevronRight size={15} />
        <strong>{t(title)}</strong>
      </div>
      <div className="topbar-actions">
        <span className="period-chip">
          <CalendarDays size={15} />{' '}
          {period ? `${day(period.start)} — ${day(period.end)}` : t('Данные')}
        </span>
        <DisplayPreferences />
        <UserMenu user={user} logout={logout} />
      </div>
    </header>
  )
}
