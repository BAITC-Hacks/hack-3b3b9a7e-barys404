import { useEffect, useState } from 'react'
import { get } from '../api/client'

export function useRemote<T>(path: string | null) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(Boolean(path))
  const [error, setError] = useState('')
  useEffect(() => {
    if (!path) {
      setData(null)
      setLoading(false)
      return
    }
    const controller = new AbortController()
    setData(null)
    setLoading(true)
    setError('')
    get<T>(path, controller.signal)
      .then((value) => {
        if (!controller.signal.aborted) setData(value)
      })
      .catch((error) => {
        if (error.name !== 'AbortError') setError(error.message)
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false)
      })
    return () => controller.abort()
  }, [path])
  return { data, loading, error }
}
