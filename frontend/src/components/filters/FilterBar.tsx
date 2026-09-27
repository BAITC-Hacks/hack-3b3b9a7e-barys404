import { CalendarDays, X } from 'lucide-react'
import { type Bootstrap, type Filters } from '../../api/types'

export function FilterBar({
  filters,
  setFilters,
  bootstrap,
}: {
  filters: Filters
  setFilters: (value: Filters) => void
  bootstrap: Bootstrap
}) {
  const set = (field: keyof Filters, value: string) => {
    const next = { ...filters, [field]: value }
    if (field === 'start' && value > next.end) next.end = value
    if (field === 'end' && value < next.start) next.start = value
    setFilters(next)
  }
  const reset = () =>
    setFilters({
      start: bootstrap.period.start,
      end: bootstrap.period.end,
      region: '',
      profile: '',
    })
  return (
    <div className="filter-bar">
      <div className="filter-intro">
        <span className="filter-icon">
          <CalendarDays size={18} />
        </span>
        <span>
          Период
          <br />
          <strong>регистрации</strong>
        </span>
      </div>
      <label>
        С{' '}
        <input
          type="date"
          min={bootstrap.period.start}
          max={bootstrap.period.end}
          value={filters.start}
          onChange={(event) => set('start', event.target.value)}
        />
      </label>
      <label>
        По{' '}
        <input
          type="date"
          min={bootstrap.period.start}
          max={bootstrap.period.end}
          value={filters.end}
          onChange={(event) => set('end', event.target.value)}
        />
      </label>
      <label className="filter-select">
        Регион происхождения{' '}
        <select value={filters.region} onChange={(event) => set('region', event.target.value)}>
          <option value="">Все регионы</option>
          {bootstrap.regions.map((region) => (
            <option key={region} value={region}>
              {region}
            </option>
          ))}
        </select>
      </label>
      <label className="filter-select">
        Профиль{' '}
        <select value={filters.profile} onChange={(event) => set('profile', event.target.value)}>
          <option value="">Все профили</option>
          {bootstrap.profiles.map((profile) => (
            <option key={profile} value={profile}>
              {profile}
            </option>
          ))}
        </select>
      </label>
      <button
        className="reset-button"
        onClick={reset}
        title="Сбросить фильтры"
        aria-label="Сбросить фильтры"
      >
        <X size={17} />
        <span>Сбросить</span>
      </button>
    </div>
  )
}
