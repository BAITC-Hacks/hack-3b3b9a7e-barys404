import { Activity } from 'lucide-react'
import { type Mode, type NavItem, type View } from '../../../shared/config/navigation'

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
          <small>Госпитальная аналитика</small>
        </div>
      </div>
      <div className="sidebar-divider" aria-hidden="true" />
      <nav aria-label="Основная навигация">
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
              <span>{item.label}</span>
              {active && <span className="nav-indicator" />}
            </button>
          )
        })}
      </nav>
      <div className="sidebar-bottom">
        <div className="sidebar-live">
          <span /> Локальное демо
        </div>
        <p>Исторические данные · 2025</p>
      </div>
    </aside>
  )
}
