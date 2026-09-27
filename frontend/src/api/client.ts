export function query(params: Record<string, string | number | undefined | null>) {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      search.set(
        key === 'hospital' ? 'hospital_id' : key,
        key === 'hospital' ? hospitalId(String(value)) : String(value),
      )
    }
  }
  const suffix = search.toString()
  return suffix ? `?${suffix}` : ''
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message)
  }
}

let hospitalIds: Record<string, string> = {}

let generation = 0

const pending = new Set<AbortController>()

export const hospitalId = (name: string) => hospitalIds[name] ?? '__unavailable__'

export const hospitalName = (id: string) =>
  Object.keys(hospitalIds).find((name) => hospitalIds[name] === id)

export function clearPrivateData() {
  generation += 1
  hospitalIds = {}
  pending.forEach((controller) => controller.abort())
  pending.clear()
}

async function request<T>(
  path: string,
  payload?: unknown,
  signal?: AbortSignal,
  format: 'json' | 'blob' = 'json',
): Promise<T> {
  const version = generation
  const controller = new AbortController()
  const abort = () => controller.abort()
  signal?.addEventListener('abort', abort, { once: true })
  if (signal?.aborted) controller.abort()
  pending.add(controller)
  try {
    let headers: Record<string, string> = {}
    if (payload !== undefined) {
      const csrf = await get<{
        token: string
      }>('/auth/csrf', controller.signal)
      headers = { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf.token }
    }
    const response = await fetch(`/api${path}`, {
      signal: controller.signal,
      credentials: 'same-origin',
      cache: 'no-store',
      method: payload === undefined ? 'GET' : 'POST',
      headers,
      body: payload === undefined ? undefined : JSON.stringify(payload),
    })
    const data =
      response.ok && format === 'blob'
        ? await response.blob()
        : await response.json().catch(() => null)
    if (version !== generation) throw new DOMException('Запрос отменён', 'AbortError')
    if (!response.ok) {
      if (response.status === 401 && !['/auth/login', '/auth/me'].includes(path))
        window.dispatchEvent(new Event('session-expired'))
      throw new ApiError(
        response.status,
        typeof data?.detail === 'string'
          ? data.detail
          : 'Не удалось выполнить запрос. Повторите попытку.',
      )
    }
    if (path === '/bootstrap') hospitalIds = data.hospital_ids
    return data as T
  } finally {
    pending.delete(controller)
    signal?.removeEventListener('abort', abort)
  }
}

export const get = <T>(path: string, signal?: AbortSignal) => request<T>(path, undefined, signal)

export function post<T>(path: string, payload: unknown, signal?: AbortSignal): Promise<T> {
  if (path === '/predictions/wait') {
    const { hospital_mo, ...values } = payload as Record<string, string>
    payload = { ...values, hospital_id: hospitalId(hospital_mo) }
  }
  return request<T>(path, payload, signal)
}

export const postPdf = (path: string, payload: unknown, signal?: AbortSignal) =>
  request<Blob>(path, payload, signal, 'blob')
