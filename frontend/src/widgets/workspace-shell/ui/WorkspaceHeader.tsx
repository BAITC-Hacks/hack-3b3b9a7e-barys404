import { useEffect, useId, useRef, useState } from 'react'
import { CalendarDays, CircleUserRound, Menu, X } from 'lucide-react'
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
  const [settingsOpen, setSettingsOpen] = useState(false)
  const settingsId = useId()
  const settingsButtonRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    if (!settingsOpen) return
    const dismiss = (event: PointerEvent) => {
      if (!headerRef.current?.contains(event.target as Node)) setSettingsOpen(false)
    }
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setSettingsOpen(false)
        settingsButtonRef.current?.focus()
      }
    }
    document.addEventListener('pointerdown', dismiss)
    document.addEventListener('keydown', onKeyDown)
    return () => {
      document.removeEventListener('pointerdown', dismiss)
      document.removeEventListener('keydown', onKeyDown)
    }
  }, [settingsOpen])

  useEffect(() => {
    let anchor = Math.max(0, window.scrollY)
    const onScroll = () => {
      // Clamp elastic overscroll and ignore small trackpad movements.
      const y = Math.max(
        0,
        Math.min(window.scrollY, document.documentElement.scrollHeight - window.innerHeight),
      )
      const delta = y - anchor
      if (Math.abs(delta) >= 8) setSettingsOpen(false)
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
      <button
        className="mobile-menu icon-button"
        onClick={() => {
          setSettingsOpen(false)
          openMenu()
        }}
        aria-label={t('Открыть меню')}
      >
        <Menu size={22} />
      </button>
      <div className="workspace-location">
        <small>MedFlow AI</small>
        <strong>{t(title)}</strong>
      </div>
      <button
        ref={settingsButtonRef}
        type="button"
        className="mobile-settings-toggle icon-button"
        aria-label={t('Настройки кабинета')}
        aria-expanded={settingsOpen}
        aria-controls={settingsId}
        onClick={() => setSettingsOpen((open) => !open)}
      >
        {settingsOpen ? <X size={20} /> : <CircleUserRound size={20} />}
      </button>
      <div
        id={settingsId}
        className={`topbar-actions${settingsOpen ? ' topbar-actions--open' : ''}`}
        onBlur={(event) => {
          if (!headerRef.current?.contains(event.relatedTarget as Node | null))
            setSettingsOpen(false)
        }}
      >
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
