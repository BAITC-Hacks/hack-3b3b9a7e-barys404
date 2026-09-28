import { useRemote } from '../../../shared/lib/useRemote'
import { PageHeading } from '../../../shared/ui/PageHeading'
import { Loading } from '../../../shared/ui/Loading'
import { ErrorState } from '../../../shared/ui/ErrorState'
import { MetricCard } from '../../../shared/ui/MetricCard'
import { decimal } from '../../../shared/lib/format'
import { Clock3, Activity } from 'lucide-react'

export function DataPage() {
  const { data, loading, error } = useRemote<{
    waiting_mae: number | null
    flow_mae: number | null
  }>('/methodology')
  return (
    <>
      <PageHeading
        eyebrow="МЕТОДОЛОГИЯ"
        title="Как читать показатели"
        description="Что означают цифры в кабинете и какие выводы можно из них делать."
      />
      <section className="panel limitations-panel">
        <span className="section-kicker">ТРИ ОСНОВНЫХ ПОНЯТИЯ</span>
        <div className="limitations-grid">
          <div>
            <b>Направления</b>
            <p>
              Зарегистрированные направления в выбранном периоде. Динамика не показывает свободные
              койки или нагрузку на персонал.
            </p>
          </div>
          <div>
            <b>Ожидание</b>
            <p>
              Полный срок от регистрации до госпитализации среди завершённых случаев. Это не
              оставшееся время ожидания конкретного пациента.
            </p>
          </div>
          <div>
            <b>Прогноз потока</b>
            <p>
              Оценка новых направлений на семь дней после последней даты в истории. Прогноз не
              описывает сегодняшнюю очередь.
            </p>
          </div>
        </div>
      </section>
      {loading && <Loading />}
      {error && <ErrorState message={error} />}
      {data && (
        <div className="methodology-metrics">
          <MetricCard
            label="Общая ошибка оценки ожидания"
            value={decimal(data.waiting_mae, 2)}
            suffix="дня"
            note="На исторической проверке; ошибка отдельных групп может отличаться"
            icon={Clock3}
          />
          <MetricCard
            label="Общая ошибка прогноза потока"
            value={decimal(data.flow_mae, 2)}
            suffix="напр."
            note="На организацию в день в историческом тесте"
            icon={Activity}
          />
        </div>
      )}
      <p className="page-note">
        Данные относятся к январю–марту 2025 года. Сравнение не учитывает сложность случаев и
        мощность больниц. Модель помогает анализировать историю; решения принимает специалист.
      </p>
    </>
  )
}
