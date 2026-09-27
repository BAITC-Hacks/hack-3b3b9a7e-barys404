import { AuthGate, UserMenu } from './Auth'
import { SignalsPage, QualityPage, ValidationPage, BriefingPanel } from './WorkspacePages'
import { useEffect, useMemo, useRef, useState } from 'react'
import {
  Activity, ArrowLeft, ArrowRight, ArrowUpRight, Building2, CalendarDays,
  Check, ChevronDown, ChevronRight, Clock3, Database, GitCompareArrows,
  Info, LayoutDashboard, Menu, Search, Sparkles, TrendingUp, X, ShieldCheck, ChartNoAxesCombined,
} from 'lucide-react'
import {
  get, post, query, type Bootstrap, type Filters, type Forecast,
  type HospitalDetail, type MetricRow, type Overview, type User, hospitalId, hospitalName,
  type WaitOptions, type WaitResult, type WeeklyPoint, type ModelEvidence, type Methodology, type EvaluationPeriod,
} from './api'

type View = 'overview' | 'hospitals' | 'hospital' | 'compare' | 'forecasts' | 'signals' | 'quality' | 'validation' | 'data'
type Mode = 'government' | 'hospital'
type NavItem = { id: View; label: string; icon: typeof LayoutDashboard }

const NAV: NavItem[] = [
  { id: 'overview', label: 'Обзор', icon: LayoutDashboard },
  { id: 'hospitals', label: 'Стационары', icon: Building2 },
  { id: 'compare', label: 'Сравнение', icon: GitCompareArrows },
  { id: 'forecasts', label: 'Прогнозы', icon: Sparkles },
  { id: 'signals', label: 'Сигналы и отклонения', icon: Activity },
  { id: 'quality', label: 'Качество данных', icon: ShieldCheck },
  { id: 'validation', label: 'Проверка моделей', icon: ChartNoAxesCombined },
  { id: 'data', label: 'Как читать показатели', icon: Database },
]

const number = (value: number | null | undefined) => value == null ? '—' : new Intl.NumberFormat('ru-RU').format(Math.round(value))
const decimal = (value: number | null | undefined, digits = 1) => value == null ? '—' : value > 0 && digits === 1 && value < 0.05 ? '<0,1' : new Intl.NumberFormat('ru-RU', { maximumFractionDigits: digits, minimumFractionDigits: digits }).format(value)
const organizations = (count: number) => `${number(count)} ${count % 10 === 1 && count % 100 !== 11 ? 'организация' : count % 10 >= 2 && count % 10 <= 4 && (count % 100 < 12 || count % 100 > 14) ? 'организации' : 'организаций'}`
const day = (value: string | undefined) => value ? new Date(`${value.slice(0, 10)}T12:00:00`).toLocaleDateString('ru-RU', { day: '2-digit', month: 'short', year: 'numeric' }) : '—'
const shortDay = (value: string | undefined) => value ? new Date(`${value.slice(0, 10)}T12:00:00`).toLocaleDateString('ru-RU', { day: '2-digit', month: 'short' }) : '—'

function useRemote<T>(path: string | null) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(Boolean(path))
  const [error, setError] = useState('')
  useEffect(() => {
    if (!path) { setData(null); setLoading(false); return }
    const controller = new AbortController()
    setData(null)
    setLoading(true)
    setError('')
    get<T>(path, controller.signal).then(value => { if (!controller.signal.aborted) setData(value) }).catch(error => {
      if (error.name !== 'AbortError') setError(error.message)
    }).finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [path])
  return { data, loading, error }
}

function currentRoute(): { view: View; hospital?: string } {
  const hash = window.location.hash.slice(1)
  if (hash.startsWith('hospital/')) {
    try { return { view: 'hospital', hospital: decodeURIComponent(hash.slice(9)) } }
    catch { return { view: 'overview' } }
  }
  const known = NAV.some(item => item.id === hash)
  return { view: known ? hash as View : 'overview' }
}

function Loading({ label = 'Загружаем данные' }: { label?: string }) {
  return <div className="loading-state"><div className="spinner" /><span>{label}…</span></div>
}

function ErrorState({ message }: { message: string }) {
  return <div className="message message-error"><Info size={18} /><span>{message}</span></div>
}

function EmptyState({ title, text }: { title: string; text: string }) {
  return <div className="empty-state"><Search size={24} /><h3>{title}</h3><p>{text}</p></div>
}

function PageHeading({ eyebrow, title, description, action }: { eyebrow: string; title: string; description: string; action?: React.ReactNode }) {
  return <div className="page-heading"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{description}</p></div>{action}</div>
}

function MetricCard({ label, value, suffix, note, tone = 'plain', icon: Icon }: { label: string; value: string; suffix?: string; note?: string; tone?: 'plain' | 'accent'; icon: typeof Activity }) {
  return <div className={`metric-card ${tone === 'accent' ? 'metric-accent' : ''}`}>
    <div className="metric-top"><span>{label}</span><Icon size={18} strokeWidth={1.7} /></div>
    <div className="metric-value">{value}<small>{suffix}</small></div>
    {note && <div className="metric-note">{note}</div>}
  </div>
}

function TrendChart({ rows, forecastFrom }: { rows: { date: string; value: number }[]; forecastFrom?: number }) {
  const [active, setActive] = useState<number | null>(null)
  const chartRef = useRef<HTMLDivElement>(null)
  const [width, setWidth] = useState(760)
  const hasRows = rows.length > 0
  useEffect(() => {
    if (!chartRef.current) return
    // Match the drawing to its container so labels stay readable on narrow cards.
    const observer = new ResizeObserver(([entry]) => setWidth(Math.max(1, Math.round(entry.contentRect.width))))
    observer.observe(chartRef.current)
    return () => observer.disconnect()
  }, [hasRows])
  if (!rows.length) return <EmptyState title="Нет данных для графика" text="Попробуйте изменить период или фильтры." />
  const height = 280, left = 68, right = 16, top = 24, bottom = 51
  const plotWidth = width - left - right, plotHeight = height - top - bottom
  const max = Math.max(1, ...rows.map(row => row.value))
  const topValue = Math.ceil(max / 5) * 5 || 5
  const x = (index: number) => left + (rows.length === 1 ? plotWidth / 2 : index / (rows.length - 1) * plotWidth)
  const y = (value: number) => top + plotHeight - value / topValue * plotHeight
  const points = rows.map((row, index) => `${x(index)},${y(row.value)}`)
  const observed = forecastFrom == null ? points : points.slice(0, forecastFrom)
  const projected = forecastFrom == null ? [] : points.slice(Math.max(0, forecastFrom - 1))
  const area = `M ${x(0)} ${top + plotHeight} L ${points.join(' L ')} L ${x(rows.length - 1)} ${top + plotHeight} Z`
  const labels = [...new Set([0, Math.floor((rows.length - 1) / 2), rows.length - 1])]
  const current = active == null ? null : rows[active]
  const tipX = active == null ? 0 : Math.min(width - 186, Math.max(6, x(active) - 90))
  return <div className="chart-wrap" ref={chartRef}>
    <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="График направлений по датам" onMouseLeave={() => setActive(null)}>
      <defs><linearGradient id="chartArea" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor="#24a99a" stopOpacity=".2" /><stop offset="100%" stopColor="#24a99a" stopOpacity="0" /></linearGradient></defs>
      {[0, .5, 1].map((fraction, index) => <g key={index}><line x1={left} x2={width - right} y1={y(topValue * fraction)} y2={y(topValue * fraction)} className="chart-grid" /><text x={left - 10} y={y(topValue * fraction) + 4} textAnchor="end" className="chart-label">{number(topValue * fraction)}</text></g>)}
      {forecastFrom != null && <rect x={x(Math.max(0, forecastFrom - 1))} y={top} width={width - right - x(Math.max(0, forecastFrom - 1))} height={plotHeight} fill="#e8f3f1" opacity=".8" />}
      <path d={area} fill="url(#chartArea)" opacity={forecastFrom == null ? 1 : .5} />
      <polyline points={observed.join(' ')} fill="none" stroke="#147c78" strokeWidth="3.3" strokeLinecap="round" strokeLinejoin="round" />
      {rows.length === 1 && <circle cx={x(0)} cy={y(rows[0].value)} r="5" fill="#147c78" />}
      {projected.length > 1 && <polyline points={projected.join(' ')} fill="none" stroke="#39a9a0" strokeWidth="3.3" strokeDasharray="7 6" strokeLinecap="round" strokeLinejoin="round" />}
      {labels.map(index => <text key={index} x={x(index)} y={height - 14} textAnchor={index === 0 ? 'start' : index === rows.length - 1 ? 'end' : 'middle'} className="chart-label">{shortDay(rows[index].date)}</text>)}
      {rows.map((row, index) => <circle key={`${row.date}-${index}`} cx={x(index)} cy={y(row.value)} r="12" fill="transparent" onMouseEnter={() => setActive(index)} onFocus={() => setActive(index)} tabIndex={0} aria-label={`${day(row.date)}: ${decimal(row.value)} направлений`} />)}
      {active != null && current && <g className="chart-tip"><line x1={x(active)} x2={x(active)} y1={top} y2={top + plotHeight} stroke="#71bcb4" strokeDasharray="4 5" /><circle cx={x(active)} cy={y(current.value)} r="5" fill="#147c78" stroke="white" strokeWidth="2" /><rect x={tipX} y="2" width="180" height="61" rx="10" fill="#143d43" /><text x={tipX + 11} y="25" fill="#bed8d7" fontSize="14">{day(current.date)}</text><text x={tipX + 11} y="49" fill="white" fontSize="16" fontWeight="700">{decimal(current.value)} направл.</text></g>}
    </svg>
  </div>
}

function StatusPill({ good, children }: { good: boolean; children: React.ReactNode }) {
  return <span className={`status-pill ${good ? 'status-good' : 'status-muted'}`}><span className="status-dot" />{children}</span>
}

export function WeeklyTrend({ rows }: { rows: WeeklyPoint[] }) {
  const full = rows.filter(row => !row.partial_week)
  const partial = rows.filter(row => row.partial_week)
  return <>
    {full.length ? <TrendChart rows={full.map(row => ({ date: row.week, value: row.referrals }))} />
      : <EmptyState title="Нет полных календарных недель" text="Выберите более длинный период. Доступные неполные интервалы показаны ниже." />}
    {partial.length > 0 && <div className="partial-weeks" role="note"><strong>Неполные недели — отдельно от графика</strong><p>Их объёмы нельзя напрямую сравнивать с полными неделями.</p>
      {partial.map(row => <div key={row.week}><span>{day(row.period_start)} — {day(row.period_end)} <small>({row.days_in_period} из 7 дней)</small></span><b>{number(row.referrals)} направл.</b></div>)}
    </div>}
    <p className="panel-footnote">На графике — полные календарные недели выбранного интервала. Ноль означает отсутствие записей в выгрузке; полнота передачи данных не подтверждена.</p>
  </>
}

function EvaluationCaption({ version, period }: { version: string | null; period: Partial<EvaluationPeriod> }) {
  return <p className="evaluation-caption">Версия: {version || 'не указана'}<br />Проверка по регистрации: {day(period.start)} — {day(period.end)}</p>
}

export function ModelQuality({ name, unit, baseline, evidence }: { name: string; unit: string; baseline: string; evidence: ModelEvidence }) {
  const available = evidence.status.available && evidence.metrics !== null
  return <section className="panel quality-callout"><span className="section-kicker">{name}</span><StatusPill good={available}>{available ? 'Метрики актуальны' : 'Модель недоступна'}</StatusPill>
    {available && evidence.metrics ? <><h2>{decimal(evidence.metrics.mae, 2)} <small>{unit}</small></h2><p>MAE — средняя абсолютная ошибка на исторической проверке. Ошибка отдельных групп может отличаться.</p><div className="quality-divider" /><p>{baseline}: <strong>{decimal(evidence.metrics.baseline_mae, 2)} {unit}</strong></p><p>RMSE: {decimal(evidence.metrics.rmse, 2)} {unit}</p><EvaluationCaption version={evidence.model_version} period={evidence.test_period} /></>
      : <><h2>Нет актуальной оценки качества</h2><p>Артефакты отсутствуют, устарели или не прошли проверку. Обратитесь к оператору для обновления данных и модели.</p>{evidence.model_version && <p className="evaluation-caption">Сохранённая версия: {evidence.model_version}. Её метрики скрыты до подтверждения актуальности.</p>}</>}
  </section>
}

export function OutcomeBreakdown({ stats }: { stats: Overview['stats'] }) {
  const categories = [
    ['Госпитализации', stats.hospitalized, 'teal'],
    ['Отказы', stats.refused, 'coral'],
    ['Исход не записан', stats.unresolved, 'gray'],
    ['Некорректные / конфликтующие', stats.invalid_outcome + stats.conflicting, 'amber'],
  ] as const
  return <section className="panel outcome-panel"><div className="panel-heading"><div><span className="section-kicker">ИСХОДЫ И КАЧЕСТВО ДАННЫХ</span><h2>Что произошло с направлениями</h2></div></div><div className="outcome-stack">
    {categories.map(([label, value, color]) => <div className="outcome-row" key={label}><span>{label}</span><div className="outcome-track"><i className={`outcome-fill ${color}`} style={{ width: `${value / Math.max(1, stats.referrals) * 100}%` }} /></div><strong>{number(value)}</strong></div>)}
    </div><p className="panel-footnote">Все категории входят в {number(stats.referrals)} направлений. Некорректных исходов: {number(stats.invalid_outcome)}, конфликтующих: {number(stats.conflicting)}. Они исключены из оценки ожидания. Отсутствие исхода не означает, что человек ожидает сейчас.</p>
  </section>
}

function HospitalChooser({ hospital, hospitals, choose }: { hospital: string; hospitals: string[]; choose: (hospital: string) => void }) {
  const [open, setOpen] = useState(false)
  const [search, setSearch] = useState('')
  const matches = useMemo(() => {
    const term = search.trim().toLocaleLowerCase('ru-RU')
    return term ? hospitals.filter(name => name.toLocaleLowerCase('ru-RU').includes(term)).slice(0, 50)
      : [hospital, ...hospitals.filter(name => name !== hospital).slice(0, 7)]
  }, [search, hospitals, hospital])
  return <div className="hospital-chooser"><button className="chooser-trigger" onClick={() => { setOpen(!open); setSearch('') }} aria-expanded={open} aria-label="Выбрать стационар"><Building2 size={16} /><span>{hospital}</span><ChevronDown size={15} /></button>
    {open && <div className="chooser-popover"><div className="chooser-search"><Search size={15} /><input autoFocus placeholder="Найти стационар" aria-label="Найти стационар" value={search} onChange={event => setSearch(event.target.value)} onKeyDown={event => { if (event.key === 'Escape') setOpen(false); if (event.key === 'Enter' && matches[0]) { choose(matches[0]); setOpen(false) } }} /></div><div className="chooser-list">{matches.length ? matches.map(name => <button key={name} onClick={() => { choose(name); setOpen(false) }}><span>{name}</span>{name === hospital && <Check size={14} />}</button>) : <p>Ничего не найдено</p>}</div></div>}
  </div>
}

function FilterBar({ filters, setFilters, bootstrap }: { filters: Filters; setFilters: (value: Filters) => void; bootstrap: Bootstrap }) {
  const set = (field: keyof Filters, value: string) => {
    const next = { ...filters, [field]: value }
    if (field === 'start' && value > next.end) next.end = value
    if (field === 'end' && value < next.start) next.start = value
    setFilters(next)
  }
  const reset = () => setFilters({ start: bootstrap.period.start, end: bootstrap.period.end, region: '', profile: '' })
  return <div className="filter-bar">
    <div className="filter-intro"><span className="filter-icon"><CalendarDays size={18} /></span><span>Период<br /><strong>регистрации</strong></span></div>
    <label>С <input type="date" min={bootstrap.period.start} max={bootstrap.period.end} value={filters.start} onChange={event => set('start', event.target.value)} /></label>
    <label>По <input type="date" min={bootstrap.period.start} max={bootstrap.period.end} value={filters.end} onChange={event => set('end', event.target.value)} /></label>
    <label className="filter-select">Регион происхождения <select value={filters.region} onChange={event => set('region', event.target.value)}><option value="">Все регионы</option>{bootstrap.regions.map(region => <option key={region} value={region}>{region}</option>)}</select></label>
    <label className="filter-select">Профиль <select value={filters.profile} onChange={event => set('profile', event.target.value)}><option value="">Все профили</option>{bootstrap.profiles.map(profile => <option key={profile} value={profile}>{profile}</option>)}</select></label>
    <button className="reset-button" onClick={reset} title="Сбросить фильтры" aria-label="Сбросить фильтры"><X size={17} /><span>Сбросить</span></button>
  </div>
}

function HospitalRow({ row, onOpen }: { row: MetricRow; onOpen: (hospital: string) => void }) {
  return <button className="hospital-row" onClick={() => onOpen(row.organization_or_region)}>
    <span className="hospital-cell name-cell"><span className="hospital-avatar"><Building2 size={17} /></span><span>{row.organization_or_region}</span></span>
    <span className="hospital-cell numeric-cell" data-label="Направления">{number(row.referrals)}</span>
    <span className="hospital-cell numeric-cell" data-label="Ожидание">{decimal(row.median_wait_days)} <small>дн.</small></span>
    <span className="hospital-cell numeric-cell">{decimal(row.refusal_share_pct)}<small>%</small></span>
    <ChevronRight size={17} className="row-chevron" />
  </button>
}

function OverviewPage({ mode, hospital, filters, openHospital, go }: { mode: Mode; hospital: string; filters: Filters; openHospital: (name: string) => void; go: (view: View) => void }) {
  const params = query({ ...filters, hospital: mode === 'hospital' ? hospital : '' })
  const { data, loading, error } = useRemote<Overview>(`/overview${params}`)
  const top = useRemote<{ items: MetricRow[] }>(mode === 'government' ? `/hospitals${query({ ...filters, limit: 5 })}` : null)
  const title = mode === 'hospital' ? 'Ваша больница в цифрах' : 'Обзор госпитального потока'
  return <>
    <PageHeading eyebrow={mode === 'hospital' ? 'РАБОЧЕЕ МЕСТО БОЛЬНИЦЫ' : 'НАЦИОНАЛЬНЫЙ ОБЗОР'} title={title} description={mode === 'hospital' ? hospital : 'Направления, наблюдаемое ожидание и изменения активности за выбранный период.'} action={<span className="heading-badge"><span /> Исторические данные</span>} />
    {loading && <Loading />}{error && <ErrorState message={error} />}
    {data && data.stats.referrals === 0 && <EmptyState title="По этим фильтрам записей нет" text="Выберите другой профиль или сбросьте фильтры над обзором." />}
    {data && data.stats.referrals > 0 && <>
      <div className="metrics-grid">
        <MetricCard label="Направления" value={number(data.stats.referrals)} note="Зарегистрировано за период" icon={Activity} tone="accent" />
        <MetricCard label="Стационары" value={number(data.stats.hospitals)} note="С направлениями в выборке" icon={Building2} />
        <MetricCard label="Медиана ожидания" value={decimal(data.stats.median_wait)} suffix="дня" note={data.stats.median_wait == null ? `Недостаточно допустимых случаев: ${number(data.stats.eligible)} из ${data.metric_minimum}` : `По ${number(data.stats.eligible)} допустимым завершённым случаям`} icon={Clock3} />
        <MetricCard label="Госпитализации" value={number(data.stats.hospitalized)} note="С известным исходом" icon={TrendingUp} />
      </div>
      <div className="main-grid">
        <section className="panel trend-panel"><div className="panel-heading"><div><span className="section-kicker">ДИНАМИКА</span><h2>Поступление направлений</h2><p>По полным неделям регистрации в выбранной выборке</p></div><span className="legend"><i /> Направления</span></div><WeeklyTrend rows={data.trend} /></section>
        <section className="panel attention-panel"><div className="panel-heading"><div><span className="section-kicker">ИЗМЕНЕНИЯ</span><h2>Что посмотреть</h2><p>Последние два полных периода по 7 дней</p></div></div>
          {data.attention.length ? <div className="attention-list">{data.attention.map(item => <button key={item.hospital} onClick={() => openHospital(item.hospital)} className="attention-item" title={item.hospital}>
            <span className="attention-arrow"><ArrowUpRight size={17} /></span>
            <span className="attention-text"><strong>{item.hospital}</strong><span className="attention-meta"><small>{number(item.previous)} → {number(item.current)} направлений</small><b>+{decimal(item.change_pct, 0)}%</b></span></span>
          </button>)}</div> : <div className="quiet-state">За этот период нет роста с достаточным числом наблюдений.</div>}
          <div className="panel-footnote">Рост записанного потока — повод проверить данные и ситуацию, а не оценка занятости коек.</div>
        </section>
      </div>
      <div className="bottom-grid">
        <OutcomeBreakdown stats={data.stats} />
        {mode === 'government' ? <section className="panel top-panel"><div className="panel-heading"><div><span className="section-kicker">ОРГАНИЗАЦИИ</span><h2>Стационары по объёму</h2></div><button className="text-button" onClick={() => go('hospitals')}>Все стационары <ArrowRight size={16} /></button></div>
          {top.data?.items.map(row => <button className="top-hospital" key={row.organization_or_region} onClick={() => openHospital(row.organization_or_region)}><span>{row.organization_or_region}</span><strong>{number(row.referrals)}</strong><ChevronRight size={16} /></button>)}
        </section> : <section className="panel next-panel"><span className="section-kicker">СЛЕДУЮЩИЙ ШАГ</span><h2>Посмотрите детали больницы</h2><p>Профили направлений, наблюдаемое ожидание и прогноз входящего потока находятся в одной карточке.</p><button className="primary-button" onClick={() => openHospital(hospital)}>Открыть карточку <ArrowRight size={17} /></button></section>}
      </div>
    </>}
  </>
}

function HospitalsPage({ filters, openHospital }: { filters: Filters; openHospital: (name: string) => void }) {
  const [search, setSearch] = useState('')
  const [debounced, setDebounced] = useState('')
  const [offset, setOffset] = useState(0)
  useEffect(() => { const id = window.setTimeout(() => setDebounced(search), 220); return () => window.clearTimeout(id) }, [search])
  useEffect(() => setOffset(0), [filters, debounced])
  const pageSize = 50
  const { data, loading, error } = useRemote<{ items: MetricRow[]; total: number }>(`/hospitals${query({ ...filters, search: debounced, limit: pageSize, offset })}`)
  return <><PageHeading eyebrow="СТАЦИОНАРЫ" title="Найдите нужную больницу" description="Откройте организацию, чтобы увидеть её профиль, исходы и прогноз." />
    <section className="panel directory-panel"><div className="directory-toolbar"><div className="search-field"><Search size={18} /><input value={search} onChange={event => { setSearch(event.target.value); setOffset(0) }} placeholder="Название стационара" aria-label="Поиск стационара" />{search && <button onClick={() => { setSearch(''); setOffset(0) }} aria-label="Очистить поиск"><X size={16} /></button>}</div><span className="result-count">{data ? organizations(data.total) : 'Поиск'}</span></div>
      {(filters.region || filters.profile) && <div className="directory-filter-note">Список ограничен фильтрами: {[filters.region, filters.profile].filter(Boolean).join(' · ')}. Сбросить их можно кнопкой выше.</div>}
      <div className="table-head hospital-table-head"><span>Стационар</span><span>Направления</span><span>Ожидание</span><span>Отказы</span><span /></div>
      {loading && <Loading />}{error && <ErrorState message={error} />}
      {data && (data.items.length ? <>{data.items.map(row => <HospitalRow key={row.organization_or_region} row={row} onOpen={openHospital} />)}<div className="directory-pagination"><span>Показаны {offset + 1}–{offset + data.items.length} из {data.total}</span><div><button disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - pageSize))}>Назад</button><button disabled={offset + pageSize >= data.total} onClick={() => setOffset(offset + pageSize)}>Далее</button></div></div></> : <EmptyState title="Стационары не найдены" text="Попробуйте другое название или сбросьте фильтры." />)}
    </section><p className="page-note">Медиана показана только при достаточном числе завершённых госпитализаций. Доля отказов считается среди известных исходов.</p>
  </>
}

function HospitalPage({ hospital, filters, mode, go, compare, inspect }: { hospital: string; filters: Filters; mode: Mode; go: (view: View) => void; compare: () => void; inspect: (view: 'signals' | 'quality') => void }) {
  const detail = useRemote<HospitalDetail>(hospital ? `/hospital/overview${query({ ...filters, hospital })}` : null)
  const trend = useRemote<Overview>(hospital ? `/overview${query({ ...filters, hospital })}` : null)
  const stats = detail.data?.stats
  return <>{mode === 'government' && <button className="back-link" onClick={() => go('hospitals')}><ArrowLeft size={16} /> К списку стационаров</button>}
    <PageHeading eyebrow="КАРТОЧКА СТАЦИОНАРА" title={hospital} description="Наблюдаемые показатели по выбранному периоду и профилю." action={<div className="heading-actions">{mode === 'government' && <button className="secondary-button" onClick={compare}>Сравнить</button>}<button className="secondary-button" onClick={() => go('forecasts')}>Открыть прогноз <ArrowRight size={16} /></button></div>} />
    {(detail.loading || trend.loading) && <Loading />}{detail.error && <ErrorState message={detail.error} />}{trend.error && <ErrorState message={trend.error} />}
    {detail.data && !stats && <EmptyState title="Нет записей для выбранных фильтров" text="Измените период, регион или профиль, чтобы увидеть показатели стационара." />}
    {stats && <><div className="metrics-grid"><MetricCard label="Направления" value={number(stats.referrals)} note="За выбранный период" icon={Activity} tone="accent" /><MetricCard label="Медиана ожидания" value={decimal(stats.median_wait_days)} suffix="дня" note="По завершённым случаям" icon={Clock3} /><MetricCard label="90% ожидали до" value={decimal(stats.p90_wait_days)} suffix="дня" note="Наблюдаемый P90" icon={TrendingUp} /><MetricCard label="Доля отказов" value={decimal(stats.refusal_share_pct)} suffix="%" note="Среди известных исходов" icon={Info} /></div>
      <div className="main-grid hospital-main"><section className="panel"><div className="panel-heading"><div><span className="section-kicker">ПОСТУПЛЕНИЕ</span><h2>Направления по неделям</h2><p>История выбранного стационара</p></div></div>{trend.data && <WeeklyTrend rows={trend.data.trend} />}</section>
        <section className="panel"><div className="panel-heading"><div><span className="section-kicker">ПРОФИЛИ</span><h2>Что поступает чаще</h2><p>Восемь наиболее частых профилей</p></div></div><div className="profile-list">{(detail.data?.profiles ?? []).map(profile => <div className="profile-row" key={profile.profile}><span>{profile.profile === '__MISSING__' ? 'Не указан' : profile.profile}</span><strong>{number(profile.referrals)}</strong></div>)}</div></section>
      </div>
      <section className="panel pathway-panel"><div><span className="section-kicker">ПРОГНОЗ</span><h2>Что ожидается дальше?</h2><p>Для этого стационара можно посмотреть прогноз входящих направлений на семь дней после последней даты в данных.</p></div><button className="primary-button" onClick={() => go('forecasts')}>Показать прогноз <ArrowRight size={17} /></button></section>
      <div className="workspace-actions"><button className="secondary-button" onClick={() => inspect('signals')}>Сигналы этой больницы <Activity size={16} /></button><button className="secondary-button" onClick={() => inspect('quality')}>Качество данных <ShieldCheck size={16} /></button></div>
      <p className="page-note">Медиана и P90 показываются от {detail.data?.metric_minimum} допустимых завершённых случаев; доля отказов — от {detail.data?.metric_minimum} известных исходов. Прочерк означает недостаток данных. P90 — наблюдённый срок у 90% завершённых случаев, а не доверительный интервал. Фильтры выше не меняют обученную модель прогноза.</p>
      <BriefingPanel filters={filters} hospitals={[hospital]} minimum={detail.data?.metric_minimum ?? 10} />
    </>}
  </>
}

function ComparePage({ filters, openHospital, focus }: { filters: Filters; openHospital: (name: string) => void; focus: string }) {
  const [search, setSearch] = useState('')
  const [debounced, setDebounced] = useState('')
  useEffect(() => { const id = window.setTimeout(() => setDebounced(search), 220); return () => window.clearTimeout(id) }, [search])
  const [selected, setSelected] = useState<string[]>(focus ? [focus] : [])
  const { data, loading, error } = useRemote<{ items: MetricRow[]; total: number }>(`/compare${query({ ...filters, minimum: 30, search: debounced, selected: selected.join('|') })}`)
  useEffect(() => { if (data?.items.length && !selected.length) setSelected(data.items.slice(0, 3).map(item => item.organization_or_region)) }, [data, selected.length])
  const chosen = data?.items.filter(item => selected.includes(item.organization_or_region)) ?? []
  const maxWait = Math.max(1, ...chosen.map(item => item.median_wait_days ?? 0))
  const toggle = (name: string) => setSelected(previous => previous.includes(name) ? previous.filter(item => item !== name) : previous.length < 3 ? [...previous, name] : previous)
  return <><PageHeading eyebrow="СРАВНЕНИЕ" title="Сопоставьте стационары" description="Выберите до трёх организаций за один период и с одинаковыми фильтрами." />
    {loading && <Loading />}{error && <ErrorState message={error} />}
    {data && <div className="compare-layout"><section className="panel compare-picker"><div className="panel-heading"><div><span className="section-kicker">ВЫБОР</span><h2>Организации</h2><p>До трёх стационаров</p></div><span className="selection-count">{selected.length} / 3</span></div><div className="search-field compare-search"><Search size={16} /><input value={search} onChange={event => setSearch(event.target.value)} placeholder="Найти организацию" aria-label="Найти организацию для сравнения" /></div><div className="compare-options">{data.items.slice(0, 18).map(item => <label className="compare-option" key={item.organization_or_region}><input type="checkbox" checked={selected.includes(item.organization_or_region)} disabled={!selected.includes(item.organization_or_region) && selected.length >= 3} onChange={() => toggle(item.organization_or_region)} /><span className="custom-check"><Check size={13} /></span><span>{item.organization_or_region}</span></label>)}</div></section>
      <section className="panel compare-results"><div className="panel-heading"><div><span className="section-kicker">ОДИН ПЕРИОД · ОДИН КОНТЕКСТ</span><h2>Наблюдаемое ожидание</h2><p>Медиана по завершённым госпитализациям</p></div></div>
        {chosen.length ? <><div className="compare-bars">{chosen.map((item, index) => <div className="compare-bar-row" key={item.organization_or_region}><div className="compare-name"><b>{String.fromCharCode(65 + index)}</b><span>{item.organization_or_region}</span></div><div className="compare-track"><i style={{ width: `${(item.median_wait_days ?? 0) / maxWait * 100}%` }} /></div><strong>{decimal(item.median_wait_days)} дн.</strong></div>)}</div>
          <div className="compare-cards">{chosen.map((item, index) => <button className="compare-card" key={item.organization_or_region} onClick={() => openHospital(item.organization_or_region)}><span>Стационар {String.fromCharCode(65 + index)} <ArrowUpRight size={15} /></span><strong>{number(item.referrals)}</strong><small>направлений · отказы {decimal(item.refusal_share_pct)}%</small></button>)}</div></> : <EmptyState title="Выберите стационары" text="Отметьте от одной до трёх организаций слева." />}
      </section></div>}
    <p className="page-note">Сравнение описывает данные, но не учитывает сложность случаев и коечную мощность. Оно не является рейтингом качества больниц.</p>
    {data && selected.some(name => !chosen.some(row => row.organization_or_region === name)) && <div className="workspace-note"><Info size={18} /><span>Часть выбранных организаций не проходит текущие фильтры или минимум 30 направлений. В сводку войдут только видимые результаты.</span><button className="text-button" onClick={() => setSelected(chosen.map(row => row.organization_or_region))}>Снять скрытый выбор</button></div>}
    {data && <BriefingPanel filters={filters} hospitals={chosen.map(row => row.organization_or_region)} />}
  </>
}

function FlowForecast({ hospital }: { hospital: string }) {
  const { data, loading, error } = useRemote<Forecast>(hospital ? `/hospital/forecast${query({ hospital })}` : null)
  const rows = useMemo(() => data ? [...data.history.map(row => ({ date: row.date, value: row.referrals })), ...data.forecast.map(row => ({ date: row.date, value: row.predicted_referrals }))] : [], [data])
  return <>{loading && <Loading label="Рассчитываем прогноз" />}{error && <ErrorState message={error} />}{data && <>
    <div className="forecast-summary"><div><span className="section-kicker">{day(data.forecast[0]?.date)} — {day(data.forecast.at(-1)?.date)}</span><h2>{number(data.total)} <small>направлений за 7 дней</small></h2><p>Прогноз после последнего наблюдения {day(data.history_end)}</p></div><StatusPill good={true}>Исторический прогноз</StatusPill></div>
    <section className="panel forecast-chart"><div className="panel-heading"><div><span className="section-kicker">ПОТОК НАПРАВЛЕНИЙ</span><h2>История и следующие семь дней</h2></div><div className="chart-legend"><span><i /> Наблюдения</span><span><i /> Прогноз</span></div></div><TrendChart rows={rows} forecastFrom={data.history.length} /><div className="forecast-note"><Info size={16} /> Прогноз показывает входящие направления, а не занятость коек или текущую очередь.</div></section>
    <div className="forecast-lower"><section className="panel"><span className="section-kicker">ПО ДНЯМ</span><h2>Детали прогноза</h2><div className="forecast-days">{data.forecast.map((row, index) => <div key={row.date}><span>{day(row.date)} <small>день {index + 1}</small></span><strong>{decimal(row.predicted_referrals)} <small>напр.</small></strong></div>)}</div></section><section className="panel quality-callout"><span className="section-kicker">ТОЧНОСТЬ МОДЕЛИ</span><StatusPill good={true}>Метрики актуальны</StatusPill><h2>{decimal(data.metrics.mae, 2)} <small>направления</small></h2><p>Средняя абсолютная ошибка на всём историческом тесте: на организацию в день. Ошибка первого дня горизонта: {decimal(data.metrics_by_horizon[0]?.mae, 2)}.</p><div className="quality-divider" /><span>Простой прогноз: {decimal(data.metrics.baseline_mae, 2)} направления</span><EvaluationCaption version={data.model_version} period={data.test_period} /></section></div>
  </>}</>
}

const WAIT_FIELDS = [
  ['icd10_ref_diag_code', 'Код диагноза направления'],
  ['bed_profile', 'Профиль койки'],
  ['territorial_type', 'Территориальный тип'],
  ['referral_purpose', 'Цель направления'],
  ['finance_source', 'Источник финансирования'],
] as const

const waitBasis = (method: string) => ({
  hospital_profile_median: 'История этой больницы и профиля',
  hospital_median: 'История этой больницы · все профили',
  profile_median: 'История профиля · разные больницы',
  global_median: 'Общая история завершённых госпитализаций',
  catboost: 'CatBoost · параметры направления',
}[method] ?? method)

function WaitEstimateCard({ result }: { result: WaitResult }) {
  return <section className="result-hero">
    <span className="section-kicker">ОЦЕНКА ОЖИДАНИЯ</span>
    <div className="result-number">{result.clipped ? '—' : result.prediction < 0.1 ? '<0,1' : decimal(result.prediction)} {!result.clipped && <span>дня</span>}</div>
    <h2>{result.clipped ? 'Оценка недоступна' : 'Типичное время ожидания'}</h2>
    <p>От регистрации направления до госпитализации, не оставшееся время в очереди.</p>
    <div className="result-reference">{waitBasis(result.method)}{result.support > 0 && <> · {number(result.support)} случаев</>}. {result.method !== 'catboost' && 'Это групповая медиана, не индивидуальный срок.'}</div>
    <div className="result-caveat">{result.group_quality ? <>Ошибка для этой больницы и профиля: {decimal(result.group_quality.mae, 1)} дня на {number(result.group_quality.observations)} более поздних случаях.</> : <>Общая ошибка на проверке: {decimal(result.mae, 2)} дня. Для этой группы отдельная ошибка не оценена.</>} Это не дата госпитализации.</div>
    <div className="result-caveat">Метрики актуальны · MAE на всём тесте: {decimal(result.mae, 2)} дня. Общая медиана обучающей выборки: MAE {decimal(result.baseline_mae, 2)} дня.<EvaluationCaption version={result.model_version} period={result.test_period} /></div>
  </section>
}

function WaitForecast({ hospital }: { hospital: string }) {
  const requestVersion = useRef(0)
  const [values, setValues] = useState<Record<string, string>>({})
  const { data, loading, error } = useRemote<WaitOptions>(hospital ? `/wait-options${query({ hospital, profile: values.bed_profile })}` : null)
  const [result, setResult] = useState<WaitResult | null>(null)
  const [busy, setBusy] = useState(false)
  const [submitError, setSubmitError] = useState('')
  useEffect(() => {
    if (!data) return
    setValues(previous => {
      const next: Record<string, string> = { registration_dt: previous.registration_dt || data.default_date }
      for (const [key] of WAIT_FIELDS) {
        const options = data.options[key] ?? []
        next[key] = options.includes(previous[key]) ? previous[key]
          : options.includes(data.example[key]) ? data.example[key] : options[0] ?? ''
      }
      return next
    })
    setResult(null)
  }, [data])
  useEffect(() => () => { requestVersion.current += 1 }, [])
  const setField = (field: string, value: string) => { requestVersion.current += 1; setBusy(false); setValues(previous => ({ ...previous, [field]: value })); setResult(null); setSubmitError('') }
  const submit = async (event: React.FormEvent) => {
    event.preventDefault()
    const version = ++requestVersion.current
    setBusy(true); setSubmitError(''); setResult(null)
    try {
      const response = await post<WaitResult>('/predictions/wait', { ...values, hospital_mo: hospital })
      if (requestVersion.current === version) setResult(response)
    }
    catch (error) { if (requestVersion.current === version) setSubmitError(error instanceof Error ? error.message : 'Не удалось рассчитать прогноз.') }
    finally { if (requestVersion.current === version) setBusy(false) }
  }
  return <>{loading && <Loading />}{error && <ErrorState message={error} />}{data && <div className="wait-layout"><section className="panel wait-form-panel"><span className="section-kicker">ПАРАМЕТРЫ ОЦЕНКИ</span><h2>Оценить типичное ожидание</h2><p>Выберите профиль направления. {data.method === 'catboost' ? 'Для редкой группы учитываются параметры направления.' : 'Оценка основана на завершённых случаях из обучающей истории.'}</p><form onSubmit={submit} className="wait-form">
    {WAIT_FIELDS.filter(([key]) => key === 'bed_profile' || data.method === 'catboost').map(([key, label]) => <label key={key}>{label}{key === 'icd10_ref_diag_code' ? <><input list="diagnosis-options" value={values[key] ?? ''} onChange={event => setField(key, event.target.value)} required /><datalist id="diagnosis-options">{data.options[key]?.map(value => <option key={value} value={value} />)}</datalist></> : <select value={values[key] ?? ''} onChange={event => setField(key, event.target.value)} required>{(data.options[key] ?? []).map(value => <option key={value} value={value}>{value}</option>)}</select>}</label>)}
    {data.method === 'catboost' && <label>Дата регистрации<input type="date" value={values.registration_dt ?? ''} min={data.min_date} max={data.default_date} onChange={event => setField('registration_dt', event.target.value)} required /></label>}
    <button className="primary-button full-button" disabled={busy || loading}>{busy ? 'Рассчитываем…' : 'Рассчитать ожидание'} <ArrowRight size={17} /></button>
    {submitError && <ErrorState message={submitError} />}
  </form></section><div className="wait-result-column">{result ? <><WaitEstimateCard result={result} />{result.contributions.length > 0 ? <section className="panel"><span className="section-kicker">ФАКТОРЫ CATBOOST</span><h2>Что повлияло на оценку</h2><div className="contribution-list">{result.contributions.slice(0, 6).map(item => <div key={item.feature}><span>{item.label}</span><strong className={item.contribution >= 0 ? 'positive' : 'negative'}>{item.contribution >= 0 ? '+' : ''}{decimal(item.contribution, 2)} дн.</strong></div>)}</div><p className="panel-footnote">Вклады показывают связи, найденные моделью, а не доказанные причины.</p></section> : <section className="panel"><span className="section-kicker">ОСНОВА ПРОГНОЗА</span><h2>{waitBasis(result.method)}</h2><p>Использованы только исходы, известные до {day(result.training_cutoff)} — более поздние случаи оставлены для проверки.</p><p className="panel-footnote">Диагноз, цель направления и дата не меняют групповую оценку. Для этого метода нет вкладов отдельных признаков.</p></section>}</> : <section className="result-placeholder"><span className="placeholder-icon"><Sparkles size={25} /></span><h2>Результат появится здесь</h2><p>Выберите профиль и нажмите «Рассчитать ожидание».</p><div className="placeholder-bottom"><Clock3 size={17} /> Историческая оценка по завершённым госпитализациям.</div></section>}</div></div>}
    {result?.group_quality && <div className="result-warning"><Info size={17} /><span>Для этой больницы и профиля ошибка на более поздних случаях: {decimal(result.group_quality.mae, 1)} дня ({number(result.group_quality.observations)} случаев). Качество отдельных групп может отличаться от общей ошибки.</span></div>}
  </>
}

function ForecastsPage({ hospital, go, canChoose }: { hospital: string; go: (view: View) => void; canChoose: boolean }) {
  const [tab, setTab] = useState<'flow' | 'wait'>('flow')
  return <><PageHeading eyebrow="ПРОГНОЗЫ" title="Что покажет модель" description={hospital ? `Стационар: ${hospital}` : 'Выберите стационар для прогноза.'} action={canChoose ? <button className="secondary-button" onClick={() => go('hospitals')}>Сменить стационар <ChevronDown size={16} /></button> : undefined} />
    <div className="tab-bar" role="tablist"><button role="tab" aria-selected={tab === 'flow'} className={tab === 'flow' ? 'active' : ''} onClick={() => setTab('flow')}><Activity size={17} /> Поток направлений</button><button role="tab" aria-selected={tab === 'wait'} className={tab === 'wait' ? 'active' : ''} onClick={() => setTab('wait')}><Clock3 size={17} /> Время ожидания</button></div>
    {hospital ? tab === 'flow' ? <FlowForecast hospital={hospital} /> : <WaitForecast key={hospital} hospital={hospital} /> : <EmptyState title="Стационар не выбран" text="Откройте список стационаров и выберите организацию." />}
    <p className="page-note">Оба прогноза построены по историческим данным. Они не назначают лечение и не изменяют очередь.</p>
    <div className="workspace-actions"><button className="secondary-button" onClick={() => go('validation')}>Проверка по периодам <ArrowRight size={16} /></button><button className="secondary-button" onClick={() => go('hospital')}>Карточка и PDF-сводка <ArrowRight size={16} /></button></div>
  </>
}

function DataPage() {
  const { data, loading, error } = useRemote<Methodology>('/methodology')
  return <><PageHeading eyebrow="МЕТОДОЛОГИЯ" title="Как читать показатели" description="Что означают цифры в кабинете и какие выводы можно из них делать." />
    <section className="panel limitations-panel"><span className="section-kicker">ТРИ ОСНОВНЫХ ПОНЯТИЯ</span><div className="limitations-grid"><div><b>Направления</b><p>Зарегистрированные направления в выбранном периоде. Динамика не показывает свободные койки или нагрузку на персонал.</p></div><div><b>Ожидание</b><p>Полный срок от регистрации до госпитализации среди завершённых случаев. Это не оставшееся время ожидания конкретного пациента.</p></div><div><b>Прогноз потока</b><p>Оценка новых направлений на семь дней после последней даты в истории. Прогноз не описывает сегодняшнюю очередь.</p></div></div></section>
    {loading && <Loading />}{error && <ErrorState message={error} />}{data && <div className="methodology-metrics"><ModelQuality name="Оценка ожидания" unit="дня" baseline="Общая медиана обучающей выборки" evidence={data.waiting} /><ModelQuality name="Прогноз потока" unit="напр. / организацию в день" baseline="Среднее предыдущих 7 дней" evidence={data.flow} /></div>}
    <p className="page-note">Данные относятся к январю–марту 2025 года. Сравнение не учитывает сложность случаев и мощность больниц. Модель помогает анализировать историю; решения принимает специалист.</p>
  </>
}

function Onboarding({ user, go }: { user: User; go: (view: View) => void }) {
  const key = `medflow-intro:${user.id}`
  const [visible, setVisible] = useState(() => localStorage.getItem(key) !== 'dismissed')
  if (!visible) return null
  return <section className="onboarding"><div><span className="section-kicker">С ЧЕГО НАЧАТЬ</span><h2>{user.role === 'hospital_analyst' ? 'Ваша больница — уже в кабинете' : 'Вся система — в вашем обзоре'}</h2><p>Посмотрите динамику направлений, откройте прогноз и узнайте, как читать показатели.</p><button className="text-button" onClick={() => go('data')}>Как устроена аналитика <ArrowRight size={15} /></button></div><button className="icon-button" aria-label="Скрыть подсказку" onClick={() => { localStorage.setItem(key, 'dismissed'); setVisible(false) }}><X size={16} /></button></section>
}

function Workspace({ user, logout }: { user: User; logout: () => Promise<void> }) {
  const boot = useRemote<Bootstrap>('/bootstrap')
  const mode: Mode = user.role === 'hospital_analyst' ? 'hospital' : 'government'
  const [route, setRoute] = useState(currentRoute)
  const [hospital, setHospital] = useState('')
  const [analysisHospital, setAnalysisHospital] = useState('')
  const [filters, setFilters] = useState<Filters>({ start: '', end: '', region: '', profile: '' })
  const [menuOpen, setMenuOpen] = useState(false)
  const [compareFocus, setCompareFocus] = useState('')

  useEffect(() => {
    const update = () => setRoute(currentRoute())
    window.addEventListener('hashchange', update)
    return () => window.removeEventListener('hashchange', update)
  }, [])
  useEffect(() => {
    if (!boot.data) return
    setFilters(previous => previous.start ? previous : { start: boot.data!.period.start, end: boot.data!.period.end, region: '', profile: '' })
    setHospital(previous => previous || (mode === 'hospital' ? user.hospital_name || '' : hospitalName(route.hospital || '') || boot.data!.featured_hospital))
  }, [boot.data, route.hospital])
  useEffect(() => { if (route.hospital && boot.data) { const name = hospitalName(route.hospital); if (name) setHospital(name) } }, [route.hospital, boot.data])

  const navigate = (view: View, name?: string) => {
    const next = view === 'hospital' ? `hospital/${hospitalId(name || hospital)}` : view
    if (window.location.hash === `#${next}`) setRoute(currentRoute())
    else window.location.hash = next
    setMenuOpen(false)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
  const openHospital = (name: string) => { setHospital(name); setAnalysisHospital(name); navigate('hospital', name) }
  const openForecast = (name: string) => { setHospital(name); setAnalysisHospital(name); navigate('forecasts') }
  const inspectHospital = (view: 'signals' | 'quality') => { setAnalysisHospital(hospital); navigate(view) }
  const openComparison = () => { setCompareFocus(hospital); navigate('compare') }
  const allowed = !(mode === 'hospital' && ['hospitals', 'compare'].includes(route.view)) && !(route.hospital && boot.data && !hospitalName(route.hospital))
  const activeView = route.view
  const title = NAV.find(item => item.id === activeView)?.label ?? 'Стационар'
  const visibleNav: NavItem[] = mode === 'hospital' ? NAV.flatMap(item => item.id === 'hospitals' ? [{ id: 'hospital' as View, label: 'Моя больница', icon: Building2 }] : item.id === 'compare' ? [] : [item]) : NAV
  const scopedHospital = mode === 'hospital' ? hospital : analysisHospital
  return <div className="app-shell">
    <aside className={`sidebar ${menuOpen ? 'sidebar-open' : ''}`}>
      <div className="brand"><div className="brand-mark"><Activity size={24} strokeWidth={2.3} /></div><div><strong>MedFlow<span>AI</span></strong><small>Госпитальная аналитика</small></div></div>
      <div className="sidebar-divider" aria-hidden="true" />
      <nav aria-label="Основная навигация">{visibleNav.map(item => { const Icon = item.icon; const active = activeView === item.id || (mode === 'government' && activeView === 'hospital' && item.id === 'hospitals'); return <button key={item.id} className={`nav-link ${active ? 'nav-active' : ''}`} onClick={() => item.id === 'hospital' ? openHospital(hospital) : navigate(item.id)}><Icon size={19} strokeWidth={1.8} /><span>{item.label}</span>{active && <span className="nav-indicator" />}</button> })}</nav>
      <div className="sidebar-bottom"><div className="sidebar-live"><span /> Локальное демо</div><p>Аналитика на исторических данных. Решения остаются за специалистами.</p><div className="sidebar-version">MEDFLOW AI · 2026</div></div>
    </aside>
    {menuOpen && <button className="mobile-overlay" onClick={() => setMenuOpen(false)} aria-label="Закрыть меню" />}
    <div className="workspace"><header className="topbar"><button className="mobile-menu icon-button" onClick={() => setMenuOpen(true)} aria-label="Открыть меню"><Menu size={22} /></button><div className="breadcrumbs"><span>MedFlow AI</span><ChevronRight size={15} /><strong>{activeView === 'hospital' ? 'Карточка стационара' : title}</strong></div><div className="topbar-actions"><span className="period-chip"><CalendarDays size={15} /> {boot.data ? `${shortDay(boot.data.period.start)} — ${shortDay(boot.data.period.end)}` : 'Данные'}</span><UserMenu user={user} logout={logout} /></div></header>
      {boot.loading ? <Loading /> : boot.error ? <div className="boot-error"><ErrorState message={boot.error} /><p>Проверьте, что API запущен и подготовленные данные находятся в папке проекта.</p></div> : boot.data && filters.start && <main className="content">
        {mode === 'hospital' && <div className="hospital-context"><Building2 size={18} /><div className="assigned-hospital"><span className="context-label">ВАША ОРГАНИЗАЦИЯ</span><strong>{user.hospital_name}</strong></div></div>}
        {mode === 'government' && activeView === 'forecasts' && <div className="hospital-context"><span className="context-label">Стационар</span><HospitalChooser hospital={hospital} hospitals={boot.data.hospitals} choose={setHospital} /></div>}
        {!allowed ? <EmptyState title="Нет доступа к этой странице" text="Выберите доступный раздел в меню. Данные других организаций закрыты." /> : <>
        {mode === 'government' && ['signals', 'quality'].includes(activeView) && <div className="hospital-context"><span className="context-label">Область анализа</span><HospitalChooser hospital={analysisHospital || 'Все стационары'} hospitals={['Все стационары', ...boot.data.hospitals]} choose={name => setAnalysisHospital(name === 'Все стационары' ? '' : name)} /></div>}
        {activeView === 'overview' && <Onboarding user={user} go={navigate} />}
        {['overview', 'hospitals', 'hospital', 'compare', 'signals', 'quality'].includes(activeView) && <FilterBar filters={filters} setFilters={setFilters} bootstrap={boot.data} />}
        {activeView === 'overview' && <OverviewPage mode={mode} hospital={hospital} filters={filters} openHospital={openHospital} go={navigate} />}
        {activeView === 'hospitals' && <HospitalsPage filters={filters} openHospital={openHospital} />}
        {activeView === 'hospital' && <HospitalPage hospital={hospital} filters={filters} mode={mode} go={navigate} compare={openComparison} inspect={inspectHospital} />}
        {activeView === 'compare' && <ComparePage filters={filters} openHospital={openHospital} focus={compareFocus} />}
        {activeView === 'forecasts' && <ForecastsPage hospital={hospital} go={navigate} canChoose={mode === 'government'} />}
        {activeView === 'signals' && <SignalsPage key={JSON.stringify([filters, scopedHospital])} filters={filters} hospital={scopedHospital} openHospital={openHospital} forecast={openForecast} quality={() => navigate('quality')} />}
        {activeView === 'quality' && <QualityPage filters={filters} hospital={scopedHospital} />}
        {activeView === 'validation' && <ValidationPage hospitalRole={mode === 'hospital'} />}
        {activeView === 'data' && <DataPage />}
        </>}
      </main>}
    </div>
  </div>
}

function App() {
  return <AuthGate>{(user, logout) => user.role === 'platform_admin' ? <div className="admin-shell"><header className="topbar"><strong>MedFlow AI · Администрирование</strong><UserMenu user={user} logout={logout} /></header><main className="content"><PageHeading eyebrow="АДМИНИСТРАТОР" title="Управление доступом" description="Учётные записи управляются локальным оператором. Аналитика доступна в отдельных кабинетах сотрудников." /><section className="panel"><h2>Команды оператора</h2><p>Список пользователей: <code>python -m scripts.auth users</code></p><p>Выдача и отзыв доступа: <code>python -m scripts.auth --help</code></p></section><DataPage /></main></div> : user.role === 'hospital_analyst' && !user.hospital_name ? <div className="auth-state"><h1>Доступ ещё не настроен</h1><p>Администратор должен назначить действующую организацию.</p><UserMenu user={user} logout={logout} /></div> : <Workspace user={user} logout={logout} />}</AuthGate>
}

export default App
