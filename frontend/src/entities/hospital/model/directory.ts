import { onApiResponse, onPrivateReset, query as serializeQuery } from '../../../shared/api/client'
import type { Bootstrap } from '../../../shared/api/types'

// The private name → ID directory belongs to the hospital entity, not HTTP.
let hospitalIds: Record<string, string> = {}
onApiResponse((path, data) => {
  if (path === '/bootstrap') hospitalIds = (data as Bootstrap).hospital_ids
})
onPrivateReset(() => {
  hospitalIds = {}
})

export const hospitalId = (name: string) => hospitalIds[name] ?? '__unavailable__'
export const hospitalName = (id: string) =>
  Object.keys(hospitalIds).find((name) => hospitalIds[name] === id)

// Presentation only. Keep the region and other distinguishing suffixes; requests
// and selections always use the untouched legal name/ID.
export function hospitalDisplayName(name: string) {
  const shortened = name
    .replace(
      /^(?:(?:Государственное коммунальное|Коммунальное государственное) (?:казенное )?предприятие(?: на праве хозяйственного ведения)?|Акционерное общество|Корпоративный фонд|Товарищество с ограниченной ответственностью)\s+/iu,
      '',
    )
    .trim()
  return shortened || name
}
export function query(params: Record<string, string | number | undefined | null>) {
  const { hospital, ...values } = params
  return serializeQuery(
    hospital ? { ...values, hospital_id: hospitalId(String(hospital)) } : values,
  )
}
