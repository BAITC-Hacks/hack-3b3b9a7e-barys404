import { Activity, ArrowRight, ChevronDown, Clock3 } from 'lucide-react'
import { useState } from 'react'
import { type View } from '../app/navigation'
import { FlowForecast } from '../components/forecasts/FlowForecast'
import { WaitForecast } from '../components/forecasts/WaitForecast'
import { EmptyState } from '../components/ui/EmptyState'
import { PageHeading } from '../components/ui/PageHeading'

export function ForecastsPage({
  hospital,
  go,
  canChoose,
}: {
  hospital: string
  go: (view: View) => void
  canChoose: boolean
}) {
  const [tab, setTab] = useState<'flow' | 'wait'>('flow')
  return (
    <>
      <PageHeading
        eyebrow="ПРОГНОЗЫ"
        title="Что покажет модель"
        description={hospital ? `Стационар: ${hospital}` : 'Выберите стационар для прогноза.'}
        action={
          canChoose ? (
            <button className="secondary-button" onClick={() => go('hospitals')}>
              Сменить стационар <ChevronDown size={16} />
            </button>
          ) : undefined
        }
      />
      <div className="tab-bar" role="tablist">
        <button
          role="tab"
          aria-selected={tab === 'flow'}
          className={tab === 'flow' ? 'active' : ''}
          onClick={() => setTab('flow')}
        >
          <Activity size={17} /> Поток направлений
        </button>
        <button
          role="tab"
          aria-selected={tab === 'wait'}
          className={tab === 'wait' ? 'active' : ''}
          onClick={() => setTab('wait')}
        >
          <Clock3 size={17} /> Время ожидания
        </button>
      </div>
      {hospital ? (
        tab === 'flow' ? (
          <FlowForecast hospital={hospital} />
        ) : (
          <WaitForecast key={hospital} hospital={hospital} />
        )
      ) : (
        <EmptyState
          title="Стационар не выбран"
          text="Откройте список стационаров и выберите организацию."
        />
      )}
      <p className="page-note">
        Оба прогноза построены по историческим данным. Они не назначают лечение и не изменяют
        очередь.
      </p>
      <div className="workspace-actions">
        <button className="secondary-button" onClick={() => go('validation')}>
          Проверка по периодам <ArrowRight size={16} />
        </button>
        <button className="secondary-button" onClick={() => go('hospital')}>
          Карточка и PDF-сводка <ArrowRight size={16} />
        </button>
      </div>
    </>
  )
}
