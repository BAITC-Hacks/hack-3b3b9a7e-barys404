import { Activity, Building2, ChevronRight, Landmark } from 'lucide-react'
import { type Mode, type NavItem, type View } from '../../../shared/config/navigation'
import { t } from '../../../shared/lib/i18n'

export function Sidebar({
  open,
  items,
  activeView,
  mode,
  navigate,
  onHospital,
}: {
  open: boolean
  items: NavItem[]
  activeView: View
  mode: Mode
  navigate: (view: View) => void
  onHospital: () => void
}) {
  return (
    <aside className={`sidebar ${open ? 'sidebar-open' : ''}`}>
      <div className="brand">
        <div className="brand-mark">
          <Activity size={21} strokeWidth={1.8} />
        </div>
        <div>
          <strong>
            MedFlow<span>AI</span>
          </strong>
          <small>{t('Госпитальная аналитика')}</small>
        </div>
      </div>
      <div className="sidebar-workspace">
        {mode === 'hospital' ? <Building2 size={18} /> : <Landmark size={18} />}
        <div>
          <small>{t('Рабочий кабинет')}</small>
          <strong>{t(mode === 'hospital' ? 'Больница' : 'Госорган')}</strong>
        </div>
      </div>
      <nav aria-label={t('Основная навигация')}>
        {items.map((item) => {
          const Icon = item.icon
          const active =
            activeView === item.id ||
            (mode === 'government' && activeView === 'hospital' && item.id === 'hospitals')
          return (
            <button
              key={item.id}
              className={`nav-link ${active ? 'nav-active' : ''}`}
              aria-current={active ? 'page' : undefined}
              onClick={() => (item.id === 'hospital' ? onHospital() : navigate(item.id))}
            >
              <Icon size={19} strokeWidth={1.8} />
              <span>{t(item.label)}</span>
              {active && <ChevronRight size={15} className="nav-chevron" aria-hidden="true" />}
            </button>
          )
        })}
      </nav>
      <div className="sidebar-bottom">
        <div className="sidebar-live">
          <span /> {t('Локальное демо')}
        </div>
        <p>{t('Исторические данные · 2025')}</p>
      </div>
    </aside>
  )
}
