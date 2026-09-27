import { useEffect, useRef, useState } from 'react'
import { Activity, ArrowRight, Download, Info, ShieldCheck } from 'lucide-react'
import { get, post, postPdf, query, hospitalId, type Filters, type SignalFeed, type DataQuality, type Validation, type ErrorMetrics, type BriefingInput, type BriefingPreview } from './api'

const count = (value: number | null | undefined) => value == null ? '—' : new Intl.NumberFormat('ru-RU').format(value)
const metric = (value: number | null | undefined) => value == null ? '—' : new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 2 }).format(value)
const day = (value: string) => new Date(`${value.slice(0, 10)}T12:00:00`).toLocaleDateString('ru-RU')
const message = (error: unknown) => error instanceof Error ? error.message : 'Не удалось выполнить действие.'

function useData<T>(path: string) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState('')
  useEffect(() => {
    const controller = new AbortController()
    setData(null); setError('')
    get<T>(path, controller.signal).then(value => { if (!controller.signal.aborted) setData(value) }).catch(error => { if (!controller.signal.aborted) setError(message(error)) })
    return () => controller.abort()
  }, [path])
  return { data, error }
}

function Heading({ title, text }: { title: string; text: string }) {
  return <div className="page-heading"><div><div className="eyebrow">РАБОЧИЙ КАБИНЕТ</div><h1>{title}</h1><p>{text}</p></div></div>
}
function ErrorBox({ text }: { text: string }) { return text ? <div className="message message-error" role="alert"><Info size={18} />{text}</div> : null }
function Pending({ error }: { error: string }) { return error ? <ErrorBox text={error} /> : <div className="loading-state" role="status">Загружаем данные…</div> }
function Pages({ total, offset, size, change }: { total: number; offset: number; size: number; change: (offset: number) => void }) {
  return <div className="directory-pagination"><span>{total ? `${offset + 1}–${Math.min(total, offset + size)} из ${total}` : 'Нет записей'}</span><div><button disabled={offset === 0} onClick={() => change(Math.max(0, offset - size))}>Назад</button><button disabled={offset + size >= total} onClick={() => change(offset + size)}>Далее</button></div></div>
}

export function SignalsPage({ filters, hospital, openHospital, forecast, quality }: { filters: Filters; hospital: string; openHospital: (name: string) => void; forecast: (name: string) => void; quality: () => void }) {
  const [kind, setKind] = useState('all')
  const [offset, setOffset] = useState(0)
  const { data, error } = useData<SignalFeed>(`/signals${query({ ...filters, hospital, kind, offset, limit: 30 })}`)
  return <><Heading title="Сигналы и отклонения" text="Изменения активности, которые стоит проверить со специалистом." />
    <div className="workspace-note"><Info size={19} /><span>Сигнал — превышение исторического P95. Это статистическое правило, не вероятность перегрузки и не оценка занятых коек. Расчёт относится к концу отмеченного дня; время доставки событий неизвестно.</span></div>
    <div className="workspace-toolbar"><label>Тип сигнала <select value={kind} onChange={e => { setKind(e.target.value); setOffset(0) }}><option value="all">Все сигналы</option><option value="referrals">Рост направлений</option><option value="refusals">Отказы</option><option value="open_growth">Рост открытой когорты</option></select></label><button className="secondary-button" onClick={quality}>Проверить качество данных <ArrowRight size={16} /></button></div>
    {!data ? <Pending error={error} /> : <><p className="page-note">Отмечено {count(data.total)} пар «стационар × день». История: до {data.history_window} предшествующих дней, минимум {data.minimum_history}. Хотя бы одному выбранному порогу не хватает истории в {count(data.insufficient_history_days)} из {count(data.hospital_days)} пар. Период выше задаёт дни сигналов; предыдущая история сохраняется.</p>
      <div className="signal-list">{data.items.map(item => <article className="panel signal-card" key={`${item.hospital}-${item.date}`}><div className="signal-heading"><Activity size={20} /><div><span className="section-kicker">{day(item.date)}</span><h2>{item.hospital}</h2></div></div>
        <ul className="signal-reasons">{item.reasons.map(reason => <li key={reason.kind}><strong>{reason.label}: {metric(reason.value)}</strong><span>Исторический P95: {metric(reason.threshold)}. Значение выше порога.</span></li>)}</ul>
        <p className="panel-footnote">Предшествующий интервал: {day(item.reference_start)} — {day(item.reference_end)} ({item.history_days} дней). Рост открытой когорты считается по разнице соседних дней; для его порога нужны допустимые предыдущие разницы.</p>
        <div className="workspace-actions"><button className="secondary-button" onClick={() => openHospital(item.hospital)}>Открыть больницу</button><button className="primary-button" onClick={() => forecast(item.hospital)}>Прогноз потока <ArrowRight size={16} /></button></div>
      </article>)}</div>
      {!data.items.length && <section className="panel"><h2>Нет отмеченных отклонений</h2><p>Это не подтверждает отсутствие нагрузки: проверьте полноту данных и достаточность истории.</p></section>}
      <Pages total={data.total} offset={offset} size={30} change={setOffset} /></>}
    <p className="page-note">Открытая когорта восстановлена из доступных направлений и исходов. Она не равна сегодняшней очереди. Нули означают отсутствие записей в предоставленных файлах.</p>
  </>
}

const SOURCE_NAMES: Record<string, string> = { waiting: 'Ожидающие — связь с направлениями', referrals: 'Направления — основа когорты и моделей', refusals: 'Самостоятельная выгрузка отказов', treated: 'Самостоятельная выгрузка пролеченных случаев' }
const PREPARATION_NAMES: Record<string, string> = {
  waiting_exact_duplicates_removed: 'Удалено точных дублей ожидающих', referrals_exact_duplicates_removed: 'Удалено точных дублей направлений',
  referrals_conflicting_key_rows_excluded: 'Исключено строк направлений с конфликтующими ключами',
  unambiguous_matched_rows: 'Однозначно связано и включено в когорту', registration_date_mismatches: 'Несовпадения дат регистрации при соединении', referral_conflicting_keys: 'Конфликтующие ключи направлений',
}

export function QualityPage({ filters, hospital }: { filters: Filters; hospital: string }) {
  const { data, error } = useData<DataQuality>(`/quality${query({ ...filters, hospital })}`)
  const stats = data?.stats
  return <><Heading title="Качество данных" text="Что вошло в анализ, что исключено из ожидания и какие ограничения нужно проверить." />
    {!data || !stats ? <Pending error={error} /> : <><section className="panel"><span className="section-kicker">ВЫБРАННЫЙ ПЕРИОД И ФИЛЬТРЫ</span><h2>{data.hospital || 'Все доступные организации'}</h2>
      <div className="integrity-grid"><div><span>Направления</span><strong>{count(stats.referrals)}</strong></div><div><span>Допустимые ожидания</span><strong>{count(stats.eligible)}</strong></div><div><span>Исключены из оценки ожидания</span><strong>{count(stats.referrals - stats.eligible)}</strong></div></div>
      <div className="evidence-table-wrap"><table className="evidence-table"><thead><tr><th>Категория</th><th>Записи</th><th>Как интерпретировать</th></tr></thead><tbody>
        {[['Госпитализации', stats.hospitalized, 'Ожидание оценивается только для допустимых завершённых случаев 0–90 дней.'], ['Отказы', stats.refused, 'Отдельный исход; время до госпитализации неизвестно.'], ['Исход не записан', stats.unresolved, 'Это не подтверждение нахождения в сегодняшней очереди.'], ['Некорректные исходы', stats.invalid_outcome, 'Исключены из расчёта ожидания и реконструкции открытой когорты.'], ['Конфликтующие исходы', stats.conflicting, 'Требуется проверка исходной записи оператором.']].map(([label, value, text]) => <tr key={String(label)}><th>{label}</th><td>{count(Number(value))}</td><td>{text}</td></tr>)}
      </tbody></table></div></section>
      {data.sources && <section className="panel evidence-section"><span className="section-kicker">ПОДГОТОВКА ВСЕЙ ВЫГРУЗКИ · ФИЛЬТРЫ ВЫШЕ НЕ ПРИМЕНЯЮТСЯ</span><h2>Источники и соединение</h2><p>Полнота частей проверяет комплект файлов, а не полноту национального охвата или доставки событий.</p>
        <div className="evidence-table-wrap"><table className="evidence-table"><thead><tr><th>Источник</th><th>Части</th><th>Строк до очистки</th><th>Комплект</th></tr></thead><tbody>{data.sources.map(source => <tr key={source.category}><th>{SOURCE_NAMES[source.category] || source.category}</th><td>{source.file_count} / {source.expected_parts}</td><td>{count(source.rows)}</td><td>{source.complete ? 'Все заявленные части' : 'Неполный'}</td></tr>)}</tbody></table></div>
        <dl className="quality-facts">{Object.entries(data.preparation || {}).map(([key, value]) => <div key={key}><dt>{PREPARATION_NAMES[key] || key}</dt><dd>{count(value)}</dd></div>)}</dl>
        <p className="panel-footnote">Отдельные отказы и пролеченные случаи не соединены с когортой по похожим названиям и не используются как признаки моделей. Для пролеченных случаев отчётный период не установлен; дата загрузки его не заменяет.</p>
      </section>}
      <div className="workspace-note"><ShieldCheck size={19} /><span>Обезличенные агрегаты не устраняют смещение отбора: незавершённые случаи и отказы не входят в измеренное время ожидания. Лабораторные данные ЕИП пока не предоставлены.</span></div>
      <p className="page-note">Подготовка данных: {new Date(data.prepared_at).toLocaleString('ru-RU')}. Для исправления исходных данных обратитесь к оператору.</p>
    </>}
  </>
}

function ErrorTable({ rows }: { rows: (ErrorMetrics & { test_start: string; test_end: string })[] }) {
  return <div className="evidence-table-wrap"><table className="evidence-table"><thead><tr><th>Период регистрации теста</th><th>MAE</th><th>Baseline MAE</th><th>RMSE</th></tr></thead><tbody>{rows.map(row => <tr key={row.test_start}><th>{day(row.test_start)} — {day(row.test_end)}</th><td>{metric(row.mae)}</td><td>{metric(row.baseline_mae)}</td><td>{metric(row.rmse)}</td></tr>)}</tbody></table></div>
}

export function ValidationPage({ hospitalRole }: { hospitalRole: boolean }) {
  const [group, setGroup] = useState('hospital_mo')
  const [search, setSearch] = useState('')
  const [debounced, setDebounced] = useState('')
  const [offset, setOffset] = useState(0)
  useEffect(() => { const timer = setTimeout(() => { setDebounced(search); setOffset(0) }, 250); return () => clearTimeout(timer) }, [search])
  const { data, error } = useData<Validation>(`/validation${query({ group, search: debounced, offset })}`)
  return <><Heading title="Проверка по периодам" text="Результаты отдельных повторных обучений на трёх временных окнах." />
    {!data ? <Pending error={error} /> : !data.available ? <section className="panel"><p>{data.reason}</p></section> : <>
      <div className="workspace-note"><Info size={19} /><span>Общие ошибки рассчитаны на всех тестовых примерах. Фильтры аналитики их не меняют. Это отдельная проверка устойчивости, а не метрики текущего прогноза выбранной больницы.</span></div>
      {(['waiting', 'forecast'] as const).map(key => <section className="panel evidence-section" key={key}><span className="section-kicker">{key === 'waiting' ? 'ОЖИДАНИЕ · ДНИ' : 'ПОТОК · НАПРАВЛЕНИЯ / ОРГАНИЗАЦИЮ В ДЕНЬ'}</span><h2>MAE {metric(data[key].pooled.mae)} · baseline {metric(data[key].pooled.baseline_mae)}</h2><p>RMSE {metric(data[key].pooled.rmse)}; P90 абсолютной ошибки {metric(data[key].pooled.p90_absolute_error)}. P90 ошибок не является персональным интервалом прогноза.</p><ErrorTable rows={data[key].folds} />
        {key === 'waiting' && data.waiting_selection_overlap && <p className="evidence-caution">Ранние окна пересекаются с историей выбора метода ожидания. Результаты исследовательские и не являются независимым подтверждением выбранного метода.</p>}
        {key === 'forecast' && <><p>Сезонный baseline «тот же день прошлой недели»: MAE {metric(data.forecast.pooled.seasonal_baseline_mae)}.</p><div className="evidence-table-wrap"><table className="evidence-table"><thead><tr><th>Горизонт</th><th>MAE</th><th>Среднее 7 дней</th><th>Прошлая неделя</th></tr></thead><tbody>{data.forecast.by_horizon.map(row => <tr key={row.horizon}><th>День {row.horizon}</th><td>{metric(row.mae)}</td><td>{metric(row.baseline_mae)}</td><td>{metric(row.seasonal_baseline_mae)}</td></tr>)}</tbody></table></div></>}
      </section>)}
      <section className="panel evidence-section"><span className="section-kicker">ОШИБКА ОЖИДАНИЯ ПО ГРУППАМ</span><h2>{hospitalRole ? 'Ваша организация' : 'Где качество отличается'}</h2>
        {!hospitalRole && <div className="workspace-toolbar"><label>Группировка <select value={group} onChange={e => { setGroup(e.target.value); setOffset(0); setSearch(''); setDebounced('') }}><option value="hospital_mo">Стационары</option><option value="region_origin_code">Регионы происхождения</option><option value="bed_profile">Профили</option></select></label><label>Поиск <input value={search} onChange={e => setSearch(e.target.value)} maxLength={100} /></label></div>}
        {data.groups.items.length ? <div className="evidence-table-wrap"><table className="evidence-table"><thead><tr><th>Группа</th><th>Тестовых случаев</th><th>MAE</th><th>Baseline MAE</th></tr></thead><tbody>{data.groups.items.map(row => <tr key={row.name}><th>{row.name}</th><td>{count(row.observations)}</td><td>{metric(row.mae)}</td><td>{metric(row.baseline_mae)}</td></tr>)}</tbody></table></div> : <p>Для этой выборки нет опубликованных групп с достаточным числом тестовых случаев.</p>}
        <Pages total={data.groups.total} offset={offset} size={30} change={setOffset} /><p className="panel-footnote">Минимум {data.minimum_group_size} тестовых случаев на группу. Различия ошибок не являются рейтингом качества больниц.</p>
      </section>
      <section className="panel evidence-section"><h2>Как устроена проверка</h2><p>Ожидание: в обучение входят только исходы, известные до начала теста. Поток: все семь дней прогнозируются из одной даты, без фактов тестовой недели в признаках. История обучения расширяется; параметры фиксированы.</p><p>Всего доступно 90 исторических дней регистрации. Нужны новые периоды и проверка в организации. Время доставки событий и поздние исправления неизвестны.</p><p className="panel-footnote">Расчёт: {new Date(data.created_at).toLocaleString('ru-RU')}.</p></section>
    </>}
  </>
}

export function BriefingPanel({ filters, hospitals, minimum = 30 }: { filters: Filters; hospitals: string[]; minimum?: number }) {
  const [question, setQuestion] = useState<BriefingInput['question']>('flow')
  const request: BriefingInput = { ...filters, hospital_ids: hospitals.map(hospitalId), minimum, question }
  return <section className="panel evidence-section"><span className="section-kicker">ПРОВЕРКА СПЕЦИАЛИСТОМ</span><h2>Сводка для обсуждения</h2><p>Период регистрации: {day(filters.start)} — {day(filters.end)}. Профиль: {filters.profile || 'все'}. Регион происхождения: {filters.region || 'все'}.</p>
    <label className="briefing-question">Вопрос для проверки <select value={question} onChange={e => setQuestion(e.target.value as BriefingInput['question'])}><option value="flow">Поток направлений и доступная мощность</option><option value="waiting">Различия наблюдаемого ожидания</option><option value="refusals">Причины отказов и полнота регистрации</option></select></label>
    {hospitals.length ? <BriefingForm key={JSON.stringify(request)} request={request} /> : <p>Выберите хотя бы один стационар.</p>}
    <p className="panel-footnote">PDF содержит агрегаты и общие метрики моделей. Подтверждение означает просмотр аналитиком, а не формальное согласование решения или назначение лечения.</p>
  </section>
}

export function BriefingReview({ preview, confirmed, change }: { preview: BriefingPreview; confirmed: boolean; change: (value: boolean) => void }) {
  return <div className="briefing-preview"><h3>Проверьте содержимое PDF</h3><p>{preview.snapshot.review_question}</p><div className="evidence-table-wrap"><table className="evidence-table"><thead><tr><th>Стационар</th><th>Направления</th><th>Медиана, дни</th><th>P90, дни</th><th>Отказы, %</th></tr></thead><tbody>{preview.snapshot.aggregates.map(row => <tr key={row.organization_or_region}><th>{row.organization_or_region}</th><td>{count(row.referrals)}</td><td>{metric(row.median_wait_days)}</td><td>{metric(row.p90_wait_days)}</td><td>{metric(row.refusal_share_pct)}</td></tr>)}</tbody></table></div>
    <p>Минимум группы и статистик: {preview.snapshot.minimum_group_size}. Прочерк означает недостаточно наблюдений. P90 — описательный квантиль ожидания, не интервал прогноза.</p>
    {(['waiting', 'forecast'] as const).map(key => <p key={key}>{key === 'waiting' ? 'Ожидание, дни' : 'Поток, направления / организацию в день'}: {preview.metrics[key] ? <>MAE {metric(preview.metrics[key].mae)}, baseline {metric(preview.metrics[key].baseline_mae)}. Версия {preview.metrics[key].model_version}; тест {preview.metrics[key].period}.</> : 'Актуальные метрики недоступны.'}</p>)}
    <p>Ошибки относятся ко всему тесту. Сравнение не учитывает тяжесть случаев и мощность. Прогноз потока не измеряет занятость коек. Полноту данных и доступные ресурсы нужно уточнить у специалиста.</p>
    <label className="review-check"><input type="checkbox" checked={confirmed} onChange={e => change(e.target.checked)} />Я проверил период, выбранные стационары, показатели и ограничения.</label>
  </div>
}

function BriefingForm({ request }: { request: BriefingInput }) {
  const [preview, setPreview] = useState<BriefingPreview | null>(null)
  const [confirmed, setConfirmed] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const pending = useRef<AbortController | null>(null)
  useEffect(() => () => pending.current?.abort(), [])
  const run = async (download: boolean) => {
    pending.current?.abort(); const controller = new AbortController(); pending.current = controller
    setBusy(true); setError('')
    try {
      if (download && preview && confirmed) {
        const blob = await postPdf('/briefings/pdf', { ...request, reviewed: true, review_token: preview.review_token }, controller.signal)
        if (controller.signal.aborted) return
        const url = URL.createObjectURL(blob); const link = document.createElement('a')
        link.href = url; link.download = 'medflow_briefing.pdf'; document.body.appendChild(link); link.click(); link.remove()
        setTimeout(() => URL.revokeObjectURL(url), 1000)
      } else {
        setPreview(null); setConfirmed(false)
        const result = await post<BriefingPreview>('/briefings/preview', request, controller.signal)
        if (!controller.signal.aborted) setPreview(result)
      }
    } catch (reason) { if (!controller.signal.aborted) { setError(message(reason)); setConfirmed(false); setPreview(null) } }
    finally { if (!controller.signal.aborted) setBusy(false) }
  }
  return <><div className="workspace-actions"><button className="secondary-button" disabled={busy} onClick={() => { void run(false) }}>{busy ? 'Подготовка…' : preview ? 'Обновить просмотр' : 'Подготовить просмотр'}</button></div><ErrorBox text={error} />
    {preview && <BriefingReview preview={preview} confirmed={confirmed} change={setConfirmed} />}
    <button className="primary-button" disabled={busy || !preview || !confirmed} onClick={() => { void run(true) }}><Download size={17} /> Скачать PDF-сводку</button>
  </>
}
