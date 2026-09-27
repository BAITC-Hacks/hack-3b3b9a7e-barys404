import { ShieldCheck } from 'lucide-react'
import { query } from '../api/client'
import { type DataQuality, type Filters } from '../api/types'
import { Pending } from '../components/ui/Pending'
import { WorkspaceHeading } from '../components/ui/WorkspaceHeading'
import { useData } from '../hooks/useData'
import { count } from '../lib/evidenceFormat'
import { PREPARATION_NAMES, SOURCE_NAMES } from './qualityLabels'

export function QualityPage({ filters, hospital }: { filters: Filters; hospital: string }) {
  const { data, error } = useData<DataQuality>(`/quality${query({ ...filters, hospital })}`)
  const stats = data?.stats
  return (
    <>
      <WorkspaceHeading
        title="Качество данных"
        text="Что вошло в анализ, что исключено из ожидания и какие ограничения нужно проверить."
      />
      {!data || !stats ? (
        <Pending error={error} />
      ) : (
        <>
          <section className="panel">
            <span className="section-kicker">ВЫБРАННЫЙ ПЕРИОД И ФИЛЬТРЫ</span>
            <h2>{data.hospital || 'Все доступные организации'}</h2>
            <div className="integrity-grid">
              <div>
                <span>Направления</span>
                <strong>{count(stats.referrals)}</strong>
              </div>
              <div>
                <span>Допустимые ожидания</span>
                <strong>{count(stats.eligible)}</strong>
              </div>
              <div>
                <span>Исключены из оценки ожидания</span>
                <strong>{count(stats.referrals - stats.eligible)}</strong>
              </div>
            </div>
            <div className="evidence-table-wrap">
              <table className="evidence-table">
                <thead>
                  <tr>
                    <th>Категория</th>
                    <th>Записи</th>
                    <th>Как интерпретировать</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    [
                      'Госпитализации',
                      stats.hospitalized,
                      'Ожидание оценивается только для допустимых завершённых случаев 0–90 дней.',
                    ],
                    [
                      'Отказы',
                      stats.refused,
                      'Отдельный исход; время до госпитализации неизвестно.',
                    ],
                    [
                      'Исход не записан',
                      stats.unresolved,
                      'Это не подтверждение нахождения в сегодняшней очереди.',
                    ],
                    [
                      'Некорректные исходы',
                      stats.invalid_outcome,
                      'Исключены из расчёта ожидания и реконструкции открытой когорты.',
                    ],
                    [
                      'Конфликтующие исходы',
                      stats.conflicting,
                      'Требуется проверка исходной записи оператором.',
                    ],
                  ].map(([label, value, text]) => (
                    <tr key={String(label)}>
                      <th>{label}</th>
                      <td>{count(Number(value))}</td>
                      <td>{text}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
          {data.sources && (
            <section className="panel evidence-section">
              <span className="section-kicker">
                ПОДГОТОВКА ВСЕЙ ВЫГРУЗКИ · ФИЛЬТРЫ ВЫШЕ НЕ ПРИМЕНЯЮТСЯ
              </span>
              <h2>Источники и соединение</h2>
              <p>
                Полнота частей проверяет комплект файлов, а не полноту национального охвата или
                доставки событий.
              </p>
              <div className="evidence-table-wrap">
                <table className="evidence-table">
                  <thead>
                    <tr>
                      <th>Источник</th>
                      <th>Части</th>
                      <th>Строк до очистки</th>
                      <th>Комплект</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.sources.map((source) => (
                      <tr key={source.category}>
                        <th>{SOURCE_NAMES[source.category] || source.category}</th>
                        <td>
                          {source.file_count} / {source.expected_parts}
                        </td>
                        <td>{count(source.rows)}</td>
                        <td>{source.complete ? 'Все заявленные части' : 'Неполный'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <dl className="quality-facts">
                {Object.entries(data.preparation || {}).map(([key, value]) => (
                  <div key={key}>
                    <dt>{PREPARATION_NAMES[key] || key}</dt>
                    <dd>{count(value)}</dd>
                  </div>
                ))}
              </dl>
              <p className="panel-footnote">
                Отдельные отказы и пролеченные случаи не соединены с когортой по похожим названиям и
                не используются как признаки моделей. Для пролеченных случаев отчётный период не
                установлен; дата загрузки его не заменяет.
              </p>
            </section>
          )}
          <div className="workspace-note">
            <ShieldCheck size={19} />
            <span>
              Обезличенные агрегаты не устраняют смещение отбора: незавершённые случаи и отказы не
              входят в измеренное время ожидания. Лабораторные данные ЕИП пока не предоставлены.
            </span>
          </div>
          <p className="page-note">
            Подготовка данных: {new Date(data.prepared_at).toLocaleString('ru-RU')}. Для исправления
            исходных данных обратитесь к оператору.
          </p>
        </>
      )}
    </>
  )
}
