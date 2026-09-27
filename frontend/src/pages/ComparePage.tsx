import { Info } from 'lucide-react'
import { useEffect, useState } from 'react'
import { query } from '../api/client'
import { type Filters, type MetricRow } from '../api/types'
import { BriefingPanel } from '../components/briefing/BriefingPanel'
import { ComparePicker } from '../components/compare/ComparePicker'
import { CompareResults } from '../components/compare/CompareResults'
import { ErrorState } from '../components/ui/ErrorState'
import { Loading } from '../components/ui/Loading'
import { PageHeading } from '../components/ui/PageHeading'
import { useRemote } from '../hooks/useRemote'

export function ComparePage({
  filters,
  openHospital,
  focus,
}: {
  filters: Filters
  openHospital: (name: string) => void
  focus: string
}) {
  const [search, setSearch] = useState('')
  const [debounced, setDebounced] = useState('')
  useEffect(() => {
    const id = window.setTimeout(() => setDebounced(search), 220)
    return () => window.clearTimeout(id)
  }, [search])
  const [selected, setSelected] = useState<string[]>(focus ? [focus] : [])
  const { data, loading, error } = useRemote<{
    items: MetricRow[]
    total: number
  }>(
    `/compare${query({ ...filters, minimum: 30, search: debounced, selected: selected.join('|') })}`,
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
      {loading && <Loading />}
      {error && <ErrorState message={error} />}
      {data && (
        <div className="compare-layout">
          <ComparePicker
            items={data.items}
            selected={selected}
            search={search}
            setSearch={setSearch}
            toggle={toggle}
          />
          <CompareResults chosen={chosen} openHospital={openHospital} />
        </div>
      )}
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
