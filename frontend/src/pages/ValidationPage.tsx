import { Info } from 'lucide-react'
import { useEffect, useState } from 'react'
import { query } from '../api/client'
import { type Validation } from '../api/types'
import { ErrorTable } from '../components/evidence/ErrorTable'
import { Pagination } from '../components/ui/Pagination'
import { Pending } from '../components/ui/Pending'
import { WorkspaceHeading } from '../components/ui/WorkspaceHeading'
import { useData } from '../hooks/useData'
import { count, metric } from '../lib/evidenceFormat'

export function ValidationPage({ hospitalRole }: { hospitalRole: boolean }) {
  const [group, setGroup] = useState('hospital_mo')
  const [search, setSearch] = useState('')
  const [debounced, setDebounced] = useState('')
  const [offset, setOffset] = useState(0)
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebounced(search)
      setOffset(0)
    }, 250)
    return () => clearTimeout(timer)
  }, [search])
  const { data, error } = useData<Validation>(
    `/validation${query({ group, search: debounced, offset })}`,
  )
  return (
    <>
      <WorkspaceHeading
        title="Проверка по периодам"
        text="Результаты отдельных повторных обучений на трёх временных окнах."
      />
      {!data ? (
        <Pending error={error} />
      ) : !data.available ? (
        <section className="panel">
          <p>{data.reason}</p>
        </section>
      ) : (
        <>
          <div className="workspace-note">
            <Info size={19} />
            <span>
              Общие ошибки рассчитаны на всех тестовых примерах. Фильтры аналитики их не меняют. Это
              отдельная проверка устойчивости, а не метрики текущего прогноза выбранной больницы.
            </span>
          </div>
          {(['waiting', 'forecast'] as const).map((key) => (
            <section className="panel evidence-section" key={key}>
              <span className="section-kicker">
                {key === 'waiting' ? 'ОЖИДАНИЕ · ДНИ' : 'ПОТОК · НАПРАВЛЕНИЯ / ОРГАНИЗАЦИЮ В ДЕНЬ'}
              </span>
              <h2>
                MAE {metric(data[key].pooled.mae)} · baseline{' '}
                {metric(data[key].pooled.baseline_mae)}
              </h2>
              <p>
                RMSE {metric(data[key].pooled.rmse)}; P90 абсолютной ошибки{' '}
                {metric(data[key].pooled.p90_absolute_error)}. P90 ошибок не является персональным
                интервалом прогноза.
              </p>
              <ErrorTable rows={data[key].folds} />
              {key === 'waiting' && data.waiting_selection_overlap && (
                <p className="evidence-caution">
                  Ранние окна пересекаются с историей выбора метода ожидания. Результаты
                  исследовательские и не являются независимым подтверждением выбранного метода.
                </p>
              )}
              {key === 'forecast' && (
                <>
                  <p>
                    Сезонный baseline «тот же день прошлой недели»: MAE{' '}
                    {metric(data.forecast.pooled.seasonal_baseline_mae)}.
                  </p>
                  <div className="evidence-table-wrap">
                    <table className="evidence-table">
                      <thead>
                        <tr>
                          <th>Горизонт</th>
                          <th>MAE</th>
                          <th>Среднее 7 дней</th>
                          <th>Прошлая неделя</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data.forecast.by_horizon.map((row) => (
                          <tr key={row.horizon}>
                            <th>День {row.horizon}</th>
                            <td>{metric(row.mae)}</td>
                            <td>{metric(row.baseline_mae)}</td>
                            <td>{metric(row.seasonal_baseline_mae)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              )}
            </section>
          ))}
          <section className="panel evidence-section">
            <span className="section-kicker">ОШИБКА ОЖИДАНИЯ ПО ГРУППАМ</span>
            <h2>{hospitalRole ? 'Ваша организация' : 'Где качество отличается'}</h2>
            {!hospitalRole && (
              <div className="workspace-toolbar">
                <label>
                  Группировка{' '}
                  <select
                    value={group}
                    onChange={(e) => {
                      setGroup(e.target.value)
                      setOffset(0)
                      setSearch('')
                      setDebounced('')
                    }}
                  >
                    <option value="hospital_mo">Стационары</option>
                    <option value="region_origin_code">Регионы происхождения</option>
                    <option value="bed_profile">Профили</option>
                  </select>
                </label>
                <label>
                  Поиск{' '}
                  <input
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    maxLength={100}
                  />
                </label>
              </div>
            )}
            {data.groups.items.length ? (
              <div className="evidence-table-wrap">
                <table className="evidence-table">
                  <thead>
                    <tr>
                      <th>Группа</th>
                      <th>Тестовых случаев</th>
                      <th>MAE</th>
                      <th>Baseline MAE</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.groups.items.map((row) => (
                      <tr key={row.name}>
                        <th>{row.name}</th>
                        <td>{count(row.observations)}</td>
                        <td>{metric(row.mae)}</td>
                        <td>{metric(row.baseline_mae)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p>
                Для этой выборки нет опубликованных групп с достаточным числом тестовых случаев.
              </p>
            )}
            <Pagination total={data.groups.total} offset={offset} size={30} change={setOffset} />
            <p className="panel-footnote">
              Минимум {data.minimum_group_size} тестовых случаев на группу. Различия ошибок не
              являются рейтингом качества больниц.
            </p>
          </section>
          <section className="panel evidence-section">
            <h2>Как устроена проверка</h2>
            <p>
              Ожидание: в обучение входят только исходы, известные до начала теста. Поток: все семь
              дней прогнозируются из одной даты, без фактов тестовой недели в признаках. История
              обучения расширяется; параметры фиксированы.
            </p>
            <p>
              Всего доступно 90 исторических дней регистрации. Нужны новые периоды и проверка в
              организации. Время доставки событий и поздние исправления неизвестны.
            </p>
            <p className="panel-footnote">
              Расчёт: {new Date(data.created_at).toLocaleString('ru-RU')}.
            </p>
          </section>
        </>
      )}
    </>
  )
}
