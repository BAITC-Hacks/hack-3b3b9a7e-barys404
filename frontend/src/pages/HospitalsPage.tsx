import { Search, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import { query } from '../api/client'
import { type Filters, type MetricRow } from '../api/types'
import { HospitalRow } from '../components/hospitals/HospitalRow'
import { EmptyState } from '../components/ui/EmptyState'
import { ErrorState } from '../components/ui/ErrorState'
import { Loading } from '../components/ui/Loading'
import { PageHeading } from '../components/ui/PageHeading'
import { useRemote } from '../hooks/useRemote'
import { organizations } from '../lib/format'

export function HospitalsPage({
  filters,
  openHospital,
}: {
  filters: Filters
  openHospital: (name: string) => void
}) {
  const [search, setSearch] = useState('')
  const [debounced, setDebounced] = useState('')
  const [offset, setOffset] = useState(0)
  useEffect(() => {
    const id = window.setTimeout(() => setDebounced(search), 220)
    return () => window.clearTimeout(id)
  }, [search])
  useEffect(() => setOffset(0), [filters, debounced])
  const pageSize = 50
  const { data, loading, error } = useRemote<{
    items: MetricRow[]
    total: number
  }>(`/hospitals${query({ ...filters, search: debounced, limit: pageSize, offset })}`)
  return (
    <>
      <PageHeading
        eyebrow="СТАЦИОНАРЫ"
        title="Найдите нужную больницу"
        description="Откройте организацию, чтобы увидеть её профиль, исходы и прогноз."
      />
      <section className="panel directory-panel">
        <div className="directory-toolbar">
          <div className="search-field">
            <Search size={18} />
            <input
              value={search}
              onChange={(event) => {
                setSearch(event.target.value)
                setOffset(0)
              }}
              placeholder="Название стационара"
              aria-label="Поиск стационара"
            />
            {search && (
              <button
                onClick={() => {
                  setSearch('')
                  setOffset(0)
                }}
                aria-label="Очистить поиск"
              >
                <X size={16} />
              </button>
            )}
          </div>
          <span className="result-count">{data ? organizations(data.total) : 'Поиск'}</span>
        </div>
        {(filters.region || filters.profile) && (
          <div className="directory-filter-note">
            Список ограничен фильтрами:{' '}
            {[filters.region, filters.profile].filter(Boolean).join(' · ')}. Сбросить их можно
            кнопкой выше.
          </div>
        )}
        <div className="table-head hospital-table-head">
          <span>Стационар</span>
          <span>Направления</span>
          <span>Ожидание</span>
          <span>Отказы</span>
          <span />
        </div>
        {loading && <Loading />}
        {error && <ErrorState message={error} />}
        {data &&
          (data.items.length ? (
            <>
              {data.items.map((row) => (
                <HospitalRow key={row.organization_or_region} row={row} onOpen={openHospital} />
              ))}
              <div className="directory-pagination">
                <span>
                  Показаны {offset + 1}–{offset + data.items.length} из {data.total}
                </span>
                <div>
                  <button
                    disabled={offset === 0}
                    onClick={() => setOffset(Math.max(0, offset - pageSize))}
                  >
                    Назад
                  </button>
                  <button
                    disabled={offset + pageSize >= data.total}
                    onClick={() => setOffset(offset + pageSize)}
                  >
                    Далее
                  </button>
                </div>
              </div>
            </>
          ) : (
            <EmptyState
              title="Стационары не найдены"
              text="Попробуйте другое название или сбросьте фильтры."
            />
          ))}
      </section>
      <p className="page-note">
        Медиана показана только при достаточном числе завершённых госпитализаций. Доля отказов
        считается среди известных исходов.
      </p>
    </>
  )
}
