import { Download } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { post, postPdf } from '../../../shared/api/client'
import { type BriefingInput, type BriefingPreview } from '../../../shared/api/types'
import { message } from '../../../shared/lib/errors'
import { ErrorBox } from '../../../shared/ui/ErrorBox'
import { BriefingReview } from './BriefingReview'

export function BriefingForm({ request }: { request: BriefingInput }) {
  const [preview, setPreview] = useState<BriefingPreview | null>(null)
  const [confirmed, setConfirmed] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const pending = useRef<AbortController | null>(null)
  useEffect(() => () => pending.current?.abort(), [])
  const run = async (download: boolean) => {
    pending.current?.abort()
    const controller = new AbortController()
    pending.current = controller
    setBusy(true)
    setError('')
    try {
      if (download && preview && confirmed) {
        const blob = await postPdf(
          '/briefings/pdf',
          { ...request, reviewed: true, review_token: preview.review_token },
          controller.signal,
        )
        if (controller.signal.aborted) return
        const url = URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = 'medflow_briefing.pdf'
        document.body.appendChild(link)
        link.click()
        link.remove()
        setTimeout(() => URL.revokeObjectURL(url), 1000)
      } else {
        setPreview(null)
        setConfirmed(false)
        const result = await post<BriefingPreview>('/briefings/preview', request, controller.signal)
        if (!controller.signal.aborted) setPreview(result)
      }
    } catch (reason) {
      if (!controller.signal.aborted) {
        setError(message(reason))
        setConfirmed(false)
        setPreview(null)
      }
    } finally {
      if (!controller.signal.aborted) setBusy(false)
    }
  }
  return (
    <>
      <div className="workspace-actions">
        <button
          className="secondary-button"
          disabled={busy}
          onClick={() => {
            void run(false)
          }}
        >
          {busy ? 'Подготовка…' : preview ? 'Обновить просмотр' : 'Подготовить просмотр'}
        </button>
      </div>
      <ErrorBox text={error} />
      {preview && <BriefingReview preview={preview} confirmed={confirmed} change={setConfirmed} />}
      <button
        className="primary-button"
        disabled={busy || !preview || !confirmed}
        onClick={() => {
          void run(true)
        }}
      >
        <Download size={17} /> Скачать PDF-сводку
      </button>
    </>
  )
}
