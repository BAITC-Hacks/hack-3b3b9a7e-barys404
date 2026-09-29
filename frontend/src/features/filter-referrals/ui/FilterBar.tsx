import { t } from '../../../shared/lib/i18n'
import { useEffect, useState } from 'react'
import { ArrowRight, CalendarDays, X } from 'lucide-react'
import { type Bootstrap, type Filters } from '../../../shared/api/types'
import { regionLabel } from '../../../entities/region/index'
import { editFilterDraft, initialFilters } from '../model/filterDraft'

export function FilterBar({
  filters,
  setFilters,
  bootstrap,
}: {
  filters: Filters
  setFilters: (value: Filters) => void
  bootstrap: Bootstrap
}) {
  const [draft, setDraft] = useState(filters)
  useEffect(() => {
    setDraft({
      start: filters.start,
      end: filters.end,
      region: filters.region,
      profile: filters.profile,
    })
  }, [filters.start, filters.end, filters.region, filters.profile])
  const dirty = (Object.keys(filters) as (keyof Filters)[]).some(
    (key) => draft[key] !== filters[key],
  )
  const set = (field: keyof Filters, value: string) => {
    setDraft((previous) => editFilterDraft(previous, field, value))
  }
  const reset = () => {
    const next = initialFilters(bootstrap.period)
    setDraft(next)
    setFilters(next)
  }
  return (
    <form
      className="filter-bar"
      aria-label={t('Фильтры направлений')}
      onSubmit={(event) => {
        event.preventDefault()
        if (dirty) setFilters({ ...draft })
      }}
    >
      <fieldset className="filter-period">
        <legend>
          <CalendarDays size={15} aria-hidden="true" /> {t('Период регистрации')}{' '}
        </legend>
        <div className="date-range-control">
          <label className="date-range-field">
            <span>{t('С')}</span>
            <input
              type="date"
              required
              min={bootstrap.period.start}
              max={bootstrap.period.end}
              value={draft.start}
              onChange={(event) => set('start', event.target.value)}
            />
          </label>
          <ArrowRight size={14} className="date-range-separator" aria-hidden="true" />
          <label className="date-range-field">
            <span>{t('По')}</span>
            <input
              type="date"
              required
              min={bootstrap.period.start}
              max={bootstrap.period.end}
              value={draft.end}
              onChange={(event) => set('end', event.target.value)}
            />
          </label>
        </div>
      </fieldset>
      <label className="filter-select">
        {t('Регион происхождения')}{' '}
        <select
          value={draft.region}
          title={regionLabel(draft.region)}
          onChange={(event) => set('region', event.target.value)}
        >
          <option value="">{t('Все регионы')}</option>
          {bootstrap.regions.map((region) => (
            <option key={region} value={region}>
              {regionLabel(region)}
            </option>
          ))}
        </select>
      </label>
      <label className="filter-select">
        {t('Профиль')}{' '}
        <select value={draft.profile} onChange={(event) => set('profile', event.target.value)}>
          <option value="">{t('Все профили')}</option>
          {bootstrap.profiles.map((profile) => (
            <option key={profile} value={profile}>
              {t(profile)}
            </option>
          ))}
        </select>
      </label>
      <div className="filter-actions">
        <button className="primary-button filter-apply" type="submit" disabled={!dirty}>
          {t('Применить')}
        </button>
        <button
          type="button"
          className="reset-button"
          onClick={reset}
          title={t('Сбросить фильтры')}
          aria-label={t('Сбросить фильтры')}
        >
          <X size={17} />
          <span>{t('Сбросить')}</span>
        </button>
      </div>
      {dirty && (
        <span className="filter-pending" role="status">
          {t('Изменения не применены')}
        </span>
      )}
    </form>
  )
}
