import { getLocale, t } from './i18n'

export const number = (value: number | null | undefined) =>
  value == null ? '—' : new Intl.NumberFormat(getLocale()).format(Math.round(value))

export const decimal = (value: number | null | undefined, digits = 1) =>
  value == null
    ? '—'
    : value > 0 && digits === 1 && value < 0.05
      ? `<${new Intl.NumberFormat(getLocale()).format(0.1)}`
      : new Intl.NumberFormat(getLocale(), {
          maximumFractionDigits: digits,
          minimumFractionDigits: digits,
        }).format(value)

export const organizations = (count: number) => {
  const plural = new Intl.PluralRules(getLocale()).select(count)
  const source =
    plural === 'one'
      ? '{count} организация'
      : plural === 'few'
        ? '{count} организации'
        : '{count} организаций'
  return t(source, { count: number(count) })
}

export const day = (value: string | undefined) =>
  value
    ? new Date(`${value.slice(0, 10)}T12:00:00`).toLocaleDateString(getLocale(), {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
      })
    : '—'

export const shortDay = (value: string | undefined) =>
  value
    ? new Date(`${value.slice(0, 10)}T12:00:00`).toLocaleDateString(getLocale(), {
        day: '2-digit',
        month: 'short',
      })
    : '—'
