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

export type WaitResult = (
  { clipped: true; prediction: null } | { clipped: false; prediction: number }
) & {
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

export type User = {
  id: string
  login: string
  display_name: string
  role: 'government_analyst' | 'hospital_analyst' | 'platform_admin'
  permissions: string[]
  hospital_id: string | null
  hospital_name: string | null
  must_change_password: boolean
}

export type AdminAccount = {
  id: string
  login: string
  display_name: string
  role: User['role']
  active: boolean
  hospital_id: string | null
  hospital_name: string | null
  organization_active: boolean
}

export type AdminAccounts = {
  items: AdminAccount[]
  total: number
  summary: { total: number; active: number; blocked: number }
}

export type BriefingInput = {
  hospital_ids: string[]
  start: string
  end: string
  region: string
  profile: string
  minimum: number
  question: 'waiting' | 'flow' | 'refusals'
}

export type BriefingPreview = {
  review_token: string
  snapshot: {
    filters: {
      start: string
      end: string
      region_origin_code?: string
      bed_profile?: string
    }
    minimum_group_size: number
    review_question: string
    aggregates: MetricRow[]
  }
  metrics: Record<
    string,
    {
      mae: number
      baseline_mae: number
      model_version: string
      period: string
    }
  >
}
