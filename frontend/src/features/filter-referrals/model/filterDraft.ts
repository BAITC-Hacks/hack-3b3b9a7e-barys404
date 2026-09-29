import { type Filters } from '../../../shared/api/types'

/** Edit locally; committing the draft remains an explicit form submission. */
export function editFilterDraft(previous: Filters, field: keyof Filters, value: string): Filters {
  const next = { ...previous, [field]: value }
  if (value && field === 'start' && next.end && value > next.end) next.end = value
  if (value && field === 'end' && next.start && value < next.start) next.start = value
  return next
}

export function initialFilters(period: Pick<Filters, 'start' | 'end'>): Filters {
  return { start: period.start, end: period.end, region: '', profile: '' }
}
