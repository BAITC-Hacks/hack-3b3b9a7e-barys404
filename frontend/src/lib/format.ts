export const number = (value: number | null | undefined) =>
  value == null ? '—' : new Intl.NumberFormat('ru-RU').format(Math.round(value))

export const decimal = (value: number | null | undefined, digits = 1) =>
  value == null
    ? '—'
    : value > 0 && digits === 1 && value < 0.05
      ? '<0,1'
      : new Intl.NumberFormat('ru-RU', {
          maximumFractionDigits: digits,
          minimumFractionDigits: digits,
        }).format(value)

export const organizations = (count: number) =>
  `${number(count)} ${count % 10 === 1 && count % 100 !== 11 ? 'организация' : count % 10 >= 2 && count % 10 <= 4 && (count % 100 < 12 || count % 100 > 14) ? 'организации' : 'организаций'}`

export const day = (value: string | undefined) =>
  value
    ? new Date(`${value.slice(0, 10)}T12:00:00`).toLocaleDateString('ru-RU', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
      })
    : '—'

export const shortDay = (value: string | undefined) =>
  value
    ? new Date(`${value.slice(0, 10)}T12:00:00`).toLocaleDateString('ru-RU', {
        day: '2-digit',
        month: 'short',
      })
    : '—'
