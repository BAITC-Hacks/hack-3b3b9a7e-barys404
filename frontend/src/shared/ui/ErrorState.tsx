import { Info } from 'lucide-react'
import { t } from '../lib/i18n'

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="message message-error">
      <Info size={18} />
      <span>{t(message)}</span>
    </div>
  )
}
