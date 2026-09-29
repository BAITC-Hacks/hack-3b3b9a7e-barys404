import { t } from '../../../shared/lib/i18n'

export const WAIT_FIELDS = [
  ['icd10_ref_diag_code', 'Код диагноза направления'],
  ['bed_profile', 'Профиль койки'],
  ['territorial_type', 'Территориальный тип'],
  ['referral_purpose', 'Цель направления'],
  ['finance_source', 'Источник финансирования'],
] as const

export const waitBasis = (method: string) =>
  t(
    {
      hospital_profile_median: 'История этой больницы и профиля',
      hospital_median: 'История этой больницы · все профили',
      profile_median: 'История профиля · разные больницы',
      global_median: 'Общая история завершённых госпитализаций',
      catboost: 'CatBoost · параметры направления',
    }[method] ?? method,
  )
