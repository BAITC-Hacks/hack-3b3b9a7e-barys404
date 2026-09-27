import { type Methodology } from '../api/types'
import { ModelQuality } from '../components/evidence/ModelQuality'
import { ErrorState } from '../components/ui/ErrorState'
import { Loading } from '../components/ui/Loading'
import { PageHeading } from '../components/ui/PageHeading'
import { useRemote } from '../hooks/useRemote'

export function DataPage() {
  const { data, loading, error } = useRemote<Methodology>('/methodology')
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
          <ModelQuality
            name="Оценка ожидания"
            unit="дня"
            baseline="Общая медиана обучающей выборки"
            evidence={data.waiting}
          />
          <ModelQuality
            name="Прогноз потока"
            unit="напр. / организацию в день"
            baseline="Среднее предыдущих 7 дней"
            evidence={data.flow}
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
