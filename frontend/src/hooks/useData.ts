import { useEffect, useState } from 'react'
import { get } from '../api/client'
import { message } from '../lib/errors'

export function useData<T>(path: string) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState('')
  useEffect(() => {
    const controller = new AbortController()
    setData(null)
    setError('')
    get<T>(path, controller.signal)
      .then((value) => {
        if (!controller.signal.aborted) setData(value)
      })
      .catch((error) => {
        if (!controller.signal.aborted) setError(message(error))
      })
    return () => controller.abort()
  }, [path])
  return { data, error }
}
