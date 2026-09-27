import { Building2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import { hospitalId, hospitalName } from '../api/client'
import { type Bootstrap, type Filters, type User } from '../api/types'
import { FilterBar } from '../components/filters/FilterBar'
import { HospitalChooser } from '../components/hospitals/HospitalChooser'
import { Onboarding } from '../components/layout/Onboarding'
import { Sidebar } from '../components/layout/Sidebar'
import { WorkspaceHeader } from '../components/layout/WorkspaceHeader'
import { EmptyState } from '../components/ui/EmptyState'
import { ErrorState } from '../components/ui/ErrorState'
import { Loading } from '../components/ui/Loading'
import { useRemote } from '../hooks/useRemote'
import { ComparePage } from '../pages/ComparePage'
import { DataPage } from '../pages/DataPage'
import { ForecastsPage } from '../pages/ForecastsPage'
import { HospitalPage } from '../pages/HospitalPage'
import { HospitalsPage } from '../pages/HospitalsPage'
import { OverviewPage } from '../pages/OverviewPage'
import { QualityPage } from '../pages/QualityPage'
import { SignalsPage } from '../pages/SignalsPage'
import { ValidationPage } from '../pages/ValidationPage'
import { currentRoute, NAV, type Mode, type NavItem, type View } from './navigation'

export function Workspace({ user, logout }: { user: User; logout: () => Promise<void> }) {
  const boot = useRemote<Bootstrap>('/bootstrap')
  const mode: Mode = user.role === 'hospital_analyst' ? 'hospital' : 'government'
  const [route, setRoute] = useState(currentRoute)
  const [hospital, setHospital] = useState('')
  const [analysisHospital, setAnalysisHospital] = useState('')
  const [filters, setFilters] = useState<Filters>({ start: '', end: '', region: '', profile: '' })
  const [menuOpen, setMenuOpen] = useState(false)
  const [compareFocus, setCompareFocus] = useState('')
  useEffect(() => {
    const update = () => setRoute(currentRoute())
    window.addEventListener('hashchange', update)
    return () => window.removeEventListener('hashchange', update)
  }, [])
  useEffect(() => {
    if (!boot.data) return
    setFilters((previous) =>
      previous.start
        ? previous
        : { start: boot.data!.period.start, end: boot.data!.period.end, region: '', profile: '' },
    )
    setHospital(
      (previous) =>
        previous ||
        (mode === 'hospital'
          ? user.hospital_name || ''
          : hospitalName(route.hospital || '') || boot.data!.featured_hospital),
    )
  }, [boot.data, route.hospital])
  useEffect(() => {
    if (route.hospital && boot.data) {
      const name = hospitalName(route.hospital)
      if (name) setHospital(name)
    }
  }, [route.hospital, boot.data])
  const navigate = (view: View, name?: string) => {
    const next = view === 'hospital' ? `hospital/${hospitalId(name || hospital)}` : view
    if (window.location.hash === `#${next}`) setRoute(currentRoute())
    else window.location.hash = next
    setMenuOpen(false)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
  const openHospital = (name: string) => {
    setHospital(name)
    setAnalysisHospital(name)
    navigate('hospital', name)
  }
  const openForecast = (name: string) => {
    setHospital(name)
    setAnalysisHospital(name)
    navigate('forecasts')
  }
  const inspectHospital = (view: 'signals' | 'quality') => {
    setAnalysisHospital(hospital)
    navigate(view)
  }
  const openComparison = () => {
    setCompareFocus(hospital)
    navigate('compare')
  }
  const allowed =
    !(mode === 'hospital' && ['hospitals', 'compare'].includes(route.view)) &&
    !(route.hospital && boot.data && !hospitalName(route.hospital))
  const activeView = route.view
  const title = NAV.find((item) => item.id === activeView)?.label ?? 'Стационар'
  const visibleNav: NavItem[] =
    mode === 'hospital'
      ? NAV.flatMap((item) =>
          item.id === 'hospitals'
            ? [{ id: 'hospital' as View, label: 'Моя больница', icon: Building2 }]
            : item.id === 'compare'
              ? []
              : [item],
        )
      : NAV
  const scopedHospital = mode === 'hospital' ? hospital : analysisHospital
  return (
    <div className="app-shell">
      <Sidebar
        open={menuOpen}
        items={visibleNav}
        activeView={activeView}
        mode={mode}
        navigate={navigate}
        onHospital={() => openHospital(hospital)}
      />
      {menuOpen && (
        <button
          className="mobile-overlay"
          onClick={() => setMenuOpen(false)}
          aria-label="Закрыть меню"
        />
      )}
      <div className="workspace">
        <WorkspaceHeader
          title={activeView === 'hospital' ? 'Карточка стационара' : title}
          period={boot.data?.period}
          user={user}
          logout={logout}
          openMenu={() => setMenuOpen(true)}
        />
        {boot.loading ? (
          <Loading />
        ) : boot.error ? (
          <div className="boot-error">
            <ErrorState message={boot.error} />
            <p>Проверьте, что API запущен и подготовленные данные находятся в папке проекта.</p>
          </div>
        ) : (
          boot.data &&
          filters.start && (
            <main className="content">
              {mode === 'hospital' && (
                <div className="hospital-context">
                  <Building2 size={18} />
                  <div className="assigned-hospital">
                    <span className="context-label">ВАША ОРГАНИЗАЦИЯ</span>
                    <strong>{user.hospital_name}</strong>
                  </div>
                </div>
              )}
              {mode === 'government' && activeView === 'forecasts' && (
                <div className="hospital-context">
                  <span className="context-label">Стационар</span>
                  <HospitalChooser
                    hospital={hospital}
                    hospitals={boot.data.hospitals}
                    choose={setHospital}
                  />
                </div>
              )}
              {!allowed ? (
                <EmptyState
                  title="Нет доступа к этой странице"
                  text="Выберите доступный раздел в меню. Данные других организаций закрыты."
                />
              ) : (
                <>
                  {mode === 'government' && ['signals', 'quality'].includes(activeView) && (
                    <div className="hospital-context">
                      <span className="context-label">Область анализа</span>
                      <HospitalChooser
                        hospital={analysisHospital || 'Все стационары'}
                        hospitals={['Все стационары', ...boot.data.hospitals]}
                        choose={(name) =>
                          setAnalysisHospital(name === 'Все стационары' ? '' : name)
                        }
                      />
                    </div>
                  )}
                  {activeView === 'overview' && <Onboarding user={user} go={navigate} />}
                  {['overview', 'hospitals', 'hospital', 'compare', 'signals', 'quality'].includes(
                    activeView,
                  ) && (
                    <FilterBar filters={filters} setFilters={setFilters} bootstrap={boot.data} />
                  )}
                  {activeView === 'overview' && (
                    <OverviewPage
                      mode={mode}
                      hospital={hospital}
                      filters={filters}
                      openHospital={openHospital}
                      go={navigate}
                    />
                  )}
                  {activeView === 'hospitals' && (
                    <HospitalsPage filters={filters} openHospital={openHospital} />
                  )}
                  {activeView === 'hospital' && (
                    <HospitalPage
                      hospital={hospital}
                      filters={filters}
                      mode={mode}
                      go={navigate}
                      compare={openComparison}
                      inspect={inspectHospital}
                    />
                  )}
                  {activeView === 'compare' && (
                    <ComparePage
                      filters={filters}
                      openHospital={openHospital}
                      focus={compareFocus}
                    />
                  )}
                  {activeView === 'forecasts' && (
                    <ForecastsPage
                      hospital={hospital}
                      go={navigate}
                      canChoose={mode === 'government'}
                    />
                  )}
                  {activeView === 'signals' && (
                    <SignalsPage
                      key={JSON.stringify([filters, scopedHospital])}
                      filters={filters}
                      hospital={scopedHospital}
                      openHospital={openHospital}
                      forecast={openForecast}
                      quality={() => navigate('quality')}
                    />
                  )}
                  {activeView === 'quality' && (
                    <QualityPage filters={filters} hospital={scopedHospital} />
                  )}
                  {activeView === 'validation' && (
                    <ValidationPage hospitalRole={mode === 'hospital'} />
                  )}
                  {activeView === 'data' && <DataPage />}
                </>
              )}
            </main>
          )
        )}
      </div>
    </div>
  )
}
