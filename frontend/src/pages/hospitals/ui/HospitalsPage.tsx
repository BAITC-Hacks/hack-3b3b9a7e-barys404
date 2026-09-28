import { useEffect, useState } from 'react'
import { query } from '../../../entities/hospital/index'
import { type Filters, type MetricRow } from '../../../shared/api/types'
import { HospitalRow } from '../../../widgets/hospital-directory/index'
import { EmptyState } from '../../../shared/ui/EmptyState'
import { ErrorState } from '../../../shared/ui/ErrorState'
import { Loading } from '../../../shared/ui/Loading'
import { PageHeading } from '../../../shared/ui/PageHeading'
import { SearchForm } from '../../../shared/ui/SearchForm'
import { useRemote } from '../../../shared/lib/useRemote'
import { useSubmittedSearch } from '../../../shared/lib/useSubmittedSearch'
import { organizations } from '../../../shared/lib/format'
import { regionLabel } from '../../../entities/region/index'

export function HospitalsPage({
  filters,
  openHospital,
}: {
  filters: Filters
  openHospital: (name: string) => void
}) {
  const search = useSubmittedSearch()
  const [offset, setOffset] = useState(0)
  useEffect(() => setOffset(0), [filters])
  const pageSize = 50
  const { data, loading, error } = useRemote<{
    items: MetricRow[]
    total: number
  }>(`/hospitals${query({ ...filters, search: search.applied, limit: pageSize, offset })}`)
  return (
    <>
      <PageHeading
        eyebrow="СТАЦИОНАРЫ"
        title="Найдите нужную больницу"
        description="Откройте организацию, чтобы увидеть её профиль, исходы и прогноз."
      />
      <section className="panel directory-panel">
        <div className="directory-toolbar">
          <SearchForm
            value={search.draft}
            onChange={search.setDraft}
            onSubmit={() => {
              search.submit()
              setOffset(0)
            }}
            onClear={() => {
              search.clear()
              setOffset(0)
            }}
            placeholder="Название стационара"
            label="Поиск стационара"
          />
          <span className="result-count">{data ? organizations(data.total) : 'Поиск'}</span>
        </div>
        {(filters.region || filters.profile) && (
          <div className="directory-filter-note">
            Список ограничен фильтрами:{' '}
            {[filters.region ? regionLabel(filters.region) : '', filters.profile]
              .filter(Boolean)
              .join(' · ')}
            . Сбросить их можно кнопкой выше.
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
