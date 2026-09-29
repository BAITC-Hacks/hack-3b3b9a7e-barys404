import { useEffect, useRef, useState } from 'react'
import { CalendarDays, Menu } from 'lucide-react'
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
  const headerRef = useRef<HTMLElement>(null)
  const [hidden, setHidden] = useState(false)

  useEffect(() => {
    let anchor = Math.max(0, window.scrollY)
    const onScroll = () => {
      // Clamp elastic overscroll and ignore small trackpad movements.
      const y = Math.max(
        0,
        Math.min(window.scrollY, document.documentElement.scrollHeight - window.innerHeight),
      )
      const delta = y - anchor
      if (y <= (headerRef.current?.offsetHeight ?? 78) + 24) {
        setHidden(false)
        anchor = y
      } else if (Math.abs(delta) >= 8) {
        setHidden(delta > 0)
        anchor = y
      }
    }
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <header
      ref={headerRef}
      className={`topbar${hidden ? ' topbar--hidden' : ''}`}
      onFocusCapture={() => setHidden(false)}
    >
      <button className="mobile-menu icon-button" onClick={openMenu} aria-label={t('Открыть меню')}>
        <Menu size={22} />
      </button>
      <div className="workspace-location">
        <small>MedFlow AI</small>
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
