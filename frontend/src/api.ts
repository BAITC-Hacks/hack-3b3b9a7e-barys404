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
  featured_hospital: string
  summary: { referral_records: number; hospitals: number; regions: number; target_eligible: number }
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
  trend: { week: string; referrals: number }[]
  attention_period: { start?: string; end?: string; previous_start?: string; previous_end?: string }
  attention: { hospital: string; current: number; previous: number; change_pct: number }[]
}

export type HospitalDetail = {
  hospital: string
  stats: MetricRow | null
  profiles: { profile: string; referrals: number; eligible: number; median_wait: number | null }[]
}

export type Forecast = {
  history: { date: string; referrals: number }[]
  forecast: { date: string; predicted_referrals: number }[]
  total: number
  history_end: string
  metrics: { mae: number; baseline_mae: number; improvement_pct: number }
  metrics_by_horizon: { horizon: number; mae: number; baseline_mae: number }[]
}

export type ModelInfo = {
  waiting: {
    status: { available: boolean; stale: boolean; reason: string }
    metrics: { mae: number; rmse: number; baseline_mae: number; improvement_pct: number }
    test_period: { start: string; end: string }
    rows: { train: number; test: number }
  }
  flow: {
    status: { available: boolean; stale: boolean; reason: string }
    metrics: { mae: number; rmse: number; baseline_mae: number; improvement_pct: number }
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
}

export function query(params: Record<string, string | number | undefined | null>) {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') search.set(key, String(value))
  }
  const suffix = search.toString()
  return suffix ? `?${suffix}` : ''
}

export async function get<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`/api${path}`, { signal })
  const data = await response.json().catch(() => null)
  if (!response.ok) throw new Error(typeof data?.detail === 'string' ? data.detail : 'Не удалось загрузить данные.')
  return data as T
}

export async function post<T>(path: string, payload: unknown): Promise<T> {
  const response = await fetch(`/api${path}`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
  })
  const data = await response.json().catch(() => null)
  if (!response.ok) throw new Error(typeof data?.detail === 'string' ? data.detail : 'Не удалось рассчитать прогноз.')
  return data as T
}
