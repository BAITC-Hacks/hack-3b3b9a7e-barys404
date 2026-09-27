export const SOURCE_NAMES: Record<string, string> = {
  waiting: 'Ожидающие — связь с направлениями',
  referrals: 'Направления — основа когорты и моделей',
  refusals: 'Самостоятельная выгрузка отказов',
  treated: 'Самостоятельная выгрузка пролеченных случаев',
}

export const PREPARATION_NAMES: Record<string, string> = {
  waiting_exact_duplicates_removed: 'Удалено точных дублей ожидающих',
  referrals_exact_duplicates_removed: 'Удалено точных дублей направлений',
  referrals_conflicting_key_rows_excluded: 'Исключено строк направлений с конфликтующими ключами',
  unambiguous_matched_rows: 'Однозначно связано и включено в когорту',
  registration_date_mismatches: 'Несовпадения дат регистрации при соединении',
  referral_conflicting_keys: 'Конфликтующие ключи направлений',
}
