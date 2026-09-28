import { Activity, ArrowRight, Clock3 } from 'lucide-react'
import { useId, useState } from 'react'
import { type View } from '../../../shared/config/navigation'
import { FlowForecast } from '../../../widgets/forecasts/index'
import { WaitForecast } from '../../../widgets/forecasts/index'
import { EmptyState } from '../../../shared/ui/EmptyState'
import { PageHeading } from '../../../shared/ui/PageHeading'
import { useEntrance } from '../../../shared/lib/useEntrance'
import { useSlidingIndicator } from '../../../shared/lib/useSlidingIndicator'

export function ForecastsPage({ hospital, go }: { hospital: string; go: (view: View) => void }) {
  const [tab, setTab] = useState<'flow' | 'wait'>('flow')
  const id = useId()
  const tabEntrance = useEntrance<HTMLDivElement>(tab, 'slide')
  const { trackRef, indicatorRef } = useSlidingIndicator<HTMLDivElement>(tab)
  return (
    <>
      <PageHeading
        eyebrow=""
        title={tab === 'flow' ? 'Прогноз направлений' : 'Оценка ожидания'}
        description={`${hospital ? `Стационар: ${hospital}. ` : ''}${
          tab === 'flow'
            ? 'Сколько направлений может поступить за следующие семь дней после конца данных.'
            : 'Оценка срока от регистрации направления до госпитализации по историческим данным.'
        }`}
      />
      <div
        className="tab-bar sliding-tabs"
        role="tablist"
        aria-label="Тип прогноза"
        ref={trackRef}
        onKeyDown={(event) => {
          if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return
          event.preventDefault()
          const next =
            event.key === 'Home'
              ? 'flow'
              : event.key === 'End'
                ? 'wait'
                : tab === 'flow'
                  ? 'wait'
                  : 'flow'
          setTab(next)
          trackRef.current?.querySelector<HTMLButtonElement>(`[data-tab="${next}"]`)?.focus()
        }}
      >
        <span className="tab-indicator" aria-hidden="true" ref={indicatorRef} />
        <button
          role="tab"
          id={`${id}-flow`}
          data-tab="flow"
          aria-controls={`${id}-panel`}
          tabIndex={tab === 'flow' ? 0 : -1}
          aria-selected={tab === 'flow'}
          className={tab === 'flow' ? 'active' : ''}
          onClick={() => setTab('flow')}
        >
          <Activity size={17} /> Поток направлений
        </button>
        <button
          role="tab"
          id={`${id}-wait`}
          data-tab="wait"
          aria-controls={`${id}-panel`}
          tabIndex={tab === 'wait' ? 0 : -1}
          aria-selected={tab === 'wait'}
          className={tab === 'wait' ? 'active' : ''}
          onClick={() => setTab('wait')}
        >
          <Clock3 size={17} /> Время ожидания
        </button>
      </div>
      <div ref={tabEntrance} role="tabpanel" id={`${id}-panel`} aria-labelledby={`${id}-${tab}`}>
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
      </div>
      <div className="workspace-actions">
        <button className="secondary-button" onClick={() => go('hospital')}>
          Карточка и PDF-сводка <ArrowRight size={16} />
        </button>
      </div>
    </>
  )
}
