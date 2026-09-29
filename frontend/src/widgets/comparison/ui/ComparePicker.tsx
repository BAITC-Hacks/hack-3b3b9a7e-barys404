import { t } from '../../../shared/lib/i18n'
import { Check } from 'lucide-react'
import type { MetricRow } from '../../../shared/api/types'
import { SearchForm } from '../../../shared/ui/SearchForm'

export function ComparePicker({
  items,
  selected,
  search,
  setSearch,
  submitSearch,
  clearSearch,
  loading,
  toggle,
}: {
  items: MetricRow[]
  selected: string[]
  search: string
  setSearch: (value: string) => void
  submitSearch: () => void
  clearSearch: () => void
  loading: boolean
  toggle: (name: string) => void
}) {
  return (
    <section className="panel compare-picker">
      <div className="panel-heading">
        <div>
          <span className="section-kicker">{t('ВЫБОР')}</span>
          <h2>{t('Организации')}</h2>
          <p>{t('До трёх стационаров')}</p>
        </div>
        <span className="selection-count">{selected.length} / 3</span>
      </div>
      <SearchForm
        value={search}
        onChange={setSearch}
        onSubmit={submitSearch}
        onClear={clearSearch}
        className="compare-search"
        placeholder={t('Найти организацию')}
        label={t('Найти организацию для сравнения')}
      />
      {loading && (
        <p className="panel-footnote" role="status">
          {t('Загружаем организации…')}{' '}
        </p>
      )}
      <div className="compare-options" aria-busy={loading}>
        {items.slice(0, 18).map((item) => (
          <label className="compare-option" key={item.organization_or_region}>
            <input
              type="checkbox"
              checked={selected.includes(item.organization_or_region)}
              disabled={!selected.includes(item.organization_or_region) && selected.length >= 3}
              onChange={() => toggle(item.organization_or_region)}
            />
            <span className="custom-check">
              <Check size={13} />
            </span>
            <span>{item.organization_or_region}</span>
          </label>
        ))}
      </div>
    </section>
  )
}
