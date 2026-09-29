import { t } from '../../../shared/lib/i18n'
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
        eyebrow={t('СТАЦИОНАРЫ')}
        title={t('Найдите нужную больницу')}
        description={t('Откройте организацию, чтобы увидеть её профиль, исходы и прогноз.')}
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
            placeholder={t('Название стационара')}
            label={t('Поиск стационара')}
          />
          <span className="result-count">{data ? organizations(data.total) : t('Поиск')}</span>
        </div>
        {(filters.region || filters.profile) && (
          <div className="directory-filter-note">
            {t('Список ограничен фильтрами:')}{' '}
            {[filters.region ? regionLabel(filters.region) : '', t(filters.profile)]
              .filter(Boolean)
              .join(' · ')}
            {t('. Сбросить их можно кнопкой выше.')}{' '}
          </div>
        )}
        <div className="table-head hospital-table-head">
          <span>{t('Стационар')}</span>
          <span>{t('Направления')}</span>
          <span>{t('Ожидание')}</span>
          <span>{t('Отказы')}</span>
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
                  {t('Показаны {start}–{end} из {total}', {
                    start: offset + 1,
                    end: offset + data.items.length,
                    total: data.total,
                  })}
                </span>
                <div>
                  <button
                    disabled={offset === 0}
                    onClick={() => setOffset(Math.max(0, offset - pageSize))}
                  >
                    {t('Назад')}{' '}
                  </button>
                  <button
                    disabled={offset + pageSize >= data.total}
                    onClick={() => setOffset(offset + pageSize)}
                  >
                    {t('Далее')}{' '}
                  </button>
                </div>
              </div>
            </>
          ) : (
            <EmptyState
              title={t('Стационары не найдены')}
              text={t('Попробуйте другое название или сбросьте фильтры.')}
            />
          ))}
      </section>
      <p className="page-note">
        {t(
          'Медиана показана только при достаточном числе завершённых госпитализаций. Доля отказов считается среди известных исходов.',
        )}{' '}
      </p>
    </>
  )
}
