export type Filters = {
  start: string
  end: string
  region: string
  profile: string
}

export type MetricRow = {
  organization_or_region: string
  referrals: number
  hospitalized: number
  refused: number
  unresolved: number
  excluded_outcomes: number
  eligible_waits: number
  median_wait_days: number | null
  p90_wait_days: number | null
  refusal_share_pct: number | null
}

export type Bootstrap = {
  period: { start: string; end: string }
  regions: string[]
  profiles: string[]
  hospitals: string[]
  hospital_ids: Record<string, string>
  featured_hospital: string
}

export type Overview = {
  stats: {
    referrals: number
    hospitals: number
    hospitalized: number
    refused: number
    unresolved: number
    conflicting: number
    invalid_outcome: number
    eligible: number
    median_wait: number | null
  }
  metric_minimum: number
  trend: WeeklyPoint[]
  attention_period: { start?: string; end?: string; previous_start?: string; previous_end?: string }
  attention: { hospital: string; current: number; previous: number; change_pct: number }[]
}

export type WeeklyPoint = {
  week: string
  referrals: number
  period_start: string
  period_end: string
  days_in_period: number
  partial_week: boolean
}

export type EvaluationPeriod = { start: string; end: string }
export type ModelEvidence = {
  status: { available: boolean; stale: boolean; reason: string }
  model_version: string | null
  test_period: Partial<EvaluationPeriod>
  metrics: { mae: number; baseline_mae: number; rmse: number } | null
}
export type Methodology = { waiting: ModelEvidence; flow: ModelEvidence }

export type HospitalDetail = {
  hospital: string
  stats: MetricRow | null
  profiles: { profile: string; referrals: number; eligible: number; median_wait: number | null }[]
  metric_minimum: number
}

export type Forecast = {
  history: { date: string; referrals: number }[]
  forecast: { date: string; predicted_referrals: number }[]
  total: number
  history_end: string
  metrics: { mae: number; baseline_mae: number; improvement_pct: number }
  metrics_by_horizon: { horizon: number; mae: number; baseline_mae: number }[]
  model_version: string
  test_period: EvaluationPeriod
}

export type ModelInfo = {
  waiting: {
    status: { available: boolean; stale: boolean; reason: string }
    model_version: string | null
    metrics: { mae: number; rmse: number; baseline_mae: number; improvement_pct: number } | null
    test_period: { start: string; end: string }
    rows: { train: number; test: number }
  }
  flow: {
    status: { available: boolean; stale: boolean; reason: string }
    model_version: string | null
    metrics: { mae: number; rmse: number; baseline_mae: number; improvement_pct: number } | null
    history_end: string
    test_period: { start: string; end: string }
    metrics_by_horizon: { horizon: number; mae: number; baseline_mae: number }[]
  }
  data: {
    ready: boolean
    summary: Record<string, number | string>
    coverage: Record<string, { complete: boolean; file_count: number; expected_parts: number }>
    created_at: string
  }
}

export type WaitOptions = {
  options: Record<string, string[]>
  example: Record<string, string>
  default_date: string
  min_date: string
  method: string
  support: number
  mae: number
}

export type WaitResult = ({ clipped: true; prediction: null } | { clipped: false; prediction: number }) & {
  raw_prediction: number
  method: string
  support: number
  training_cutoff: string
  group_quality: { observations: number; mae: number } | null
  reference: { eligible: number; median_wait_days: number | null }
  mae: number
  tested_until: string
  contributions: { feature: string; label: string; contribution: number }[]
  model_version: string
  test_period: EvaluationPeriod
  baseline_mae: number
}

export function query(params: Record<string, string | number | undefined | null>) {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      search.set(key === 'hospital' ? 'hospital_id' : key, key === 'hospital' ? hospitalId(String(value)) : String(value))
    }
  }
  const suffix = search.toString()
  return suffix ? `?${suffix}` : ''
}

export type User = {
  id: string; login: string; display_name: string
  role: 'government_analyst' | 'hospital_analyst' | 'platform_admin'
  permissions: string[]; hospital_id: string | null; hospital_name: string | null
  must_change_password: boolean
}

export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message) }
}

let hospitalIds: Record<string, string> = {}
let generation = 0
const pending = new Set<AbortController>()
export const hospitalId = (name: string) => hospitalIds[name] ?? '__unavailable__'
export const hospitalName = (id: string) => Object.keys(hospitalIds).find(name => hospitalIds[name] === id)

export function clearPrivateData() {
  generation += 1
  hospitalIds = {}
  pending.forEach(controller => controller.abort())
  pending.clear()
}

async function request<T>(path: string, payload?: unknown, signal?: AbortSignal, format: 'json' | 'blob' = 'json'): Promise<T> {
  const version = generation
  const controller = new AbortController()
  const abort = () => controller.abort()
  signal?.addEventListener('abort', abort, { once: true })
  if (signal?.aborted) controller.abort()
  pending.add(controller)
  try {
    let headers: Record<string, string> = {}
    if (payload !== undefined) {
      const csrf = await get<{ token: string }>('/auth/csrf', controller.signal)
      headers = { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf.token }
    }
    const response = await fetch(`/api${path}`, {
      signal: controller.signal, credentials: 'same-origin', cache: 'no-store',
      method: payload === undefined ? 'GET' : 'POST', headers,
      body: payload === undefined ? undefined : JSON.stringify(payload),
    })
    const data = response.ok && format === 'blob' ? await response.blob() : await response.json().catch(() => null)
    if (version !== generation) throw new DOMException('Запрос отменён', 'AbortError')
    if (!response.ok) {
      if (response.status === 401 && !['/auth/login', '/auth/me'].includes(path)) window.dispatchEvent(new Event('session-expired'))
      throw new ApiError(response.status, typeof data?.detail === 'string' ? data.detail : 'Не удалось выполнить запрос. Повторите попытку.')
    }
    if (path === '/bootstrap') hospitalIds = data.hospital_ids
    return data as T
  } finally {
    pending.delete(controller)
    signal?.removeEventListener('abort', abort)
  }
}

export const get = <T>(path: string, signal?: AbortSignal) => request<T>(path, undefined, signal)
export function post<T>(path: string, payload: unknown, signal?: AbortSignal): Promise<T> {
  if (path === '/predictions/wait') {
    const { hospital_mo, ...values } = payload as Record<string, string>
    payload = { ...values, hospital_id: hospitalId(hospital_mo) }
  }
  return request<T>(path, payload, signal)
}

export const postPdf = (path: string, payload: unknown, signal?: AbortSignal) => request<Blob>(path, payload, signal, 'blob')

export type SignalFeed = {
  total: number; hospital_days: number; insufficient_history_days: number; history_window: number; minimum_history: number
  items: { hospital: string; date: string; history_days: number; reference_start: string; reference_end: string
    reasons: { kind: string; label: string; value: number; threshold: number }[] }[]
}
export type DataQuality = {
  stats: Overview['stats']; hospital: string | null; prepared_at: string
  sources: { category: string; file_count: number; expected_parts: number; complete: boolean; rows: number }[] | null
  preparation: Record<string, number | null> | null
}
export type ErrorMetrics = { mae: number; baseline_mae: number; rmse: number; improvement_pct: number | null; seasonal_baseline_mae: number | null; p90_absolute_error: number | null }
export type Validation = { available: false; reason: string } | {
  available: true; created_at: string; hospital: string | null; waiting_selection_overlap: boolean; minimum_group_size: number
  waiting: { pooled: ErrorMetrics; folds: (ErrorMetrics & { test_start: string; test_end: string })[] }
  forecast: { pooled: ErrorMetrics; folds: (ErrorMetrics & { test_start: string; test_end: string })[]; by_horizon: (ErrorMetrics & { horizon: number })[] }
  groups: { dimension: string; total: number; items: (ErrorMetrics & { name: string; observations: number })[] }
}
export type BriefingInput = { hospital_ids: string[]; start: string; end: string; region: string; profile: string; minimum: number; question: 'waiting' | 'flow' | 'refusals' }
export type BriefingPreview = {
  review_token: string
  snapshot: { filters: { start: string; end: string; region_origin_code?: string; bed_profile?: string }; minimum_group_size: number; review_question: string; aggregates: MetricRow[] }
  metrics: Record<string, { mae: number; baseline_mae: number; model_version: string; period: string }>
}
