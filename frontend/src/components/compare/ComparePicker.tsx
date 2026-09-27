import { Check, Search } from 'lucide-react'
import type { MetricRow } from '../../api/types'

export function ComparePicker({
  items,
  selected,
  search,
  setSearch,
  toggle,
}: {
  items: MetricRow[]
  selected: string[]
  search: string
  setSearch: (value: string) => void
  toggle: (name: string) => void
}) {
  return (
    <section className="panel compare-picker">
      <div className="panel-heading">
        <div>
          <span className="section-kicker">ВЫБОР</span>
          <h2>Организации</h2>
          <p>До трёх стационаров</p>
        </div>
        <span className="selection-count">{selected.length} / 3</span>
      </div>
      <div className="search-field compare-search">
        <Search size={16} />
        <input
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Найти организацию"
          aria-label="Найти организацию для сравнения"
        />
      </div>
      <div className="compare-options">
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
