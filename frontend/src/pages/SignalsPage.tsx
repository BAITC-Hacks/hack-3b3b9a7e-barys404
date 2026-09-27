import { Activity, ArrowRight, Info } from 'lucide-react'
import { useState } from 'react'
import { query } from '../api/client'
import { type Filters, type SignalFeed } from '../api/types'
import { Pagination } from '../components/ui/Pagination'
import { Pending } from '../components/ui/Pending'
import { WorkspaceHeading } from '../components/ui/WorkspaceHeading'
import { useData } from '../hooks/useData'
import { count, day, metric } from '../lib/evidenceFormat'

export function SignalsPage({
  filters,
  hospital,
  openHospital,
  forecast,
  quality,
}: {
  filters: Filters
  hospital: string
  openHospital: (name: string) => void
  forecast: (name: string) => void
  quality: () => void
}) {
  const [kind, setKind] = useState('all')
  const [offset, setOffset] = useState(0)
  const { data, error } = useData<SignalFeed>(
    `/signals${query({ ...filters, hospital, kind, offset, limit: 30 })}`,
  )
  return (
    <>
      <WorkspaceHeading
        title="Сигналы и отклонения"
        text="Изменения активности, которые стоит проверить со специалистом."
      />
      <div className="workspace-note">
        <Info size={19} />
        <span>
          Сигнал — превышение исторического P95. Это статистическое правило, не вероятность
          перегрузки и не оценка занятых коек. Расчёт относится к концу отмеченного дня; время
          доставки событий неизвестно.
        </span>
      </div>
      <div className="workspace-toolbar">
        <label>
          Тип сигнала{' '}
          <select
            value={kind}
            onChange={(e) => {
              setKind(e.target.value)
              setOffset(0)
            }}
          >
            <option value="all">Все сигналы</option>
            <option value="referrals">Рост направлений</option>
            <option value="refusals">Отказы</option>
            <option value="open_growth">Рост открытой когорты</option>
          </select>
        </label>
        <button className="secondary-button" onClick={quality}>
          Проверить качество данных <ArrowRight size={16} />
        </button>
      </div>
      {!data ? (
        <Pending error={error} />
      ) : (
        <>
          <p className="page-note">
            Отмечено {count(data.total)} пар «стационар × день». История: до {data.history_window}{' '}
            предшествующих дней, минимум {data.minimum_history}. Хотя бы одному выбранному порогу не
            хватает истории в {count(data.insufficient_history_days)} из {count(data.hospital_days)}{' '}
            пар. Период выше задаёт дни сигналов; предыдущая история сохраняется.
          </p>
          <div className="signal-list">
            {data.items.map((item) => (
              <article className="panel signal-card" key={`${item.hospital}-${item.date}`}>
                <div className="signal-heading">
                  <Activity size={20} />
                  <div>
                    <span className="section-kicker">{day(item.date)}</span>
                    <h2>{item.hospital}</h2>
                  </div>
                </div>
                <ul className="signal-reasons">
                  {item.reasons.map((reason) => (
                    <li key={reason.kind}>
                      <strong>
                        {reason.label}: {metric(reason.value)}
                      </strong>
                      <span>
                        Исторический P95: {metric(reason.threshold)}. Значение выше порога.
                      </span>
                    </li>
                  ))}
                </ul>
                <p className="panel-footnote">
                  Предшествующий интервал: {day(item.reference_start)} — {day(item.reference_end)} (
                  {item.history_days} дней). Рост открытой когорты считается по разнице соседних
                  дней; для его порога нужны допустимые предыдущие разницы.
                </p>
                <div className="workspace-actions">
                  <button className="secondary-button" onClick={() => openHospital(item.hospital)}>
                    Открыть больницу
                  </button>
                  <button className="primary-button" onClick={() => forecast(item.hospital)}>
                    Прогноз потока <ArrowRight size={16} />
                  </button>
                </div>
              </article>
            ))}
          </div>
          {!data.items.length && (
            <section className="panel">
              <h2>Нет отмеченных отклонений</h2>
              <p>
                Это не подтверждает отсутствие нагрузки: проверьте полноту данных и достаточность
                истории.
              </p>
            </section>
          )}
          <Pagination total={data.total} offset={offset} size={30} change={setOffset} />
        </>
      )}
      <p className="page-note">
        Открытая когорта восстановлена из доступных направлений и исходов. Она не равна сегодняшней
        очереди. Нули означают отсутствие записей в предоставленных файлах.
      </p>
    </>
  )
}
