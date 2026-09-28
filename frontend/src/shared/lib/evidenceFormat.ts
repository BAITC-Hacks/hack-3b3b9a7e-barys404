export const count = (value: number | null | undefined) =>
  value == null ? '—' : new Intl.NumberFormat('ru-RU').format(value)

export const metric = (value: number | null | undefined) =>
  value == null ? '—' : new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 2 }).format(value)

export const day = (value: string) =>
  new Date(`${value.slice(0, 10)}T12:00:00`).toLocaleDateString('ru-RU')
