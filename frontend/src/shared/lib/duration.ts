export type DurationPart = { value: number | '<1'; unit: 'д' | 'ч' | 'мин' }

// Presentation only: the API and model continue to use fractional days.
export function durationParts(days: number | null | undefined): DurationPart[] {
  if (days == null || !Number.isFinite(days) || days < 0) return []
  if (days > 0 && days * 1440 < 1) return [{ value: '<1', unit: 'мин' }]

  const minutes = Math.round(days * 1440)
  if (minutes < 60) return [{ value: minutes, unit: 'мин' }]
  if (minutes < 1440) {
    const parts: DurationPart[] = [{ value: Math.floor(minutes / 60), unit: 'ч' }]
    if (minutes % 60) parts.push({ value: minutes % 60, unit: 'мин' })
    return parts
  }

  const hours = Math.round(minutes / 60)
  const parts: DurationPart[] = [{ value: Math.floor(hours / 24), unit: 'д' }]
  if (hours % 24) parts.push({ value: hours % 24, unit: 'ч' })
  return parts
}
