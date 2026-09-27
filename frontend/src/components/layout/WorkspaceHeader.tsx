import { CalendarDays, ChevronRight, Menu } from 'lucide-react'
import { type Bootstrap, type User } from '../../api/types'
import { shortDay } from '../../lib/format'
import { UserMenu } from './UserMenu'

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
      <button className="mobile-menu icon-button" onClick={openMenu} aria-label="Открыть меню">
        <Menu size={22} />
      </button>
      <div className="breadcrumbs">
        <span>MedFlow AI</span>
        <ChevronRight size={15} />
        <strong>{title}</strong>
      </div>
      <div className="topbar-actions">
        <span className="period-chip">
          <CalendarDays size={15} />{' '}
          {period ? `${shortDay(period.start)} — ${shortDay(period.end)}` : 'Данные'}
        </span>
        <UserMenu user={user} logout={logout} />
      </div>
    </header>
  )
}
