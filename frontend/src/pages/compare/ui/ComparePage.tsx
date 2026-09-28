import { Info } from 'lucide-react'
import { useEffect, useState } from 'react'
import { query } from '../../../entities/hospital/index'
import { type Filters, type MetricRow } from '../../../shared/api/types'
import { BriefingPanel } from '../../../features/export-briefing/index'
import { ComparePicker } from '../../../widgets/comparison/index'
import { CompareResults } from '../../../widgets/comparison/index'
import { ErrorState } from '../../../shared/ui/ErrorState'
import { Loading } from '../../../shared/ui/Loading'
import { PageHeading } from '../../../shared/ui/PageHeading'
import { useRemote } from '../../../shared/lib/useRemote'
import { useSubmittedSearch } from '../../../shared/lib/useSubmittedSearch'

export function ComparePage({
  filters,
  openHospital,
  focus,
}: {
  filters: Filters
  openHospital: (name: string) => void
  focus: string
}) {
  const search = useSubmittedSearch()
  const [selected, setSelected] = useState<string[]>(focus ? [focus] : [])
  const { data, loading, error } = useRemote<{
    items: MetricRow[]
    total: number
  }>(
    `/compare${query({ ...filters, minimum: 30, search: search.applied, selected: selected.join('|') })}`,
  )
  useEffect(() => {
    if (data?.items.length && !selected.length)
      setSelected(data.items.slice(0, 3).map((item) => item.organization_or_region))
  }, [data, selected.length])
  const chosen = data?.items.filter((item) => selected.includes(item.organization_or_region)) ?? []
  const toggle = (name: string) =>
    setSelected((previous) =>
      previous.includes(name)
        ? previous.filter((item) => item !== name)
        : previous.length < 3
          ? [...previous, name]
          : previous,
    )
  return (
    <>
      <PageHeading
        eyebrow="СРАВНЕНИЕ"
        title="Сопоставьте стационары"
        description="Выберите до трёх организаций за один период и с одинаковыми фильтрами."
      />
      {error && <ErrorState message={error} />}
      <div className="compare-layout">
        <ComparePicker
          items={data?.items ?? []}
          selected={selected}
          search={search.draft}
          setSearch={search.setDraft}
          submitSearch={search.submit}
          clearSearch={search.clear}
          loading={loading}
          toggle={toggle}
        />
        {loading ? (
          <section className="panel compare-results">
            <Loading />
          </section>
        ) : data ? (
          <CompareResults chosen={chosen} openHospital={openHospital} />
        ) : null}
      </div>
      <p className="page-note">
        Сравнение описывает данные, но не учитывает сложность случаев и коечную мощность. Оно не
        является рейтингом качества больниц.
      </p>
      {data &&
        selected.some((name) => !chosen.some((row) => row.organization_or_region === name)) && (
          <div className="workspace-note">
            <Info size={18} />
            <span>
              Часть выбранных организаций не проходит текущие фильтры или минимум 30 направлений. В
              сводку войдут только видимые результаты.
            </span>
            <button
              className="text-button"
              onClick={() => setSelected(chosen.map((row) => row.organization_or_region))}
            >
              Снять скрытый выбор
            </button>
          </div>
        )}
      {data && (
        <BriefingPanel
          filters={filters}
          hospitals={chosen.map((row) => row.organization_or_region)}
        />
      )}
    </>
  )
}
