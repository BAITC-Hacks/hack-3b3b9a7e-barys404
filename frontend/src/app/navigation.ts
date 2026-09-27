import { LayoutDashboard, Building2, GitCompareArrows, Sparkles, Database } from 'lucide-react'

export type View = 'overview' | 'hospitals' | 'hospital' | 'compare' | 'forecasts' | 'data'

export type Mode = 'government' | 'hospital'

export type NavItem = { id: View; label: string; icon: typeof LayoutDashboard }

export const NAV: NavItem[] = [
  { id: 'overview', label: 'Обзор', icon: LayoutDashboard },
  { id: 'hospitals', label: 'Стационары', icon: Building2 },
  { id: 'compare', label: 'Сравнение', icon: GitCompareArrows },
  { id: 'forecasts', label: 'Прогнозы', icon: Sparkles },
  { id: 'data', label: 'Как читать показатели', icon: Database },
]

export function currentRoute(): { view: View; hospital?: string } {
  const hash = window.location.hash.slice(1)
  if (hash.startsWith('hospital/')) {
    try {
      return { view: 'hospital', hospital: decodeURIComponent(hash.slice(9)) }
    } catch {
      return { view: 'overview' }
    }
  }
  const known = NAV.some((item) => item.id === hash)
  return { view: known ? (hash as View) : 'overview' }
}
